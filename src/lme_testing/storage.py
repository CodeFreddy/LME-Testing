from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


# 生成 run 目录使用 UTC 时间戳，保证跨时区协作时排序一致。
def timestamp_slug() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


# 确保目录存在。
def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


# 读取普通 JSON 文件。
def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


# 读取 JSONL 文件，每一行都是一个独立 JSON 对象。
def load_jsonl(path: Path) -> list[dict]:
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            lines.append(json.loads(line))
    return lines


# 写普通 JSON 文件，便于人工查阅。
def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# 原子写入 JSON 文件：先写 .tmp，再 rename。防止快速连续写入导致文件损坏。
def atomic_write_json(path: Path, data: object) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)  # 跨平台原子操作（同一文件系统内）


# 追加写 JSONL，用于记录批量模型调用结果。
def append_jsonl(path: Path, records: list[dict]) -> None:
    if not records:
        return
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")
