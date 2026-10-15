"""ihg_core.config — cau hinh duong dan qua bien moi truong.

KHONG hard-code parents[N] hoac duong dan worktree.
Moi thu muc phai qua env var (co fallback mac dinh).

Thu tu uu tien (uu tien thap den cao):
1. Hard-code default trong class
2. File runtime/ihg.env (KEY=value, moi dong 1 cap)
3. Environment variable
4. Heuristic tuyet doi cuoi cung
"""
import os
from pathlib import Path


_ENV_FILE_LOADED = False


def _load_env_file():
    """Load runtime/ihg.env neu co. Chi load 1 lan."""
    global _ENV_FILE_LOADED
    if _ENV_FILE_LOADED:
        return
    _ENV_FILE_LOADED = True
    root = _root()
    env_file = root / "runtime" / "ihg.env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v


def _root() -> Path:
    """Thu muc goc IHG (worktree hoac repo).
    Mac dinh: thu muc hien tai neu co .claude hoac AI-Office, nguoc lai parent cua src/."""
    env = os.environ.get("IHG_ROOT")
    if env:
        return Path(env).resolve()
    # Heuristic: len cho den khi thay AI-Office hoac .claude
    p = Path.cwd().resolve()
    for _ in range(8):
        if (p / "AI-Office").exists() and (p / ".claude").exists():
            return p
        p = p.parent
    # Fallback: thu muc chua src/
    return Path(__file__).resolve().parents[3]


def _sub(name: str, default_relative_to_root: str) -> Path:
    env_key = f"IHG_{name.upper()}"
    val = os.environ.get(env_key)
    if val:
        return Path(val).resolve()
    return _root() / default_relative_to_root


class Config:
    # Load env file truoc khi tinh toan
    IHG_ROOT = _root()
    _ = _load_env_file()  # nap runtime/ihg.env vao os.environ neu co
    IHG_ROOT = _root()  # tinh lai sau khi load env
    STATE_DIR = _sub("state_dir", "state")
    OUTPUT_DIR = _sub("output_dir", "output")
    KNOWLEDGE_DIR = _sub("knowledge_dir", "knowledge")
    PRIVATE_CORE_DIR = _sub("private_core_dir", "private_core")
    SECOND_BRAIN_DIR = _sub("second_brain_dir", "knowledge/second-brain")
    AI_OFFICE_DIR = _sub("ai_office_dir", "AI-Office")
    LOG_DIR = _sub("log_dir", "logs")
    AGENT_RUNTIME_BIN = os.environ.get("IHG_AGENT_RUNTIME_BIN", "claude")
    AGENT_RUNTIME_TIMEOUT = int(os.environ.get("IHG_AGENT_RUNTIME_TIMEOUT", "120"))
    PRINCIPAL = os.environ.get("IHG_PRINCIPAL", "gd-ihg")
    MAX_RETRY = int(os.environ.get("IHG_MAX_RETRY", "2"))

    # Gateway (Anthropic-compatible API)
    # Base URL mac dinh. Co the doi qua env IHG_GATEWAY_BASE_URL
    GATEWAY_BASE_URL = os.environ.get("IHG_GATEWAY_BASE_URL", "").rstrip("/")
    # Ten env var chua token (khong hard-code gia tri)
    GATEWAY_TOKEN_ENV = os.environ.get("IHG_GATEWAY_TOKEN_ENV", "ANTHROPIC_AUTH_TOKEN")
    # Model mac dinh neu agent không chỉ định
    GATEWAY_DEFAULT_MODEL = os.environ.get("IHG_GATEWAY_DEFAULT_MODEL", "claude-opus-5-5")
    # Timeout goi HTTP (giay)
    GATEWAY_TIMEOUT_S = int(os.environ.get("IHG_GATEWAY_TIMEOUT_S", "60"))
    # So lan retry mac dinh cho loi 429/5xx/timeouts
    GATEWAY_MAX_RETRY = int(os.environ.get("IHG_GATEWAY_MAX_RETRY", "2"))
    # Bat/tat runtime gateway (cho phep bat/tat ma khong sua code)
    GATEWAY_ENABLED = os.environ.get("IHG_GATEWAY_ENABLED", "true").lower() in ("1", "true", "yes")

    @classmethod
    def ensure(cls):
        for d in [cls.STATE_DIR, cls.OUTPUT_DIR, cls.LOG_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    @classmethod
    def summary(cls) -> dict:
        return {
            "IHG_ROOT": str(cls.IHG_ROOT),
            "STATE_DIR": str(cls.STATE_DIR),
            "OUTPUT_DIR": str(cls.OUTPUT_DIR),
            "KNOWLEDGE_DIR": str(cls.KNOWLEDGE_DIR),
            "PRIVATE_CORE_DIR": str(cls.PRIVATE_CORE_DIR),
            "AI_OFFICE_DIR": str(cls.AI_OFFICE_DIR),
            "LOG_DIR": str(cls.LOG_DIR),
            "AGENT_RUNTIME_BIN": cls.AGENT_RUNTIME_BIN,
            "PRINCIPAL": cls.PRINCIPAL,
            "GATEWAY_ENABLED": cls.GATEWAY_ENABLED,
            "GATEWAY_BASE_URL": cls.GATEWAY_BASE_URL or "(unset)",
            "GATEWAY_TOKEN_ENV": cls.GATEWAY_TOKEN_ENV,
            "GATEWAY_DEFAULT_MODEL": cls.GATEWAY_DEFAULT_MODEL,
            "GATEWAY_TOKEN_PRESENT": bool(os.environ.get(cls.GATEWAY_TOKEN_ENV, "")),
        }


if __name__ == "__main__":
    import json
    Config.ensure()
    print(json.dumps(Config.summary(), indent=2, ensure_ascii=False))
