import os

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from model.factory import embed_model
from utils.config_handler import chroma_conf
from utils.file_handler import (
    get_file_md5_hex,
    listdir_with_allowed_type,
    pdf_loader,
    txt_loader,
)
from utils.loger_handler import logger
from utils.path_tools import get_abs_path

class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name = chroma_conf["collection_name"],
            embedding_function = embed_model,
            persist_directory = get_abs_path(chroma_conf["persist_directory"]),
        )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len,
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k":chroma_conf["k"]})

    def load_document(self) -> int:
        """
        从数据文件夹内读取数据文件，转为向量存入向量库、要计算文件的MD5做去重
        ：return None
        """
        def check_md5_hex(md5_for_check: str) -> bool:
            if not md5_for_check:
                return False
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                # 创建文件
                open(get_abs_path(chroma_conf["md5_hex_store"]),"w",encoding="utf-8").close()
                return False
            with open(get_abs_path(chroma_conf["md5_hex_store"]),"r",encoding="utf-8") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == md5_for_check:
                        return True   # md5处理过
                return False   # md5没处理过

        def save_md5_hex(md5_for_check: str) -> None:
            with open(get_abs_path(chroma_conf["md5_hex_store"]),"a",encoding="utf-8") as f:
                f.write(md5_for_check + "\n")

        def get_file_documents(read_path: str) -> list[Document]:
            suffix = os.path.splitext(read_path)[1].lower()
            if suffix == ".txt":
                return txt_loader(read_path)

            if suffix == ".pdf":
                return pdf_loader(read_path)

            return []

        allowed_files_path = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"])
        )

        loaded_count = 0
        failures: list[str] = []
        for path in allowed_files_path:
            # 获取文件的md5
            md5_hex = get_file_md5_hex(path)
            if not md5_hex:
                logger.warning(f"[加载知识库]{path}无法计算MD5，跳过")
                continue

            if check_md5_hex(md5_hex):
                logger.info(f"[加载知识库]{path}内容已经存在知识库内，跳过")
                continue

            try:
                documents: list[Document] = get_file_documents(path)
                if not documents:
                    logger.warning(f"[加载知识库]{path}文件内没有有效文本内容，跳过")
                    continue
                split_document: list[Document] = self.splitter.split_documents(documents)

                if not split_document:
                    logger.warning(f"[加载知识库]{path}分片后没有有效文本内容，跳过")
                    continue

                # 将内容存入向量库中
                self.vector_store.add_documents(split_document)

                # 记录已经处理好的文件的md5
                save_md5_hex(md5_hex)
                loaded_count += 1

                logger.info(f"[加载知识库]{path}内容加载成功")
            except Exception as e:
                logger.error(f"[加载知识库]{path}加载失败：{str(e)}",exc_info = True)
                failures.append(f"{path}: {e}")

        if failures:
            raise RuntimeError(
                f"{len(failures)} 个知识文件入库失败：{' | '.join(failures)}"
            )
        return loaded_count
