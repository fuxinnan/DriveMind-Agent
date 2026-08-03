import csv
import json
import os
from functools import lru_cache
from typing import Any

from langchain.tools import ToolRuntime, tool

from agent.context import AgentContext
from utils.config_handler import agent_conf
from utils.loger_handler import logger
from utils.path_tools import get_abs_path


def _records_path() -> str:
    return get_abs_path(agent_conf["external_data_path"])


@lru_cache(maxsize=1)
def load_eval_records() -> tuple[dict[str, str], ...]:
    """Load immutable evaluation records from the configured UTF-8 CSV."""
    path = _records_path()
    if not os.path.isfile(path):
        raise FileNotFoundError(f"评测数据文件不存在：{path}")

    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        records = tuple(dict(row) for row in csv.DictReader(file))

    required = {"owner_id", "run_id", "eval_region", "env_condition"}
    missing = required.difference(records[0].keys() if records else set())
    if missing:
        raise ValueError(f"评测数据缺少字段：{', '.join(sorted(missing))}")
    return records


def clear_records_cache() -> None:
    """Clear the CSV cache, primarily for tests and local data refreshes."""
    load_eval_records.cache_clear()


def list_eval_owners() -> list[str]:
    return sorted({row["owner_id"] for row in load_eval_records()})


def list_runs_for_owner(owner_id: str) -> list[str]:
    return sorted(
        (row["run_id"] for row in load_eval_records() if row["owner_id"] == owner_id),
        reverse=True,
    )


def get_eval_record(owner_id: str, run_id: str) -> dict[str, str] | None:
    return next(
        (
            dict(row)
            for row in load_eval_records()
            if row["owner_id"] == owner_id and row["run_id"] == run_id
        ),
        None,
    )


def _context_value(runtime: ToolRuntime[AgentContext], key: str) -> str:
    value = runtime.context.get(key, "")
    return str(value).strip()


@lru_cache(maxsize=1)
def _rag_service():
    from rag.rag_service import RagSummaryService

    return RagSummaryService()


@tool(description="从 DriveMind 评测知识库检索资料；仅基于检索资料回答评测知识问题")
def rag_summarize(query: str) -> str:
    return _rag_service().rag_summarize(query)


@tool(description="返回当前侧边栏选中的评测负责人 owner_id，不生成随机值")
def get_eval_owner_id(runtime: ToolRuntime[AgentContext]) -> str:
    return _context_value(runtime, "owner_id")


@tool(description="返回当前侧边栏选中的评测跑次 run_id，不生成随机值")
def get_run_id(runtime: ToolRuntime[AgentContext]) -> str:
    return _context_value(runtime, "run_id")


@tool(description="返回当前选中跑次的评测地图或评测域")
def get_eval_region(runtime: ToolRuntime[AgentContext]) -> str:
    record = get_eval_record(
        _context_value(runtime, "owner_id"), _context_value(runtime, "run_id")
    )
    return record["eval_region"] if record else ""


@tool(description="返回当前选中跑次的光照、天气、道路等评测环境条件")
def get_env_condition(runtime: ToolRuntime[AgentContext]) -> str:
    record = get_eval_record(
        _context_value(runtime, "owner_id"), _context_value(runtime, "run_id")
    )
    return record["env_condition"] if record else ""


def build_external_data(
    owner_id: str, run_id: str, baseline_run_id: str = ""
) -> dict[str, Any] | None:
    """Return selected run data and an optional baseline, without inference."""
    record = get_eval_record(owner_id, run_id)
    if record is None:
        return None

    baseline = None
    if baseline_run_id:
        baseline = get_eval_record(owner_id, baseline_run_id)

    return {
        "selected_run": record,
        "baseline_run": baseline,
        "baseline_requested": baseline_run_id or None,
        "data_policy": "仅可引用以上原始字段；空值或缺失字段不得推断。",
    }


@tool(
    description=(
        "按 owner_id 与 run_id 查询评测记录，可附带 baseline_run_id。"
        "仅允许查询当前侧边栏选中的负责人和跑次；未命中时返回明确无数据结果。"
    )
)
def fetch_external_data(
    owner_id: str,
    run_id: str,
    runtime: ToolRuntime[AgentContext],
    baseline_run_id: str = "",
) -> str:
    selected_owner = _context_value(runtime, "owner_id")
    selected_run = _context_value(runtime, "run_id")
    selected_baseline = _context_value(runtime, "baseline_run_id")

    if owner_id != selected_owner or run_id != selected_run:
        logger.warning(
            "[fetch_external_data]拒绝查询非当前上下文数据：owner=%s run=%s",
            owner_id,
            run_id,
        )
        return "无数据：请求的 owner_id 或 run_id 与当前侧边栏选择不一致。"

    if baseline_run_id and baseline_run_id != selected_baseline:
        return "无数据：请求的 baseline_run_id 与当前侧边栏选择不一致。"

    result = build_external_data(
        selected_owner, selected_run, selected_baseline or baseline_run_id
    )
    if result is None:
        logger.warning(
            "[fetch_external_data]未找到 owner=%s run=%s", selected_owner, selected_run
        )
        return "无数据：未检索到当前负责人和跑次的评测记录。"
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool(
    description=(
        "报告生成的前置工具。调用后由中间件切换至报告提示词；"
        "仅在用户明确要求生成或查询评测报告时调用。"
    )
)
def fill_context_for_report() -> str:
    return "报告上下文已启用"