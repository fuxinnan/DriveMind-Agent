from langchain.agents.middleware import AgentState, ModelRequest, Runtime, dynamic_prompt, wrap_tool_call,before_model
from langchain.tools.tool_node import ToolCallRequest
from typing import Callable
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from utils.loger_handler import logger
from utils.prompt_loader import load_report_prompts,load_system_prompts


@wrap_tool_call
def monitor_tool(
    # 请求的数据封装
    request: ToolCallRequest,
    # 执行的函数本身
    handler: Callable[[ToolCallRequest],ToolMessage | Command],
) -> ToolMessage | Command:                         # 工具执行监控
    logger.info(f"[tool monitor]执行工具：{request.tool_call['name']}")
    logger.info(f"[tool monitor]传入参数：{request.tool_call['args']}")

    try:
        res = handler(request)
        logger.info(f"[tool monitor]工具{request.tool_call['name']}调用成功")

        if request.tool_call['name'] == "fill_context_for_report":
            request.runtime.context["report"] = True

        return res
    except Exception as e:
        logger.error(f"工具{request.tool_call['name']}调用失败,原因：{str(e)}")
        raise e


@before_model
def log_before_model(
    state: AgentState,           # 整个智能体的状态记录
    runtime: Runtime,             # 记录着呢更个执行过程的上下文信息
):   # 在模型中执行前输出日志
    logger.info(f"[log_before_model]即将调用模型,带有{len(state['messages'])}条消息")

    if not state['messages']:
        return None
    
    last_msg = state['messages'][-1]
    content = getattr(last_msg, 'content', None) or ''
    logger.debug(f"[log_before_model]{type(last_msg).__name__} | {content.strip()}")
    
    return None


def select_system_prompt(report: bool) -> str:
    """Select a prompt without coupling tests to LangChain's middleware wrapper."""
    return load_report_prompts() if report else load_system_prompts()


@dynamic_prompt
def report_prompt_switch(request: ModelRequest):
    is_report = request.runtime.context.get("report", False)
    return select_system_prompt(is_report)

