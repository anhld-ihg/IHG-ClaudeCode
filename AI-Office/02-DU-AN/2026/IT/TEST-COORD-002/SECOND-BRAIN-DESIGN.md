# IHG Second Brain — Thiết kế khởi đầu (CHẶNG 3)

> Trạng thái: BẢN THẢO. CHƯA TRIỂN KHAI.

## 1. Mục tiêu

IHG Second Brain là **bộ nhớ dài hạn** cho hệ thống AI IHG:
- Lưu lại tất cả cuộc hội thoại, quyết định, kiến thức.
- Có thể **truy vấn** từ nhiều Agent khác nhau.
- Có **phân quyền** rõ (nhân viên không thấy Private, Agent chỉ thấy khu vực mình).
- Có **lifecycle**: tự động thu hồi bản cũ khi có bản mới, đánh dấu lỗi thời.
- Có **audit**: ai viết, khi nào, sửa bao nhiêu lần.

## 2. Cấu trúc

```
knowledge/
├── public/                  # Tất cả Agent + nhân viên đều đọc được
│   ├── 01-policies/         # Chính sách công ty (AI-Office/00-DIEU-HANH mirror)
│   ├── 02-procedures/       # Quy trình chuẩn
│   └── 03-faq/              # Câu hỏi thường gặp
├── employee/                # Chỉ nhân viên + GD
│   ├── 01-onboarding/
│   ├── 02-handbook/
│   └── 03-forms/
├── project/                 # Theo dự án
│   └── <project_id>/
│       ├── decisions/       # Quyết định trong dự án
│       ├── conversations/   # Hội thoại quan trọng
│       └── artifacts/       # Bản snapshot của artifact
├── conversation/            # Tất cả hội thoại Agent-Agent, Agent-GD
│   └── YYYY-MM-DD/
│       └── <conv_id>.json
└── index/                   # Chỉ mục tìm kiếm
    ├── tag-index.json       # tag -> [entry]
    ├── actor-index.json     # actor -> [entry]
    └── search.db            # SQLite FTS5 (chặng 4)
```

## 3. Entry Schema

```json
{
  "id": "kb-2026-10-14-001",
  "type": "decision" | "conversation" | "artifact" | "policy" | "procedure" | "faq",
  "title": "...",
  "content": "...",
  "tags": ["hr", "policy", "leave"],
  "actor": "ihg-it" | "ihg-hr" | "gd-ihg" | "nhan-vien",
  "visibility": "public" | "employee" | "project" | "private",
  "project_id": "TEST-COORD-002" | null,
  "created_at": "2026-10-14T13:00:00+07:00",
  "updated_at": "2026-10-14T13:00:00+07:00",
  "version": 1,
  "supersedes": "kb-..." | null,
  "sha256": "...",
  "source": "ai-office/02-DU-AN/2026/IT/TEST-COORD-002/BAO-CAO-HOAN-THANH.md"
}
```

## 4. API

```python
class SecondBrain:
    def add(self, entry: dict) -> str:
        """Tra ve entry id. Tu choi neu actor khong co quyen visibility."""

    def get(self, entry_id: str) -> dict:
        """Doc 1 entry. Tra ve None neu actor khong co quyen."""

    def search(self, query: str, tags: list = None, actor: str = None) -> list:
        """Full-text search. Chi tra ve entry actor duoc doc."""

    def version(self, entry_id: str) -> list:
        """Lich su cac phien ban cua entry."""

    def link(self, src_id: str, dst_id: str, relation: str) -> None:
        """Tao lien ket giua 2 entry (vd: decision lien quan conversation)."""
```

## 5. Phân quyền truy cập

| Visibility | GD | Nhân viên | Agent (khu vực) | Agent (khác) |
|------------|----|-----------|------------------|---------------|
| public     | R/W | R         | R                | R             |
| employee   | R/W | R/W       | DENY             | DENY          |
| project    | R/W | (project member) R | R (nếu trong project) | DENY |
| private    | R/W | DENY      | DENY             | DENY          |

## 6. Lifecycle

- **supersedes**: Khi entry mới `supersedes` entry cũ, entry cũ chuyển sang `archived/` (vẫn truy vấn được qua version history).
- **Tự động tag outdated**: Sau 12 tháng không ai `touch` → tag `outdated`. Sau 24 tháng → chuyển `archive/`.
- **Conversation cutoff**: Mỗi hội thoại dài quá 50K tokens → tách thành nhiều entry `conversation-part-N`.

## 7. Tích hợp với ihg_core hiện tại

```python
from ihg_core.second_brain import SecondBrain

# Sau khi QA PASS, tu dong add vao Second Brain
store.transition(task_id, "DELIVERED")
sb.add({
    "type": "artifact",
    "title": f"Artifact cua {task_id}",
    "content": artifact_text,
    "tags": ["artifact", agent_id],
    "actor": agent_id,
    "visibility": "project",
    "project_id": project_id,
    "source": artifact_path,
})
```

## 8. Bước tiếp theo (CHẶNG 3)

1. Tạo `src/ihg_core/second_brain.py` (cơ bản, JSON store)
2. Tạo `tests/test_second_brain.py` (5 test)
3. Tích hợp: Coordinator tự động add vào Second Brain khi DELIVERED
4. CLI: `python -m ihg_core.second_brain search "tu khoa"`
5. Viết CLI xem entry: `python -m ihg_core.second_brain get <id>`

## 9. CHƯA làm trong pilot 002

- ✗ Implementation file — chờ CHẶNG 2 PASS
- ✗ SQLite FTS5 — chặng 4
- ✗ Vector search / embedding — chặng 5 (khi có LLM mạnh hơn)
- ✗ Web UI — chặng 6

## 10. Cam kết

- Phân quyền **thật** ở code, không dựa vào prompt.
- Mọi ghi đều qua AuthZ, ghi SHA-256, có audit log.
- Mỗi phiên bản entry có thể khôi phục.
