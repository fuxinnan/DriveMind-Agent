from langchain_chroma import Chroma
from utils.config_handler import chroma_conf
from model.factory import embed_model

class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name = chroma_conf["collection_name"],
            embedding_function = embed_model,
            persist_directory = chroma_conf["persist_directory"],
        )

        self.spliter = None