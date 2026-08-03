from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk

from agent.context import AgentContext
from agent.tools.agent_tools import (
    fetch_external_data,
    fill_context_for_report,
    get_env_condition,
    get_eval_owner_id,
    get_eval_region,
    get_run_id,
    rag_summarize,
)
from agent.tools.middleware import log_before_model, monitor_tool, report_prompt_switch
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts


class ReactAgent:
    def __init__(self):
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=[
                rag_summarize,
                get_eval_owner_id,
                get_run_id,
                get_eval_region,
                get_env_condition,
                fetch_external_data,
                fill_context_for_report,
            ],
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
            context_schema=AgentContext,
        )

    def execute_stream(
        self,
        query: str,
        owner_id: str,
        run_id: str,
        baseline_run_id: str = "",
    ):
        input_dict = {
            "messages": [
                {"role": "user", "content": query}
            ]
        }

        context: AgentContext = {
            "report": False,
            "owner_id": owner_id,
            "run_id": run_id,
            "baseline_run_id": baseline_run_id,
        }
        for message, _metadata in self.agent.stream(
            input_dict, stream_mode="messages", context=context
        ):
            if isinstance(message, AIMessageChunk) and isinstance(message.content, str):
                if message.content:
                    yield message.content