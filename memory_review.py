"""
记忆清理审查工具
- 支持选择清理阈值：7 天 / 15 天 / 30 天 / 自定义
- 按条件列出可清理的记忆（默认 30 天，非高重要）
- 用户勾选（输入序号/范围/ALL）决定保留或删除
"""

import sys
import textwrap
from typing import List

sys.path.insert(0, ".")

try:
    from memory_service import get_memory_service
except ImportError:
    print("导入 memory_service 失败，请确保已安装依赖并在项目根目录运行。")
    sys.exit(1)


def human_preview(text: str, width: int = 80, max_lines: int = 3) -> str:
    wrapped = textwrap.wrap(text, width=width)
    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines] + ["..."]
    return "\n       ".join(wrapped)


def parse_selection(user_input: str, total: int) -> List[int]:
    user_input = user_input.strip().lower()
    if user_input in ["all", "a"]:
        return list(range(total))
    if not user_input:
        return []
    indices = set()
    parts = user_input.replace("，", ",").split(",")
    for part in parts:
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-")
                start_i, end_i = int(start), int(end)
                for i in range(start_i, end_i + 1):
                    indices.add(i)
            except Exception:
                continue
        else:
            try:
                indices.add(int(part))
            except Exception:
                continue
    return [i for i in indices if 0 <= i < total]


def choose_days() -> int:
    print("选择清理时间阈值（天）：[7] / [15] / [30] / 自定义(输入数字，回车默认30)")
    val = input("选择：").strip()
    if val == "7":
        return 7
    if val == "15":
        return 15
    if val == "30" or val == "":
        return 30
    try:
        num = int(val)
        if num <= 0:
            return 30
        return num
    except Exception:
        return 30


def main():
    service = get_memory_service()
    older_days = choose_days()
    candidates = service.list_cleanup_candidates(older_than_days=older_days, importance_max="medium", limit=500)

    if not candidates:
        print(f"没有发现超过{older_days}天的低/普通重要性记忆，无需清理。")
        return

    print(f"发现 {len(candidates)} 条可清理的记忆（超过 {older_days} 天，非高重要）：\n")

    for idx, item in enumerate(candidates):
        meta = item["metadata"]
        topic = meta.get("topic", "未知话题")
        imp = meta.get("importance", "medium")
        module = meta.get("module", "normal")
        ts = meta.get("timestamp", "未知时间")
        preview = human_preview(item["text"])
        print(f"[{idx}] ({imp}/{module}) {topic} | 时间: {ts} | 年龄: {item['age_days']}天\n       {preview}\n")

    print("输入要删除的序号，支持：\n- 单个: 0,2,5\n- 范围: 0-10\n- 全部: all\n- 直接回车跳过删除")
    selection = input("删除哪些？ ").strip()
    indices = parse_selection(selection, len(candidates))

    if not indices:
        print("未选择任何条目，未执行删除。")
        return

    delete_ids = [candidates[i]["id"] for i in indices]
    print(f"即将删除 {len(delete_ids)} 条，确认执行？ (y/N)")
    confirm = input().strip().lower()
    if confirm not in ["y", "yes"]:
        print("已取消删除。")
        return

    service.collection.delete(ids=delete_ids)
    print(f"已删除 {len(delete_ids)} 条记忆。")


if __name__ == "__main__":
    main()
