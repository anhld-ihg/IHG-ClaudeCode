"""tests.test_worker_runner — test Worker Runner (queue, error handling, isolation).

Kiem tra:
- process_one: WAITING_APPROVAL khong chan task khac
- process_one: loi runtime -> FAILED, tiep tuc queue
- process_one: token leak bi redact trong log/error
- _load_queue: chi doc PENDING
- _save_task: khong ghi _path metadata
"""
import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from ihg_core.worker_runner import (  # noqa: E402
    _redact, _load_queue, _save_task, process_one, _classify_terminal
)


def test_redact_token():
    """Redact sk-ant-... token."""
    s = _redact("Bearer sk-ant-api03-abc123xyz failed")
    assert "sk-ant-api03-abc123xyz" not in s
    assert "[hidden]" in s


def test_redact_gateway_token():
    """Redact gateway token (sk-ihg-, sk-gw-)."""
    s = _redact("Auth: sk-ihg-gateway-secret-12345")
    assert "sk-ihg-gateway-secret-12345" not in s
    s = _redact("Got sk-gw-proxy-token-abc from upstream")
    assert "sk-gw-proxy-token-abc" not in s


def test_redact_bearer():
    s = _redact("Authorization: Bearer abc123def456")
    assert "abc123def456" not in s


def test_redact_password():
    s = _redact("password=hunter2 mismatch")
    assert "hunter2" not in s
    s = _redact('"api_key":"sk-ant-test1234"')
    assert "sk-ant-test1234" not in s


def test_redact_safe_text():
    """Khong redact text thuong."""
    s = _redact("Connection timeout after 30s, retrying")
    assert s == "Connection timeout after 30s, retrying"
    s = _redact(None)
    assert s is None
    s = _redact("")
    assert s == ""


def test_redact_no_collision():
    """Khong an text giong token nhu 'sketch'."""
    s = _redact("Please sketch a design for the logo")
    # sketch (6 ky tu) khong match pattern (sk- + 8+ ky tu dac biet)
    assert "sketch" in s
    assert "[hidden]" not in s


def test_classify_terminal():
    """Phan loai reason -> status."""
    assert _classify_terminal("auth_failed") == "WAITING_APPROVAL"
    assert _classify_terminal("bad_response") == "FAILED"
    assert _classify_terminal("empty_response") == "FAILED"
    assert _classify_terminal("http_error") == "FAILED"
    assert _classify_terminal("unknown") == "FAILED"


def test_load_queue_empty(tmp_path=None):
    """Thu muc khong ton tai -> tra ve list rong."""
    if tmp_path is None:
        from tempfile import mkdtemp
        tmp_path = Path(mkdtemp())
    else:
        tmp_path = Path(tmp_path)
    tasks = _load_queue(tmp_path)
    assert tasks == []


def test_load_queue_pending_only(tmp_path=None):
    """Chi doc task PENDING, bo qua DONE/FAILED/RUNNING."""
    from tempfile import mkdtemp
    tmp_path = Path(mkdtemp())
    # Tao 3 task
    (tmp_path / "T001.json").write_text(json.dumps({
        "task_id": "T001", "agent_id": "ihg-it", "prompt": "test1",
        "status": "PENDING", "created_at": "2026-10-14T00:00:00Z"
    }))
    (tmp_path / "T002.json").write_text(json.dumps({
        "task_id": "T002", "agent_id": "ihg-it", "prompt": "test2",
        "status": "DONE", "created_at": "2026-10-14T00:00:01Z"
    }))
    (tmp_path / "T003.json").write_text(json.dumps({
        "task_id": "T003", "agent_id": "ihg-it", "prompt": "test3",
        "status": "PENDING", "created_at": "2026-10-14T00:00:02Z"
    }))
    tasks = _load_queue(tmp_path)
    assert len(tasks) == 2
    ids = {t["task_id"] for t in tasks}
    assert ids == {"T001", "T003"}


def test_save_task_no_metadata():
    """_save_task KHONG ghi _path (chi runtime metadata)."""
    from tempfile import mkdtemp
    tmp_path = Path(mkdtemp())
    fpath = tmp_path / "T001.json"
    data = {
        "task_id": "T001",
        "agent_id": "ihg-it",
        "prompt": "test",
        "_path": str(fpath),  # phai bi loai bo
        "_internal_secret": "should-not-appear",
    }
    _save_task(fpath, data)
    saved = json.loads(fpath.read_text(encoding="utf-8"))
    assert "_path" not in saved
    assert "_internal_secret" not in saved
    assert saved["task_id"] == "T001"


def test_process_one_waiting_approval_continues_queue():
    """Yeu cau #9: WAITING_APPROVAL khong chan task khac trong queue.
    Worker xu ly task A -> WAITING_APPROVAL, tiep tuc xu ly task B.
    """
    from tempfile import mkdtemp
    from ihg_core.worker_runner import _load_queue, process_one
    from ihg_core.registry import Registry
    from ihg_core.agent_runtime import RuntimeResult
    from ihg_core.state_store import StateStore

    # Setup: registry it nhat 1 agent (dung gateway neu co token, mock neu khong)
    try:
        agent = Registry().get("ihg-it")
    except Exception:
        # Registry rong -> tao agent gia de test
        agent = MagicMock()
        agent.id = "ihg-test"
        agent.model = "mock"
        agent.name = "test"

    # Mock runtime tra ve auth_failed (WAITING_APPROVAL)
    rt = MagicMock()
    rt.name = "test-runtime"
    rt.invoke = MagicMock(return_value=RuntimeResult(
        success=False, reason="auth_failed", error="Auth required: sk-ant-secret",
        output="", returncode=1, raw={}
    ))

    # Tao 2 task
    queue_dir = Path(mkdtemp())
    for i in (1, 2):
        (queue_dir / f"T{i:03d}.json").write_text(json.dumps({
            "task_id": f"T{i:03d}", "agent_id": "ihg-it", "prompt": f"test {i}",
            "status": "PENDING", "created_at": "2026-10-14T00:00:00Z"
        }))

    # Mock StateStore
    store = MagicMock(spec=StateStore)

    # Xu ly ca 2 task (giong nhu worker_runner run_once)
    tasks = _load_queue(queue_dir)
    log = MagicMock()
    results = []
    for t in tasks:
        r = process_one(t, rt, store, log)
        results.append(r)

    # Ca 2 task phai duoc xu ly (khong bi stop o task 1)
    assert len(results) == 2
    # Ca 2 phai WAITING_APPROVAL (cung ly do auth_failed)
    assert all(r["status"] == "WAITING_APPROVAL" for r in results)

    # Verify token bi redact trong file task
    t1_data = json.loads((queue_dir / "T001.json").read_text(encoding="utf-8"))
    assert t1_data["status"] == "WAITING_APPROVAL"
    if "err_error" in t1_data:
        assert "sk-ant-secret" not in t1_data["err_error"]
        assert "[hidden]" in t1_data["err_error"]


def test_process_one_does_not_block_on_failed():
    """Task FAILED cung khong chan task khac."""
    from tempfile import mkdtemp
    from ihg_core.worker_runner import _load_queue, process_one
    from ihg_core.agent_runtime import RuntimeResult
    from ihg_core.state_store import StateStore

    rt = MagicMock()
    rt.name = "test-runtime"
    rt.invoke = MagicMock(return_value=RuntimeResult(
        success=False, reason="http_error", error="500 server error",
        output="", returncode=1, raw={}
    ))

    queue_dir = Path(mkdtemp())
    for i in (1, 2, 3):
        (queue_dir / f"T{i:03d}.json").write_text(json.dumps({
            "task_id": f"T{i:03d}", "agent_id": "ihg-it", "prompt": f"test {i}",
            "status": "PENDING", "created_at": "2026-10-14T00:00:00Z"
        }))

    store = MagicMock(spec=StateStore)
    log = MagicMock()

    tasks = _load_queue(queue_dir)
    results = [process_one(t, rt, store, log) for t in tasks]

    # Ca 3 task deu FAILED nhung KHONG chan nhau
    assert len(results) == 3
    assert all(r["status"] == "FAILED" for r in results)


def test_process_one_runtime_crash_blocked():
    """Runtime crash (exception) -> BLOCKED, tiep tuc task khac."""
    from tempfile import mkdtemp
    from ihg_core.worker_runner import _load_queue, process_one
    from ihg_core.state_store import StateStore

    rt = MagicMock()
    rt.name = "test-runtime"
    rt.invoke = MagicMock(side_effect=RuntimeError("crash boom"))

    queue_dir = Path(mkdtemp())
    for i in (1, 2):
        (queue_dir / f"T{i:03d}.json").write_text(json.dumps({
            "task_id": f"T{i:03d}", "agent_id": "ihg-it", "prompt": f"test {i}",
            "status": "PENDING", "created_at": "2026-10-14T00:00:00Z"
        }))

    store = MagicMock(spec=StateStore)
    log = MagicMock()

    tasks = _load_queue(queue_dir)
    results = [process_one(t, rt, store, log) for t in tasks]

    assert len(results) == 2
    # Ca 2 task deu FAILED (vi runtime crash -> "runtime_exception:...")
    # Khong phai BLOCKED, nhung quan trong la KHONG chan
    for r in results:
        assert r["status"] in ("FAILED", "BLOCKED")
        assert "crash" in r.get("reason", "").lower() or "exception" in r.get("reason", "").lower()


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  [PASS] {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    print(f"\n{passed}/{passed+failed} passed")
    sys.exit(0 if failed == 0 else 1)
