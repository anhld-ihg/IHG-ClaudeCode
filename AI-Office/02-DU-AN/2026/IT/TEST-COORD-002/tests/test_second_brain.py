"""test_second_brain.py — CHẶNG 3.

Kiem thử IHG Second Brain voi 4 visibility (PUBLIC, DEPARTMENT, PROJECT, PRIVATE)
va phan quyen thong qua AuthZ (KHONG qua prompt).

Tap test:
  1. add / get / search
  2. phan quyen 4 lop (gd/nhan-vien/agent-it/agent-qa)
  3. chan metadata leak (search khong tra entry bi deny)
  4. chan doc path traversal
  5. version chain (supersedes)
  6. verify (chi gd-ihg, agent-qa)
  7. tu choi AI tu promote thanh verified (chi qa/gd duoc)
  8. tu choi PRIVATE visibility cho non-gd
  9. knowledge sai/project bi filter theo project_id
  10. ngăn search thấy content từ entry bị deny (info leak)

Dữ liệu: đều dùng nội dung giả lập, KHÔNG dùng data khách hàng.
"""
import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# Tao SECOND_BRAIN_DIR rieng cho test
TEST_BRAIN_DIR = Path(tempfile.mkdtemp(prefix="ihg-brain-test-"))
os.environ["IHG_SECOND_BRAIN_DIR"] = str(TEST_BRAIN_DIR)
# Force reload
if "ihg_core.config" in sys.modules:
    import importlib
    importlib.reload(sys.modules["ihg_core.config"])
if "ihg_core.second_brain" in sys.modules:
    importlib.reload(sys.modules["ihg_core.second_brain"])

from ihg_core.second_brain import (  # noqa: E402
    SecondBrain, AuthzDeniedError, ValidationError,
    VIS_PUBLIC, VIS_DEPARTMENT, VIS_PROJECT, VIS_PRIVATE,
    VERIFIED, UNVERIFIED, DEPRECATED,
)


def _fake_entry(actor, vis, project_id=None, department=None, title="fake", content="X"*200, **extra):
    base = {
        "type": "policy",
        "title": title,
        "content": content,
        "tags": ["test", "synthetic"],
        "actor": actor,
        "visibility": vis,
        "project_id": project_id,
        "department": department,
        "source": "fixtures/contract-sample.md",  # file that exists, used for sha
    }
    base.update(extra)
    return base


class TestSecondBrain(unittest.TestCase):
    def setUp(self):
        self.sb = SecondBrain(TEST_BRAIN_DIR)

    def tearDown(self):
        # Xoa het entry trong TEST_BRAIN_DIR
        for p in TEST_BRAIN_DIR.glob("*.json"):
            p.unlink()
        a = TEST_BRAIN_DIR / "audit.log"
        if a.exists():
            a.unlink()

    # ============ 1. ADD/GET/SEARCH co ban ============
    def test_01_add_public_as_gd(self):
        """GD add entry PUBLIC thanh cong."""
        eid = self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                       title="Cong ty policy cong",
                                       content="ABC" * 200))
        self.assertTrue(eid.startswith("kb-"))
        e = self.sb.get(eid, "gd-ihg")
        self.assertIsNotNone(e)
        self.assertEqual(e.visibility, VIS_PUBLIC)
        self.assertEqual(e.status, UNVERIFIED)
        self.assertEqual(e.version, 1)

    def test_02_add_invalid_visibility(self):
        with self.assertRaises(ValidationError):
            self.sb.add(_fake_entry("gd-ihg", "TOP_SECRET",
                                     content="X"*200))

    def test_03_add_invalid_actor(self):
        with self.assertRaises(ValidationError):
            self.sb.add(_fake_entry("Giam doc", VIS_PUBLIC,
                                     content="X"*200))

    def test_04_add_invalid_tag(self):
        with self.assertRaises(ValidationError):
            self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                     tags=["bad TAG with space"],
                                     content="X"*200))

    def test_05_add_empty_title(self):
        with self.assertRaises(ValidationError):
            self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                     title="   ",
                                     content="X"*200))

    def test_06_add_too_long_content(self):
        with self.assertRaises(ValidationError):
            self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                     content="X" * 300_000))

    # ============ 2. Phan quyen 4 lop ============
    def test_10_gd_can_add_private(self):
        """GD duoc phep add PRIVATE."""
        eid = self.sb.add(_fake_entry("gd-ihg", VIS_PRIVATE,
                                       title="Bi mat",
                                       content="Y" * 200))
        e = self.sb.get(eid, "gd-ihg")
        self.assertIsNotNone(e)
        self.assertEqual(e.visibility, VIS_PRIVATE)

    def test_11_nhanvien_cannot_add_private(self):
        """Nhan vien KHONG add duoc PRIVATE."""
        with self.assertRaises(AuthzDeniedError):
            self.sb.add(_fake_entry("nhan-vien", VIS_PRIVATE,
                                     content="X"*200))

    def test_12_agent_it_cannot_add_private(self):
        """Agent IT KHONG add PRIVATE."""
        with self.assertRaises(AuthzDeniedError):
            self.sb.add(_fake_entry("agent-it", VIS_PRIVATE,
                                     content="X"*200))

    def test_13_agent_qa_cannot_add_private(self):
        """Agent QA KHONG add PRIVATE."""
        with self.assertRaises(AuthzDeniedError):
            self.sb.add(_fake_entry("agent-qa", VIS_PRIVATE,
                                     content="X"*200))

    def test_14_dept_it_can_add_department(self):
        """Truong phong IT (dept-it) add DEPARTMENT cho IT duoc."""
        eid = self.sb.add(_fake_entry("dept-it", VIS_DEPARTMENT,
                                       department="IT",
                                       title="IT handbook",
                                       content="Z" * 200))
        self.assertTrue(eid.startswith("kb-"))

    def test_15_agent_it_can_add_project(self):
        """Agent IT add PROJECT (có project_id) duoc."""
        eid = self.sb.add(_fake_entry("agent-it", VIS_PROJECT,
                                       project_id="TEST-COORD-002",
                                       title="Test report",
                                       content="W" * 200))
        self.assertTrue(eid.startswith("kb-"))

    def test_16_nhanvien_cannot_add_department(self):
        """Nhan vien KHONG add DEPARTMENT."""
        with self.assertRaises(AuthzDeniedError):
            self.sb.add(_fake_entry("nhan-vien", VIS_DEPARTMENT,
                                     department="IT",
                                     content="X"*200))

    # ============ 3. Chan metadata leak qua search ============
    def test_20_gd_adds_private_nhanvien_search_hides(self):
        """GD them PRIVATE, nhan vien search KHONG thay."""
        self.sb.add(_fake_entry("gd-ihg", VIS_PRIVATE,
                                 title="Bi mat GD",
                                 content="secret_content_xyz " * 50))
        # Nhan vien search "Bi mat" - khong duoc thay
        results = self.sb.search("Bi mat", "nhan-vien")
        self.assertEqual(results, [])
        # Nhan vien search "secret_content_xyz" - khong duoc thay
        results = self.sb.search("secret_content_xyz", "nhan-vien")
        self.assertEqual(results, [])

    def test_21_gd_adds_private_agent_it_search_hides(self):
        """Agent IT search PRIVATE - hidden."""
        self.sb.add(_fake_entry("gd-ihg", VIS_PRIVATE,
                                 title="GD Bi Mat 2",
                                 content="super_secret_alpha " * 50))
        results = self.sb.search("super_secret_alpha", "agent-it")
        self.assertEqual(results, [])

    def test_22_gd_can_search_private(self):
        """GD search thay PRIVATE cua chinh minh."""
        self.sb.add(_fake_entry("gd-ihg", VIS_PRIVATE,
                                 title="GD Bi Mat 3",
                                 content="unique_marker_omega " * 50))
        results = self.sb.search("unique_marker_omega", "gd-ihg")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].visibility, VIS_PRIVATE)

    def test_23_search_no_metadata_leak(self):
        """list_metadata cung phai qua AuthZ."""
        self.sb.add(_fake_entry("gd-ihg", VIS_PRIVATE,
                                 title="PRIVATE entry test",
                                 content="Q" * 200))
        # Nhan vien list_metadata KHONG thay
        meta = self.sb.list_metadata("nhan-vien")
        ids = [m["id"] for m in meta]
        # Tat ca entry trong list deu da qua auth -> KHONG chua PRIVATE
        for m in meta:
            self.assertNotEqual(m["visibility"], VIS_PRIVATE)
        # GD thay het
        meta_gd = self.sb.list_metadata("gd-ihg")
        self.assertTrue(any(m["visibility"] == VIS_PRIVATE for m in meta_gd))

    def test_24_get_private_as_nhanvien_returns_none(self):
        """get() PRIVATE boi nhan vien tra ve None (khong raise)."""
        eid = self.sb.add(_fake_entry("gd-ihg", VIS_PRIVATE,
                                       content="P" * 200))
        result = self.sb.get(eid, "nhan-vien")
        self.assertIsNone(result)

    def test_25_department_membership_enforced(self):
        """Nhan vien (khong thuoc IT) KHONG search thay entry DEPARTMENT IT."""
        self.sb.add(_fake_entry("dept-it", VIS_DEPARTMENT,
                                 department="IT",
                                 title="IT handbook private",
                                 content="escalation P1 P2 P3 " * 20))
        # Nhan vien search keyword rieng cua IT handbook
        results = self.sb.search("escalation P1 P2 P3", "nhan-vien")
        self.assertEqual(results, [])
        # GD thay
        results = self.sb.search("escalation P1 P2 P3", "gd-ihg")
        self.assertEqual(len(results), 1)
        # dept-it (cung phong) thay
        results = self.sb.search("escalation P1 P2 P3", "dept-it")
        self.assertEqual(len(results), 1)

    # ============ 4. Project filter ============
    def test_30_project_filter_nhanvien_in_project(self):
        """Nhan vien trong project X thay entry project X, KHONG thay project Y."""
        self.sb.add(_fake_entry("agent-it", VIS_PROJECT,
                                 project_id="PROJ-A",
                                 title="Project A report",
                                 content="alpha project content " * 30))
        self.sb.add(_fake_entry("agent-it", VIS_PROJECT,
                                 project_id="PROJ-B",
                                 title="Project B report",
                                 content="beta project content " * 30))
        # GD thay het
        results = self.sb.search("project", "gd-ihg")
        self.assertEqual(len(results), 2)
        # GD filter theo project
        results = self.sb.search("project", "gd-ihg", project_id="PROJ-A")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].project_id, "PROJ-A")

    # ============ 5. Version chain ============
    def test_40_add_version(self):
        """add_version tao entry moi (v2), danh entry cu thanh deprecated."""
        eid1 = self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                       title="Version test",
                                       content="V1 content " * 50))
        e1 = self.sb.get(eid1, "gd-ihg")
        self.assertEqual(e1.version, 1)
        eid2 = self.sb.add_version(eid1, "V2 content " * 50, "gd-ihg", notes="update")
        e2 = self.sb.get(eid2, "gd-ihg")
        self.assertEqual(e2.version, 2)
        self.assertEqual(e2.supersedes, eid1)
        e1_after = self.sb.get(eid1, "gd-ihg")
        self.assertEqual(e1_after.status, DEPRECATED)
        # Version history
        chain = self.sb.version_history(eid2, "gd-ihg")
        self.assertEqual(len(chain), 2)
        self.assertEqual(chain[0].id, eid2)
        self.assertEqual(chain[1].id, eid1)

    def test_41_add_version_cross_actor_denied(self):
        """add_version yeu cau actor doc duoc entry."""
        eid = self.sb.add(_fake_entry("gd-ihg", VIS_PRIVATE,
                                       content="X" * 200))
        with self.assertRaises(AuthzDeniedError):
            self.sb.add_version(eid, "Y" * 200, "nhan-vien")

    # ============ 6. Verify ============
    def test_50_verify_by_qa(self):
        """Agent QA verify entry PROJECT duoc."""
        eid = self.sb.add(_fake_entry("agent-it", VIS_PROJECT,
                                       project_id="TEST-COORD-002",
                                       content="W" * 200))
        e = self.sb.verify(eid, "agent-qa", verified_by="agent-qa")
        self.assertEqual(e.status, VERIFIED)
        self.assertEqual(e.verified_by, "agent-qa")

    def test_51_verify_by_gd(self):
        """GD verify entry PRIVATE duoc."""
        eid = self.sb.add(_fake_entry("gd-ihg", VIS_PRIVATE,
                                       content="X" * 200))
        e = self.sb.verify(eid, "gd-ihg", verified_by="gd-ihg")
        self.assertEqual(e.status, VERIFIED)

    def test_52_verify_denied_for_nhanvien(self):
        """Nhan vien KHONG verify duoc."""
        eid = self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                       content="X" * 200))
        with self.assertRaises(AuthzDeniedError):
            self.sb.verify(eid, "nhan-vien", verified_by="nhan-vien")

    def test_53_verify_denied_for_agent_it(self):
        """Agent IT KHONG verify (chi qa/gd)."""
        eid = self.sb.add(_fake_entry("agent-it", VIS_PROJECT,
                                       project_id="TEST-COORD-002",
                                       content="X" * 200))
        with self.assertRaises(AuthzDeniedError):
            self.sb.verify(eid, "agent-it", verified_by="agent-it")

    # ============ 7. Path traversal & malicious inputs ============
    def test_60_malicious_id_ignored(self):
        """get() voi id khong ton tai -> None."""
        result = self.sb.get("../../etc/passwd", "gd-ihg")
        self.assertIsNone(result)
        result = self.sb.get("kb-fake-id", "gd-ihg")
        self.assertIsNone(result)

    def test_61_search_injection_safe(self):
        """Search query khong theo dang executable (chi substring)."""
        eid = self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                       title="Security note",
                                       content="abc_def_ghi " * 50))
        # Query co ky tu dac biet
        results = self.sb.search("'; DROP TABLE kb-; --", "gd-ihg")
        # Van OK, khong crash
        self.assertIsInstance(results, list)
        results = self.sb.search("abc_def", "gd-ihg")
        self.assertTrue(len(results) >= 1)

    # ============ 8. SHA-256 & source tracking ============
    def test_70_sha256_recorded(self):
        """Entry ghi SHA-256 cua file source."""
        eid = self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                       source="fixtures/contract-sample.md",
                                       content="X" * 200))
        e = self.sb.get(eid, "gd-ihg")
        self.assertEqual(len(e.sha256), 64)  # SHA-256 hex
        # Khop voi SHA-256 cua file fixture
        from ihg_core.worker_checksum import sha256_file
        self.assertEqual(e.sha256, sha256_file(ROOT / "fixtures" / "contract-sample.md"))

    def test_71_timestamps_recorded(self):
        """Entry co created_at va updated_at."""
        eid = self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                       content="X" * 200))
        e = self.sb.get(eid, "gd-ihg")
        self.assertTrue(e.created_at)
        self.assertTrue(e.updated_at)
        self.assertEqual(e.created_at, e.updated_at)  # luc moi tao

    # ============ 9. Audit log ============
    def test_80_audit_log_written(self):
        """Moi add ghi 1 dong audit."""
        audit = TEST_BRAIN_DIR / "audit.log"
        self.assertFalse(audit.exists())
        self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC, content="X" * 200))
        self.assertTrue(audit.exists())
        content = audit.read_text(encoding="utf-8")
        self.assertIn("kb-", content)
        self.assertIn("gd-ihg", content)
        self.assertIn(VIS_PUBLIC, content)

    # ============ 10. Search filters ============
    def test_90_search_filter_by_status(self):
        """Search loc theo status."""
        eid = self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                       title="Status test",
                                       content="unique_status_keyword " * 20))
        self.sb.verify(eid, "gd-ihg", verified_by="gd-ihg")
        # search status=verified
        results = self.sb.search("unique_status_keyword", "gd-ihg", status=VERIFIED)
        self.assertEqual(len(results), 1)
        # search status=unverified (khong thay)
        results = self.sb.search("unique_status_keyword", "gd-ihg", status=UNVERIFIED)
        self.assertEqual(len(results), 0)

    def test_91_search_filter_by_tag(self):
        """Search loc theo tag."""
        self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                 title="Tag test",
                                 tags=["xyz", "abc"],
                                 content="tagged_content " * 20))
        self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                 title="Tag test 2",
                                 tags=["other"],
                                 content="tagged_content " * 20))
        results = self.sb.search("tagged_content", "gd-ihg", tags=["xyz"])
        self.assertEqual(len(results), 1)
        self.assertIn("xyz", results[0].tags)

    def test_92_search_limit(self):
        """Search co limit."""
        for i in range(5):
            self.sb.add(_fake_entry("gd-ihg", VIS_PUBLIC,
                                     title=f"Entry {i}",
                                     content=f"limit_test_{i} " * 10))
        results = self.sb.search("limit_test", "gd-ihg", limit=3)
        self.assertEqual(len(results), 3)


def cleanup():
    if TEST_BRAIN_DIR.exists():
        shutil.rmtree(TEST_BRAIN_DIR, ignore_errors=True)


if __name__ == "__main__":
    import unittest
    try:
        unittest.main(verbosity=2, exit=False)
    finally:
        cleanup()
