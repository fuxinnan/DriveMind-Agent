import hashlib
import os

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

from utils.loger_handler import logger


def get_file_md5_hex(filepath: str) -> str | None:
    if not os.path.exists(filepath):
        logger.error(f"[md5计算]文件{filepath}不存在")
        return None
    
    if not os.path.isfile(filepath):
        logger.error(f"[md5计算]路径{filepath}不是文件")
        return None

    md5_obj = hashlib.md5()

    chunk_size = 4096    # 4kb分片，避免文件过大爆内存
    try:
        with open(filepath,"rb") as f:      # 必须二进制读取
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)
            
            md5_hex = md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error(f"计算文件{filepath}md5失败, {str(e)}")
        return None



def listdir_with_allowed_type(
    path: str, allowed_types: tuple[str, ...]
) -> tuple[str, ...]:
    files = []

    if not os.path.isdir(path):
        logger.error(f"[listdir_with_allowed_type]{path}不是文件夹")
        return ()

    normalized_types = tuple(
        suffix.lower() if suffix.startswith(".") else f".{suffix.lower()}"
        for suffix in allowed_types
    )
    
    for f in os.listdir(path):
        file_path = os.path.join(path, f)
        if os.path.isfile(file_path) and f.lower().endswith(normalized_types):
            files.append(file_path)
    
    return tuple(sorted(files))


def pdf_loader(filepath: str, passwd=None) -> list[Document]:
    loader = PyPDFLoader(filepath, password=passwd)
    return loader.load()


def txt_loader(filepath: str) -> list[Document]:
    loader = TextLoader(filepath, encoding="utf-8", autodetect_encoding=True)
    return loader.load()