"""ihg_core.qa_check — QA goi qua AI Agent ihg-qa that.

Khi runtime kha dung (Claude CLI login), ihg-qa that se review artifact.
Khi khong kha dung, ghi QA_UNVERIFIED va ghi ro ly do.

QA cung cap 4 check ky thuat (co the chay khi khong co AI):
  Q1. artifact ton tai, khong rong.
  Q2. SHA-256 khop expected.
  Q3. artifact co it nhat 1 dong noi dung co y nghia.
  Q4. state.task.state ∈ {SUCCEEDED, QA_PENDING, REUSED, DELIVERED}.

Neu Q1-Q4 PASS va runtime AI QA tra PASS -> overall PASS.
Neu Q1-Q4 PASS nhung runtime khong kha dung -> QA_UNVERIFIED (ky thuat OK, AI QA khong chay duoc).
Neu Q1-Q4 FAIL -> FAIL.
"""
import json
import hashlib
import sys
from pathlib import Path
from typing import Optional

from .config import Config
from .state_store import StateStore
from .registry import Registry
from .agent_runtime import default_runtime


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_qa(task_id: str, qa_agent_id: str = "ihg-qa",
           use_ai: bool = True, expected_runtime: Optional[str] = None) -> dict:
    """Chay QA. Tra ve dict: {overall, qa_agent, qa_result, qa_detail, checks: [...]}."""
    Config.ensure()
    store = StateStore()
    reg = Registry()
    task = store.get(task_id)
    if task is None:
        return {"overall": "FAIL", "qa_agent": qa_agent_id,
                "qa_result": "FAIL", "qa_detail": f"task {task_id} khong ton tai", "checks": []}

    checks = []
    # Q1
    if task.artifact_path and Path(task.artifact_path).exists() and Path(task.artifact_path).stat().st_size > 50:
        checks.append({"name": "Q1_artifact_exists", "ok": True, "detail": f"size={Path(task.artifact_path).stat().st_size}"})
    else:
        checks.append({"name": "Q1_artifact_exists", "ok": False, "detail": f"path={task.artifact_path}"})
    # Q2
    if task.artifact_path and Path(task.artifact_path).exists():
        actual = _sha256_file(Path(task.artifact_path))
        if actual == task.expected_sha256:
            checks.append({"name": "Q2_sha256_match", "ok": True, "detail": f"sha={actual[:16]}"})
        else:
            checks.append({"name": "Q2_sha256_match", "ok": False, "detail": f"actual={actual[:16]} expected={task.expected_sha256[:16]}"})
    else:
        checks.append({"name": "Q2_sha256_match", "ok": False, "detail": "khong co artifact"})
    # Q3
    if task.artifact_path and Path(task.artifact_path).exists():
        text = Path(task.artifact_path).read_text(encoding="utf-8")
        meaningful_lines = [l for l in text.splitlines() if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("|")]
        if len(meaningful_lines) >= 1:
            checks.append({"name": "Q3_meaningful_content", "ok": True, "detail": f"lines={len(meaningful_lines)}"})
        else:
            checks.append({"name": "Q3_meaningful_content", "ok": False, "detail": "khong co noi dung co y nghia"})
    else:
        checks.append({"name": "Q3_meaningful_content", "ok": False, "detail": "khong co artifact"})
    # Q4
    valid_states = {"SUCCEEDED", "QA_PENDING", "REUSED", "DELIVERED", "QA_PASS"}
    if task.state in valid_states:
        checks.append({"name": "Q4_state_valid", "ok": True, "detail": f"state={task.state}"})
    else:
        checks.append({"name": "Q4_state_valid", "ok": False, "detail": f"state={task.state} (khong hop le cho QA)"})

    tech_pass = all(c["ok"] for c in checks)

    # AI QA agent (neu use_ai va runtime kha dung)
    ai_result = None
    if use_ai and tech_pass:
        runtime = default_runtime() if not expected_runtime else None
        if expected_runtime:
            from .agent_runtime import get_runtime
            runtime = get_runtime(expected_runtime)
        if runtime and runtime.available() and runtime.name != "mock":
            qa_agent = reg.get(qa_agent_id)
            if qa_agent:
                # Chong tu xac nhan: QA agent phai khac executor agent
                if task.executor_agent and task.executor_agent == qa_agent_id:
                    ai_result = {
                        "runtime": runtime.name,
                        "success": False,
                        "output": "",
                        "error": f"QA agent == executor agent ({qa_agent_id}). Tu choi.",
                        "reason": "qa_self_verify_blocked",
                    }
                    qa_agent = None  # bo qua phan goi QA
            if qa_agent:
                # Tao prompt: mo ta artifact + checklist
                prompt = (
                    f"Kiem tra artifact cua task {task_id}.\n"
                    f"State: {task.state}\n"
                    f"Artifact: {task.artifact_path}\n"
                    f"Expected SHA256: {task.expected_sha256}\n\n"
                    f"Noi dung artifact:\n{Path(task.artifact_path).read_text(encoding='utf-8')[:2000]}\n\n"
                    f"Tra ve JSON: {{qa_result: 'PASS' hoac 'FAIL', detail: '...'}}\n"
                )
                rt_result = runtime.invoke(qa_agent, prompt)
                ai_result = {
                    "runtime": rt_result.runtime,
                    "success": rt_result.success,
                    "output": rt_result.output[:500] if rt_result.output else "",
                    "error": rt_result.error[:200] if rt_result.error else "",
                    "reason": rt_result.reason,
                }
                # Parse output JSON neu co
                if rt_result.success and rt_result.output:
                    try:
                        # Tim JSON trong output
                        out = rt_result.output
                        start = out.find("{")
                        end = out.rfind("}")
                        if start >= 0 and end > start:
                            data = json.loads(out[start:end+1])
                            ai_qa = data.get("qa_result", "PASS").upper()
                            if ai_qa in ("PASS", "FAIL", "UNVERIFIED"):
                                ai_result["parsed_qa_result"] = ai_qa
                                ai_result["parsed_detail"] = data.get("detail", "")
                    except Exception:
                        pass

    # Tong hop
    if not tech_pass:
        overall = "FAIL"
        qa_result = "FAIL"
        qa_detail = "ky thuat check that bai"
    elif ai_result and ai_result.get("success"):
        ai_qa = ai_result.get("parsed_qa_result", "FAIL")
        if ai_qa == "PASS":
            overall = "PASS"
            qa_result = "PASS"
            qa_detail = f"AI QA {ai_result['runtime']} PASS. {ai_result.get('parsed_detail', '')[:200]}"
        else:
            overall = "FAIL"
            qa_result = "FAIL"
            qa_detail = f"AI QA {ai_result['runtime']} {ai_qa}. {ai_result.get('parsed_detail', '')[:200]}"
    elif ai_result:
        overall = "QA_UNVERIFIED"
        qa_result = "QA_UNVERIFIED"
        qa_detail = f"AI QA runtime {ai_result['runtime']} khong kha dung (reason={ai_result['reason']}). Ky thuat OK nhung AI QA khong chay."
    else:
        overall = "QA_UNVERIFIED"
        qa_result = "QA_UNVERIFIED"
        qa_detail = "khong goi AI QA (use_ai=False). Ky thuat OK."

    # Cap nhat state
    if overall == "PASS":
        store.transition(task_id, "QA_PASS", qa_agent=qa_agent_id, qa_result="PASS", qa_detail=qa_detail[:500])
        store.transition(task_id, "DELIVERED")
    elif overall == "FAIL":
        store.transition(task_id, "QA_FAIL", qa_agent=qa_agent_id, qa_result="FAIL", qa_detail=qa_detail[:500])
    else:  # QA_UNVERIFIED
        store.transition(task_id, "QA_UNVERIFIED", qa_agent=qa_agent_id, qa_result="QA_UNVERIFIED", qa_detail=qa_detail[:500])

    return {
        "task_id": task_id,
        "qa_agent": qa_agent_id,
        "qa_result": qa_result,
        "qa_detail": qa_detail,
        "overall": overall,
        "checks": checks,
        "ai_qa_attempt": ai_result,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: qa_check.py <task_id> [qa_agent_id] [use_ai:0|1] [runtime]")
        sys.exit(2)
    task_id = sys.argv[1]
    qa_agent = sys.argv[2] if len(sys.argv) > 2 else "ihg-qa"
    use_ai = (sys.argv[3] != "0") if len(sys.argv) > 3 else True
    runtime = sys.argv[4] if len(sys.argv) > 4 else None
    result = run_qa(task_id, qa_agent, use_ai, runtime)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["overall"] in ("PASS", "QA_UNVERIFIED") else 1)
