"""ihg_core.state_store — state machine hop le, co kiem tra chuyen trang thai.

Trang thai hop le (transition graph):
    PENDING    -> DISPATCHED   (coordinator lay agent)
    PENDING    -> BLOCKED      (khong co agent khop)
    DISPATCHED -> RUNNING      (agent that dang chay)
    DISPATCHED -> FAILED       (khong the khoi dong agent)
    RUNNING    -> SUCCEEDED    (agent tra artifact + SHA)
    RUNNING    -> FAILED       (agent loi hoac timeout)
    SUCCEEDED  -> QA_PENDING   (queue QA)
    SUCCEEDED  -> DRIFT        (output bi mat/thay doi)
    FAILED     -> RETRY        (coordinator chay lai)
    RETRY      -> DISPATCHED
    QA_PENDING -> QA_PASS
    QA_PENDING -> QA_FAIL
    QA_PENDING -> QA_UNVERIFIED  (QA agent khong kha dung)
    QA_PASS    -> DELIVERED
    QA_FAIL    -> FAILED

QUY TAC:
- Mot task FAILED khong duoc phep nhay thang len DONE.
- Mot task DRIFT (output mat/thay doi) khong duoc xem la SUCCEEDED.
- Khi skip, KHONG dem la DONE ma ghi "REUSED" (artifact tu lan truoc).
- Moi chuyen trang thai qua transition() de dam bao tinh hop le.
- Khi SHA khong khop voi file ngoai, chuyen sang DRIFT.
"""
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

from .config import Config


# Trang thai ket thuc (terminal) — co the dung audit
TERMINAL_OK = {"SUCCEEDED", "QA_PASS", "DELIVERED", "REUSED"}
TERMINAL_FAIL = {"FAILED", "QA_FAIL", "DRIFT", "BLOCKED"}

VALID_TRANSITIONS = {
    "PENDING": {"DISPATCHED", "BLOCKED", "FAILED"},
    "DISPATCHED": {"RUNNING", "FAILED", "REUSED"},
    "RUNNING": {"SUCCEEDED", "FAILED"},
    "SUCCEEDED": {"QA_PENDING", "DRIFT"},
    "QA_PENDING": {"QA_PASS", "QA_FAIL", "QA_UNVERIFIED", "DRIFT"},  # artifact mat/thay doi giua dispatch va QA
    "QA_PASS": {"DELIVERED", "DRIFT"},
    "QA_FAIL": {"FAILED"},
    "REUSED": {"DRIFT", "SUCCEEDED"},   # kiem tra lai thi co the len SUCCEEDED neu khop
    "FAILED": {"RETRY", "BLOCKED"},
    "RETRY": {"DISPATCHED", "BLOCKED"},
    "DRIFT": {"RUNNING", "FAILED"},
    "BLOCKED": {"PENDING", "QA_FAIL"},   # admin unlock hoac QA danh fail that
    "DELIVERED": {"DRIFT"},   # audit phat hien artifact bi sua/mat sau khi giao
    "QA_UNVERIFIED": {"QA_PENDING", "FAILED"},
}


@dataclass
class TaskRecord:
    id: str
    state: str = "PENDING"
    capability: str = ""
    agent: str = ""
    executor_agent: str = ""  # Agent thuc su chay task (co the khac agent duoc assign)
    artifact_path: str = ""
    expected_sha256: str = ""
    actual_sha256: str = ""
    attempt: int = 0
    last_error: str = ""
    qa_agent: str = ""
    qa_result: str = ""  # PASS / FAIL / QA_UNVERIFIED
    qa_detail: str = ""
    created_at: str = ""
    updated_at: str = ""
    history: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class StateMachineError(Exception):
    pass


class StateStore:
    def __init__(self, path: Optional[Path] = None):
        Config.ensure()
        self.path = path or (Config.STATE_DIR / "tasks.json")
        self.log_path = Config.LOG_DIR / "state.log"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"tasks": {}})

    def _read(self) -> dict:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"tasks": {}}

    def _write(self, data: dict):
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(self.path)
        # Log append
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} state-write tasks={len(data.get('tasks', {}))}\n")

    def _log(self, msg: str):
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {msg}\n")

    def get(self, task_id: str) -> Optional[TaskRecord]:
        data = self._read()
        d = data["tasks"].get(task_id)
        if not d:
            return None
        return TaskRecord(**d)

    def all(self) -> list:
        return [TaskRecord(**d) for d in self._read()["tasks"].values()]

    def _save(self, rec: TaskRecord):
        data = self._read()
        rec.updated_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        data["tasks"][rec.id] = rec.to_dict()
        self._write(data)

    def create(self, task_id: str, capability: str) -> TaskRecord:
        existing = self.get(task_id)
        if existing:
            return existing
        now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        rec = TaskRecord(id=task_id, capability=capability, created_at=now, updated_at=now)
        rec.history.append({"state": "PENDING", "at": now, "note": "created"})
        self._save(rec)
        self._log(f"create {task_id} capability={capability}")
        return rec

    def transition(self, task_id: str, new_state: str, **fields: Any) -> TaskRecord:
        """Chuyen trang thai co kiem tra tinh hop le.
        Raise StateMachineError neu chuyen trang thai khong hop le."""
        rec = self.get(task_id)
        if rec is None:
            raise StateMachineError(f"task {task_id} khong ton tai")
        old = rec.state
        valid = VALID_TRANSITIONS.get(old, set())
        if new_state not in valid:
            raise StateMachineError(
                f"chuyen trang thai khong hop le: {old} -> {new_state}. "
                f"Allowed: {sorted(valid)}")
        rec.state = new_state
        for k, v in fields.items():
            if hasattr(rec, k):
                setattr(rec, k, v)
        now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        rec.history.append({"state": new_state, "at": now, "from": old, "note": fields.get("last_error", "")})
        self._save(rec)
        self._log(f"transition {task_id} {old}->{new_state} attempt={rec.attempt} agent={rec.agent}")
        return rec

    def record_artifact(self, task_id: str, path: str, sha256: str) -> TaskRecord:
        rec = self.get(task_id)
        if rec is None:
            raise StateMachineError(f"task {task_id} khong ton tai")
        rec.artifact_path = str(path)
        rec.expected_sha256 = sha256
        rec.actual_sha256 = sha256
        return self.transition(task_id, "SUCCEEDED",
                                artifact_path=str(path), actual_sha256=sha256, expected_sha256=sha256)

    def record_failure(self, task_id: str, error: str) -> TaskRecord:
        rec = self.get(task_id)
        if rec is None:
            raise StateMachineError(f"task {task_id} khong ton tai")
        return self.transition(task_id, "FAILED", last_error=error)

    def verify_artifact_integrity(self, task_id: str) -> TaskRecord:
        """Kiem tra SHA-256 cua artifact con khop voi expected_sha256 khong.
        Neu mat -> chuyen DRIFT. Neu khop -> giu nguyen state (co the SUCCEEDED hoac REUSED)."""
        rec = self.get(task_id)
        if not rec or not rec.artifact_path:
            return rec
        p = Path(rec.artifact_path)
        if not p.exists():
            return self.transition(task_id, "DRIFT", last_error=f"artifact mat: {p}")
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        actual = h.hexdigest()
        if rec.expected_sha256 and actual != rec.expected_sha256:
            return self.transition(task_id, "DRIFT",
                                    last_error=f"SHA khong khop: actual={actual[:16]} expected={rec.expected_sha256[:16]}",
                                    actual_sha256=actual)
        # Khop: ghi nhan actual, giu state
        rec.actual_sha256 = actual
        self._save(rec)
        return rec


if __name__ == "__main__":
    import sys
    s = StateStore()
    if len(sys.argv) >= 3 and sys.argv[1] == "test":
        # chay self-test nho
        tid = sys.argv[2]
        s.create(tid, "test")
        s.transition(tid, "DISPATCHED", agent="test-agent")
        s.transition(tid, "RUNNING")
        s.record_artifact(tid, "test.md", "fakehash")
        s.transition(tid, "QA_PENDING")
        s.transition(tid, "QA_PASS", qa_agent="ihg-qa", qa_result="PASS")
        s.transition(tid, "DELIVERED")
        r = s.get(tid)
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2, default=str))
    elif len(sys.argv) >= 3 and sys.argv[1] == "bad-transition":
        tid = sys.argv[2]
        s.create(tid, "test")
        try:
            s.transition(tid, "DELIVERED")  # khong hop le tu PENDING
        except StateMachineError as e:
            print(f"CAUGHT: {e}")
    else:
        for t in s.all():
            print(t.id, t.state, t.artifact_path)
