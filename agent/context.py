from typing import TypedDict


class AgentContext(TypedDict):
    """Per-request context selected by the user in the Streamlit sidebar."""

    report: bool
    owner_id: str
    run_id: str
    baseline_run_id: str
