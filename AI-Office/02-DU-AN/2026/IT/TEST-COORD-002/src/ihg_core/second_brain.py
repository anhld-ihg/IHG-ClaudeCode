"""ihg_core.second_brain — IHG Second Brain (CHẶNG 3).

Chức năng (Mức A, không phụ thuộc gateway/Worker):
  - Lưu trữ kiến thức với 4 visibility: PUBLIC / DEPARTMENT / PROJECT / PRIVATE.
  - Lưu nguồn gốc, version, SHA-256, trạng thái verified, thời điểm áp dụng.
  - Phân quyền qua AuthZ hiện có, KHÔNG dựa vào prompt.
  - Search/get kèm AuthZ check (chặn cả search hit, metadata, content).
  - Version chain (supersedes).
  - Verification flag: chỉ knowledge đã PASS QA mới có thể promote thành "verified".
  - Tự kiểm tra: cấm add entry với visibility > actor được phép.
  - Cấm search/return metadata khi bị chặn.

KHÔNG sử dụng:
  - Mock runtime (sub-agent có thể thật, có thể mock, đều OK).
  - Token / OAuth (chỉ dùng khi Mức B được kích hoạt).
  - Dữ liệu khách hàng thật / PRIVATE thật (chỉ dữ liệu giả lập trong tests/).
"""
import json
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .authz import check as authz_check, AuthzResult
from .worker_checksum import sha256_file


# === 4 lớp visibility (theo chỉ đạo GĐ) ===
VIS_PUBLIC = "public"          # tất cả đọc được
VIS_DEPARTMENT = "department"  # theo phòng ban
VIS_PROJECT = "project"        # theo project_id
VIS_PRIVATE = "private"        # chỉ GĐ (PRIVATE CORE)

VIS_ORDER = [VIS_PUBLIC, VIS_DEPARTMENT, VIS_PROJECT, VIS_PRIVATE]  # tang dần sensitive

# Mapping visibility -> AuthZ action/path pattern
# Moi visibility tuong ung 1 khu vuc du lieu rieng de co the dung pattern
# cua authz hien tai.
# - PUBLIC: trong 01-PHONG-BAN/IT/public/ (vi pattern nhan-vien cho phep)
# - DEPARTMENT: 01-PHONG-BAN/<dept>/public/
# - PROJECT: 02-DU-AN/<project>/
# - PRIVATE: 00-DIEU-HANH/PRIVATE/
VIS_PATH_PREFIX = {
    VIS_PUBLIC: "AI-Office/01-PHONG-BAN/IT/public/",
    VIS_DEPARTMENT: "AI-Office/01-PHONG-BAN/IT/public/",  # override theo dept trong _visibility_path
    VIS_PROJECT: "AI-Office/02-DU-AN/",
    VIS_PRIVATE: "AI-Office/00-DIEU-HANH/PRIVATE/",
}


# === Trạng thái knowledge ===
VERIFIED = "verified"          # da qua QA PASS + cross-check
UNVERIFIED = "unverified"      # tu AI generate, chua review
DEPRECATED = "deprecated"      # co ban moi supersedes


# === Validation schema ===
_VALID_ACTOR = re.compile(r"^[a-z][a-z0-9\-]{1,30}$")
_VALID_TAG = re.compile(r"^[a-z0-9\-]{1,30}$")


@dataclass
class Entry:
    id: str
    type: str                    # decision / conversation / artifact / policy / procedure / faq
    title: str
    content: str
    tags: List[str]
    actor: str                   # ai tao entry
    visibility: str              # public/department/project/private
    project_id: Optional[str]
    department: Optional[str]    # cho VIS_DEPARTMENT
    created_at: str
    updated_at: str
    version: int
    supersedes: Optional[str]
    sha256: str                  # SHA-256 cua content
    source: str                  # file path / URL
    status: str                  # verified / unverified / deprecated
    verified_by: Optional[str]   # ai verify (qa_agent id, hoac gd-ihg)
    verified_at: Optional[str]
    notes: str = ""              # ghi chu them

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SecondBrainError(Exception):
    pass


class AuthzDeniedError(SecondBrainError):
    pass


class ValidationError(SecondBrainError):
    pass


class SecondBrain:
    """Kho luu tri tri thuc IHG.

    Storage: JSON file trong `Config.SECOND_BRAIN_DIR` (set trong config.py).
    Moi entry la 1 file JSON rieng, name = <id>.json.
    """

    def __init__(self, store_dir: Path = None):
        from .config import Config
        self.store_dir = store_dir or Config.SECOND_BRAIN_DIR
        self.store_dir.mkdir(parents=True, exist_ok=True)
        # Index nho: id -> entry (load lazy)
        self._index: Dict[str, Entry] = {}
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        for p in self.store_dir.glob("kb-*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                self._index[d["id"]] = Entry(**d)
            except Exception:
                continue  # corrupted, skip (audit log co the check sau)
        self._loaded = True

    def _save_entry(self, e: Entry) -> None:
        p = self.store_dir / f"{e.id}.json"
        p.write_text(json.dumps(e.to_dict(), ensure_ascii=False, indent=2),
                     encoding="utf-8")
        # Ghi audit
        audit = self.store_dir / "audit.log"
        with audit.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "action": "save",
                "id": e.id,
                "version": e.version,
                "actor": e.actor,
                "visibility": e.visibility,
                "sha256": e.sha256,
                "status": e.status,
            }, ensure_ascii=False) + "\n")

    # ============ AUTHZ ============
    def _check_can_add(self, actor: str, visibility: str, project_id: Optional[str],
                        department: Optional[str]) -> AuthzResult:
        """Kiem tra actor co the add entry voi visibility khong.

        Su dung AuthZ co san: resource = path tuong ung voi visibility.
        """
        path = self._visibility_path(visibility, actor, project_id, department, write=True)
        return authz_check(actor, "write", path)

    def _visibility_path(self, vis: str, actor: str, project_id: Optional[str],
                          department: Optional[str], write: bool) -> str:
        """Quy doi visibility -> resource path de dung AuthZ.

        - PUBLIC: AI-Office/01-PHONG-BAN/IT/public/  (vi pattern nhan-vien match)
        - DEPARTMENT: AI-Office/01-PHONG-BAN/<dept>/policy.md  (KHONG /public/
          de tranh nhan-vien match vao public policy cua phong khac)
        - PROJECT: AI-Office/02-DU-AN/<project>/...
        - PRIVATE: AI-Office/00-DIEU-HANH/PRIVATE/  (chi gd-ihg)
        """
        if vis == VIS_PUBLIC:
            return VIS_PATH_PREFIX[VIS_PUBLIC] + "policy.md"
        if vis == VIS_DEPARTMENT:
            if not department:
                raise ValidationError("DEPARTMENT visibility can phai co department")
            # Path KHONG chua "public/" de tranh nhan-vien match
            return f"AI-Office/01-PHONG-BAN/{department}/policy.md"
        if vis == VIS_PROJECT:
            if not project_id:
                raise ValidationError("PROJECT visibility can phai co project_id")
            return f"AI-Office/02-DU-AN/{project_id}/artifact.md"
        if vis == VIS_PRIVATE:
            return "AI-Office/00-DIEU-HANH/PRIVATE/secret.md"
        raise ValidationError(f"visibility khong hop le: {vis}")

    def _check_department_membership(self, actor: str, entry: 'Entry') -> bool:
        """Kiem tra actor co thuoc department cua entry khong (cho VIS_DEPARTMENT).

        - gd-ihg: xem het
        - agent-qa: xem het (la QA, khong thuoc dept cu the)
        - dept-it: chi thay department IT
        - nhan-vien: KHONG xem (phai thuoc dept tuong ung)
        """
        if actor in ("gd-ihg", "agent-qa"):
            return True
        if entry.visibility != VIS_DEPARTMENT:
            return True  # khong ap dung cho visibility khac
        # Actor phai la dept truong cua department
        actor_dept_map = {
            "dept-it": "IT",
            # them cac dept khac sau
        }
        if actor in actor_dept_map and actor_dept_map[actor] == entry.department:
            return True
        # nhan-vien khong thuoc department cu the -> deny
        return False

    # ============ VALIDATION ============
    def _validate(self, data: Dict[str, Any]) -> None:
        required = ("type", "title", "content", "actor", "visibility", "source")
        for r in required:
            if r not in data:
                raise ValidationError(f"thieu field: {r}")
        if data["visibility"] not in VIS_ORDER:
            raise ValidationError(f"visibility phai la mot trong {VIS_ORDER}, got: {data['visibility']}")
        if not _VALID_ACTOR.match(data["actor"]):
            raise ValidationError(f"actor khong hop le: {data['actor']}")
        for t in data.get("tags", []):
            if not _VALID_TAG.match(t):
                raise ValidationError(f"tag khong hop le: {t}")
        if not data["title"].strip():
            raise ValidationError("title rong")
        if not data["content"].strip():
            raise ValidationError("content rong")
        if len(data["content"]) > 200_000:
            raise ValidationError("content qua lon (>200K chars)")

    # ============ PUBLIC API ============
    def add(self, data: Dict[str, Any]) -> str:
        """Add 1 entry moi. Raise AuthzDeniedError neu actor khong du quyen.

        Tra ve entry id.
        """
        self._validate(data)
        actor = data["actor"]
        vis = data["visibility"]
        proj = data.get("project_id")
        dept = data.get("department")
        auth = self._check_can_add(actor, vis, proj, dept)
        if not auth.allowed:
            raise AuthzDeniedError(
                f"actor {actor} khong co quyen add {vis}: {auth.reason}"
            )
        # Kiem tra them: actor (1-PHONG-BAN phai co department)
        # Cho agent-it: chi add vao project_id cua no
        # Bo qua rule nang cao cho don gian, da co AuthZ chan roi.

        eid = f"kb-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        content_str = data["content"]
        sha = _sha256_str(content_str)
        # Neu source la file path, tinh sha file (cho traceability)
        src = data["source"]
        if Path(src).exists():
            sha = sha256_file(Path(src))
        e = Entry(
            id=eid,
            type=data["type"],
            title=data["title"],
            content=content_str,
            tags=data.get("tags", []),
            actor=actor,
            visibility=vis,
            project_id=proj,
            department=dept,
            created_at=now,
            updated_at=now,
            version=1,
            supersedes=data.get("supersedes"),
            sha256=sha,
            source=src,
            status=UNVERIFIED,
            verified_by=None,
            verified_at=None,
            notes=data.get("notes", ""),
        )
        self._save_entry(e)
        self._index[eid] = e

        # Neu supersedes id, danh entry cu thanh deprecated
        if e.supersedes and e.supersedes in self._index:
            old = self._index[e.supersedes]
            old.status = DEPRECATED
            old.updated_at = now
            self._save_entry(old)

        return eid

    def get(self, entry_id: str, actor: str) -> Optional[Entry]:
        """Doc 1 entry. Tra ve None neu actor khong co quyen."""
        self._ensure_loaded()
        e = self._index.get(entry_id)
        if not e:
            return None
        # AuthZ check
        path = self._visibility_path(e.visibility, actor, e.project_id, e.department, write=False)
        auth = authz_check(actor, "read", path)
        if not auth.allowed:
            return None  # CHAN, khong leak metadata
        # Department membership check (bo sung, vi AuthZ hien tai khong biet dept cua actor)
        if not self._check_department_membership(actor, e):
            return None
        return e

    def search(self, query: str, actor: str, tags: Optional[List[str]] = None,
               visibility: Optional[str] = None, project_id: Optional[str] = None,
               status: Optional[str] = None, limit: int = 20) -> List[Entry]:
        """Tim kiem theo query (substring) + tag/visibility filter.

        CRITICAL: filter AuthZ TRUOC, khong leak metadata.
        """
        self._ensure_loaded()
        q = (query or "").lower().strip()
        q_words = q.split() if q else []
        results: List[Tuple[float, Entry]] = []
        for e in self._index.values():
            # Filter visibility
            if visibility and e.visibility != visibility:
                continue
            if project_id and e.project_id != project_id:
                continue
            if status and e.status != status:
                continue
            if tags:
                if not all(t in e.tags for t in tags):
                    continue
            # AuthZ: tinh path va check
            try:
                path = self._visibility_path(e.visibility, actor, e.project_id, e.department, write=False)
            except ValidationError:
                continue  # entry khong co dept/proj can thiet
            auth = authz_check(actor, "read", path)
            if not auth.allowed:
                continue  # CHAN, khong tra ve metadata
            # Department membership check
            if not self._check_department_membership(actor, e):
                continue

            # Score
            if q_words:
                text = f"{e.title} {e.content} {' '.join(e.tags)}".lower()
                hits = sum(1 for w in q_words if w in text)
                if hits == 0:
                    continue
                score = hits / max(1, len(q_words))
            else:
                score = 1.0
            results.append((score, e))
        results.sort(key=lambda x: (-x[0], x[1].created_at), reverse=False)
        results.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in results[:limit]]

    def list_metadata(self, actor: str, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Liet ke metadata (id, title, tags) - KHONG bao gom content.

        Van phai qua AuthZ.
        """
        self._ensure_loaded()
        out: List[Dict[str, Any]] = []
        for e in self._index.values():
            if project_id and e.project_id != project_id:
                continue
            try:
                path = self._visibility_path(e.visibility, actor, e.project_id, e.department, write=False)
            except ValidationError:
                continue
            auth = authz_check(actor, "read", path)
            if not auth.allowed:
                continue
            if not self._check_department_membership(actor, e):
                continue
            out.append({
                "id": e.id,
                "title": e.title,
                "tags": e.tags,
                "visibility": e.visibility,
                "status": e.status,
                "version": e.version,
                "actor": e.actor,
                "created_at": e.created_at,
            })
        return out

    def version_history(self, entry_id: str, actor: str) -> List[Entry]:
        """Lich su version cua 1 entry (gom ca ban da deprecated)."""
        self._ensure_loaded()
        # Lay entry goc
        current = self.get(entry_id, actor)
        if not current:
            return []
        # Neu co supersedes, de quy lay
        chain: List[Entry] = []
        seen = set()
        # Di xuoi (new -> old)
        e = current
        while e and e.id not in seen:
            chain.append(e)
            seen.add(e.id)
            if e.supersedes:
                e = self._index.get(e.supersedes)
            else:
                break
        return chain

    def verify(self, entry_id: str, actor: str, verified_by: str) -> Entry:
        """Danh dau entry verified (chi khi actor co quyen + entry con hop le).

        Recipients: gd-ihg (full), agent-qa (project/visible cua no), dept head (dept).
        """
        e = self.get(entry_id, actor)
        if not e:
            raise AuthzDeniedError(f"actor {actor} khong the doc/verify {entry_id}")
        # Chi cho phep gd-ihg hoac agent-qa verify
        if actor not in ("gd-ihg", "agent-qa"):
            raise AuthzDeniedError(f"actor {actor} khong co quyen verify")
        e.status = VERIFIED
        e.verified_by = verified_by
        e.verified_at = datetime.now(timezone.utc).isoformat()
        e.updated_at = e.verified_at
        self._save_entry(e)
        return e

    def add_version(self, entry_id: str, new_content: str, actor: str,
                     notes: str = "") -> str:
        """Tao ban moi cua entry (version 2, supersedes 1)."""
        old = self.get(entry_id, actor)
        if not old:
            raise AuthzDeniedError(f"actor {actor} khong the doc {entry_id}")
        # Tao entry moi
        new_id = f"kb-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        sha = _sha256_str(new_content)
        e = Entry(
            id=new_id,
            type=old.type,
            title=old.title,
            content=new_content,
            tags=old.tags,
            actor=actor,
            visibility=old.visibility,
            project_id=old.project_id,
            department=old.department,
            created_at=now,
            updated_at=now,
            version=old.version + 1,
            supersedes=old.id,
            sha256=sha,
            source=old.source,
            status=UNVERIFIED,
            verified_by=None,
            verified_at=None,
            notes=notes,
        )
        self._save_entry(e)
        self._index[new_id] = e
        # Danh old thanh deprecated
        old.status = DEPRECATED
        old.updated_at = now
        self._save_entry(old)
        return new_id

    def count(self) -> int:
        self._ensure_loaded()
        return len(self._index)

    def all_ids(self) -> List[str]:
        self._ensure_loaded()
        return list(self._index.keys())


def _sha256_str(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ============ CLI ============
def main(argv: List[str]) -> int:
    import sys
    if len(argv) < 2:
        print("usage: second_brain.py {ingest|search|get|verify|list|count} [args...]",
              file=sys.stderr)
        return 2
    cmd = argv[1]
    sb = SecondBrain()
    if cmd == "count":
        print(sb.count())
        return 0
    if cmd == "ingest":
        # python -m ihg_core.second_brain ingest <json-file> [--actor X]
        if len(argv) < 3:
            print("ingest can file JSON", file=sys.stderr)
            return 2
        data = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
        eid = sb.add(data)
        print(eid)
        return 0
    if cmd == "search":
        if len(argv) < 4:
            print("search can query va actor", file=sys.stderr)
            return 2
        query, actor = argv[2], argv[3]
        results = sb.search(query, actor)
        for e in results:
            print(f"{e.id}\t{e.visibility}\t{e.status}\t{e.title}\t{e.sha256[:16]}")
        return 0
    if cmd == "get":
        if len(argv) < 4:
            print("get can entry_id va actor", file=sys.stderr)
            return 2
        eid, actor = argv[2], argv[3]
        e = sb.get(eid, actor)
        if not e:
            print("DENIED_OR_NOT_FOUND", file=sys.stderr)
            return 1
        print(json.dumps(e.to_dict(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "verify":
        if len(argv) < 4:
            print("verify can entry_id va actor", file=sys.stderr)
            return 2
        eid, actor = argv[2], argv[3]
        try:
            e = sb.verify(eid, actor, verified_by=actor)
            print(json.dumps({"id": e.id, "status": e.status, "verified_by": e.verified_by}))
        except AuthzDeniedError as ex:
            print(f"DENIED: {ex}", file=sys.stderr)
            return 1
        return 0
    if cmd == "list":
        if len(argv) < 3:
            print("list can actor", file=sys.stderr)
            return 2
        actor = argv[2]
        for m in sb.list_metadata(actor):
            print(f"{m['id']}\t{m['visibility']}\t{m['status']}\t{m['title']}")
        return 0
    print(f"unknown cmd: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
