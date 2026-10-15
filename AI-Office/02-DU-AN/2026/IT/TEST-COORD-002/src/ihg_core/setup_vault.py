"""ihg_core.setup_vault — CLI an toan de GĐ nhap token mot lan.

Workflow:
  1. GĐ chay: python -m ihg_core.setup_vault
  2. CLI hoi Gateway URL (mac dinh san)
  3. CLI hoi token (dung getpass, KHONG echo)
  4. Token duoc luu vao Windows Credential Manager (DPAPI)
  5. Verify that: goi 1 request toi gateway de xac nhan token hoat dong
  6. In ra fingerprint (sha256 8-char) de GĐ xac nhan

Token KHONG bao gio:
- Hien thi tren stdout (chi fingerprint)
- Ghi vao file .env / source code
- Truyen qua argv (chi qua stdin / getpass)
- In trong log/bao cao (redactor loc truoc khi in)
- Doc lai tu file backup, cookie, log cũ
"""
import argparse
import getpass
import json
import os
import sys
from pathlib import Path

# them src vao path
HERE = Path(__file__).resolve()
SRC = HERE.parent
sys.path.insert(0, str(SRC.parent))

from ihg_core.token_vault import (  # noqa: E402
    TokenVault, fingerprint, has_token_shape, _verify_token
)
from ihg_core.config import Config  # noqa: E402


def _redact(s: str) -> str:
    """An toan hoa text truoc khi in: xoa token/secret/bi-mat co the xuat hien trong error.

    Dung placeholder don gian [hidden] de tranh pattern REDACTED bi match vong lap.
    """
    if not s:
        return s
    import re
    s = re.sub(r"(?i)Bearer\s+[A-Za-z0-9_\-\.=]+", "Bearer [hidden]", s)
    s = re.sub(r"(?i)(password|secret|api[_-]?key|token)[\"']?\s*[:=]\s*[\"']?[^\s\"',}]+",
               r"\1=[hidden]", s)
    s = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "sk-[hidden]", s)
    return s[:1000]


def ask(question: str, default: str = "", secret: bool = False) -> str:
    if secret:
        return getpass.getpass(question + " ").strip()
    prompt = f"{question}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    val = input(prompt).strip()
    return val if val else default


def cmd_status(vault: TokenVault) -> int:
    """In trang thai vault (KHONG bao gom token)."""
    print(json.dumps(vault.status(), ensure_ascii=False, indent=2))
    return 0


def cmd_delete(vault: TokenVault) -> int:
    """Xoa token khoi Credential Manager."""
    ok = vault.delete()
    print(json.dumps({"action": "delete", "deleted": ok, "status": vault.status()},
                     ensure_ascii=False, indent=2))
    return 0


def cmd_setup(vault: TokenVault, gateway_url_arg: str = None, auto_test: bool = False) -> int:
    """Flow chinh: nhap URL + token, luu, verify."""
    print("=== Trang thai vault hien tai ===")
    print(json.dumps(vault.status(), ensure_ascii=False, indent=2))
    print()

    # 1) URL
    default_url = (gateway_url_arg or Config.GATEWAY_BASE_URL
                   or "https://api.agentshop247.com/api/claude")
    url = ask("Gateway URL", default=default_url)
    if not url.startswith("https://"):
        print("ERROR: URL phai bat dau bang https://", file=sys.stderr)
        return 2
    if "localhost" in url or "127.0.0.1" in url:
        print("ERROR: Khong cho phep localhost (chi gateway that)", file=sys.stderr)
        return 2

    # 2) Token (getpass -> khong echo)
    print()
    print("Token duoc luu ma hoa bang DPAPI. Ky tu nhap se bi an.")
    token = ask("API token:", secret=True)
    if not token:
        print("ERROR: Token rong", file=sys.stderr)
        return 2

    # 3) Check shape (khong check prefix cu the - gateway chap nhan bat ky)
    if not has_token_shape(token):
        print(f"ERROR: Token co hinh dang khong hop le (do dai 8..256, khong co whitespace).",
              file=sys.stderr)
        del token
        return 2

    # 4) Luu truoc
    result = vault.set(token)
    print()
    print("=== Da luu token ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()

    # 5) Verify that (KHONG in token - chi in fingerprint va reason)
    print("=== Xac thuc token voi gateway (1 request that) ===")
    verify = _verify_token(token, url, timeout_s=15)
    # In ket qua an toan (khong co token, chi fingerprint + reason)
    print(json.dumps({
        "ok": verify.get("ok"),
        "status": verify.get("status"),
        "reason": verify.get("reason"),
        "fingerprint": verify.get("fingerprint"),
        "error_snippet": _redact(verify.get("error_snippet", "")) if not verify.get("ok") else None,
    }, ensure_ascii=False, indent=2))

    # Xoa token khoi memory SOMAT SAU khi verify
    del token

    if not verify.get("ok"):
        print()
        print("Token da luu NHUNG verify that that bai (reason: " + verify.get("reason", "?") + ").",
              file=sys.stderr)
        print("Ly do co the: token sai, het han, hoac gateway tam thoi khong phan hoi.",
              file=sys.stderr)
        print("Goi y:", file=sys.stderr)
        print("  - Kiem tra lai token tu nha cung cap", file=sys.stderr)
        print("  - Thu lai: python -m ihg_core.token_vault verify", file=sys.stderr)
        print("  - Neu token sai, dat lai: python -m ihg_core.setup_vault",
              file=sys.stderr)
        return 7  # verify fail - token van o vault nhung can xac nhan

    # 6) Smoke test (optional) - goi 1 agent gia lap
    if auto_test or ask("Chay smoke test voi prompt gia lap? (y/n)", default="n").lower() in ("y", "yes"):
        print()
        print("=== Smoke test ===")
        from ihg_core.gateway_runtime import GatewayRuntime
        from ihg_core.registry import AgentManifest
        # Lay lai token tu vault (runtime can no)
        tok = vault.get()
        if not tok:
            print("ERROR: Khong doc duoc token tu vault", file=sys.stderr)
            return 4
        rt = GatewayRuntime(base_url=url, token=tok, timeout_s=30, max_retry=1)
        del tok
        if not rt.available():
            print(f"ERROR: Runtime khong san sang: {json.dumps(rt.status(), ensure_ascii=False)}",
                  file=sys.stderr)
            return 5
        agent = AgentManifest(
            id="smoke", name="smoke", kind="ai_agent", runtime="gateway",
            capabilities=[], allowed_paths=[], model=Config.GATEWAY_DEFAULT_MODEL
        )
        prompt = "Tra ve 1 cau: ping thanh cong (smoke test tu IHG-AI-OS)"
        print(f"Prompt: {prompt}")
        print("Dang goi gateway...")
        r = rt.invoke(agent, prompt)
        print()
        print("=== Ket qua smoke ===")
        print(json.dumps({
            "success": r.success,
            "reason": r.reason,
            "error": _redact(r.error or ""),
            "returncode": r.returncode,
            "output": r.output[:500],  # cat de tranh leak qua stdout
            "duration_s": round(r.duration_s, 2) if hasattr(r, "duration_s") else None,
            "model": (r.raw or {}).get("model"),
            "input_tokens": (r.raw or {}).get("usage", {}).get("input_tokens", 0),
            "output_tokens": (r.raw or {}).get("usage", {}).get("output_tokens", 0),
        }, ensure_ascii=False, indent=2))
        return 0 if r.success else 6

    print()
    print("Setup xong. Worker se tu dong doc token tu vault.")
    print("Kiem tra: python -m ihg_core.token_vault status")
    print("Xac thuc: python -m ihg_core.token_vault verify")
    return 0


def main():
    p = argparse.ArgumentParser(description="IHG-AI-OS Token Vault Setup")
    p.add_argument("--gateway-url", help="Gateway URL (mac dinh: config hoac https://api.agentshop247.com/api/claude)")
    p.add_argument("--delete", action="store_true", help="Xoa token hien tai")
    p.add_argument("--status", action="store_true", help="Chi xem trang thai")
    p.add_argument("--test", action="store_true", help="Sau khi set, chay smoke test voi prompt gia lap")
    args = p.parse_args()

    vault = TokenVault()

    if args.delete:
        return cmd_delete(vault)
    if args.status:
        return cmd_status(vault)
    return cmd_setup(vault, args.gateway_url, args.test)


if __name__ == "__main__":
    sys.exit(main())
