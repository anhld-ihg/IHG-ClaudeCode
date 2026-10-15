"""ihg_core.gateway_runtime — goi AI that qua Anthropic-compatible HTTP gateway.

Thiet ke:
- Doc base URL va model tu Config (khong hard-code).
- Token doc tu env var (ten env lay tu Config.GATEWAY_TOKEN_ENV).
- KHONG log gia tri token. Chi log: "present" hoac "missing", va 4 ky tu dau.
- Co co che retry co gioi han cho 429/5xx/timeout.
- Tra ve RuntimeResult giong ClaudeCliRuntime de khong sua code caller.

Bao mat:
- Che token trong log (chi ghi 4 ky tu dau cua sha hoac 'unset').
- Timeout khong vuot qua Config.GATEWAY_TIMEOUT_S.
- Request body chi chua: model, max_tokens, messages. Khong kem metadata nhay cam.
"""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from .config import Config
from .agent_runtime import AgentRuntime, RuntimeResult
from .registry import AgentManifest
from .token_vault import TokenVault  # noqa: E402


def _token_fingerprint(token: str) -> str:
    """Tra ve fingerprint an toan cua token (4 ky tu dau cua sha256).
    Dung de log, KHONG phai de so sanh token."""
    if not token:
        return "unset"
    h = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"sha256:{h[:8]}"


class GatewayRuntime(AgentRuntime):
    name = "gateway"

    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout_s: Optional[int] = None,
        max_retry: Optional[int] = None,
        use_vault: bool = True,
    ):
        self.base_url = (base_url or Config.GATEWAY_BASE_URL).rstrip("/")
        # Token: uu tien thu tu (chi mot nguon duoc doc)
        # 1) Constructor (chi cho test)
        # 2) Windows Credential Manager vault (DPAPI-encrypted) neu use_vault=True
        # 3) Env var (Config.GATEWAY_TOKEN_ENV)
        token_env = Config.GATEWAY_TOKEN_ENV
        if token is not None:
            self._token = token
            self._token_source = "constructor"
        elif use_vault:
            try:
                vault = TokenVault()
                vt = vault.get()
                if vt:
                    self._token = vt
                    self._token_source = "vault"
                else:
                    # Fallback env
                    self._token = os.environ.get(token_env, "")
                    self._token_source = "env"
            except Exception:
                self._token = os.environ.get(token_env, "")
                self._token_source = "env"
        else:
            self._token = os.environ.get(token_env, "")
            self._token_source = "env"
        self.default_model = default_model or Config.GATEWAY_DEFAULT_MODEL
        self.timeout_s = timeout_s if timeout_s is not None else Config.GATEWAY_TIMEOUT_S
        self.max_retry = max_retry if max_retry is not None else Config.GATEWAY_MAX_RETRY

    def available(self) -> bool:
        """Co the su dung neu: GATEWAY_ENABLED, base_url co, va token co gia tri."""
        if not Config.GATEWAY_ENABLED:
            return False
        if not self.base_url:
            return False
        if not self._token:
            return False
        return True

    def status(self) -> dict:
        """Bao cao trang thai runtime (khong lo token)."""
        return {
            "runtime": self.name,
            "enabled": Config.GATEWAY_ENABLED,
            "base_url": self.base_url or "(unset)",
            "token_env": Config.GATEWAY_TOKEN_ENV,
            "token_source": getattr(self, "_token_source", "unknown"),
            "token_present": bool(self._token),
            "token_fingerprint": _token_fingerprint(self._token),
            "default_model": self.default_model,
            "timeout_s": self.timeout_s,
            "max_retry": self.max_retry,
        }

    def _build_url(self) -> str:
        """Anthropic Messages API path."""
        if not self.base_url:
            return ""
        # Neu base URL co /v1 thi khong them, neu khong them /v1/messages
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/messages"
        return f"{self.base_url}/v1/messages"

    def _build_request_body(self, agent: AgentManifest, prompt: str) -> dict:
        """Build body theo Anthropic Messages API schema.
        Moi agent co system prompt rieng (agent.prompt_template)."""
        body = {
            "model": agent.model or self.default_model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        # Neu agent co system prompt, them vao
        if agent.prompt_template and agent.prompt_template.strip():
            body["system"] = agent.prompt_template.strip()
        return body

    def _http_post(self, url: str, body: dict) -> tuple:
        """POST JSON den URL. Tra ve (status_code, response_text, error_str)."""
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "x-api-key": self._token,           # Anthropic SDK style
                "anthropic-version": "2023-06-01",  # Anthropic API version
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                text = resp.read().decode("utf-8", errors="replace")
                return (resp.status, text, "")
        except urllib.error.HTTPError as e:
            text = ""
            try:
                text = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            return (e.code, text, f"http_{e.code}")
        except urllib.error.URLError as e:
            return (0, "", f"url_error: {e.reason}")
        except TimeoutError:
            return (0, "", "timeout")
        except Exception as e:
            return (0, "", f"exception: {type(e).__name__}: {e}")

    def _extract_text(self, response_body: dict) -> str:
        """Anthropic Messages response: content la list cua {type, text}."""
        if not isinstance(response_body, dict):
            return ""
        contents = response_body.get("content") or []
        parts = []
        for item in contents:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(parts).strip()

    def _classify_error(self, status: int, error_str: str) -> str:
        """Phan loai loi de coordinator xu ly (retry / blocked / unavailable)."""
        if status == 401 or status == 403:
            return "auth_failed"
        if status == 429:
            return "rate_limited"
        if status >= 500:
            return "server_error"
        if "timeout" in error_str:
            return "timeout"
        if "url_error" in error_str:
            return "network_unreachable"
        if status == 0:
            return "network_error"
        return "http_error"

    def invoke(self, agent: AgentManifest, prompt: str, **kwargs) -> RuntimeResult:
        if not self.available():
            s = self.status()
            missing = []
            if not s["enabled"]:
                missing.append("disabled")
            if s["base_url"] == "(unset)":
                missing.append("base_url")
            if not s["token_present"]:
                missing.append(f"token({s['token_env']})")
            return RuntimeResult(
                success=False, runtime=self.name,
                reason="gateway_unavailable",
                error=f"thieu: {', '.join(missing)}",
            )

        url = self._build_url()
        body = self._build_request_body(agent, prompt)

        last_status = 0
        last_error = ""
        last_body = ""

        # Retry loop: retryable = 429, 5xx, timeout, network_error
        attempts = self.max_retry + 1
        for attempt in range(1, attempts + 1):
            t0 = time.time()
            status, text, err = self._http_post(url, body)
            duration = time.time() - t0
            last_status = status
            last_error = err
            last_body = text

            # Success: 200
            if status == 200:
                try:
                    parsed = json.loads(text)
                except Exception as e:
                    return RuntimeResult(
                        success=False, runtime=self.name,
                        returncode=status, duration_s=duration,
                        error=f"response khong phai JSON: {e}",
                        reason="bad_response",
                        raw={"status": status, "body_head": text[:300]},
                    )
                output = self._extract_text(parsed)
                if not output:
                    return RuntimeResult(
                        success=False, runtime=self.name,
                        returncode=status, duration_s=duration,
                        error="response 200 nhung khong co text content",
                        reason="empty_response",
                        raw={"status": status, "body": parsed},
                    )
                return RuntimeResult(
                    success=True, runtime=self.name,
                    returncode=0, output=output,
                    duration_s=duration,
                    reason="",
                    raw={
                        "status": status,
                        "model": parsed.get("model"),
                        "usage": parsed.get("usage"),
                        "stop_reason": parsed.get("stop_reason"),
                        "attempt": attempt,
                        "token_fingerprint": _token_fingerprint(self._token),
                    },
                )

            reason = self._classify_error(status, err)
            # Retryable
            if reason in ("rate_limited", "server_error", "timeout", "network_error", "network_unreachable"):
                if attempt < attempts:
                    # Exponential backoff: 1s, 2s, 4s...
                    time.sleep(min(2 ** (attempt - 1), 4))
                    continue

            # Non-retryable hoac het retry
            break

        # Het retry / non-retryable
        return RuntimeResult(
            success=False, runtime=self.name,
            returncode=last_status, error=last_error or f"http {last_status}",
            reason=self._classify_error(last_status, last_error),
            raw={
                "status": last_status,
                "body_head": last_body[:500],
                "attempts": min(attempts, self.max_retry + 1),
            },
        )


# Registry hook (de get_runtime('gateway') tra ve GatewayRuntime)
def _register_gateway():
    from . import agent_runtime
    agent_runtime._RUNTIMES["gateway"] = GatewayRuntime


_register_gateway()


if __name__ == "__main__":
    import sys
    r = GatewayRuntime()
    print(json.dumps(r.status(), indent=2, ensure_ascii=False))
    print("available:", r.available())
    if r.available():
        from .registry import Registry
        agent = Registry().get("ihg-it")
        # Prompt rat ngan, khong kem du lieu nhay cam
        res = r.invoke(agent, "Tra ve dung 1 cau: ping")
        print(json.dumps(res.to_dict(), ensure_ascii=False, indent=2))
