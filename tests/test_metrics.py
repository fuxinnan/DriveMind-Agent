import pytest

from evaluation.metrics import aggregate_run, validate_raw_records


def telemetry_row(
    scenario: str,
    timestamp_ms: int,
    predicted_y_m: float,
    *,
    sample_valid: int = 1,
    timed_out: int = 0,
    collision_event_id: str = "",
    takeover_event_id: str = "",
    distance_delta_m: float = 25_000,
    planned_route_m: float = 100,
    completed_route_m: float = 0,
) -> dict[str, str]:
    values = {
        "owner_id": "owner_test",
        "run_id": "run_20260801_01",
        "baseline_run_id": "",
        "scenario_id": scenario,
        "timestamp_ms": timestamp_ms,
        "model_version": "model-test",
        "dataset": "dataset-test",
        "eval_region": "测试区域",
        "road_type": "城区道路",
        "weather": "晴天",
        "light_condition": "白天",
        "traffic_density": "中等交通",
        "ego_x_m": 0,
        "ego_y_m": 0,
        "speed_mps": 10,
        "acceleration_mps2": 0,
        "yaw_rate_rps": 0,
        "steering_angle_deg": 0,
        "predicted_x_m": 0,
        "predicted_y_m": predicted_y_m,
        "ground_truth_x_m": 0,
        "ground_truth_y_m": 0,
        "sample_valid": sample_valid,
        "timed_out": timed_out,
        "collision_event_id": collision_event_id,
        "takeover_event_id": takeover_event_id,
        "distance_delta_m": distance_delta_m,
        "planned_route_m": planned_route_m,
        "completed_route_m": completed_route_m,
    }
    return {key: str(value) for key, value in values.items()}


def test_trajectory_metrics_use_valid_points_and_scenario_endpoints():
    rows = [
        telemetry_row("scenario_a", 0, 1),
        telemetry_row("scenario_a", 100, 3, completed_route_m=80),
        telemetry_row("scenario_b", 0, 1),
        telemetry_row("scenario_b", 100, 1, completed_route_m=100),
    ]

    summary = aggregate_run(rows)

    assert float(summary["ade"]) == pytest.approx(1.5)
    assert float(summary["fde"]) == pytest.approx(2.0)
    assert float(summary["miss_rate"]) == pytest.approx(0.5)
    assert float(summary["route_completion"]) == pytest.approx(0.9)


def test_events_are_deduplicated_before_per_distance_normalization():
    rows = [
        telemetry_row(
            "scenario_a",
            0,
            0,
            collision_event_id="collision-1",
            takeover_event_id="takeover-1",
        ),
        telemetry_row(
            "scenario_a",
            100,
            0,
            collision_event_id="collision-1",
            takeover_event_id="takeover-1",
            completed_route_m=100,
        ),
        telemetry_row("scenario_b", 0, 0),
        telemetry_row("scenario_b", 100, 0, completed_route_m=100),
    ]

    summary = aggregate_run(rows)

    assert float(summary["collision_rate"]) == pytest.approx(0.5)
    assert float(summary["closed_loop_collision_per_100km"]) == pytest.approx(1.0)
    assert float(summary["closed_loop_takeover_per_100km"]) == pytest.approx(1.0)


def test_invalid_and_timeout_frames_are_excluded_from_trajectory_error():
    rows = [
        telemetry_row("scenario_a", 0, 100, sample_valid=0, timed_out=1),
        telemetry_row("scenario_a", 100, 1, completed_route_m=100),
    ]

    summary = aggregate_run(rows)

    assert float(summary["ade"]) == pytest.approx(1.0)
    assert float(summary["fde"]) == pytest.approx(1.0)
    assert float(summary["invalid_sample_rate"]) == pytest.approx(0.5)
    assert summary["timeout_count"] == "1"
    assert summary["gate_status"] == "INCONCLUSIVE"


def test_validation_rejects_unknown_baseline():
    rows = (telemetry_row("scenario_a", 0, 0),)
    rows[0]["baseline_run_id"] = "run_20260731_01"

    with pytest.raises(ValueError, match="baseline_run_id"):
        validate_raw_records(rows)
