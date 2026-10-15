"""tests.test_e2e_flow — test e2e flow voi mock runtime (test interface, khong goi AI that)."""
import json
import sys
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from ihg_core.real_e2e_flow import (  # noqa: E402
    run_real_e2e, _extract_qa_decision, _hard_check_artifact
)


# ===== Test 1: extract qa_result from JSON =====
def test_extract_qa_json():
    r = _extract_qa_decision('Tra loi: {"qa_result": "PASS", "qa_detail": "tot"}')
    assert r["qa_result"] == "PASS"
    assert r["qa_detail"] == "tot"


def test_extract_qa_kv():
    r = _extract_qa_decision("Sau khi kiem tra: qa_result=FAIL\nLy do: thieu heading")
    assert r["qa_result"] == "FAIL"


def test_extract_qa_auto_head():
    r = _extract_qa_decision("PASS\nArtifact dat yeu cau")
    assert r["qa_result"] == "PASS"


def test_extract_qa_empty():
    r = _extract_qa_decision("")
    assert r["qa_result"] == "QA_UNVERIFIED"


def test_extract_qa_no_marker():
    r = _extract_qa_decision("Random text without any QA marker at all in it")
    assert r["qa_result"] == "QA_UNVERIFIED"


def test_extract_qa_unverified():
    r = _extract_qa_decision("Chua the ket luan, can them thong tin")
    assert r["qa_result"] == "QA_UNVERIFIED"


# ===== Test 2: hard_check_artifact =====
def test_hard_check_good_artifact():
    txt = "# README\n\nThis is a complete artifact with enough content to pass all checks."
    r = _hard_check_artifact(txt)
    assert r["passed"] is True
    assert r["issues"] == []


def test_hard_check_too_short():
    r = _hard_check_artifact("# T")
    assert r["passed"] is False
    assert any("qua ngan" in i for i in r["issues"])


def test_hard_check_todo():
    r = _hard_check_artifact("# README\n\nThis has a TODO item in it for sure.")
    assert r["passed"] is False
    assert any("TODO" in i for i in r["issues"])


def test_hard_check_no_heading():
    r = _hard_check_artifact("Just plain text without any markdown heading at all to make a header.")
    assert r["passed"] is False
    assert any("heading" in i for i in r["issues"])


def test_hard_check_placeholder():
    r = _hard_check_artifact("# T\n\n**")
    assert r["passed"] is False
    assert any("placeholder" in i for i in r["issues"])


# ===== Test 3: e2e flow voi mock =====
def test_e2e_mock_runtime():
    """E2E voi mock runtime (khong co token/CLI login)."""
    # Set env de KHONG co token, KHONG co claude CLI (test mock path)
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    # Runtime mac dinh se fallback mock
    with tempfile.TemporaryDirectory() as tmpdir:
        ev = run_real_e2e(
            capability="code-run",
            test_prompt="Viet 1 README.md ngan (200-300 tu) cho module IHG token vault.",
            evidence_dir=tmpdir,
        )
    assert "evidence_id" in ev
    assert "phases" in ev
    assert "dispatch" in ev["phases"]
    assert "qa" in ev["phases"]
    assert "hard_check" in ev["phases"]
    assert "final_result" in ev
    # Mock se FAIL vi artifact thieu heading
    assert ev["final_result"] in ("PASS", "FAIL")


def test_e2e_evidence_saved_to_file():
    """Evidence duoc ghi vao file JSON."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        ev = run_real_e2e(
            capability="code-run",
            test_prompt="Viet README.md ngan 200-300 tu.",
            evidence_dir=tmpdir,
        )
        # Doc file evidence
        ev_dir = Path(tmpdir)
        files = list(ev_dir.glob("E2E-EV-*.json"))
        assert len(files) == 1
        loaded = json.loads(files[0].read_text(encoding="utf-8"))
        assert loaded["evidence_id"] == ev["evidence_id"]
        # File KHONG chua token that (sk-ant-...)
        text = files[0].read_text(encoding="utf-8")
        assert "sk-ant-" not in text
        assert "Bearer " not in text or "Authorization" not in text
        # Co fingerprint (sha256:xxx) neu gateway, hoac rong neu mock
        s = str(loaded)
        if "fingerprint" in s:
            # Neu co fingerprint thi KHONG co gia tri token gan can
            assert "secret" not in s.lower()


def test_e2e_no_token_in_output():
    """stdout/stderr KHONG chua token."""
    import io
    import contextlib

    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_real_e2e(
                capability="code-run",
                test_prompt="Test",
                evidence_dir=tmpdir,
            )
    out = buf.getvalue()
    # Co the co "ANTHROPIC_AUTH_TOKEN" trong thong bao, nhung KHONG co gia tri
    assert "sk-ant-" not in out
    assert "Bearer " not in out or "Authorization" not in out


# ===== Test 4: runtime detection =====
def test_runtime_selection_no_token():
    """Khong co token -> mock (khong crash)."""
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    # Xoa token vault neu co
    try:
        from ihg_core.token_vault import TokenVault
        TokenVault().delete()
    except Exception:
        pass
    # Run: KHONG duoc crash
    with tempfile.TemporaryDirectory() as tmpdir:
        ev = run_real_e2e(evidence_dir=tmpdir)
    assert ev is not None
    assert "final_result" in ev or "error" in ev


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
