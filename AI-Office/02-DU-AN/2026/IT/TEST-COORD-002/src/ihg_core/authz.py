"""ihg_core.authz — phan quyen that o tang chuong trinh.

Nguyen tac:
- Default DENY. Khong co quyen thi tu choi.
- Principal: nguoi dung (gd-ihg, dept-it, dept-finance, ...).
- Action: read, write, audit, dispatch, run_agent, deliver.
- Resource: path tuyet doi hoac pattern (regex).
- Khong dua vao prompt de bao ve. Tat ca quyet dinh o day.

Tich hop:
- Coordinator goi AuthZ.check() truoc moi thao tac doc/ghi.
- Agent chi duoc phep truy cap path trong allowed_paths cua registry.
- Chatbot nhan vien (principal=nhan-vien) khong bao gio vao PRIVATE_CORE.
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Chinh sach phan quyen: principal -> action -> pattern (regex) -> allow
# Mac dinh: khong co entry = DENY.
PRINCIPAL_POLICY = {
    "gd-ihg": {  # Giam doc
        "read": [r".*"],
        "write": [r".*"],
        "audit": [r".*"],
        "dispatch": [r".*"],
        "run_agent": [r".*"],
        "deliver": [r".*"],
    },
    "dept-it": {  # Truong phong IT - KHONG vao 00-DIEU-HANH/PRIVATE
        "read": [r".*AI-Office/(01-PHONG-BAN|02-DU-AN|03-TRI-THUC)/.*",
                 r".*knowledge/public/.*"],
        "write": [r".*AI-Office/01-PHONG-BAN/IT/.*", r".*AI-Office/02-DU-AN/.*"],
        "audit": [r".*AI-Office/02-DU-AN/.*"],
        "dispatch": [r".*AI-Office/02-DU-AN/.*"],
        "run_agent": [r"^ihg-(it|qa|admin-legal)$"],
        "deliver": [r".*AI-Office/02-DU-AN/.*"],
    },
    "agent-it": {  # Agent IT - chi duoc phep trong khu vuc IT, KHONG vao 00-DIEU-HANH/PRIVATE
        "read": [r".*AI-Office/01-PHONG-BAN/IT/.*",
                 r".*AI-Office/02-DU-AN/.*",
                 r".*AI-Office/03-TRI-THUC/(IT|EMPLOYEE)/.*"],
        "write": [r".*AI-Office/02-DU-AN/.*"],
        "audit": [],
        "dispatch": [],
        "run_agent": [],
        "deliver": [],
    },
    "agent-qa": {  # Agent QA - doc duoc du an de review, KHONG vao 00-DIEU-HANH
        "read": [r".*AI-Office/01-PHONG-BAN/.*",
                 r".*AI-Office/02-DU-AN/.*",
                 r".*AI-Office/03-TRI-THUC/.*"],
        "write": [r".*AI-Office/02-DU-AN/.*/qa/.*", r".*AI-Office/02-DU-AN/.*/state/.*"],
        "audit": [r".*AI-Office/02-DU-AN/.*"],
        "dispatch": [],
        "run_agent": [],
        "deliver": [],
    },
    "agent-admin-legal": {  # Agent Phap ly - doc PRIVATE de review hop dong, write phai vao 00-DIEU-HANH
        "read": [r".*AI-Office/00-DIEU-HANH/.*",
                 r".*AI-Office/01-PHONG-BAN/HANH-CHINH-PHAP-LY/.*",
                 r".*AI-Office/02-DU-AN/.*",
                 r".*AI-Office/03-TRI-THUC/.*"],
        "write": [r".*AI-Office/00-DIEU-HANH/.*",
                  r".*AI-Office/01-PHONG-BAN/HANH-CHINH-PHAP-LY/.*",
                  r".*AI-Office/02-DU-AN/.*"],
        "audit": [r".*AI-Office/02-DU-AN/.*"],
        "dispatch": [],
        "run_agent": [],
        "deliver": [],
    },
    "nhan-vien": {  # Chatbot nhan vien - gioi han
        "read": [r".*AI-Office/01-PHONG-BAN/[^/]+/public/.*", r".*AI-Office/03-TRI-THUC/EMPLOYEE/.*"],
        "write": [],
        "audit": [],
        "dispatch": [],
        "run_agent": [],
        "deliver": [],
    },
}


@dataclass
class AuthzResult:
    allowed: bool
    reason: str
    principal: str
    action: str
    resource: str


def _match_any(patterns: list, resource: str) -> bool:
    if not patterns:
        return False
    for p in patterns:
        if re.match(p, resource):
            return True
    return False


def check(principal: str, action: str, resource: str) -> AuthzResult:
    """Kiem tra quyen. Tra ve AuthzResult, allowed=True/False."""
    if not principal or not action or not resource:
        return AuthzResult(False, "thieu principal/action/resource", principal, action, resource)
    policy = PRINCIPAL_POLICY.get(principal)
    if policy is None:
        return AuthzResult(False, f"principal khong ton tai: {principal}", principal, action, resource)
    # Normalize backslash -> slash (Windows path)
    resource_norm = resource.replace("\\", "/")
    allowed_patterns = policy.get(action, [])
    if _match_any(allowed_patterns, resource_norm):
        return AuthzResult(True, "ok", principal, action, resource)
    return AuthzResult(False, f"khong co pattern nao cho phep {action} tren {resource}",
                        principal, action, resource)


def check_path(principal: str, action: str, path_like: str) -> AuthzResult:
    """Kiem tra quyen voi path (co the la tuyet doi hoac tuong doi).
    Chuyen path tuyet doi thanh path tuong doi voi IHG_ROOT de match pattern.
    Neu path_like khong phai path (vd: agent id 'ihg-it'), goi check() truc tiep."""
    from .config import Config
    p = Path(path_like)
    # Heuristic: neu khong co separator va khong co drive letter -> khong phai path
    if (not p.is_absolute()
        and "/" not in path_like
        and "\\" not in path_like
        and ":" not in path_like
        and p.name == path_like):
        # Co the la 1 identifier nhu agent id
        return check(principal, action, path_like)
    try:
        rel = str(p.resolve().relative_to(Config.IHG_ROOT)).replace("\\", "/")
        return check(principal, action, rel)
    except ValueError:
        # Path nam ngoai IHG_ROOT -> tu choi
        return AuthzResult(False, f"path nam ngoai IHG_ROOT", principal, action, path_like)


def require(principal: str, action: str, path_like: str):
    """Raise PermissionError neu khong co quyen."""
    r = check_path(principal, action, path_like)
    if not r.allowed:
        raise PermissionError(f"AUTHZ_DENIED principal={r.principal} action={r.action} "
                             f"resource={r.resource} reason={r.reason}")


# ============== TESTS (chay khi goi truc tiep) ==============
def _self_tests():
    """Tra ve (passed, failed, messages)."""
    cases = [
        # (principal, action, resource, expected_allowed, mo_ta)
        ("gd-ihg", "read", "AI-Office/00-DIEU-HANH/PRIVATE/foo.md", True, "GD doc duoc PRIVATE"),
        ("nhan-vien", "read", "AI-Office/00-DIEU-HANH/PRIVATE/foo.md", False, "nhan vien KHONG doc duoc PRIVATE"),
        ("nhan-vien", "read", "AI-Office/01-PHONG-BAN/IT/public/help.md", True, "nhan vien doc public"),
        ("nhan-vien", "write", "AI-Office/01-PHONG-BAN/IT/public/help.md", False, "nhan vien KHONG ghi"),
        ("nhan-vien", "dispatch", "AI-Office/02-DU-AN/FOO", False, "nhan vien KHONG dispatch"),
        ("agent-qa", "read", "AI-Office/02-DU-AN/2026/IT/FOO/spec.md", True, "QA doc duoc du an"),
        ("agent-qa", "write", "AI-Office/00-DIEU-HANH/PRIVATE/foo.md", False, "QA KHONG ghi PRIVATE"),
        ("agent-it", "run_agent", "ahihi", False, "Agent it KHONG run_agent"),
        ("dept-it", "run_agent", "ihg-it", True, "dept-it chay duoc ihg-it"),
        ("dept-it", "run_agent", "ihg-finance", False, "dept-it KHONG chay ihg-finance (khong ton tai)"),
        ("unknown", "read", "AI-Office/00-DIEU-HANH/x.md", False, "principal khong ton tai"),
        ("gd-ihg", "", "x", False, "thieu action"),
    ]
    passed = []
    failed = []
    for principal, action, resource, expected, mo_ta in cases:
        r = check(principal, action, resource)
        ok = (r.allowed == expected)
        if ok:
            passed.append((mo_ta, r.allowed, expected))
        else:
            failed.append((mo_ta, principal, action, resource, r.allowed, expected, r.reason))
    return passed, failed


if __name__ == "__main__":
    p, f = _self_tests()
    print(f"PASS: {len(p)}")
    for mo_ta, got, exp in p:
        print(f"  OK  {mo_ta} (got={got}, expected={exp})")
    print(f"FAIL: {len(f)}")
    for mo_ta, principal, action, resource, got, exp, reason in f:
        print(f"  XX  {mo_ta} principal={principal} action={action} resource={resource}")
        print(f"      got={got} expected={exp} reason={reason}")
    if f:
        raise SystemExit(1)
    print("ALL AUTHZ TESTS PASS")
