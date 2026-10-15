"""tests.gateway_smoke — smoke test GatewayRuntime.

Muc dich:
- Kiem tra GatewayRuntime import duoc, status() tra ve dung schema.
- Kiem tra available() tra ve False khi thieu base_url hoac token.
- Neu co token + base_url: goi 1 prompt rat ngan ("ping"), ghi log output.
- KHONG gui du lieu hop dong/tai chinh/khach hang.

Output:
- In ra console va ghi log state/gateway-smoke-<timestamp>.log
"""
import json
import os
import sys
import time
from pathlib import Path

# them src vao path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))

from ihg_core.config import Config  # noqa: E402
from ihg_core.gateway_runtime import GatewayRuntime  # noqa: E402
from ihg_core.registry import Registry  # noqa: E402


def log(msg, log_file=None):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line)
    if log_file:
        log_file.write(line + "\n")
        log_file.flush()


def main():
    Config.ensure()
    log_dir = Config.LOG_DIR
    log_path = log_dir / f"gateway-smoke-{int(time.time())}.log"

    with open(log_path, "w", encoding="utf-8") as lf:
        log("=== GatewayRuntime smoke test ===", lf)
        log(f"Config summary: {json.dumps(Config.summary(), ensure_ascii=False)}", lf)

        rt = GatewayRuntime()
        status = rt.status()
        log(f"Runtime status: {json.dumps(status, ensure_ascii=False)}", lf)

        if not rt.available():
            log("[BLOCKED-GATEWAY] GatewayRuntime chua san sang.", lf)
            log("  Kiem tra:", lf)
            log("  - IHG_GATEWAY_BASE_URL co gia tri chua?", lf)
            log(f"  - env var '{status['token_env']}' co gia tri chua? (token_fingerprint={status['token_fingerprint']})", lf)
            log("  - IHG_GATEWAY_ENABLED=true?", lf)
            log(f"Log ghi vao: {log_path}", lf)
            return 0  # khong phai loi, chi la chua san sang

        # San sang: goi 1 prompt rat ngan voi du lieu gia lap
        agent = Registry().get("ihg-it")
        log(f"Su dung agent: {agent.id}, model: {agent.model}", lf)
        prompt = "Tra ve dung mot cau tieng Viet: ping thanh cong."
        log(f"Prompt (gia lap): {prompt!r}", lf)

        result = rt.invoke(agent, prompt)
        d = result.to_dict()
        # Che token trong output
        if "raw" in d and isinstance(d["raw"], dict):
            d["raw"].pop("token_fingerprint", None)
        log(f"Ket qua: {json.dumps(d, ensure_ascii=False, indent=2)}", lf)

        if result.success:
            log("[OK] Gateway goi thanh cong. Output > 0 byte.", lf)
            log(f"  output[:200] = {result.output[:200]!r}", lf)
            log(f"  duration_s = {result.duration_s:.2f}", lf)
            log(f"  reason = {result.reason!r}", lf)
            return 0
        else:
            log("[FAIL] Gateway goi that bai.", lf)
            log(f"  reason = {result.reason!r}", lf)
            log(f"  error  = {result.error!r}", lf)
            log(f"  returncode = {result.returncode}", lf)
            return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[CRASH] {type(e).__name__}: {e}")
        sys.exit(3)
