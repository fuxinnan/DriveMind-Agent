import json
import re

from langchain.tools import ToolRuntime

from agent.tools.agent_tools import (
    build_external_data,
    fetch_external_data,
    get_env_condition,
    get_eval_owner_id,
    get_eval_region,
    get_run_id,
    list_eval_owners,
    list_runs_for_owner,
    load_eval_records,
    load_raw_records,
)


def make_runtime(owner_id: str, run_id: str, baseline_run_id: str = ""):
    return ToolRuntime(
        state={},
        context={
            "report": False,
            "owner_id": owner_id,
            "run_id": run_id,
            "baseline_run_id": baseline_run_id,
        },
        config={},
        stream_writer=lambda _chunk: None,
        tool_call_id=None,
        store=None,
    )


def test_native_records_are_consistent():
    raw_records = load_raw_records()
    records = load_eval_records()
    owners = list_eval_owners()

    assert len(raw_records) > len(records)
    assert {
        "scenario_id",
        "timestamp_ms",
        "speed_mps",
        "predicted_x_m",
        "ground_truth_x_m",
        "weather",
    }.issubset(raw_records[0])
    assert len(owners) >= 3
    assert len(records) >= 12
    assert len({row["run_id"] for row in records}) == len(records)
    assert all(re.fullmatch(r"run_\d{8}_\d{2}", row["run_id"]) for row in records)
    assert all(row["source"] == "computed_from_raw_telemetry" for row in records)
    assert all(row["gate_status"] == "INCONCLUSIVE" for row in records)

    keys = {(row["owner_id"], row["run_id"]) for row in records}
    for row in records:
        baseline = row.get("baseline_run_id", "")
        if baseline:
            assert (row["owner_id"], baseline) in keys


def test_context_tools_return_selected_values():
    owner_id = list_eval_owners()[0]
    run_id = list_runs_for_owner(owner_id)[0]
    runtime = make_runtime(owner_id, run_id)
    selected = build_external_data(owner_id, run_id)

    assert get_eval_owner_id.func(runtime=runtime) == owner_id
    assert get_run_id.func(runtime=runtime) == run_id
    assert get_eval_region.func(runtime=runtime) == selected["selected_run"]["eval_region"]
    assert (
        get_env_condition.func(runtime=runtime)
        == selected["selected_run"]["env_condition"]
    )


def test_fetch_external_data_includes_optional_baseline():
    owner_id = list_eval_owners()[0]
    runs = list_runs_for_owner(owner_id)
    run_id, baseline_run_id = runs[0], runs[1]
    runtime = make_runtime(owner_id, run_id, baseline_run_id)

    result = fetch_external_data.func(
        owner_id=owner_id,
        run_id=run_id,
        baseline_run_id=baseline_run_id,
        runtime=runtime,
    )
    payload = json.loads(result)

    assert payload["selected_run"]["run_id"] == run_id
    assert payload["baseline_run"]["run_id"] == baseline_run_id


def test_fetch_rejects_context_mismatch():
    owners = list_eval_owners()
    owner_id = owners[0]
    run_id = list_runs_for_owner(owner_id)[0]
    runtime = make_runtime(owner_id, run_id)

    result = fetch_external_data.func(
        owner_id=owners[1],
        run_id=run_id,
        baseline_run_id="",
        runtime=runtime,
    )

    assert result.startswith("无数据")
