"""Compute run-level evaluation metrics from frame-level vehicle telemetry."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from functools import lru_cache
from typing import Any, Iterable, Mapping

import yaml

from utils.path_tools import get_abs_path


IDENTITY_FIELDS = (
    "owner_id",
    "run_id",
    "baseline_run_id",
    "model_version",
    "dataset",
    "eval_region",
)
FLOAT_FIELDS = (
    "timestamp_ms",
    "ego_x_m",
    "ego_y_m",
    "speed_mps",
    "acceleration_mps2",
    "yaw_rate_rps",
    "steering_angle_deg",
    "predicted_x_m",
    "predicted_y_m",
    "ground_truth_x_m",
    "ground_truth_y_m",
    "distance_delta_m",
    "planned_route_m",
    "completed_route_m",
)


@lru_cache(maxsize=1)
def load_metrics_config() -> dict[str, Any]:
    path = get_abs_path("config/metrics.yml")
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def _number(row: Mapping[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            f"原始遥测字段 {field} 必须是数值，"
            f"run={row.get('run_id', '')} scenario={row.get('scenario_id', '')}"
        ) from error
    if not math.isfinite(value):
        raise ValueError(f"原始遥测字段 {field} 必须是有限数值")
    return value


def _flag(row: Mapping[str, str], field: str) -> bool:
    value = str(row.get(field, "")).strip().lower()
    if value in {"1", "true", "yes"}:
        return True
    if value in {"0", "false", "no"}:
        return False
    raise ValueError(
        f"原始遥测字段 {field} 必须是 0/1 或 true/false，"
        f"实际值为 {row.get(field)!r}"
    )


def _event_ids(rows: Iterable[Mapping[str, str]], field: str) -> set[str]:
    return {
        str(row.get(field, "")).strip()
        for row in rows
        if str(row.get(field, "")).strip()
    }


def _format_metric(value: float | None, digits: int = 6) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def validate_raw_records(
    records: tuple[dict[str, str], ...],
    config: Mapping[str, Any] | None = None,
) -> None:
    """Validate schema, identity consistency, references, and numeric ranges."""
    if not records:
        raise ValueError("原始遥测 CSV 为空")

    config = config or load_metrics_config()
    required = set(config["required_fields"])
    missing = required.difference(records[0])
    if missing:
        raise ValueError(f"原始遥测 CSV 缺少字段：{', '.join(sorted(missing))}")

    run_pattern = re.compile(str(config["run_id_pattern"]))
    run_metadata: dict[tuple[str, str], tuple[str, ...]] = {}
    keys: set[tuple[str, str]] = set()

    for row in records:
        owner_id = row["owner_id"].strip()
        run_id = row["run_id"].strip()
        scenario_id = row["scenario_id"].strip()
        if not owner_id or not scenario_id:
            raise ValueError("owner_id 和 scenario_id 不得为空")
        if not run_pattern.fullmatch(run_id):
            raise ValueError(f"run_id 格式无效：{run_id}")

        key = (owner_id, run_id)
        keys.add(key)
        metadata = tuple(row[field].strip() for field in IDENTITY_FIELDS[2:])
        if key in run_metadata and run_metadata[key] != metadata:
            raise ValueError(f"同一跑次的身份元数据不一致：{owner_id}/{run_id}")
        run_metadata[key] = metadata

        for field in FLOAT_FIELDS:
            value = _number(row, field)
            if field in {
                "timestamp_ms",
                "speed_mps",
                "distance_delta_m",
                "planned_route_m",
                "completed_route_m",
            } and value < 0:
                raise ValueError(f"字段 {field} 不得为负数")
        _flag(row, "sample_valid")
        _flag(row, "timed_out")

    for (owner_id, _run_id), metadata in run_metadata.items():
        baseline_run_id = metadata[0]
        if baseline_run_id and (owner_id, baseline_run_id) not in keys:
            raise ValueError(
                f"baseline_run_id 不存在或不属于同一 owner：{baseline_run_id}"
            )


def _environment_summary(rows: list[dict[str, str]]) -> str:
    conditions = {
        "_".join(
            (
                row["light_condition"].strip(),
                row["weather"].strip(),
                row["traffic_density"].strip(),
            )
        )
        for row in rows
    }
    return next(iter(conditions)) if len(conditions) == 1 else f"多环境_{len(conditions)}类"


def _observed_risks(rows: list[dict[str, str]]) -> str:
    event_rows = [
        row
        for row in rows
        if row["collision_event_id"].strip() or row["takeover_event_id"].strip()
    ]
    if not event_rows:
        return "原始遥测中未记录碰撞或接管事件"
    slices = {
        "/".join(
            (
                row["road_type"].strip(),
                row["weather"].strip(),
                row["light_condition"].strip(),
                row["traffic_density"].strip(),
            )
        )
        for row in event_rows
    }
    return "记录到碰撞或接管事件的切片：" + "；".join(sorted(slices))


def aggregate_run(
    rows: list[dict[str, str]],
    config: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Aggregate one run while preserving evidence and metric provenance."""
    if not rows:
        raise ValueError("无法聚合空跑次")
    config = config or load_metrics_config()
    miss_threshold = float(config["miss_threshold_m"])

    scenarios: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        scenarios[row["scenario_id"]].append(row)

    valid_errors: list[float] = []
    final_errors: list[float] = []
    total_frames = len(rows)
    invalid_frames = 0
    timeout_count = 0
    planned_route_m = 0.0
    completed_route_m = 0.0

    for scenario_rows in scenarios.values():
        ordered = sorted(scenario_rows, key=lambda item: _number(item, "timestamp_ms"))
        valid_rows: list[dict[str, str]] = []
        for row in ordered:
            timed_out = _flag(row, "timed_out")
            is_valid = _flag(row, "sample_valid") and not timed_out
            timeout_count += int(timed_out)
            invalid_frames += int(not is_valid)
            if is_valid:
                valid_rows.append(row)
                error = math.hypot(
                    _number(row, "predicted_x_m")
                    - _number(row, "ground_truth_x_m"),
                    _number(row, "predicted_y_m")
                    - _number(row, "ground_truth_y_m"),
                )
                valid_errors.append(error)

        if valid_rows:
            endpoint = valid_rows[-1]
            final_errors.append(
                math.hypot(
                    _number(endpoint, "predicted_x_m")
                    - _number(endpoint, "ground_truth_x_m"),
                    _number(endpoint, "predicted_y_m")
                    - _number(endpoint, "ground_truth_y_m"),
                )
            )

        final_row = ordered[-1]
        planned_route_m += _number(final_row, "planned_route_m")
        completed_route_m += min(
            _number(final_row, "completed_route_m"),
            _number(final_row, "planned_route_m"),
        )

    total_distance_m = sum(_number(row, "distance_delta_m") for row in rows)
    collision_ids = _event_ids(rows, "collision_event_id")
    takeover_ids = _event_ids(rows, "takeover_event_id")
    scenarios_with_collision = sum(
        bool(_event_ids(items, "collision_event_id"))
        for items in scenarios.values()
    )

    ade = sum(valid_errors) / len(valid_errors) if valid_errors else None
    fde = sum(final_errors) / len(final_errors) if final_errors else None
    miss_rate = (
        sum(error > miss_threshold for error in final_errors) / len(final_errors)
        if final_errors
        else None
    )
    collision_rate = (
        scenarios_with_collision / len(scenarios) if scenarios else None
    )
    route_completion = (
        completed_route_m / planned_route_m if planned_route_m > 0 else None
    )
    distance_km = total_distance_m / 1000
    takeover_per_100km = (
        len(takeover_ids) / distance_km * 100 if distance_km > 0 else None
    )
    collision_per_100km = (
        len(collision_ids) / distance_km * 100 if distance_km > 0 else None
    )

    first = rows[0]
    return {
        "owner_id": first["owner_id"].strip(),
        "run_id": first["run_id"].strip(),
        "baseline_run_id": first["baseline_run_id"].strip(),
        "model_version": first["model_version"].strip(),
        "dataset": first["dataset"].strip(),
        "eval_region": first["eval_region"].strip(),
        "env_condition": _environment_summary(rows),
        "ade": _format_metric(ade),
        "fde": _format_metric(fde),
        "miss_rate": _format_metric(miss_rate),
        "collision_rate": _format_metric(collision_rate),
        "route_completion": _format_metric(route_completion),
        "closed_loop_takeover_per_100km": _format_metric(takeover_per_100km),
        "closed_loop_collision_per_100km": _format_metric(collision_per_100km),
        "timeout_count": str(timeout_count),
        "invalid_sample_rate": _format_metric(invalid_frames / total_frames),
        "gate_status": "INCONCLUSIVE",
        "comparison_summary": "指标由原始逐时刻遥测确定性聚合，未执行自动门禁判定",
        "scenario_risks": _observed_risks(rows),
        "notes": (
            f"原始帧{total_frames}条；场景{len(scenarios)}个；"
            f"有效轨迹点{len(valid_errors)}个；有效里程{distance_km:.3f}km"
        ),
        "source": "computed_from_raw_telemetry",
        "raw_frame_count": str(total_frames),
        "scenario_count": str(len(scenarios)),
        "valid_trajectory_point_count": str(len(valid_errors)),
        "valid_distance_km": _format_metric(distance_km),
        "miss_threshold_m": _format_metric(miss_threshold),
        "coordinate_unit": str(config["coordinate_unit"]),
    }


def aggregate_runs(
    records: tuple[dict[str, str], ...],
    config: Mapping[str, Any] | None = None,
) -> tuple[dict[str, str], ...]:
    """Validate and aggregate all owner/run groups in deterministic order."""
    config = config or load_metrics_config()
    validate_raw_records(records, config)
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in records:
        grouped[(row["owner_id"].strip(), row["run_id"].strip())].append(row)
    return tuple(
        aggregate_run(grouped[key], config)
        for key in sorted(grouped)
    )
