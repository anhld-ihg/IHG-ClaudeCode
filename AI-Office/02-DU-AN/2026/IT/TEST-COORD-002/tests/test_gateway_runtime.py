"""tests.test_gateway_runtime — test GatewayRuntime (khong can token that).

Pham vi:
- Test schema: status() tra ve cac field dung, KHONG co gia tri token.
- Test available() tra ve False khi thieu base_url hoac token hoac disabled.
- Test _classify_error() mapping dung.
- Test _extract_text() voi response gia lap.
- Test request body chi chua model/max_tokens/messages/system.
- Test token fingerprint khong lo gia tri.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from ihg_core.gateway_runtime import (  # noqa: E402
    GatewayRuntime, _token_fingerprint
)
from ihg_core.config import Config  # noqa: E402


# ===== Test 1: status() schema =====
def test_status_schema_no_token():
    rt = GatewayRuntime(base_url="https://x.example.com", token="super-secret-token")
    s = rt.status()
    # Co cac field can thiet
    for k in ["runtime", "enabled", "base_url", "token_env",
              "token_present", "token_fingerprint",
              "default_model", "timeout_s", "max_retry"]:
        assert k in s, f"missing key: {k}"
    # KHONG co gia tri token
    assert "token" not in s
    assert "api_key" not in s
    # token chi la fingerprint
    assert s["token_fingerprint"].startswith("sha256:") or s["token_fingerprint"] == "unset"
    # Gia tri token that KHONG xuat hien trong s (kiem tra ca chuoi)
    s_str = json.dumps(s)
    assert "super-secret-token" not in s_str, "Token bi lo qua status!"


# ===== Test 2: available() =====
def test_available_when_no_base_url():
    rt = GatewayRuntime(base_url="", token="x")
    assert rt.available() is False


def test_available_when_no_token():
    rt = GatewayRuntime(base_url="https://x.example.com", token="")
    assert rt.available() is False


def test_available_when_disabled(monkeypatch=None):
    # Set env de GATEWAY_ENABLED=false
    import os
    old = os.environ.get("IHG_GATEWAY_ENABLED")
    os.environ["IHG_GATEWAY_ENABLED"] = "false"
    try:
        from importlib import reload
        from ihg_core import config as cfg_mod
        from ihg_core import gateway_runtime as gr_mod
        reload(cfg_mod)
        reload(gr_mod)  # can reload ca gateway_runtime vi no doc Config luc import
        from ihg_core.gateway_runtime import GatewayRuntime as GR
        from ihg_core.config import Config
        assert Config.GATEWAY_ENABLED is False
        rt = GR(base_url="https://x.example.com", token="x")
        assert rt.available() is False
    finally:
        if old is None:
            os.environ.pop("IHG_GATEWAY_ENABLED", None)
        else:
            os.environ["IHG_GATEWAY_ENABLED"] = old
        # Reload lai de khoi phuc
        from ihg_core import config as cfg_mod
        from ihg_core import gateway_runtime as gr_mod
        reload(cfg_mod)
        reload(gr_mod)


def test_available_when_all_set():
    rt = GatewayRuntime(base_url="https://x.example.com", token="x")
    assert rt.available() is True


# ===== Test 3: _token_fingerprint =====
def test_token_fingerprint_masks_value():
    fp = _token_fingerprint("super-secret-token-value")
    assert "super-secret" not in fp
    assert fp.startswith("sha256:")


def test_token_fingerprint_empty():
    assert _token_fingerprint("") == "unset"


def test_token_fingerprint_distinct():
    a = _token_fingerprint("token-A")
    b = _token_fingerprint("token-B")
    assert a != b


# ===== Test 4: _classify_error =====
def test_classify_error_401():
    rt = GatewayRuntime(base_url="https://x", token="x")
    assert rt._classify_error(401, "") == "auth_failed"


def test_classify_error_403():
    rt = GatewayRuntime(base_url="https://x", token="x")
    assert rt._classify_error(403, "") == "auth_failed"


def test_classify_error_429():
    rt = GatewayRuntime(base_url="https://x", token="x")
    assert rt._classify_error(429, "") == "rate_limited"


def test_classify_error_500():
    rt = GatewayRuntime(base_url="https://x", token="x")
    assert rt._classify_error(500, "") == "server_error"


def test_classify_error_503():
    rt = GatewayRuntime(base_url="https://x", token="x")
    assert rt._classify_error(503, "") == "server_error"


def test_classify_error_timeout():
    rt = GatewayRuntime(base_url="https://x", token="x")
    assert rt._classify_error(0, "timeout") == "timeout"


def test_classify_error_network():
    rt = GatewayRuntime(base_url="https://x", token="x")
    assert rt._classify_error(0, "url_error: dns") == "network_unreachable"


# ===== Test 5: _build_url =====
def test_build_url_with_v1_suffix():
    rt = GatewayRuntime(base_url="https://api.example.com/v1", token="x")
    url = rt._build_url()
    assert url == "https://api.example.com/v1/messages"


def test_build_url_without_v1():
    rt = GatewayRuntime(base_url="https://api.example.com", token="x")
    url = rt._build_url()
    assert url == "https://api.example.com/v1/messages"


def test_build_url_strips_trailing_slash():
    rt = GatewayRuntime(base_url="https://api.example.com/", token="x")
    url = rt._build_url()
    assert url.endswith("/v1/messages")
    assert "//v1" not in url


# ===== Test 6: _build_request_body =====
def test_build_request_body_minimal():
    from ihg_core.registry import AgentManifest
    agent = AgentManifest(id="test", name="test", kind="ai_agent", runtime="gateway",
                          capabilities=[], allowed_paths=[], model="claude-test")
    rt = GatewayRuntime(base_url="https://x", token="x")
    body = rt._build_request_body(agent, "Hello")
    assert body["model"] == "claude-test"
    assert body["max_tokens"] > 0
    assert "messages" in body
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][0]["content"] == "Hello"


def test_build_request_body_uses_default_model():
    from ihg_core.registry import AgentManifest
    agent = AgentManifest(id="test", name="test", kind="ai_agent", runtime="gateway",
                          capabilities=[], allowed_paths=[], model="")
    rt = GatewayRuntime(base_url="https://x", token="x", default_model="claude-default")
    body = rt._build_request_body(agent, "Hi")
    assert body["model"] == "claude-default"


def test_build_request_body_includes_system():
    from ihg_core.registry import AgentManifest
    agent = AgentManifest(id="test", name="test", kind="ai_agent", runtime="gateway",
                          capabilities=[], allowed_paths=[],
                          model="m", prompt_template="You are a test agent.")
    rt = GatewayRuntime(base_url="https://x", token="x")
    body = rt._build_request_body(agent, "Do")
    assert "system" in body
    assert "test agent" in body["system"]


def test_request_body_no_token_leak():
    """Body gui di KHONG bao gio chua token, metadata nhay cam, hay path local."""
    from ihg_core.registry import AgentManifest
    agent = AgentManifest(id="ihg-it", name="IT", kind="ai_agent", runtime="gateway",
                          capabilities=[], allowed_paths=[],
                          model="sonnet", prompt_template="sys prompt")
    rt = GatewayRuntime(base_url="https://x", token="my-secret-key-12345")
    body = rt._build_request_body(agent, "do task")
    body_str = json.dumps(body)
    assert "my-secret-key-12345" not in body_str
    # Khong kem path local
    assert "C:\\" not in body_str
    assert "/Users/" not in body_str


# ===== Test 7: _extract_text =====
def test_extract_text_single_text_block():
    body = {"content": [{"type": "text", "text": "Hello world"}]}
    rt = GatewayRuntime(base_url="https://x", token="x")
    assert rt._extract_text(body) == "Hello world"


def test_extract_text_multiple_blocks():
    body = {"content": [
        {"type": "text", "text": "Line 1"},
        {"type": "text", "text": "Line 2"},
    ]}
    rt = GatewayRuntime(base_url="https://x", token="x")
    assert rt._extract_text(body) == "Line 1\nLine 2"


def test_extract_text_empty():
    body = {"content": []}
    rt = GatewayRuntime(base_url="https://x", token="x")
    assert rt._extract_text(body) == ""


def test_extract_text_tool_use_ignored():
    body = {"content": [
        {"type": "tool_use", "id": "x", "name": "y", "input": {}},
        {"type": "text", "text": "only text"},
    ]}
    rt = GatewayRuntime(base_url="https://x", token="x")
    assert rt._extract_text(body) == "only text"


# ===== Test 8: invoke() voi runtime khong san sang =====
def test_invoke_unavailable_graceful():
    rt = GatewayRuntime(base_url="", token="")
    from ihg_core.registry import AgentManifest
    agent = AgentManifest(id="x", name="x", kind="ai_agent", runtime="gateway",
                          capabilities=[], allowed_paths=[], model="m")
    result = rt.invoke(agent, "test")
    assert result.success is False
    assert result.reason == "gateway_unavailable"
    # Error mo ta nhung thieu (chi ten config), KHONG gom gia tri token
    # No co the chua tu "token" (vi "token(ENV_NAME)" la config), nhung
    # KHONG duoc chua gia tri token that.
    assert "my-secret" not in result.error  # Gia tri token that
    # Phai thong bao ro thieu gi
    assert any(k in result.error.lower() for k in ["base_url", "token", "thieu"])


# ===== Test 9: status() khong bao gio in token =====
def test_status_in_str_format():
    rt = GatewayRuntime(base_url="https://x", token="PRIVATE-DO-NOT-LEAK")
    s = rt.status()
    text = str(s)
    assert "PRIVATE-DO-NOT-LEAK" not in text


if __name__ == "__main__":
    import traceback
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
            traceback.print_exc()
            failed += 1
    print(f"\n{passed}/{passed+failed} passed")
    sys.exit(0 if failed == 0 else 1)
