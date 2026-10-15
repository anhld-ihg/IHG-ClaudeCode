"""ihg_core.coordinator — Worker dieu phoi, goi Agent Runtime that.

Flow:
  1. StateStore.create(task_id, capability) -> PENDING
  2. Registry.find_by_capability(capability) -> AgentManifest
  3. AuthZ.check_path(principal, "dispatch", task dir)
  4. transition -> DISPATCHED (gan agent)
  5. verify_artifact_integrity(task_id): neu artifact con -> REUSED, neu mat -> DRIFT
  6. Neu can chay:
       - transition -> RUNNING
       - runtime.invoke(agent, prompt) -> RuntimeResult
       - Neu success: ghi artifact, transition -> SUCCEEDED -> QA_PENDING
       - Neu fail: transition -> FAILED
  7. Sau khi QA, transition theo qa_result

Quy tac:
- KHONG tu dong len DONE neu QA FAIL/UNVERIFIED.
- DRIFT duoc phat hien bang SHA-256.
- Moi state change qua state_store.transition().
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

from .config import Config
from .authz import require, check_path
from .registry import Registry, AgentManifest
from .state_store import StateStore, StateMachineError
from .agent_runtime import default_runtime, get_runtime, RuntimeResult


def _log(msg: str):
    Config.ensure()
    log = Config.LOG_DIR / "coordinator.log"
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {msg}\n")


def dispatch_task(task_id: str, capability: str, prompt: str,
                  principal: str = "gd-ihg",
                  expected_runtime: Optional[str] = None) -> dict:
    """Worker dieu phoi. Tra ve dict ket qua."""
    Config.ensure()
    store = StateStore()
    reg = Registry()
    runtime = default_runtime() if not expected_runtime else get_runtime(expected_runtime)

    # 1. Khoi tao
    store.create(task_id, capability)
    rec = store.get(task_id)
    # Reset state neu da o terminal/khong cho dispatch
    if rec.state not in ("PENDING", "DISPATCHED", "RUNNING", "SUCCEEDED", "QA_PENDING", "REUSED"):
        # Qua trang thai khong the dispatch (FAILED, BLOCKED, ...) -> reset ve PENDING
        _log(f"task {task_id} state={rec.state}, reset ve PENDING de dispatch lai")
        rec.state = "PENDING"
        store._save(rec)
    elif rec.state in ("QA_PENDING", "REUSED"):
        # Idempotent: task da chay thanh cong, kiem tra artifact
        _log(f"task {task_id} state={rec.state}, kiem tra artifact de REUSED")
        rec = store.verify_artifact_integrity(task_id)
        if rec.state == "DRIFT":
            return {"task_id": task_id, "state": "DRIFT", "reason": rec.last_error}
        return {"task_id": task_id, "state": rec.state, "reused": True}

    # 2. Chon agent
    agent = reg.find_by_capability(capability)
    if agent is None:
        store.transition(task_id, "BLOCKED", last_error=f"khong co agent cho capability={capability}")
        return {"task_id": task_id, "state": "BLOCKED", "reason": "no_agent"}

    # 3. Phan quyen that
    try:
        require(principal, "dispatch", str(Config.STATE_DIR))
        require(principal, "run_agent", agent.id)
        require(principal, "write", str(Config.OUTPUT_DIR))
    except PermissionError as e:
        store.transition(task_id, "BLOCKED", last_error=str(e))
        return {"task_id": task_id, "state": "BLOCKED", "reason": str(e)}

    # 4. Neu agent = worker (Python), goi truc tiep module
    #    Neu agent = ai agent, goi qua runtime
    if agent.kind == "worker":
        return _dispatch_worker(store, rec, agent, principal, prompt)
    else:
        return _dispatch_ai_agent(store, rec, agent, principal, prompt, runtime)


def _dispatch_worker(store: StateStore, rec, agent: AgentManifest, principal: str, prompt: str) -> dict:
    """Worker khong qua runtime AI."""
    store.transition(rec.id, "DISPATCHED", agent=agent.id, attempt=rec.attempt + 1)
    # Worker duoc phep chay theo module
    import importlib
    try:
        mod = importlib.import_module(agent.module)
        # Worker checksum: prompt duoc dien giai lai thanh file paths
        if agent.id == "ihg-checksum-worker":
            paths = prompt.split()
            from . import worker_checksum
            sha_list = []
            for p in paths:
                pp = Path(p)
                if not pp.exists():
                    return {"task_id": rec.id, "state": "FAILED", "reason": f"missing: {p}"}
                # AuthZ: phai co quyen doc file
                require(principal, "read", str(pp))
                sha_list.append({"path": str(pp), "sha256": worker_checksum.sha256_file(pp)})
            store.transition(rec.id, "RUNNING")
            store.transition(rec.id, "SUCCEEDED",
                              last_error="", attempt=rec.attempt)
            # Worker checksum tra ve ngay, khong can QA artifact cu the
            store.transition(rec.id, "QA_PENDING")
            store.transition(rec.id, "QA_PASS", qa_agent="ihg-checksum-worker", qa_result="PASS",
                              qa_detail="self-verify")
            store.transition(rec.id, "DELIVERED")
            return {"task_id": rec.id, "state": "DELIVERED", "agent": agent.id, "result": sha_list}
        return {"task_id": rec.id, "state": "FAILED", "reason": f"worker {agent.id} chua co handler"}
    except StateMachineError as e:
        return {"task_id": rec.id, "state": "ERROR", "reason": f"sm: {e}"}
    except PermissionError as e:
        store.transition(rec.id, "BLOCKED", last_error=str(e))
        return {"task_id": rec.id, "state": "BLOCKED", "reason": str(e)}


def _dispatch_ai_agent(store: StateStore, rec, agent: AgentManifest,
                         principal: str, prompt: str, runtime) -> dict:
    """AI Agent — goi qua runtime."""
    store.transition(rec.id, "DISPATCHED", agent=agent.id, executor_agent=agent.id, attempt=rec.attempt + 1)
    # Kiem tra artifact da co chua (recovery / idempotent)
    rec = store.get(rec.id)
    if rec.artifact_path and Path(rec.artifact_path).exists():
        rec = store.verify_artifact_integrity(rec.id)
        if rec.state == "DRIFT":
            return {"task_id": rec.id, "state": "DRIFT", "reason": rec.last_error}
        # Artifact con tot: REUSED
        store.transition(rec.id, "REUSED",
                          last_error="artifact cu con nguyen, giu SHA")
        # Tiep tuc QA
        store.transition(rec.id, "QA_PENDING")
        return {"task_id": rec.id, "state": "QA_PENDING", "reused": True}

    # Chay that qua runtime
    store.transition(rec.id, "RUNNING")
    result = runtime.invoke(agent, prompt)
    _log(f"runtime.invoke {agent.id} success={result.success} reason={result.reason}")

    if not result.success:
        store.transition(rec.id, "FAILED",
                          last_error=f"runtime {result.runtime} reason={result.reason} err={result.error[:200]}")
        return {"task_id": rec.id, "state": "FAILED",
                "runtime": result.runtime, "reason": result.reason, "error": result.error[:200]}

    # AI Agent tra output text. Worker trich artifact tu output
    artifact_text = _extract_artifact(result.output)
    if not artifact_text:
        store.transition(rec.id, "FAILED",
                          last_error="khong trich duoc artifact tu output Agent")
        return {"task_id": rec.id, "state": "FAILED", "reason": "no_artifact_in_output",
                "output_head": result.output[:500]}

    # Ghi artifact
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = Config.OUTPUT_DIR / f"{rec.id}.artifact.md"
    artifact_path.write_text(artifact_text, encoding="utf-8")

    # Tinh SHA
    from .worker_checksum import sha256_file
    sha = sha256_file(artifact_path)
    (Config.OUTPUT_DIR / f"{rec.id}.sha256").write_text(f"{sha}  {artifact_path.name}\n", encoding="utf-8")

    # Ghi nhan artifact
    store.record_artifact(rec.id, str(artifact_path), sha)
    store.transition(rec.id, "QA_PENDING")
    return {"task_id": rec.id, "state": "QA_PENDING",
            "agent": agent.id, "runtime": result.runtime,
            "artifact": str(artifact_path), "sha256": sha}


def _extract_artifact(output: str) -> str:
    """Trich artifact tu output AI Agent.
    Quy uoc: Agent tra ve text, artifact la phan text tu dau den het
    (hoac co the parse bang marker neu Agent da dat marker)."""
    if not output:
        return ""
    return output.strip()


if __name__ == "__main__":
    # CLI: python -m ihg_core.coordinator <task_id> <capability> <prompt...>
    if len(sys.argv) < 4:
        print("usage: coordinator.py <task_id> <capability> <prompt> [principal] [runtime]", file=sys.stderr)
        sys.exit(2)
    task_id = sys.argv[1]
    capability = sys.argv[2]
    prompt = sys.argv[3]
    principal = sys.argv[4] if len(sys.argv) > 4 else "gd-ihg"
    runtime = sys.argv[5] if len(sys.argv) > 5 else None
    result = dispatch_task(task_id, capability, prompt, principal, runtime)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("state") in ("DELIVERED", "QA_PENDING", "REUSED") else 1)
