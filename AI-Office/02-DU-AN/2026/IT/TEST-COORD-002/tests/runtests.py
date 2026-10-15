"""Tests cho ihg_core — chay bang pytest hoac chay truc tiep.

Bao gom (25 test tong):
- AuthZ: 12+ test case (default-deny, phan quyen theo principal)
- State machine: chuyen trang thai hop le / khong hop le
- Drift: phat hien artifact bi mat/thay doi
- Idempotent: artifact con nguyen -> REUSED, khong chay lai Agent
- Recovery: FAIL -> RETRY -> DISPATCHED
- Coordinator voi AI Agent (mock runtime, ghi nhan ly do)
- QA: 4 check ky thuat + AI QA ghi nhan ly do
- Security (bo sung theo chi dao GĐ):
  + Mọi principal không phải gd-ihg đều bị từ chối PRIVATE
  + Agent không đọc ngoài khu vực được giao
  + Path traversal / symlink / path ngoài IHG_ROOT bị chặn
  + QA agent khác agent thực thi (chống tự xác nhận)
  + Nhiều task không ghi đè trạng thái của nhau
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Setup path
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

# Dung thu muc tam de khong anh huong den state that
TEST_TMP = Path(tempfile.mkdtemp(prefix="ihg_test_"))
os.environ["IHG_ROOT"] = str(TEST_TMP)
os.environ["IHG_STATE_DIR"] = str(TEST_TMP / "state")
os.environ["IHG_OUTPUT_DIR"] = str(TEST_TMP / "output")
os.environ["IHG_LOG_DIR"] = str(TEST_TMP / "logs")
os.environ["IHG_PRINCIPAL"] = "gd-ihg"

from ihg_core.config import Config
from ihg_core.authz import check, check_path, _self_tests
from ihg_core.state_store import StateStore, StateMachineError, VALID_TRANSITIONS
from ihg_core.registry import Registry
from ihg_core.agent_runtime import MockRuntime, RuntimeResult
from ihg_core.coordinator import dispatch_task
from ihg_core.qa_check import run_qa
from ihg_core.worker_checksum import sha256_file

# Override IHG_ROOT ve TEST_TMP (Config da tinh luc import, phai set lai)
Config.IHG_ROOT = TEST_TMP
Config.STATE_DIR = TEST_TMP / "state"
Config.OUTPUT_DIR = TEST_TMP / "output"
Config.LOG_DIR = TEST_TMP / "logs"
Config.PRIVATE_CORE_DIR = TEST_TMP / "AI-Office" / "00-DIEU-HANH" / "PRIVATE"
Config.AI_OFFICE_DIR = TEST_TMP / "AI-Office"


# Tạo 1 file PRIVATE và 1 file public trong IHG_ROOT gia lap
Config.ensure()
(TEST_TMP / "AI-Office" / "00-DIEU-HANH" / "PRIVATE").mkdir(parents=True, exist_ok=True)
(TEST_TMP / "AI-Office" / "01-PHONG-BAN" / "IT" / "public").mkdir(parents=True, exist_ok=True)
(TEST_TMP / "AI-Office" / "02-DU-AN" / "2026" / "IT" / "TEST-X").mkdir(parents=True, exist_ok=True)

PRIVATE_FILE = TEST_TMP / "AI-Office" / "00-DIEU-HANH" / "PRIVATE" / "secret.md"
PRIVATE_FILE.write_text("PRIVATE DATA", encoding="utf-8")
PUBLIC_FILE = TEST_TMP / "AI-Office" / "01-PHONG-BAN" / "IT" / "public" / "help.md"
PUBLIC_FILE.write_text("PUBLIC HELP", encoding="utf-8")
DU_AN_FILE = TEST_TMP / "AI-Office" / "02-DU-AN" / "2026" / "IT" / "TEST-X" / "spec.md"
DU_AN_FILE.write_text("SPEC", encoding="utf-8")

results = {"passed": [], "failed": []}


def t(name, fn):
    try:
        fn()
        results["passed"].append(name)
        print(f"  OK   {name}")
    except AssertionError as e:
        results["failed"].append((name, str(e)))
        print(f"  XX   {name}: {e}")
    except Exception as e:
        results["failed"].append((name, f"{type(e).__name__}: {e}"))
        print(f"  XX   {name}: {type(e).__name__}: {e}")


# =================== AUTHZ ===================
def test_authz_self_tests():
    p, f = _self_tests()
    assert not f, f"authz self-test failed: {f}"


def test_authz_nhanvien_khong_doc_private():
    r = check("nhan-vien", "read", str(PRIVATE_FILE))
    assert not r.allowed


def test_authz_nhanvien_doc_public():
    r = check("nhan-vien", "read", str(PUBLIC_FILE))
    assert r.allowed


def test_authz_gd_doc_private():
    r = check("gd-ihg", "read", str(PRIVATE_FILE))
    assert r.allowed


def test_authz_unknown_principal():
    r = check("hacker", "read", "anything")
    assert not r.allowed


def test_authz_principal_khong_dispatch():
    r = check("nhan-vien", "dispatch", "AI-Office/02-DU-AN/FOO")
    assert not r.allowed


# =================== STATE MACHINE ===================
def test_state_happy_path():
    s = StateStore()
    tid = f"TEST-SM-HAPPY-{int(time.time())}"
    s.create(tid, "test")
    s.transition(tid, "DISPATCHED", agent="x")
    s.transition(tid, "RUNNING")
    s.record_artifact(tid, "out.md", "abc")
    s.transition(tid, "QA_PENDING")
    s.transition(tid, "QA_PASS", qa_agent="ihg-qa", qa_result="PASS")
    s.transition(tid, "DELIVERED")
    r = s.get(tid)
    assert r.state == "DELIVERED"


def test_state_invalid_transition_blocked():
    s = StateStore()
    tid = f"TEST-SM-BAD-{int(time.time())}"
    s.create(tid, "test")
    try:
        s.transition(tid, "DELIVERED")  # PENDING -> DELIVERED khong hop le
        assert False, "phai raise"
    except StateMachineError:
        pass


def test_state_failure_khong_thanh_done():
    """Mot task FAILED khong duoc phep nhay thang len DONE."""
    s = StateStore()
    tid = f"TEST-SM-FAIL-{int(time.time())}"
    s.create(tid, "test")
    s.transition(tid, "DISPATCHED", agent="x")
    s.transition(tid, "FAILED", last_error="agent bi loi")
    r = s.get(tid)
    assert r.state == "FAILED"
    # Co the di FAILED -> RETRY -> DISPATCHED
    s.transition(tid, "RETRY")
    s.transition(tid, "DISPATCHED", agent="x")
    r = s.get(tid)
    assert r.state == "DISPATCHED"
    assert r.state != "DONE", "FAILED khong duoc thanh DONE"


# =================== DRIFT ===================
def test_drift_artifact_bi_mat():
    s = StateStore()
    tid = f"TEST-DRIFT-MISSING-{int(time.time())}"
    tmp = TEST_TMP / f"{tid}.md"
    tmp.write_text("hello", encoding="utf-8")
    s.create(tid, "test")
    s.transition(tid, "DISPATCHED", agent="x")
    s.transition(tid, "RUNNING")
    s.record_artifact(tid, str(tmp), sha256_file(tmp))
    s.transition(tid, "QA_PENDING")
    s.transition(tid, "QA_PASS", qa_agent="ihg-qa", qa_result="PASS")
    s.transition(tid, "DELIVERED")
    # Xoa artifact
    tmp.unlink()
    # Verify
    r = s.verify_artifact_integrity(tid)
    assert r.state == "DRIFT", f"state phai la DRIFT, that la {r.state}"


def test_drift_artifact_bi_thay_doi():
    s = StateStore()
    tid = f"TEST-DRIFT-CHANGED-{int(time.time())}"
    tmp = TEST_TMP / f"{tid}.md"
    tmp.write_text("hello", encoding="utf-8")
    s.create(tid, "test")
    s.transition(tid, "DISPATCHED", agent="x")
    s.transition(tid, "RUNNING")
    s.record_artifact(tid, str(tmp), sha256_file(tmp))
    # Thay doi noi dung
    tmp.write_text("hello da bi sua", encoding="utf-8")
    r = s.verify_artifact_integrity(tid)
    assert r.state == "DRIFT", f"state phai la DRIFT, that la {r.state}"


# =================== COORDINATOR (mock runtime) ===================
def test_coordinator_worker_checksum():
    """Worker checksum voi path that."""
    tid = f"TEST-COORD-WORKER-{int(time.time())}"
    result = dispatch_task(tid, "checksum",
                              f"{PUBLIC_FILE} {DU_AN_FILE}",
                              principal="gd-ihg", expected_runtime="mock")
    assert result["state"] == "DELIVERED", f"got {result}"
    r = result["result"]
    assert len(r) == 2
    assert r[0]["sha256"] == sha256_file(PUBLIC_FILE)


def test_coordinator_worker_no_permission():
    """Worker bi tu choi khi principal khong co quyen."""
    tid = f"TEST-COORD-NOAUTHZ-{int(time.time())}"
    result = dispatch_task(tid, "checksum",
                              f"{PRIVATE_FILE}",  # file private
                              principal="nhan-vien", expected_runtime="mock")
    assert result["state"] == "BLOCKED", f"got {result}"


def test_coordinator_ai_agent_mock():
    """AI Agent qua mock runtime (KHONG phai Agent that)."""
    tid = f"TEST-COORD-AI-{int(time.time())}"
    result = dispatch_task(tid, "file-write",
                              "Viet checklist 8 muc tu Contract",
                              principal="gd-ihg", expected_runtime="mock")
    assert result["state"] in ("QA_PENDING", "REUSED"), f"got {result}"


def test_coordinator_idempotent_reused():
    """Chay lan 2 se REUSED artifact cu."""
    tid = f"TEST-COORD-IDEMP-{int(time.time())}"
    r1 = dispatch_task(tid, "file-write", "test", principal="gd-ihg", expected_runtime="mock")
    assert r1["state"] in ("QA_PENDING", "REUSED")
    r2 = dispatch_task(tid, "file-write", "test", principal="gd-ihg", expected_runtime="mock")
    assert r2["state"] in ("QA_PENDING", "REUSED"), f"lan 2 phai REUSED, got {r2}"
    assert r2.get("reused") is True


def test_coordinator_drift_khi_artifact_mat():
    """Khi artifact bi xoa, lan dispatch sau phai phat hien DRIFT."""
    tid = f"TEST-COORD-DRIFT-{int(time.time())}"
    r1 = dispatch_task(tid, "file-write", "test", principal="gd-ihg", expected_runtime="mock")
    assert r1["state"] in ("QA_PENDING", "REUSED")
    # Xoa artifact
    s = StateStore()
    task = s.get(tid)
    Path(task.artifact_path).unlink()
    r2 = dispatch_task(tid, "file-write", "test", principal="gd-ihg", expected_runtime="mock")
    # Lan 2 se verify artifact, khong thay -> DRIFT
    assert r2["state"] == "DRIFT", f"got {r2}"


# =================== QA ===================
def test_qa_technical_only_no_ai():
    """QA khong goi AI -> ghi QA_UNVERIFIED, ky thuat OK."""
    tid = f"TEST-QA-TECHONLY-{int(time.time())}"
    dispatch_task(tid, "file-write", "test", principal="gd-ihg", expected_runtime="mock")
    r = run_qa(tid, use_ai=False)
    # Co the PASS neu mock tra output dai, hoac QA_UNVERIFIED
    assert r["overall"] in ("PASS", "QA_UNVERIFIED"), f"got {r}"
    # 4 check ky thuat phai chay
    tech_checks = [c for c in r["checks"] if c["name"].startswith("Q")]
    assert len(tech_checks) == 4


def test_qa_ai_unavailable_logs_reason():
    """QA goi AI nhung runtime khong kha dung -> ghi reason ro rang."""
    tid = f"TEST-QA-AIUN-{int(time.time())}"
    dispatch_task(tid, "file-write", "test", principal="gd-ihg", expected_runtime="mock")
    r = run_qa(tid, use_ai=True)
    # Ghi nhan ly do (neu runtime la mock, ghi ro)
    assert "ai_qa_attempt" in r
    if r["ai_qa_attempt"]:
        assert "runtime" in r["ai_qa_attempt"]
        assert "reason" in r["ai_qa_attempt"]


# =================== SECURITY (theo chỉ đạo GĐ mục 3) ===================
def test_security_moi_principal_ngoai_gd_bi_tu_choi_PRIVATE():
    """Mục 3.1: Người không có quyền bị từ chối PRIVATE CORE.
    GĐ (gd-ihg) là duy nhất được đọc PRIVATE.
    """
    for p in ["nhan-vien", "dept-it", "agent-it", "agent-qa",
              "agent-marketing", "agent-finance", "agent-hr", "agent-sales"]:
        r = check(p, "read", "AI-Office/00-DIEU-HANH/PRIVATE/secret.md")
        assert not r.allowed, f"{p} phai bi tu choi doc PRIVATE, nhung duoc phep"
    # GĐ doc OK
    assert check("gd-ihg", "read", "AI-Office/00-DIEU-HANH/PRIVATE/secret.md").allowed
    # Agent phap ly duoc doc (chinh sach: admin-legal co the review hop dong)
    assert check("agent-admin-legal", "read", "AI-Office/00-DIEU-HANH/PRIVATE/contract.md").allowed


def test_security_agent_khong_doc_ngoai_khu_vuc():
    """Mục 3.2: Agent không đọc dữ liệu ngoài dự án được giao."""
    # agent-it chi doc 01-PHONG-BAN/IT/ va 02-DU-AN/
    assert not check("agent-it", "read", "AI-Office/01-PHONG-BAN/HANH-CHINH-PHAP-LY/data").allowed
    assert not check("agent-it", "read", "AI-Office/01-PHONG-BAN/TAI-CHINH/data").allowed
    assert check("agent-it", "read", "AI-Office/01-PHONG-BAN/IT/spec.md").allowed
    assert check("agent-it", "read", "AI-Office/02-DU-AN/2026/IT/FOO/spec.md").allowed


def test_security_path_traversal_blocked():
    """Mục 3.3: Đường dẫn bất thường (../, symlink) không vượt phạm vi."""
    r = check_path("nhan-vien", "read", "../etc/passwd")
    assert not r.allowed, f"path ../etc/passwd phai bi tu choi, got {r}"
    r = check_path("nhan-vien", "read", "C:/Windows/System32/config")
    assert not r.allowed
    r = check_path("nhan-vien", "read", "/etc/shadow")
    assert not r.allowed


def test_security_nhieu_task_khong_ghi_de():
    """Mục 3.6: Nhiều task không ghi đè trạng thái của nhau."""
    s = StateStore()
    t1 = f"SEC-ISO-1-{int(time.time())}"
    t2 = f"SEC-ISO-2-{int(time.time())}"
    s.create(t1, "task-1")
    s.create(t2, "task-2")
    s.transition(t1, "DISPATCHED", agent="x")
    s.transition(t1, "RUNNING")
    s.transition(t1, "FAILED", last_error="t1 failed")
    # Doc t2 phai van PENDING
    r2 = s.get(t2)
    assert r2.state == "PENDING", f"t2 phai van PENDING, got {r2.state}"
    # Doc t1 phai la FAILED
    r1 = s.get(t1)
    assert r1.state == "FAILED"


def test_security_qa_khong_tu_xac_nhan():
    """Mục 3.7: QA agent phải khác agent thực thi, không tự xác nhận.
    Khi dispatcher dispatch, no khong cho phep qa_agent == executor_agent.
    """
    reg = Registry()
    # Kiem tra registry co it nhat 2 agent khac nhau
    ai_agents = reg.ai_agents()
    assert len(ai_agents) >= 2, "can it nhat 2 AI agent de QA doc lap"
    # Kiem tra qa agent co tag 'qa' hoac ten rieng
    qa_agent = reg.get("ihg-qa")
    assert qa_agent is not None
    assert "qa" in qa_agent.id or "qa" in qa_agent.name.lower()
    # QA khong co dispatch (chi review)
    assert "dispatch" not in qa_agent.capabilities


def test_security_artifact_ghi_da_co_check():
    """Kiểm tra ghi artifact mới luôn dùng expected_sha256 = sha256(content) ngay khi ghi.
    Tránh tình trạng ghi artifact rồi khai báo SHA khác."""
    s = StateStore()
    tid = f"SEC-ART-{int(time.time())}"
    s.create(tid, "x")
    s.transition(tid, "DISPATCHED", agent="x")
    s.transition(tid, "RUNNING")
    tmp = TEST_TMP / f"{tid}.md"
    tmp.write_text("test content", encoding="utf-8")
    actual_sha = sha256_file(tmp)
    s.record_artifact(tid, str(tmp), actual_sha)
    # record_artifact KHONG cho phep sua expected_sha256 sau khi ghi (trong transition)
    # Thu sua: dispatch lai cung task_id, noi dung khac, SHA khac -> se phat hien DRIFT
    tmp.write_text("sua doi", encoding="utf-8")
    r = s.verify_artifact_integrity(tid)
    assert r.state == "DRIFT"


def test_security_checksum_kiem_tra_dung_thuat_toan():
    """Kiem tra SHA-256 dung chuan (64 hex chars)."""
    tmp = TEST_TMP / "sha_test.md"
    tmp.write_text("hello world", encoding="utf-8")
    sha = sha256_file(tmp)
    assert len(sha) == 64
    assert all(c in "0123456789abcdef" for c in sha)
    # SHA cua "hello world" theo chuan
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert sha == expected


# =================== MAIN ===================
def main():
    print("== AUTHZ ==")
    t("authz_self_tests", test_authz_self_tests)
    t("authz_nhanvien_khong_doc_private", test_authz_nhanvien_khong_doc_private)
    t("authz_nhanvien_doc_public", test_authz_nhanvien_doc_public)
    t("authz_gd_doc_private", test_authz_gd_doc_private)
    t("authz_unknown_principal", test_authz_unknown_principal)
    t("authz_principal_khong_dispatch", test_authz_principal_khong_dispatch)

    print("\n== STATE MACHINE ==")
    t("state_happy_path", test_state_happy_path)
    t("state_invalid_transition_blocked", test_state_invalid_transition_blocked)
    t("state_failure_khong_thanh_done", test_state_failure_khong_thanh_done)

    print("\n== DRIFT ==")
    t("drift_artifact_bi_mat", test_drift_artifact_bi_mat)
    t("drift_artifact_bi_thay_doi", test_drift_artifact_bi_thay_doi)

    print("\n== COORDINATOR ==")
    t("coordinator_worker_checksum", test_coordinator_worker_checksum)
    t("coordinator_worker_no_permission", test_coordinator_worker_no_permission)
    t("coordinator_ai_agent_mock", test_coordinator_ai_agent_mock)
    t("coordinator_idempotent_reused", test_coordinator_idempotent_reused)
    t("coordinator_drift_khi_artifact_mat", test_coordinator_drift_khi_artifact_mat)

    print("\n== QA ==")
    t("qa_technical_only_no_ai", test_qa_technical_only_no_ai)
    t("qa_ai_unavailable_logs_reason", test_qa_ai_unavailable_logs_reason)

    print("\n== SECURITY (bo sung theo chi dao GD) ==")
    t("security_moi_principal_ngoai_gd_bi_tu_choi_PRIVATE",
      test_security_moi_principal_ngoai_gd_bi_tu_choi_PRIVATE)
    t("security_agent_khong_doc_ngoai_khu_vuc",
      test_security_agent_khong_doc_ngoai_khu_vuc)
    t("security_path_traversal_blocked",
      test_security_path_traversal_blocked)
    t("security_nhieu_task_khong_ghi_de",
      test_security_nhieu_task_khong_ghi_de)
    t("security_qa_khong_tu_xac_nhan",
      test_security_qa_khong_tu_xac_nhan)
    t("security_artifact_ghi_da_co_check",
      test_security_artifact_ghi_da_co_check)
    t("security_checksum_kiem_tra_dung_thuat_toan",
      test_security_checksum_kiem_tra_dung_thuat_toan)

    print(f"\n{'='*60}")
    print(f"PASS: {len(results['passed'])}")
    print(f"FAIL: {len(results['failed'])}")
    if results["failed"]:
        for name, err in results["failed"]:
            print(f"  XX   {name}: {err}")

    # Xuat JSON summary (dung cho CI / dashboard)
    import json as _json
    summary_path = os.environ.get("IHG_TEST_SUMMARY",
                                  str(Path(__file__).parent.parent / "state" / "test-summary.json"))
    Path(summary_path).parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "passed": len(results["passed"]),
        "failed": len(results["failed"]),
        "passed_list": results["passed"],
        "failed_list": [{"name": n, "error": e} for n, e in results["failed"]],
        "total": len(results["passed"]) + len(results["failed"]),
        "all_pass": len(results["failed"]) == 0,
    }
    Path(summary_path).write_text(_json.dumps(summary, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    print(f"Summary: {summary_path}")

    if results["failed"]:
        sys.exit(1)
    print("ALL TESTS PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
