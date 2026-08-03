import os
from abc import ABC, abstractmethod
from typing import Optional

from dotenv import load_dotenv
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from utils.config_handler import rag_conf

load_dotenv()


def _get_api_key() -> str:
    """Return the configured model API key or fail with an actionable message."""
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "缺少模型 API Key。请设置 DASHSCOPE_API_KEY 环境变量；"
            "也可使用 OPENAI_API_KEY 作为兼容回退。"
        )
    return api_key


API_KEY = _get_api_key()
os.environ.setdefault("DASHSCOPE_API_KEY", API_KEY)
os.environ.setdefault("DASHSCOPE_BASE_URL", rag_conf["base_url"])


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        raise NotImplementedError

class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatOpenAI(
            model=rag_conf["chat_model_name"],
            api_key=API_KEY,
            base_url=rag_conf["base_url"],
        )


class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return DashScopeEmbeddings(
            model=rag_conf["embedding_model_name"],
            dashscope_api_key=API_KEY,
        )

chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()
