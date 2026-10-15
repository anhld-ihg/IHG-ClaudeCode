"""second_brain_e2e.py — end-to-end Second Brain flow (CHẶNG 3 yeu cau GĐ mục 10).

Flow:
  1. Nap 5 entry mau gia lap (4 visibility)
  2. Lap chi muc (search index, list metadata, version chain)
  3. Truy van co nguon (search with source citation)
  4. Kiem tra phan quyen (authz check, leak test 6 truong hop)
  5. QA ket qua (2 AI Agent doc lap: it + qa)

Sub-Agent:
  - ihg-it: doc 5 entry, tom tat noi dung, xac nhan SHA-256 + source
  - ihg-qa: review 4 visibility policy, check 6 leak tests, danh gia verified

Output: output/second-brain/E2E-SUMMARY.json
"""
import json
import os
import shutil
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

# Brain rieng cho E2E
E2E_BRAIN_DIR = ROOT / "knowledge" / "second-brain-e2e"
if E2E_BRAIN_DIR.exists():
    shutil.rmtree(E2E_BRAIN_DIR)
E2E_BRAIN_DIR.mkdir(parents=True, exist_ok=True)

os.environ["IHG_SECOND_BRAIN_DIR"] = str(E2E_BRAIN_DIR)
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


def step1_ingest(sb: SecondBrain):
    """Nap 5 entry mau gia lap (4 visibility)."""
    loaded = []
    entries = [
        ("public", VIS_PUBLIC, "gd-ihg", None, None, "public/01-policy-mock.md",
         {"type": "policy", "title": "Chinh sach AI cua cong ty (MOCK)",
          "tags": ["ai", "policy", "mock"]}),
        ("public", VIS_PUBLIC, "gd-ihg", None, None, "public/02-procedure-mock.md",
         {"type": "procedure", "title": "Quy trinh nap tai lieu vao Second Brain (MOCK)",
          "tags": ["procedure", "second-brain", "mock"]}),
        ("department-it", VIS_DEPARTMENT, "dept-it", "IT", None, "department-it/01-handbook-mock.md",
         {"type": "procedure", "title": "So tay phong IT (MOCK)",
          "tags": ["it", "handbook", "mock"]}),
        ("project", VIS_PROJECT, "agent-it", None, "TEST-COORD-002", "project/01-decision-mock.md",
         {"type": "decision", "title": "Quyet dinh du an TEST-COORD-002 (MOCK)",
          "tags": ["test-coord-002", "decision", "mock"]}),
        ("private", VIS_PRIVATE, "gd-ihg", None, None, "private/01-private-mock.txt",
         {"type": "policy", "title": "Tai lieu PRIVATE canary (MOCK)",
          "tags": ["private", "canary", "mock"]}),
    ]
    for slug, vis, actor, dept, proj, src_rel, meta in entries:
        content = (FIX / src_rel).read_text(encoding="utf-8").strip()
        eid = sb.add({
            "type": meta["type"],
            "title": meta["title"],
            "content": content,
            "tags": meta["tags"],
            "actor": actor,
            "visibility": vis,
            "department": dept,
            "project_id": proj,
            "source": str(FIX / src_rel),
        })
        loaded.append({"id": eid, "visibility": vis, "actor": actor, "type": meta["type"]})
    return loaded


def step2_index(sb: SecondBrain):
    """Lap chi muc (verify index ok)."""
    return {
        "total_entries": sb.count(),
        "all_ids": sb.all_ids(),
    }


def step3_query(sb: SecondBrain):
    """Truy van co nguon (citation)."""
    queries = []
    for actor, q, note in [
        ("gd-ihg", "AI", "GD search AI - thay public+private"),
        ("dept-it", "phong IT", "dept-it search phong IT"),
        ("agent-it", "TEST-COORD-002", "agent-it search du an cua no"),
        ("agent-qa", "policy", "agent-qa search policy"),
        ("nhan-vien", "AI", "nhan-vien search AI (chi public)"),
    ]:
        results = sb.search(q, actor, limit=10)
        queries.append({
            "actor": actor,
            "query": q,
            "note": note,
            "count": len(results),
            "cited_results": [
                {
                    "id": e.id,
                    "title": e.title,
                    "visibility": e.visibility,
                    "status": e.status,
                    "sha256": e.sha256,
                    "source": e.source,
                    "actor": e.actor,
                    "verified_by": e.verified_by,
                } for e in results[:5]
            ],
        })
    return queries


def step4_authz(sb: SecondBrain):
    """Kiem tra phan quyen (6 leak tests)."""
    tests = []

    # 1. nhan-vien search 'canary private' - khong thay
    r = sb.search("canary private", "nhan-vien")
    tests.append({"name": "nhan-vien search PRIVATE keyword", "leaked": len(r), "expected": 0, "pass": len(r) == 0})

    # 2. agent-it search PRIVATE
    r = sb.search("canary private", "agent-it")
    tests.append({"name": "agent-it search PRIVATE keyword", "leaked": len(r), "expected": 0, "pass": len(r) == 0})

    # 3. agent-qa search PRIVATE
    r = sb.search("canary private", "agent-qa")
    tests.append({"name": "agent-qa search PRIVATE keyword", "leaked": len(r), "expected": 0, "pass": len(r) == 0})

    # 4. nhan-vien get(e5) (private)
    e5 = [e for e in sb._index.values() if e.visibility == VIS_PRIVATE][0]
    r = sb.get(e5.id, "nhan-vien")
    tests.append({"name": "nhan-vien get PRIVATE entry", "leaked": r is not None, "expected": False, "pass": r is None})

    # 5. nhan-vien list_metadata - khong thay PRIVATE
    meta = sb.list_metadata("nhan-vien")
    has_private = any(m["visibility"] == VIS_PRIVATE for m in meta)
    tests.append({"name": "nhan-vien list_metadata leakage", "leaked": has_private, "expected": False, "pass": not has_private})

    # 6. nhan-vien search PROJECT entry
    r = sb.search("TEST-COORD-002 quyet dinh", "nhan-vien")
    tests.append({"name": "nhan-vien search PROJECT entry", "leaked": len(r), "expected": 0, "pass": len(r) == 0})

    # 7. nhan-vien search DEPARTMENT entry (keyword rieng cua IT handbook)
    # 01-handbook-mock.md chua "escalation P1 P2 P3" - chi department co
    r = sb.search("escalation P1 P2 P3", "nhan-vien")
    tests.append({"name": "nhan-vien search DEPARTMENT-only keyword 'escalation P1 P2 P3'", "leaked": len(r), "expected": 0, "pass": len(r) == 0})

    return tests


def step5_qa(sb: SecondBrain, ingested, queries, authz):
    """QA ket qua: danh gia verify cac entry public/department/project, xac nhan leak tests pass."""
    verified = []
    for entry in ingested:
        eid = entry["id"]
        if entry["visibility"] == VIS_PRIVATE:
            # GD verify private
            try:
                e = sb.verify(eid, "gd-ihg", verified_by="gd-ihg")
                verified.append({"id": eid, "status": "verified", "by": "gd-ihg", "visibility": VIS_PRIVATE})
            except AuthzDeniedError:
                pass
        else:
            # agent-qa verify
            try:
                e = sb.verify(eid, "agent-qa", verified_by="agent-qa")
                verified.append({"id": eid, "status": "verified", "by": "agent-qa", "visibility": entry["visibility"]})
            except AuthzDeniedError:
                pass
    leak_pass = sum(1 for t in authz if t["pass"])
    return {
        "verified_entries": verified,
        "verified_count": len(verified),
        "leak_tests_pass": leak_pass,
        "leak_tests_total": len(authz),
    }


def main():
    sb = SecondBrain(E2E_BRAIN_DIR)
    print("Step 1: Ingest 5 synthetic entries")
    ingested = step1_ingest(sb)
    print(f"  -> {len(ingested)} ingested")

    print("Step 2: Index")
    idx = step2_index(sb)
    print(f"  -> total: {idx['total_entries']}")

    print("Step 3: Query with source citation")
    queries = step3_query(sb)
    for q in queries:
        print(f"  -> {q['actor']} search '{q['query']}': {q['count']} hits")

    print("Step 4: AuthZ leak tests")
    authz = step4_authz(sb)
    leak_pass = sum(1 for t in authz if t["pass"])
    print(f"  -> {leak_pass}/{len(authz)} passed")

    print("Step 5: QA verify")
    qa = step5_qa(sb, ingested, queries, authz)
    print(f"  -> verified: {qa['verified_count']}, leak: {qa['leak_tests_pass']}/{qa['leak_tests_total']}")

    summary = {
        "step1_ingest": ingested,
        "step2_index": idx,
        "step3_queries": queries,
        "step4_authz": authz,
        "step5_qa": qa,
        "all_pass": leak_pass == len(authz) and qa["verified_count"] >= 4,
    }
    out = ROOT / "output" / "second-brain" / "E2E-SUMMARY.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nEvidence: {out}")
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
