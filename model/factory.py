from abc import ABC,abstractmethod
from typing import Optional
import os
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from utils.config_handler import rag_conf

os.environ["DASHSCOPE_BASE_URL"] = rag_conf["base_url"]

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_openai import ChatOpenAI


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass

class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatOpenAI(
            model = rag_conf["chat_model_name"],
            api_key = rag_conf["api_key"],
            base_url = rag_conf["base_url"],
        )


class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return DashScopeEmbeddings(
            model = rag_conf["embedding_model_name"],
            dashscope_api_key = rag_conf["api_key"],
        )

chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()
