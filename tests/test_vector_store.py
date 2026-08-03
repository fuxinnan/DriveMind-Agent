from pathlib import Path

from utils.config_handler import chroma_conf
from utils.path_tools import get_abs_path


def test_chroma_indexes_only_drivemind_knowledge():
    knowledge_dir = Path(get_abs_path(chroma_conf["data_path"]))
    files = sorted(knowledge_dir.glob("*.txt"))

    assert chroma_conf["collection_name"] == "drivemind_eval"
    assert knowledge_dir.name == "knowledge"
    assert len(files) == 8


def test_knowledge_has_no_legacy_domain_terms():
    knowledge_dir = Path(get_abs_path(chroma_conf["data_path"]))
    content = "\n".join(
        path.read_text(encoding="utf-8") for path in knowledge_dir.glob("*.txt")
    )

    assert "扫地机器人" not in content
    assert "尘盒" not in content
