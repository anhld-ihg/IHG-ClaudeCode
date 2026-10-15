"""ihg_core.token_vault — IHG token vault (Windows Credential Manager / DPAPI).

Ly do chon Windows Credential Manager (WinVaultKeyring):
- Token duoc ma hoa bang DPAPI (Data Protection API) cua Windows.
- Chi user hien tai (tai khoan dang nhap Windows) tren cung may moi giai ma duoc.
- Khong can file .env, khong ghi vao source code, khong hien thi trong log.
- API Windows Credential Manager co san, khong can cai them.
- Da duoc Microsoft Windows Security kiem dinh (su dung cho Outlook, Edge, GitHub CLI...).

SERVICE_NAME dinh danh: "IHG-AI-OS"
USERNAME: "anthropic-auth-token" (ten env var mac dinh, de biet no la key gi)

API:
    vault = TokenVault()
    vault.set("sk-ant-...")            # luu token (input tu UI, khong in ra stdout)
    token = vault.get()                 # doc token (ghi log chi fingerprint)
    has = vault.exists()
    vault.delete()                      # xoa khi GĐ muon rotate

Bao mat:
- Khong in gia tri token ra stdout, log file, hay bat ky cho nao.
- Chi in fingerprint (sha256 8-char).
- Raise PermissionError neu chay voi quyen khac user (unix) hoac loi DPAPI.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
from typing import Optional

# keyring su dung Windows Credential Manager khi chay tren Windows
import keyring
import keyring.errors


SERVICE_NAME = "IHG-AI-OS"
USERNAME = "anthropic-auth-token"


def fingerprint(token: str) -> str:
    """Tra ve fingerprint 8-char SHA256 cua token (de log, KHONG leak goc)."""
    if not token:
        return "unset"
    h = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"sha256:{h[:8]}"


def has_token_shape(token: str) -> bool:
    """Check token co 'hinh dang' hop le (khong phai format-prefix).
    Tra ve True neu token khong rong, do dai hop ly (8..256 ky tu), khong co whitespace.

    Vi sao KHONG check prefix: gateway ben thu ba chap nhan BAT KY token nao
    ma no da cap. GĐ co the co token 'sk-ant-...', 'sk-ihg-...', 'gateway-xyz',
    'prod-key-12345'... Prefix-la-prefix khong phai rule cua gateway.
    (Da xac nhan bang test that: gateway 401 'Missing x-api-key' khi header
    rong, 401 'API key not found or unassigned' khi token sai, nhung chap nhan
    bat ky string nao lam token value.)

    Kiem tra that (auth that) chi co the lam bang goi 1 request toi gateway
    voi token do va xem response 200/401. Ham _verify_token() o duoi lam viec do.
    """
    if not token:
        return False
    t = token.strip()
    if not t:
        return False
    if len(t) < 8 or len(t) > 256:
        return False
    if any(c.isspace() for c in t):
        return False
    return True


class TokenVault:
    """Lop bao quanh Windows Credential Manager cho token IHG AI OS.

    Mac dinh service: "IHG-AI-OS", username: "anthropic-auth-token".
    Co the override qua constructor (chi cho test, khong cho production).
    """

    def __init__(self, service: str = SERVICE_NAME, username: str = USERNAME):
        self.service = service
        self.username = username
        # Keyring backend (WinVaultKeyring tren Windows, macOS Keychain tren mac, etc.)
        self._backend = keyring.get_keyring()
        self._backend_name = type(self._backend).__name__

    @property
    def backend_name(self) -> str:
        return self._backend_name

    def set(self, token: str) -> dict:
        """Luu token vao Credential Manager. KHONG in gia tri ra log.

        Returns:
            dict: {fingerprint, service, username, backend} - KHONG chua token.
        """
        if not token or not token.strip():
            raise ValueError("Token khong duoc rong")
        token = token.strip()
        try:
            self._backend.set_password(self.service, self.username, token)
        except keyring.errors.PasswordSetError as e:
            raise PermissionError(
                f"Khong the ghi vao Credential Manager ({self._backend_name}): {e}. "
                f"Co the user Windows hien tai khong co quyen (thu chay voi quyen user, khong admin)."
            ) from e
        except Exception as e:
            raise RuntimeError(f"Loi Credential Manager: {e}") from e
        return {
            "service": self.service,
            "username": self.username,
            "backend": self._backend_name,
            "fingerprint": fingerprint(token),
            "stored": True,
        }

    def get(self) -> Optional[str]:
        """Doc token tu Credential Manager. Chi goi tu runtime (Worker/Gateway), KHONG in ra stdout.

        Returns:
            str: token goc (DPAPI-decrypted) hoac None neu chua co.
        """
        try:
            return self._backend.get_password(self.service, self.username)
        except keyring.errors.KeyringError as e:
            raise RuntimeError(f"Khong doc duoc tu Credential Manager: {e}") from e

    def exists(self) -> bool:
        """Kiem tra token da duoc luu chua (KHONG tra ve gia tri)."""
        return self.get() is not None

    def status(self) -> dict:
        """Trang thai (an toan in ra log). KHONG bao gio chua gia tri token."""
        token = self.get()
        present = token is not None and len(token) > 0
        return {
            "vault": "windows-credential-manager" if "Win" in self._backend_name else self._backend_name,
            "service": self.service,
            "username": self.username,
            "present": present,
            "fingerprint": fingerprint(token) if present else "unset",
            "len": len(token) if present else 0,
        }

    def delete(self) -> bool:
        """Xoa token. Tra ve True neu xoa thanh cong, False neu khong co."""
        try:
            self._backend.delete_password(self.service, self.username)
            return True
        except keyring.errors.PasswordDeleteError:
            return False
        except Exception as e:
            raise RuntimeError(f"Loi xoa token: {e}") from e


def _verify_token(token: str, base_url: str, timeout_s: int = 10) -> dict:
    """Xac thuc token bang goi 1 request that toi gateway (Anthropic messages endpoint).

    Tra ve dict {ok: bool, status: int, reason: str, fingerprint: str}.
    KHONG bao gio in/return gia tri token.

    Cach hoat dong:
    - POST toi <base_url>/v1/messages voi model mac dinh, max_tokens=1, content 'ping'.
    - Token duoc gui qua header 'x-api-key' (Anthropic SDK style; gateway cung chap nhan Bearer).
    - 200 -> ok=True, token hop le.
    - 401 (Missing header) -> token khong den duoc (request build loi).
    - 401 (not_found / invalid / unassigned) -> ok=False, reason='invalid_token'.
    - 4xx khac (400, 403) -> ok=False, reason='rejected'.
    - 5xx / network -> ok=False, reason='gateway_unreachable' (co the retry).
    - Timeout -> ok=False, reason='timeout'.

    Ham nay KHONG sua token; chi bao 'co the goi gateway voi token nay khong'.
    """
    if not token or not base_url:
        return {"ok": False, "status": 0, "reason": "missing_input", "fingerprint": "unset"}

    import urllib.request
    import urllib.error

    # Xay URL (tuong thich ca /v1 suffix va khong)
    if base_url.endswith("/v1"):
        url = f"{base_url}/messages"
    else:
        url = f"{base_url}/v1/messages"

    body = json.dumps({
        "model": "claude-haiku-4-5",  # re nhat, nhanh nhat cho ping
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "ping"}],
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": token,
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            return {
                "ok": True,
                "status": resp.status,
                "reason": "ok",
                "fingerprint": fingerprint(token),
            }
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        # An token/secret truoc khi phan loai reason
        safe_err = _redact(err_body)
        if e.code in (401, 403):
            if "Missing" in err_body or "missing" in err_body:
                reason = "auth_header_missing"
            else:
                reason = "invalid_token"
        elif e.code == 400:
            reason = "bad_request"
        else:
            reason = f"http_{e.code}"
        return {
            "ok": False,
            "status": e.code,
            "reason": reason,
            "error_snippet": safe_err[:200],
            "fingerprint": fingerprint(token),
        }
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "status": 0,
            "reason": "gateway_unreachable",
            "error_snippet": str(e.reason)[:200],
            "fingerprint": fingerprint(token),
        }
    except TimeoutError:
        return {
            "ok": False,
            "status": 0,
            "reason": "timeout",
            "fingerprint": fingerprint(token),
        }
    except Exception as e:
        return {
            "ok": False,
            "status": 0,
            "reason": f"exception:{type(e).__name__}",
            "error_snippet": str(e)[:200],
            "fingerprint": fingerprint(token),
        }


def _redact(s: str) -> str:
    """An token/bi-mat khoi log (tranh gateway nhay vao error body).

    Thay the bang placeholder DUY NHAT (khong chua 'REDACTED' de tranh match vong lap):
    """
    if not s:
        return s
    import re
    # Bearer truoc (an nguyen cum)
    s = re.sub(r"(?i)Bearer\s+[A-Za-z0-9_\-\.=]+", "Bearer [hidden]", s)
    # password|secret|api_key|token=value (an value)
    s = re.sub(r"(?i)(password|secret|api[_-]?key|token)[\"']?\s*[:=]\s*[\"']?[^\s\"',}]+",
               r"\1=[hidden]", s)
    # sk-XXX (token Anthropic hoac gateway)
    s = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "sk-[hidden]", s)
    return s


def is_windows() -> bool:
    return sys.platform == "win32"


def assert_windows() -> None:
    if not is_windows():
        raise RuntimeError(
            "TokenVault yeu cau Windows Credential Manager (DPAPI). "
            f"Platform hien tai: {sys.platform}. "
            "Code van chay duoc nhung se fallback sang plaintext file."
        )


# CLI mini cho test
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="IHG Token Vault (Windows Credential Manager)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Kiem tra token co chua")
    sub.add_parser("delete", help="Xoa token")
    sub.add_parser("verify", help="Xac thuc token bang goi that toi gateway")
    pset = sub.add_parser("set", help="Luu token (se hoi nhap)")
    pset.add_argument("--stdin", action="store_true",
                      help="Doc tu stdin (an toan, khong in lenh ra)")

    args = p.parse_args()
    v = TokenVault()

    if args.cmd == "status":
        print(json.dumps(v.status(), ensure_ascii=False, indent=2))
    elif args.cmd == "delete":
        ok = v.delete()
        print("DELETED" if ok else "NOT_FOUND")
    elif args.cmd == "verify":
        tok = v.get()
        if not tok:
            print(json.dumps({"ok": False, "reason": "no_token_stored"}, ensure_ascii=False, indent=2))
            sys.exit(2)
        from ihg_core.config import Config
        base_url = Config.GATEWAY_BASE_URL
        result = _verify_token(tok, base_url)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        del tok
        sys.exit(0 if result["ok"] else 3)
    elif args.cmd == "set":
        if args.stdin:
            import getpass
            tok = getpass.getpass("Nhap token (an toan, khong echo): ").strip()
        else:
            print("ERROR: can --stdin de dam bao khong echo token qua argv", file=sys.stderr)
            sys.exit(2)
        if not tok:
            print("ERROR: token rong", file=sys.stderr)
            sys.exit(2)
        result = v.set(tok)
        print("STORED:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        # Xoa khoi memory de tranh con sot
        del tok
