"""ihg_core.registry — Worker dang ky Agent.

Manifest: id, capabilities, kind, runtime, allowed_paths, prompt_template.
Hai loai Agent:
- "worker" : chuong trinh Python co logic xac dinh (KHONG phai AI Agent)
- "agent"  : AI Agent that, can runtime de goi (Claude CLI, ...)

Phan biet 2 loai de tranh nham lan.

Load tu DEFAULT_AGENTS (hard-code) hoac tu file JSON (runtime/agents.json).
"""
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .config import Config

# Co 8 Agent theo IHG AI OS, hien chua trien khai het.
# Pilot nay chi su mot subset.
DEFAULT_AGENTS = [
    {
        "id": "ihg-it",
        "name": "Phong ban IT",
        "kind": "agent",  # AI Agent
        "runtime": "claude-cli",
        "capabilities": ["code-run", "script-exec", "file-write", "build-coordinator", "doc-write"],
        "model": "sonnet",
        "allowed_paths": ["AI-Office/02-DU-AN/", "AI-Office/01-PHONG-BAN/IT/"],
        "prompt_template": (
            "Ban la Agent Phong ban IT cua IHG AI OS. "
            "Lam theo yeu cau sau, tra ve JSON: {output_marker} ket thuc."
        ),
    },
    {
        "id": "ihg-qa",
        "name": "Kiem tra chat luong",
        "kind": "agent",  # AI Agent that
        "runtime": "claude-cli",
        "capabilities": ["audit", "schema-check", "checksum-verify", "qa-review"],
        "model": "sonnet",
        "allowed_paths": ["AI-Office/02-DU-AN/"],
        "prompt_template": (
            "Ban la Agent QA cua IHG AI OS. "
            "Kiem tra san pham, tra ve JSON voi truong qa_result (PASS/FAIL/QA_UNVERIFIED)."
        ),
    },
    {
        "id": "ihg-admin-legal",
        "name": "Hanh chinh - phap ly",
        "kind": "agent",
        "runtime": "claude-cli",
        "capabilities": ["legal-check", "contract-review", "compliance-audit"],
        "model": "sonnet",
        "allowed_paths": ["AI-Office/00-DIEU-HANH/", "AI-Office/01-PHONG-BAN/HANH-CHINH-PHAP-LY/"],
        "prompt_template": "Ban la Agent Hanh chinh - Phap ly cua IHG AI OS.",
    },
    # Worker (Python script) — co logic xac dinh, khong phai AI
    {
        "id": "ihg-checksum-worker",
        "name": "Worker tinh checksum",
        "kind": "worker",
        "runtime": "python",
        "module": "ihg_core.worker_checksum",
        "capabilities": ["checksum", "sha256"],
        "allowed_paths": ["AI-Office/", "state/", "output/"],
    },
    {
        "id": "ihg-coordinator-worker",
        "name": "Worker dieu phoi",
        "kind": "worker",
        "runtime": "python",
        "module": "ihg_core.coordinator",
        "capabilities": ["dispatch", "state-mgmt", "recovery"],
        "allowed_paths": ["AI-Office/02-DU-AN/", "state/"],
    },
]


@dataclass
class AgentManifest:
    id: str
    name: str
    kind: str  # "agent" hoac "worker"
    runtime: str
    capabilities: List[str]
    allowed_paths: List[str]
    model: str = ""
    module: str = ""
    prompt_template: str = ""

    @property
    def is_ai_agent(self) -> bool:
        return self.kind == "agent"

    @property
    def is_worker(self) -> bool:
        return self.kind == "worker"


class Registry:
    def __init__(self, agents: Optional[list] = None, load_from: Optional[Path] = None):
        if load_from and Path(load_from).exists():
            with open(load_from, "r", encoding="utf-8") as f:
                data = json.load(f)
            src = data.get("agents", data if isinstance(data, list) else [])
        else:
            src = agents or DEFAULT_AGENTS
        self.agents = {a["id"]: AgentManifest(**a) for a in src}

    @classmethod
    def from_json(cls, path: Path) -> "Registry":
        return cls(load_from=path)

    def find_by_capability(self, capability: str) -> Optional[AgentManifest]:
        for a in self.agents.values():
            if capability in a.capabilities:
                return a
        return None

    def get(self, agent_id: str) -> Optional[AgentManifest]:
        return self.agents.get(agent_id)

    def all(self) -> List[AgentManifest]:
        return list(self.agents.values())

    def ai_agents(self) -> List[AgentManifest]:
        return [a for a in self.all() if a.is_ai_agent]

    def workers(self) -> List[AgentManifest]:
        return [a for a in self.all() if a.is_worker]


if __name__ == "__main__":
    import sys
    # Mac dinh load tu runtime/agents.json neu co, nguoc lai DEFAULT_AGENTS
    default_json = Config.IHG_ROOT / "runtime" / "agents.json"
    if default_json.exists():
        r = Registry.from_json(default_json)
    else:
        r = Registry()
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        for a in r.all():
            print(f"{a.id:30s} kind={a.kind:7s} runtime={a.runtime:10s} caps={','.join(a.capabilities)}")
    elif len(sys.argv) > 1 and sys.argv[1] == "find":
        cap = sys.argv[2]
        a = r.find_by_capability(cap)
        if a:
            print(json.dumps(a.__dict__, ensure_ascii=False, indent=2))
        else:
            print("NOT FOUND")
    else:
        # Mac dinh in so luong
        ai = r.ai_agents()
        wk = r.workers()
        print(f"AI Agents: {len(ai)} | Workers: {len(wk)} | Total: {len(r.all())}")
