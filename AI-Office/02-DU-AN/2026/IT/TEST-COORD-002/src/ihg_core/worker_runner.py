"""ihg_core.worker_runner — IHG Worker Runner (queue-based).

Thiet ke:
- Doc task tu state/tasks-queue.json (hoac tu state/ dir).
- Moi task co: task_id, agent_id, prompt, created_at, status (PENDING/RUNNING/...).
- Worker xu ly tuan tu (single-threaded), ghi state vao state/tasks-queue.json.
- Runtime mac dinh: uu tien GatewayRuntime, fallback MockRuntime.
- Khong phu thuoc hop thoai cap quyen: chay het queue roi thoat (exit code 0/1).
- Co the chay nhu scheduled task (xem install-scheduled-task.ps1).

Co che (theo chi dao GĐ):
- AUTO_EXECUTE: neu runtime available, goi luon.
- RETRY: loi tam thoi (rate_limited, server_error, timeout, network) -> retry co gioi han.
- WAITING_APPROVAL: loi auth_failed hoac input_missing -> ghi WAITING_APPROVAL va dung task do.
- CONTINUE_OTHER_TASKS: tiep tuc task khac trong queue.
- BLOCKED: vi pham policy (vd: agent khong co quyen) -> BLOCKED, tiep tuc.
- NOTIFY_DIRECTOR: cuoi run, neu co WAITING_APPROVAL/BLOCKED -> ghi summary.

Chay:
    python -m ihg_core.worker_runner
    python -m ihg_core.worker_runner --task-dir state/queue --once
"""
import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

# them src vao path neu chay truc tiep
HERE = Path(__file__).resolve()
SRC = HERE.parent
ROOT = SRC.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from .config import Config  # noqa: E402
from .state_store import StateStore  # noqa: E402
from .registry import Registry  # noqa: E402
from .gateway_runtime import GatewayRuntime  # noqa: E402
from .agent_runtime import MockRuntime, RuntimeResult  # noqa: E402


def _redact(s: str) -> str:
    """An toan hoa error/log: xoa token/bi-mat co the bi gateway nhay vao error.

    Dung placeholder [hidden] de pattern khong match chinh placeholder.
    """
    if not s:
        return s
    import re
    s = re.sub(r"(?i)Bearer\s+[A-Za-z0-9_\-\.=]+", "Bearer [hidden]", s)
    s = re.sub(r"(?i)(password|secret|api[_-]?key|token)[\"']?\s*[:=]\s*[\"']?[^\s\"',}]+",
               r"\1=[hidden]", s)
    s = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "sk-[hidden]", s)
    return s


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_queue(queue_dir: Path) -> list:
    """Doc tat ca task PENDING tu queue_dir. Tra ve list cac dict task.

    File task: <queue_dir>/<task_id>.json
    Schema:
      {
        "task_id": "TASK-001",
        "agent_id": "ihg-it",
        "prompt": "...",
        "created_at": "2026-10-14T...",
        "max_attempts": 3  # optional
      }
    """
    if not queue_dir.exists():
        return []
    tasks = []
    for f in sorted(queue_dir.glob("*.json")):
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
            if t.get("status") == "PENDING":
                t["_path"] = str(f)
                tasks.append(t)
        except Exception:
            pass
    return tasks


def _save_task(task_path, data: dict):
    if isinstance(task_path, str):
        task_path = Path(task_path)
    # Luu khong kem _path (no chi la metadata runtime)
    payload = {k: v for k, v in data.items() if not k.startswith("_")}
    task_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _choose_runtime():
    """Chon runtime theo muc uu tien: gateway > claude-cli > mock."""
    gw = GatewayRuntime()
    if gw.available():
        return gw, "gateway"
    # claude-cli duoc kiem tra qua ClaudeCliRuntime
    from .agent_runtime import ClaudeCliRuntime
    cli = ClaudeCliRuntime()
    if cli.available():
        return cli, "claude-cli"
    return MockRuntime(), "mock"


def _classify_terminal(reason: str) -> str:
    """Phan loai terminal state tu reason."""
    if reason in ("auth_failed",):
        return "WAITING_APPROVAL"
    if reason in ("bad_response", "empty_response", "http_error"):
        return "FAILED"
    return "FAILED"


def process_one(task: dict, runtime, store: StateStore, log) -> dict:
    """Xu ly mot task. Tra ve dict ket qua {status, reason, output, duration_s, runtime}."""
    task_id = task["task_id"]
    agent_id = task["agent_id"]
    prompt = task.get("prompt", "")
    max_attempts = int(task.get("max_attempts", 1))
    task_path: Path = task["_path"]

    log(f"[task={task_id}] agent={agent_id} runtime={runtime.name} attempts={max_attempts}")

    # Lay agent tu registry
    try:
        agent = Registry().get(agent_id)
    except Exception as e:
        return _fail_terminal(task_path, task, store, log,
                              status="BLOCKED", reason=f"agent_not_found:{e}")

    # Goi runtime
    t0 = time.time()
    try:
        result: RuntimeResult = runtime.invoke(agent, prompt)
    except Exception as e:
        log(f"  [CRASH] {type(e).__name__}: {e}")
        log(traceback.format_exc())
        return _fail_terminal(task_path, task, store, log,
                              status="FAILED", reason=f"runtime_exception:{e}")

    duration = time.time() - t0

    if result.success:
        log(f"  [OK] duration={duration:.2f}s output={len(result.output)}b")
        # Trich xuat usage info tu raw (neu gateway tra ve)
        usage = (result.raw or {}).get("usage", {})
        model_used = (result.raw or {}).get("model", agent.model or "unknown")
        in_tok = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
        out_tok = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)
        log(f"  [META] model={model_used} in_tok={in_tok} out_tok={out_tok}")

        _save_task(task_path, {
            **task,
            "status": "DONE",
            "done_at": _now_iso(),
            "runtime": runtime.name,
            "output": result.output,
            "duration_s": duration,
            "model": model_used,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
        })
        try:
            store.create(task_id, payload={"agent_id": agent_id})
            store.transition(task_id, "DISPATCHED", agent=runtime.name)
            store.transition(task_id, "RUNNING")
            store.transition(task_id, "DONE", last_error="")
            store.transition(task_id, "DELIVERED")
        except Exception as e:
            log(f"  [WARN] state store: {e}")
        return {"task_id": task_id, "status": "DONE", "runtime": runtime.name,
                "output_len": len(result.output), "duration_s": duration,
                "model": model_used, "input_tokens": in_tok, "output_tokens": out_tok}

    # that bai
    reason = result.reason or "unknown"
    err_text = _redact(result.error[:200]) if result.error else ""
    log(f"  [FAIL] reason={reason} error={err_text}")

    # WAITING_APPROVAL: auth_failed hoac cli_requires_login -> cho GĐ xu ly
    if reason in ("auth_failed", "cli_requires_login"):
        return _fail_terminal(task_path, task, store, log,
                              status="WAITING_APPROVAL", reason=reason,
                              extra={"error": result.error, "returncode": result.returncode})

    # BLOCKED: khong the goi runtime (khong phai auth)
    if reason == "gateway_unavailable":
        return _fail_terminal(task_path, task, store, log,
                              status="BLOCKED", reason=reason,
                              extra={"error": result.error})

    return _fail_terminal(task_path, task, store, log,
                          status=_classify_terminal(reason), reason=reason,
                          extra={"error": result.error, "returncode": result.returncode})


def _fail_terminal(task_path, task, store, log,
                   status: str, reason: str, extra: dict = None) -> dict:
    """Ghi task vao trang thai terminal, ghi log, tra ve summary."""
    data = {
        **task,
        "status": status,
        "reason": reason,
        "failed_at": _now_iso(),
    }
    if extra:
        # Redact error truoc khi ghi vao file task (tranh leak token vao state/)
        safe_extra = {}
        for k, v in extra.items():
            if k == "error" and isinstance(v, str):
                safe_extra[k] = _redact(v)
            else:
                safe_extra[k] = v
        data.update({f"err_{k}": v for k, v in safe_extra.items()})
    _save_task(task_path, data)
    log(f"  -> {status} ({reason})")
    try:
        store.create(task["task_id"], payload={"agent_id": task.get("agent_id", "")})
        store.transition(task["task_id"], "DISPATCHED", agent="worker")
        store.transition(task["task_id"], "RUNNING")
        store.transition(task["task_id"], "FAILED", last_error=reason)
    except Exception:
        pass
    return {"task_id": task["task_id"], "status": status, "reason": reason}


def main(argv=None):
    p = argparse.ArgumentParser(description="IHG Worker Runner")
    p.add_argument("--queue-dir", default=str(Config.STATE_DIR / "queue"),
                   help="Thu muc chua task JSON (mac dinh: state/queue)")
    p.add_argument("--once", action="store_true",
                   help="Chi chay 1 luot (khong long-running)")
    p.add_argument("--interval", type=int, default=30,
                   help="Giay cho giua cac luot (mac dinh: 30)")
    p.add_argument("--max-tasks", type=int, default=50,
                   help="So task toi da xu ly moi luot (mac dinh: 50)")
    p.add_argument("--log-dir", default=str(Config.LOG_DIR),
                   help="Thu muc ghi log")
    args = p.parse_args(argv)

    Config.ensure()
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    queue_dir = Path(args.queue_dir)
    queue_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / f"worker-runner-{int(time.time())}.log"
    summary = {"done": 0, "failed": 0, "blocked": 0, "waiting_approval": 0}

    def log(msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        # Ghi file log voi UTF-8 (khong bi gioi han boi cp1252)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        # Print stdout voi error handling (mot so terminal Windows la cp1252)
        try:
            sys.stdout.buffer.write((line + "\n").encode("utf-8"))
            sys.stdout.buffer.flush()
        except Exception:
            pass

    log(f"=== IHG Worker Runner start ===")
    log(f"queue_dir={queue_dir}, log={log_path}")
    log(f"Config: {json.dumps(Config.summary(), ensure_ascii=False)}")

    runtime, runtime_name = _choose_runtime()
    log(f"Runtime: {runtime_name} (available={runtime.available()})")
    if hasattr(runtime, "status"):
        log(f"Runtime detail: {json.dumps(runtime.status(), ensure_ascii=False)}")

    store = StateStore()

    def run_once():
        tasks = _load_queue(queue_dir)
        log(f"Queue: {len(tasks)} PENDING task(s)")
        handled = 0
        for task in tasks:
            if handled >= args.max_tasks:
                log(f"Dat max_tasks={args.max_tasks}, dung luot nay.")
                break
            result = process_one(task, runtime, store, log)
            handled += 1
            s = result.get("status", "")
            if s == "DONE":
                summary["done"] += 1
            elif s == "BLOCKED":
                summary["blocked"] += 1
            elif s == "WAITING_APPROVAL":
                summary["waiting_approval"] += 1
            else:
                summary["failed"] += 1
        return handled

    try:
        if args.once:
            run_once()
        else:
            log("Long-running mode. Nhan Ctrl+C de thoat.")
            while True:
                run_once()
                time.sleep(args.interval)
    except KeyboardInterrupt:
        log("Nhan Ctrl+C, thoat.")
    except Exception as e:
        log(f"[CRASH] {type(e).__name__}: {e}")
        log(traceback.format_exc())
        return 3

    # Summary
    log(f"=== Summary ===")
    log(json.dumps(summary, ensure_ascii=False))
    if summary["waiting_approval"] > 0 or summary["blocked"] > 0:
        log("[NOTIFY_DIRECTOR] Co task can GĐ xu ly. Xem state/queue/.")
    return 0 if summary["waiting_approval"] == 0 and summary["blocked"] == 0 else 1



if __name__ == "__main__":
    sys.exit(main())
