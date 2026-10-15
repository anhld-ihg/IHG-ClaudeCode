"""ihg_core.real_e2e_flow — Luong AI thật: Coordinator → IT Agent → QA Agent độc lập.

Muc dich (theo yêu cầu GĐ #7):
    1. Coordinator.dispatch_task() goi ihg-it agent qua runtime (gateway hoac claude-cli)
    2. IT Agent tra artifact (markdown)
    3. Coordinator goi ihg-qa agent (runtime rieng, prompt doc lap)
    4. QA Agent tra qa_result (PASS/FAIL/QA_UNVERIFIED)
    5. Ghi evidence: model, duration, input/output tokens, cost (neu co)

Tokens KHONG bao gio:
- In ra log
- Ghi vao file evidence (chi fingerprint)
- Truyen qua argv

Chi goi 1 luot, ko retry, ko loop, ko nhieu task (giam chi phi).
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
SRC = HERE.parent
sys.path.insert(0, str(SRC))

from .config import Config  # noqa: E402
from .state_store import StateStore  # noqa: E402
from .registry import Registry, AgentManifest  # noqa: E402
from .gateway_runtime import GatewayRuntime  # noqa: E402
from .agent_runtime import MockRuntime, RuntimeResult  # noqa: E402
from .coordinator import dispatch_task  # noqa: E402


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_qa_decision(output: str) -> dict:
    """Trich qa_result va qa_detail tu output cua QA Agent.
    Chap nhan nhieu format:
      - JSON: {"qa_result": "PASS", "qa_detail": "..."}
      - Text: "qa_result=PASS" hoac "PASS" don gian
    """
    if not output:
        return {"qa_result": "QA_UNVERIFIED", "qa_detail": "empty output"}

    # Thu 1: parse JSON
    m = re.search(r"\{[^{}]*\"qa_result\"[^{}]*\}", output, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group(0))
            return {
                "qa_result": d.get("qa_result", "QA_UNVERIFIED").upper(),
                "qa_detail": d.get("qa_detail", "")[:500],
            }
        except Exception:
            pass

    # Thu 2: regex
    m = re.search(r"qa_result\s*[:=]\s*\"?(PASS|FAIL|QA_UNVERIFIED)\"?", output, re.IGNORECASE)
    if m:
        return {"qa_result": m.group(1).upper(), "qa_detail": output[:500]}

    # Thu 3: chi tim PASS/FAIL trong 200 ky tu dau
    head = output[:200].upper()
    if "PASS" in head and "FAIL" not in head:
        return {"qa_result": "PASS", "qa_detail": "auto-detected in head"}
    if "FAIL" in head:
        return {"qa_result": "FAIL", "qa_detail": "auto-detected in head"}

    return {"qa_result": "QA_UNVERIFIED", "qa_detail": output[:500]}


def _hard_check_artifact(artifact_text: str) -> dict:
    """Checker cung (khong phai AI) — 4 check ky thuat, KHONG goi AI.

    Yêu cầu GĐ #2: QA doc lap voi 4 check ky thuat
    """
    issues = []
    if not artifact_text or len(artifact_text.strip()) < 20:
        issues.append("artifact qua ngan (<20 chars)")
    if "TODO" in artifact_text or "TBD" in artifact_text:
        issues.append("chua hoan thanh (TODO/TBD)")
    # Check no co it nhat 1 heading
    if not re.search(r"^#\s+", artifact_text, re.MULTILINE):
        issues.append("thieu heading (markdown)")
    # Check no co it nhat 50 chars noi dung (khong phai placeholder)
    meaningful = re.sub(r"[#*\s`\[\]]", "", artifact_text).strip()
    if len(meaningful) < 30:
        issues.append("noi dung qua it (placeholder?)")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "artifact_len": len(artifact_text),
        "heading_count": len(re.findall(r"^#+\s+", artifact_text, re.MULTILINE)),
    }


def run_real_e2e(
    capability: str = "code-run",
    test_prompt: str = None,
    evidence_dir: str = None,
) -> dict:
    """Chay e2e that.

    Returns: dict chua evidence (model, duration, tokens, cost, qa_result, ...).
    """
    Config.ensure()
    store = StateStore()
    reg = Registry()
    gateway = GatewayRuntime()
    cli_runtime = None

    # Agent (set truoc khi probe)
    it_agent = reg.find_by_capability(capability) or reg.get("ihg-it")
    qa_agent = reg.get("ihg-qa")
    if not it_agent or not qa_agent:
        return {"error": f"missing agent: it={it_agent}, qa={qa_agent}"}

    # Chon runtime (gateway > claude-cli > mock)
    if gateway.available():
        runtime_name = "gateway"
        runtime = gateway
        # Yeu cau GĐ: KHONG retry khi gateway tra ve loi xac thuc.
        # (GĐ: "Khong thu lien tuc khi gateway tra ve loi xac thuc")
        # GatewayRuntime._classify_error() KHONG dat 401/403 vao retryable list,
        # nen chi retry voi 429/5xx/timeout/network. -> 401 fail ngay lan dau.
    else:
        from .agent_runtime import ClaudeCliRuntime
        cli_runtime = ClaudeCliRuntime()
        if cli_runtime.available():
            # Claude CLI ton tai nhu co the chua login. Thu probe nhanh.
            try:
                probe = cli_runtime.invoke(it_agent, "ping")
                if probe and not probe.success and probe.reason == "cli_requires_login":
                    print("[NOTICE] Claude CLI chua login. Fallback mock. Neu muon dung that, thiet lap token gateway.", file=sys.stderr)
                    runtime_name = "mock"
                    runtime = MockRuntime()
                else:
                    runtime_name = "claude-cli"
                    runtime = cli_runtime
            except Exception:
                # Probe failed -> fallback
                runtime_name = "claude-cli"
                runtime = cli_runtime
        else:
            # Khong co runtime that -> fallback mock
            runtime_name = "mock"
            runtime = MockRuntime()
            # Nhac GĐ: neu gateway khong san sang, can setup token
            if not gateway.status().get("token_present"):
                print("[NOTICE] Gateway chua co token. Vao setup-token-vault.ps1 hoac dat ANTHROPIC_AUTH_TOKEN.", file=sys.stderr)

    # Prompt mac dinh: gia lap (KHONG dung data that)
    if not test_prompt:
        test_prompt = (
            "Viet 1 README.md ngan (200-300 tu) cho module IHG token vault. "
            "Bao gom: (1) Muc dich, (2) Cai dat (Windows Credential Manager), "
            "(3) Su dung (3 vi du), (4) Bao mat. "
            "Tra ve 1 file markdown hoan chinh."
        )

    # === Step 1: Coordinator dispatch IT Agent ===
    # Task_id unique: timestamp + uuid4 short de tranh collision khi chay nhieu lan trong 1s
    import uuid
    task_id = f"E2E-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    print(f"[1/4] Dispatch task_id={task_id} cap={capability} runtime={runtime_name}")
    print(f"      prompt_len={len(test_prompt)} chars")
    t0 = time.time()
    dispatch_result = dispatch_task(task_id, capability, test_prompt, "gd-ihg", runtime_name)
    t_dispatch = time.time() - t0
    print(f"      state={dispatch_result.get('state')} ({t_dispatch:.2f}s)")

    if dispatch_result.get("state") not in ("QA_PENDING", "REUSED"):
        return {
            "task_id": task_id,
            "phase": "dispatch",
            "runtime": runtime_name,
            "error": f"dispatch state={dispatch_result.get('state')}",
            "result": dispatch_result,
        }

    artifact_path = dispatch_result.get("artifact")
    if not artifact_path or not Path(artifact_path).exists():
        return {
            "task_id": task_id,
            "phase": "dispatch",
            "error": f"artifact missing: {artifact_path}",
            "result": dispatch_result,
        }
    artifact_text = Path(artifact_path).read_text(encoding="utf-8")
    artifact_sha = dispatch_result.get("sha256", "")

    # === Step 2: Independent QA Agent (prompt rieng, khong dung prompt cua IT) ===
    print(f"[2/4] QA Agent (doc lap) kiem tra artifact")
    qa_prompt = (
        f"Kiem tra san pham sau day (artifact). "
        f"Tra ve JSON: {{\"qa_result\": \"PASS|FAIL|QA_UNVERIFIED\", \"qa_detail\": \"<ly do ngan>\"}}\n\n"
        f"---\n{artifact_text[:3000]}\n---"
    )
    t1 = time.time()
    qa_result = runtime.invoke(qa_agent, qa_prompt)
    t_qa = time.time() - t1
    print(f"      success={qa_result.success} reason={qa_result.reason} ({t_qa:.2f}s)")

    if not qa_result.success:
        return {
            "task_id": task_id,
            "phase": "qa",
            "runtime": runtime_name,
            "error": f"QA runtime failed: {qa_result.reason} {qa_result.error[:200]}",
        }

    qa_decision = _extract_qa_decision(qa_result.output)
    print(f"      qa_result={qa_decision['qa_result']}")

    # === Step 3: Hard checker (4 check cung, KHONG goi AI) ===
    print(f"[3/4] Hard checker (4 check cung, khong AI)")
    hard = _hard_check_artifact(artifact_text)
    print(f"      passed={hard['passed']} issues={hard['issues']}")

    # QA Agent PASS nhung hard FAIL -> he thong khoa (safety net)
    if qa_decision["qa_result"] == "PASS" and not hard["passed"]:
        final = "FAIL"
        final_detail = f"QA Agent PASS nhung hard checker FAIL: {hard['issues']}"
    elif qa_decision["qa_result"] == "FAIL":
        final = "FAIL"
        final_detail = qa_decision.get("qa_detail", "QA FAIL")
    elif hard["passed"]:
        final = "PASS"
        final_detail = qa_decision.get("qa_detail", "all checks pass")
    else:
        final = "FAIL"
        final_detail = f"hard issues: {hard['issues']}"

    # === Step 4: Ghi evidence ===
    print(f"[4/4] Ghi evidence")
    it_usage = (dispatch_result.get("result", {}) or {}).get("usage", {}) if isinstance(dispatch_result, dict) else {}
    qa_usage = (qa_result.raw or {}).get("usage", {}) or {}
    it_model = (qa_result.raw or {}).get("model", it_agent.model or "unknown")

    evidence = {
        "evidence_id": f"E2E-EV-{int(time.time())}",
        "timestamp": _now_iso(),
        "task_id": task_id,
        "runtime": runtime_name,
        "runtime_status": runtime.status() if hasattr(runtime, "status") else {},
        "phases": {
            "dispatch": {
                "duration_s": round(t_dispatch, 2),
                "state": dispatch_result.get("state"),
                "agent": it_agent.id,
                "artifact": artifact_path,
                "artifact_sha256": artifact_sha,
                "artifact_len": len(artifact_text),
            },
            "qa": {
                "duration_s": round(t_qa, 2),
                "agent": qa_agent.id,
                "qa_decision": qa_decision,
                "model": (qa_result.raw or {}).get("model", "unknown"),
                "input_tokens": (qa_usage or {}).get("input_tokens", 0) or (qa_usage or {}).get("prompt_tokens", 0),
                "output_tokens": (qa_usage or {}).get("output_tokens", 0) or (qa_usage or {}).get("completion_tokens", 0),
            },
            "hard_check": hard,
        },
        "final_result": final,
        "final_detail": final_detail,
        "total_duration_s": round(t_dispatch + t_qa, 2),
    }

    # Ghi evidence file (KHONG co token)
    ev_dir = Path(evidence_dir) if evidence_dir else Config.STATE_DIR / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    ev_path = ev_dir / f"{evidence['evidence_id']}.json"
    ev_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"      evidence: {ev_path}")

    # Update state store
    try:
        if final == "PASS":
            store.transition(task_id, "QA_PASS",
                              qa_agent=qa_agent.id, qa_result="PASS",
                              qa_detail=final_detail[:200])
            store.transition(task_id, "DELIVERED")
        else:
            # FAIL -> chi chuyen ve FAILED, KHONG DELIVERED
            store.transition(task_id, "QA_FAIL",
                              qa_agent=qa_agent.id, qa_result="FAIL",
                              qa_detail=final_detail[:200])
            store.transition(task_id, "FAILED", last_error=final_detail[:200])
    except Exception as e:
        print(f"      [WARN] state: {e}")

    return evidence


def main(argv=None):
    p = argparse.ArgumentParser(description="IHG Real E2E Flow")
    p.add_argument("--capability", default="code-run")
    p.add_argument("--prompt", help="Prompt tuy chinh (mac dinh: prompt gia lap)")
    p.add_argument("--evidence-dir", help="Thu muc ghi evidence (mac dinh: state/evidence)")
    args = p.parse_args(argv)

    result = run_real_e2e(args.capability, args.prompt, args.evidence_dir)
    print()
    print("=== Evidence ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("final_result") == "PASS":
        return 0
    elif result.get("error"):
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
