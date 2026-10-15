"""ihg_core — IHG AI OS core modules.

Modules:
- config      : cau hinh qua env vars
- authz       : phan quyen that o tang chuong trinh (default-deny)
- state_store : state machine cho task (PENDING -> ... -> DELIVERED)
- registry    : dang ky Agent (phan biet AI Agent vs Worker)
- agent_runtime: goi AI Agent that qua Runtime (Claude CLI, mock, ...)
- worker_checksum: Worker tinh SHA-256 (Python, logic xac dinh)
- coordinator: Worker dieu phoi, goi AI Agent qua runtime
- qa_check   : QA goi qua AI Agent ihg-qa that, kem 4 check ky thuat
- second_brain: IHG Second Brain (CHẶNG 3) — 4 lớp visibility, phân quyền thật
"""
from .config import Config
from .authz import check, check_path, require
from .state_store import StateStore, StateMachineError, VALID_TRANSITIONS
from .registry import Registry, AgentManifest, DEFAULT_AGENTS
from .agent_runtime import (AgentRuntime, ClaudeCliRuntime, MockRuntime,
                             default_runtime, get_runtime, RuntimeResult)
from .gateway_runtime import GatewayRuntime
from .worker_checksum import sha256_file
from .coordinator import dispatch_task
from .qa_check import run_qa
from .second_brain import (SecondBrain, SecondBrainError, AuthzDeniedError,
                            ValidationError, Entry,
                            VIS_PUBLIC, VIS_DEPARTMENT, VIS_PROJECT, VIS_PRIVATE,
                            VERIFIED, UNVERIFIED, DEPRECATED)

__all__ = [
    "Config", "check", "check_path", "require",
    "StateStore", "StateMachineError", "VALID_TRANSITIONS",
    "Registry", "AgentManifest", "DEFAULT_AGENTS",
    "AgentRuntime", "ClaudeCliRuntime", "MockRuntime", "GatewayRuntime",
    "default_runtime", "get_runtime", "RuntimeResult",
    "sha256_file", "dispatch_task", "run_qa",
    "SecondBrain", "SecondBrainError", "AuthzDeniedError", "ValidationError", "Entry",
    "VIS_PUBLIC", "VIS_DEPARTMENT", "VIS_PROJECT", "VIS_PRIVATE",
    "VERIFIED", "UNVERIFIED", "DEPRECATED",
]
