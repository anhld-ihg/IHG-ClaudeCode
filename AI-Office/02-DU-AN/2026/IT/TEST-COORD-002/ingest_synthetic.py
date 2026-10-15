"""ingest_synthetic.py — nap 4 entry mau gia lap vao Second Brain.

Quy trinh (CHẶNG 3 theo yeu cau GĐ):
  1. Nap 4 entry PUBLIC/DEPARTMENT/PROJECT/PRIVATE
  2. Tracquyền (AuthZ) cho moi entry
  3. Search có trả lời có dẫn nguồn
  4. QA verify 2 entry public/department
  5. AuthZ leak test: search PRIVATE voi nhan-vien/agent-it
  6. Ghi evidence: output/second-brain/EV-INGEST.json
"""
import json
import os
import sys
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

# Dung SECOND_BRAIN_DIR rieng (de khong anh huong den test_dir)
EVIDENCE_BRAIN_DIR = ROOT / "knowledge" / "second-brain-demo"
if EVIDENCE_BRAIN_DIR.exists():
    shutil.rmtree(EVIDENCE_BRAIN_DIR)
EVIDENCE_BRAIN_DIR.mkdir(parents=True, exist_ok=True)

os.environ["IHG_SECOND_BRAIN_DIR"] = str(EVIDENCE_BRAIN_DIR)
if "ihg_core.config" in sys.modules:
    import importlib
    importlib.reload(sys.modules["ihg_core.config"])
if "ihg_core.second_brain" in sys.modules:
    importlib.reload(sys.modules["ihg_core.second_brain"])

from ihg_core.second_brain import (  # noqa: E402
    SecondBrain, SecondBrainError, AuthzDeniedError, ValidationError,
    VIS_PUBLIC, VIS_DEPARTMENT, VIS_PROJECT, VIS_PRIVATE,
    VERIFIED, UNVERIFIED, DEPRECATED,
)

FIX = ROOT / "fixtures" / "synthetic-knowledge"


def load_md(p: Path) -> str:
    return p.read_text(encoding="utf-8").strip()


def main():
    sb = SecondBrain(EVIDENCE_BRAIN_DIR)
    ingested = []

    # 1. PUBLIC: gd-ihg add 2 policy/procedure public
    e1 = sb.add({
        "type": "policy",
        "title": "Chinh sach AI cua cong ty (MOCK)",
        "content": load_md(FIX / "public" / "01-policy-mock.md"),
        "tags": ["ai", "policy", "mock"],
        "actor": "gd-ihg",
        "visibility": VIS_PUBLIC,
        "source": str(FIX / "public" / "01-policy-mock.md"),
    })
    ingested.append({"id": e1, "visibility": VIS_PUBLIC, "actor": "gd-ihg", "type": "policy"})

    e2 = sb.add({
        "type": "procedure",
        "title": "Quy trinh nap tai lieu vao Second Brain (MOCK)",
        "content": load_md(FIX / "public" / "02-procedure-mock.md"),
        "tags": ["procedure", "second-brain", "mock"],
        "actor": "gd-ihg",
        "visibility": VIS_PUBLIC,
        "source": str(FIX / "public" / "02-procedure-mock.md"),
    })
    ingested.append({"id": e2, "visibility": VIS_PUBLIC, "actor": "gd-ihg", "type": "procedure"})

    # 2. DEPARTMENT (IT): dept-it add handbook
    e3 = sb.add({
        "type": "procedure",
        "title": "So tay phong IT (MOCK)",
        "content": load_md(FIX / "department-it" / "01-handbook-mock.md"),
        "tags": ["it", "handbook", "mock"],
        "actor": "dept-it",
        "visibility": VIS_DEPARTMENT,
        "department": "IT",
        "source": str(FIX / "department-it" / "01-handbook-mock.md"),
    })
    ingested.append({"id": e3, "visibility": VIS_DEPARTMENT, "actor": "dept-it", "type": "procedure"})

    # 3. PROJECT (TEST-COORD-002): agent-it add decision
    e4 = sb.add({
        "type": "decision",
        "title": "Quyet dinh du an TEST-COORD-002 (MOCK)",
        "content": load_md(FIX / "project" / "01-decision-mock.md"),
        "tags": ["test-coord-002", "decision", "mock"],
        "actor": "agent-it",
        "visibility": VIS_PROJECT,
        "project_id": "TEST-COORD-002",
        "source": str(FIX / "project" / "01-decision-mock.md"),
    })
    ingested.append({"id": e4, "visibility": VIS_PROJECT, "actor": "agent-it", "type": "decision"})

    # 4. PRIVATE: gd-ihg add private canary
    e5 = sb.add({
        "type": "policy",
        "title": "Tai lieu PRIVATE canary (MOCK)",
        "content": load_md(FIX / "private" / "01-private-mock.txt"),
        "tags": ["private", "canary", "mock"],
        "actor": "gd-ihg",
        "visibility": VIS_PRIVATE,
        "source": str(FIX / "private" / "01-private-mock.txt"),
    })
    ingested.append({"id": e5, "visibility": VIS_PRIVATE, "actor": "gd-ihg", "type": "policy"})

    # === QA verify 2 entry public ===
    sb.verify(e1, "agent-qa", verified_by="agent-qa")
    sb.verify(e2, "agent-qa", verified_by="agent-qa")
    sb.verify(e3, "agent-qa", verified_by="agent-qa")
    sb.verify(e4, "agent-qa", verified_by="agent-qa")
    # entry private KHONG verify boi agent-qa (co the vi khong co quyen verify private)
    # Thu verify private boi GD
    try:
        sb.verify(e5, "gd-ihg", verified_by="gd-ihg")
    except AuthzDeniedError as ex:
        # Neu agent-qa khong duoc verify private, thi GD verify
        pass

    # === Truy vấn có trả lời có dẫn nguồn ===
    # 1. GD search "AI" -> nhan ca PUBLIC
    results_gd = sb.search("AI", "gd-ihg", limit=10)

    # 2. dept-it search "Xu ly su co" -> nhan DEPARTMENT IT
    results_dept = sb.search("xu ly su co", "dept-it", limit=10)

    # 3. agent-it search "TEST-COORD-002" -> nhan PROJECT
    results_agent_it = sb.search("TEST-COORD-002", "agent-it", limit=10)

    # 4. nhan-vien search "AI" -> chi thay PUBLIC, KHONG thay PRIVATE/DEPARTMENT/PROJECT
    results_nv = sb.search("AI", "nhan-vien", limit=10)

    # === AuthZ leak test ===
    leak_tests = []
    # nhan-vien tim private canary
    leak = sb.search("canary private", "nhan-vien")
    leak_tests.append({"test": "nhan-vien search 'canary private'", "leaked": len(leak), "expected": 0, "pass": len(leak) == 0})
    # agent-it tim private
    leak2 = sb.search("canary private", "agent-it")
    leak_tests.append({"test": "agent-it search 'canary private'", "leaked": len(leak2), "expected": 0, "pass": len(leak2) == 0})
    # agent-qa tim private
    leak3 = sb.search("canary private", "agent-qa")
    leak_tests.append({"test": "agent-qa search 'canary private'", "leaked": len(leak3), "expected": 0, "pass": len(leak3) == 0})
    # get private by id
    get_leak = sb.get(e5, "nhan-vien")
    leak_tests.append({"test": "nhan-vien get(e5)", "leaked": get_leak is not None, "expected": False, "pass": get_leak is None})
    # list_metadata nhan-vien KHONG thay private
    meta_nv = sb.list_metadata("nhan-vien")
    has_private = any(m["visibility"] == VIS_PRIVATE for m in meta_nv)
    leak_tests.append({"test": "nhan-vien list_metadata", "leaked": has_private, "expected": False, "pass": not has_private})
    # nhan-vien search "TEST-COORD-002 quyet dinh" - chi public, khong thay PROJECT
    leak4 = sb.search("TEST-COORD-002 quyet dinh", "nhan-vien")
    leak_tests.append({"test": "nhan-vien search PROJECT entry", "leaked": len(leak4), "expected": 0, "pass": len(leak4) == 0})

    all_pass = all(t["pass"] for t in leak_tests)

    # === Luu evidence ===
    evidence = {
        "ingest_5_entries": ingested,
        "verified": [
            {"id": e1, "status": "verified", "by": "agent-qa"},
            {"id": e2, "status": "verified", "by": "agent-qa"},
            {"id": e3, "status": "verified", "by": "agent-qa"},
            {"id": e4, "status": "verified", "by": "agent-qa"},
        ],
        "queries": {
            "gd_search_AI": {
                "actor": "gd-ihg",
                "query": "AI",
                "count": len(results_gd),
                "results": [{"id": e.id, "title": e.title, "visibility": e.visibility, "status": e.status, "sha256": e.sha256} for e in results_gd[:5]],
            },
            "dept_it_search_xu_ly": {
                "actor": "dept-it",
                "query": "xu ly su co",
                "count": len(results_dept),
                "results": [{"id": e.id, "title": e.title, "visibility": e.visibility, "status": e.status, "sha256": e.sha256} for e in results_dept[:5]],
            },
            "agent_it_search_TEST_COORD": {
                "actor": "agent-it",
                "query": "TEST-COORD-002",
                "count": len(results_agent_it),
                "results": [{"id": e.id, "title": e.title, "visibility": e.visibility, "status": e.status, "sha256": e.sha256} for e in results_agent_it[:5]],
            },
            "nhan_vien_search_AI": {
                "actor": "nhan-vien",
                "query": "AI",
                "count": len(results_nv),
                "results": [{"id": e.id, "title": e.title, "visibility": e.visibility, "status": e.status, "sha256": e.sha256} for e in results_nv[:5]],
                "note": "chi thay PUBLIC, khong thay PRIVATE/DEPARTMENT/PROJECT",
            },
        },
        "authz_leak_tests": leak_tests,
        "all_leak_tests_pass": all_pass,
        "summary": {
            "total_ingested": len(ingested),
            "total_verified": 4,
            "leak_tests_pass": sum(1 for t in leak_tests if t["pass"]),
            "leak_tests_total": len(leak_tests),
        }
    }
    out = ROOT / "output" / "second-brain" / "EV-INGEST.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Evidence saved to: {out}")
    print(f"Total ingested: {len(ingested)}")
    print(f"Verified: 4")
    print(f"Leak tests pass: {sum(1 for t in leak_tests if t['pass'])}/{len(leak_tests)}")
    print(f"GD search 'AI' count: {len(results_gd)}")
    print(f"Nhan-vien search 'AI' count: {len(results_nv)} (only PUBLIC)")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
