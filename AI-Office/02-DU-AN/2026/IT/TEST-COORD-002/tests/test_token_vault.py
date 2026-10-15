"""tests.test_token_vault — test TokenVault (Windows Credential Manager / DPAPI).

Kiem tra:
- Set/get/delete
- Khong leak token qua status()
- Reject URL khong https / localhost
- Wrapper status chi tra ve fingerprint, khong bao gio tra ve token
"""
import json
import sys
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from ihg_core.token_vault import TokenVault, fingerprint, SERVICE_NAME  # noqa: E402


# ===== Test 1: fingerprint =====
def test_fingerprint_masks_value():
    fp = fingerprint("sk-ant-real-token-secret-12345")
    assert "sk-ant-real" not in fp
    assert "12345" not in fp
    assert fp.startswith("sha256:")


def test_fingerprint_empty():
    assert fingerprint("") == "unset"


def test_fingerprint_distinct():
    a = fingerprint("token-A")
    b = fingerprint("token-B")
    assert a != b


# ===== Test 2: Vault co backend Windows =====
def test_vault_backend_is_windows():
    v = TokenVault()
    # Phai la Windows Credential Manager
    assert "Win" in v.backend_name or "Windows" in v.backend_name, \
        f"Backend khong phai Windows: {v.backend_name}"


# ===== Test 3: status KHONG leak token =====
def test_status_no_token_leak():
    v = TokenVault()
    v.set("PRIVATE-SECRET-TOKEN-12345")
    s = v.status()
    s_str = json.dumps(s)
    assert "PRIVATE-SECRET-TOKEN-12345" not in s_str
    assert "PRIVATE" not in s_str
    # Phai co fingerprint thay the
    assert s["present"] is True
    assert s["fingerprint"].startswith("sha256:")
    v.delete()


# ===== Test 4: set/get/delete =====
def test_set_get_delete():
    v = TokenVault()
    # Dam bao clean
    v.delete()
    assert v.exists() is False

    v.set("test-token-12345")
    assert v.exists() is True
    got = v.get()
    assert got == "test-token-12345"
    v.delete()
    assert v.exists() is False


# ===== Test 5: set reject empty =====
def test_set_reject_empty():
    v = TokenVault()
    try:
        v.set("")
    except ValueError:
        return
    assert False, "Phai raise ValueError khi token rong"


def test_set_reject_whitespace():
    v = TokenVault()
    try:
        v.set("   ")
    except ValueError:
        return
    assert False, "Phai raise ValueError khi token chi co whitespace"


# ===== Test 6: status() truoc/sau =====
def test_status_before_after():
    v = TokenVault()
    v.delete()
    s0 = v.status()
    assert s0["present"] is False
    assert s0["fingerprint"] == "unset"
    assert s0["len"] == 0

    v.set("test-xyz")
    s1 = v.status()
    assert s1["present"] is True
    assert s1["fingerprint"] != "unset"
    assert s1["len"] == len("test-xyz")

    v.delete()
    s2 = v.status()
    assert s2["present"] is False


# ===== Test 7: Token khong xuat hien trong string cua status =====
def test_status_no_token_in_str():
    v = TokenVault()
    v.set("UNIQUE-MARKER-XYZ-789")
    s = v.status()
    text = str(s)
    assert "UNIQUE-MARKER-XYZ-789" not in text
    v.delete()


# ===== Test 8: SERVICE_NAME =====
def test_service_name():
    assert SERVICE_NAME == "IHG-AI-OS"


# ===== Test 9: Per-instance service de test =====
def test_independent_services():
    v1 = TokenVault(service="test-svc-1", username="u")
    v2 = TokenVault(service="test-svc-2", username="u")
    v1.delete()
    v2.delete()
    v1.set("token-1")
    v2.set("token-2")
    assert v1.get() == "token-1"
    assert v2.get() == "token-2"
    # Status rieng
    assert v1.status()["fingerprint"] != v2.status()["fingerprint"]
    v1.delete()
    v2.delete()


# ===== Test 10: Token duoc giu qua cac lan goi get() =====
def test_get_idempotent():
    v = TokenVault()
    v.delete()
    v.set("test-stable-token")
    a = v.get()
    b = v.get()
    c = v.get()
    assert a == b == c == "test-stable-token"
    v.delete()


# ===== Test 11: Token moi ghi de token cu =====
def test_set_overwrite():
    v = TokenVault()
    v.delete()
    v.set("token-A")
    assert v.get() == "token-A"
    v.set("token-B")
    assert v.get() == "token-B"
    v.delete()


# ===== Test 12: set tra ve dict khong chua token =====
def test_set_returns_safe_dict():
    v = TokenVault()
    v.delete()
    r = v.set("test-secret-abc")
    r_str = json.dumps(r)
    assert "test-secret-abc" not in r_str
    assert r["stored"] is True
    assert r["fingerprint"].startswith("sha256:")
    v.delete()


def test_has_token_shape():
    """Helper kiem tra hinh dang token (KHONG check prefix cu the).
    Gateway ben thu ba chap nhan bat ky string nao lam token value, nen
    chi check: khong rong, do dai 8..256, khong co whitespace.
    """
    from ihg_core.token_vault import has_token_shape
    # Hop le (cac dang pho bien)
    assert has_token_shape("sk-ant-api03-abc123") is True
    assert has_token_shape("sk-ant-fancy-2024") is True
    assert has_token_shape("sk-ihg-gw-xyz-12345") is True
    assert has_token_shape("sk-gw-proxy-abc-1234") is True
    # KHONG check prefix: gateway chap nhan bat ky token string
    assert has_token_shape("gateway-key-abc-12345") is True
    assert has_token_shape("plain-token-value-1234") is True
    # Khong hop le
    assert has_token_shape("") is False
    assert has_token_shape(None) is False
    assert has_token_shape("foobar") is False  # < 8 ky tu
    assert has_token_shape("abc") is False  # qua ngan
    assert has_token_shape("abc def ghi") is False  # co whitespace
    assert has_token_shape("x" * 257) is False  # qua dai
    # Edge: 8 ky tu (min)
    assert has_token_shape("12345678") is True
    # Edge: 256 ky tu (max)
    assert has_token_shape("x" * 256) is True


def test_fingerprint_stable():
    """Cung token -> cung fingerprint."""
    from ihg_core.token_vault import fingerprint
    a = fingerprint("sk-ant-test-token-abc")
    b = fingerprint("sk-ant-test-token-abc")
    assert a == b
    assert a.startswith("sha256:")
    # Token khac -> fingerprint khac
    c = fingerprint("sk-ant-test-token-xyz")
    assert a != c


def test_setup_vault_redactor():
    """_redact trong setup_vault phai an token/bi-mat.
    Dung placeholder [hidden] de pattern khong match chinh placeholder.
    """
    from ihg_core.setup_vault import _redact
    # An sk-ant-...
    r = _redact("Bearer sk-ant-api03-abc123xyz - 401")
    assert "sk-ant-api03-abc123xyz" not in r
    assert "[hidden]" in r
    # An sk-ihg-...
    r = _redact("Token = sk-ihg-gateway-secret-12345")
    assert "sk-ihg-gateway-secret-12345" not in r
    # An sk-gw-...
    r = _redact("Got: sk-gw-proxy-abc123 from upstream")
    assert "sk-gw-proxy-abc123" not in r
    # An Bearer
    r = _redact("Authorization: Bearer abc.def.ghi")
    assert "abc.def.ghi" not in r
    # An password=
    r = _redact('Error: password=hunter2 mismatch')
    assert "hunter2" not in r
    # An api_key=
    r = _redact('api_key=sk-ant-secret1234 not valid')
    assert "sk-ant-secret1234" not in r
    # Giu lai text thuong
    r = _redact("Connection timeout after 30s")
    assert "timeout" in r
    assert "[hidden]" not in r
    # Empty / None
    assert _redact("") == ""
    assert _redact(None) is None


def test_setup_vault_redactor_no_collision():
    """Redactor KHONG duoc an text nhu 'sketch' (chi an sk-XXX dai)."""
    from ihg_core.setup_vault import _redact
    r = _redact("Please sketch the design")
    # 'sketch' (7 ky tu) khong match pattern (sk- + 8+ ky tu dac biet)
    # nen r phai giu nguyen "sketch" va KHONG co [hidden]
    assert "[hidden]" not in r
    assert "sketch" in r


def test_token_vault_redactor():
    """_redact trong token_vault cung an token/bi-mat."""
    from ihg_core.token_vault import _redact as tv_redact
    r = tv_redact("Bearer sk-ant-api03-abc123xyz - 401")
    assert "sk-ant-api03-abc123xyz" not in r
    r = tv_redact("auth: token=secretvalue123abc fail")
    assert "secretvalue123abc" not in r
    r = tv_redact("normal text 12345")
    assert r == "normal text 12345"
    assert tv_redact(None) is None
    assert tv_redact("") == ""


def test_verify_token_fake():
    """_verify_token voi token gia -> reason='invalid_token' (HTTP 401)."""
    from ihg_core.token_vault import _verify_token
    r = _verify_token("fake-token-12345678",
                      "https://api.agentshop247.com/api/claude", timeout_s=10)
    assert r["ok"] is False
    assert r["status"] == 401
    assert r["reason"] in ("invalid_token", "auth_header_missing")
    # KHONG bao gio chua token value
    assert "fake-token-12345678" not in json.dumps(r)
    # Co fingerprint (an toan in ra log)
    assert r["fingerprint"].startswith("sha256:")


def test_verify_token_bad_url():
    """_verify_token voi URL khong phan hoi -> reason='gateway_unreachable' hoac 'timeout'."""
    from ihg_core.token_vault import _verify_token
    r = _verify_token("anytoken-12345678", "https://this-does-not-exist-12345.invalid",
                      timeout_s=3)
    assert r["ok"] is False
    assert r["reason"] in ("gateway_unreachable", "timeout", "url_error",
                           "exception:RemoteDisconnected")


def test_verify_token_no_input():
    """_verify_token voi input rong -> reason='missing_input'."""
    from ihg_core.token_vault import _verify_token
    assert _verify_token("", "https://x.com")["reason"] == "missing_input"
    assert _verify_token(None, "https://x.com")["reason"] == "missing_input"
    assert _verify_token("abc", "")["reason"] == "missing_input"


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
