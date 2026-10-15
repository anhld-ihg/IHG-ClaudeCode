"""Smoke test nhanh — chi kiem tra import + syntax, khong chay logic.

Muc dich: xac minh moi truong Python co import duoc cac module ihg_core khong.
Khong thay the 25 test case chinh.
Exit code: 0 = tat ca import OK, 1 = co loi import.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
sys.path.insert(0, str(SRC))

modules = [
    "ihg_core.config",
    "ihg_core.authz",
    "ihg_core.state_store",
    "ihg_core.registry",
    "ihg_core.agent_runtime",
    "ihg_core.worker_checksum",
    "ihg_core.coordinator",
    "ihg_core.qa_check",
    "ihg_core",
]

ok = 0
fail = 0
for m in modules:
    try:
        __import__(m)
        print(f"  OK   {m}")
        ok += 1
    except Exception as e:
        print(f"  XX   {m}: {e}")
        fail += 1

print(f"\nImport OK: {ok}/{ok+fail}")
sys.exit(0 if fail == 0 else 1)
