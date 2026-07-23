from abc import ABC,abstractmethod
from typing import Optional
from langchain_core.embeddings import Embeddings

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models.tongyi import ChatTongyi,BaseChatModel

from utils.config_handler import rag_conf

class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        pass

class ChatModelFactory(BaseChatModel):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatTongyi(
            model = rag_conf["chat_model_name"]
        )


class EmbeddingsFactory(BaseChatModel):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return DashScopeEmbeddings(
            model = rag_conf["embedding_model_name"]
        )

chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()
