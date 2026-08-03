"""Rebuild the local DriveMind Chroma knowledge collection."""

import argparse
import os
import shutil
from pathlib import Path

from utils.config_handler import chroma_conf
from utils.path_tools import get_abs_path


def validate_sources() -> list[Path]:
    knowledge_dir = Path(get_abs_path(chroma_conf["data_path"]))
    allowed = {
        suffix if suffix.startswith(".") else f".{suffix}"
        for suffix in chroma_conf["allow_knowledge_file_type"]
    }
    files = sorted(
        path
        for path in knowledge_dir.iterdir()
        if path.is_file() and path.suffix.lower() in allowed
    )
    if not files:
        raise RuntimeError(f"知识目录中没有可入库文件：{knowledge_dir}")
    for path in files:
        if not path.read_text(encoding="utf-8").strip():
            raise RuntimeError(f"知识文件为空：{path}")
    return files


def rebuild() -> None:
    from rag.vector_store import VectorStoreService

    files = validate_sources()
    persist_directory = get_abs_path(chroma_conf["persist_directory"])
    md5_store = get_abs_path(chroma_conf["md5_hex_store"])

    if os.path.isdir(persist_directory):
        shutil.rmtree(persist_directory)
    if os.path.isfile(md5_store):
        os.remove(md5_store)

    service = VectorStoreService()
    service.load_document()
    print(f"DriveMind 评测知识库重建完成，共处理 {len(files)} 个源文件。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="仅验证知识源，不调用嵌入模型"
    )
    arguments = parser.parse_args()
    if arguments.check:
        print(f"知识源校验通过，共 {len(validate_sources())} 个文件。")
    else:
        rebuild()
