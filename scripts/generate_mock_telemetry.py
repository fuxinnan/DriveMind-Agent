"""Generate deterministic frame-level Mock telemetry for local development."""

from __future__ import annotations

import csv
from pathlib import Path

from utils.path_tools import get_abs_path


FIELDS = [
    "owner_id",
    "run_id",
    "baseline_run_id",
    "scenario_id",
    "timestamp_ms",
    "model_version",
    "dataset",
    "eval_region",
    "road_type",
    "weather",
    "light_condition",
    "traffic_density",
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
    "sample_valid",
    "timed_out",
    "collision_event_id",
    "takeover_event_id",
    "distance_delta_m",
    "planned_route_m",
    "completed_route_m",
]


RUNS = [
    ("owner_alpha", "run_20260701_01", "run_20260701_01", "dm-planner-1.0", "dm-eval-urban-v3", "华东城区", "城区道路", "晴天", "白天", "中等交通", 1.72, .912, 320, 4, 1, 1),
    ("owner_alpha", "run_20260708_01", "run_20260701_01", "dm-planner-1.1", "dm-eval-urban-v3", "华东城区", "城区道路", "晴天", "白天", "中等交通", 1.61, .921, 350, 3, 1, 1),
    ("owner_alpha", "run_20260715_01", "run_20260701_01", "dm-planner-1.2", "dm-eval-urban-v3", "华东城区", "城区道路", "小雨", "夜间", "高交通", 2.15, .884, 300, 6, 2, 2),
    ("owner_alpha", "run_20260722_01", "run_20260701_01", "dm-planner-1.3", "dm-eval-urban-v3", "华东城区", "城区道路", "晴天", "白天", "中等交通", 1.52, .934, 410, 3, 1, 0),
    ("owner_beta", "run_20260702_01", "run_20260702_01", "dm-perception-2.0", "dm-eval-highway-v2", "华北高速", "高速公路", "晴天", "白天", "低交通", 1.34, .957, 500, 3, 1, 0),
    ("owner_beta", "run_20260709_01", "run_20260702_01", "dm-perception-2.1", "dm-eval-highway-v2", "华北高速", "高速公路", "晴天", "白天", "低交通", 1.27, .963, 520, 2, 1, 0),
    ("owner_beta", "run_20260716_01", "run_20260702_01", "dm-perception-2.2", "dm-eval-highway-v2", "华北高速", "高速公路", "大雨", "夜间", "中等交通", 2.30, .901, 330, 6, 2, 2),
    ("owner_beta", "run_20260723_01", "run_20260702_01", "dm-perception-2.3", "dm-eval-highway-v2", "华北高速", "高速公路", "晴天", "白天", "低交通", 1.19, .969, 610, 2, 1, 0),
    ("owner_gamma", "run_20260703_01", "run_20260703_01", "dm-stack-0.9", "dm-eval-mixed-v5", "华南混合道路", "混合道路", "多云", "黄昏", "高交通", 2.40, .861, 280, 7, 2, 2),
    ("owner_gamma", "run_20260710_01", "run_20260703_01", "dm-stack-1.0", "dm-eval-mixed-v5", "华南混合道路", "混合道路", "多云", "黄昏", "高交通", 2.05, .883, 300, 6, 2, 1),
    ("owner_gamma", "run_20260717_01", "run_20260703_01", "dm-stack-1.1", "dm-eval-mixed-v5", "华南混合道路", "混合道路", "晴天", "白天", "中等交通", 1.69, .914, 340, 5, 1, 1),
    ("owner_gamma", "run_20260724_01", "run_20260703_01", "dm-stack-1.2", "dm-eval-mixed-v5", "华南混合道路", "混合道路", "多云", "黄昏", "高交通", 1.77, .902, 390, 5, 1, 1),
]


def generate_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    steps = 5
    scenarios = ("primary", "risk_slice")
    for run in RUNS:
        (
            owner,
            run_id,
            baseline,
            model,
            dataset,
            region,
            road_type,
            weather,
            light,
            traffic,
            final_error,
            completion,
            distance_km,
            takeover_count,
            collision_count,
            invalid_count,
        ) = run
        positions = [(scenario, step) for scenario in scenarios for step in range(steps)]
        takeover_positions = positions[:takeover_count]
        collision_positions = [
            (scenarios[index % len(scenarios)], steps - 2 - index // len(scenarios))
            for index in range(collision_count)
        ]
        invalid_positions = set(positions[1 : 1 + invalid_count])

        for scenario_index, scenario in enumerate(scenarios):
            planned_route_m = 1000 + scenario_index * 250
            scenario_error = final_error * (.8 if scenario_index == 0 else 1.2)
            for step in range(steps):
                timestamp_ms = scenario_index * 10_000_000 + step * 900_000
                ground_truth_x = scenario_index * 1000 + step * 40
                ground_truth_y = scenario_index * 4 + step * .8
                progress = (step + 1) / steps
                lateral_error = scenario_error * progress
                position = (scenario, step)
                collision_index = (
                    collision_positions.index(position) + 1
                    if position in collision_positions
                    else None
                )
                takeover_index = (
                    takeover_positions.index(position) + 1
                    if position in takeover_positions
                    else None
                )
                rows.append(
                    {
                        "owner_id": owner,
                        "run_id": run_id,
                        "baseline_run_id": baseline,
                        "scenario_id": f"{run_id}_{scenario}",
                        "timestamp_ms": timestamp_ms,
                        "model_version": model,
                        "dataset": dataset,
                        "eval_region": region,
                        "road_type": road_type,
                        "weather": weather,
                        "light_condition": light,
                        "traffic_density": traffic,
                        "ego_x_m": f"{ground_truth_x:.3f}",
                        "ego_y_m": f"{ground_truth_y:.3f}",
                        "speed_mps": f"{(13 + scenario_index * 8 + step * .2):.3f}",
                        "acceleration_mps2": f"{(.15 - step * .05):.3f}",
                        "yaw_rate_rps": f"{(.01 * scenario_index + step * .002):.3f}",
                        "steering_angle_deg": f"{(scenario_index * 2.5 + step * .3):.3f}",
                        "predicted_x_m": f"{ground_truth_x:.3f}",
                        "predicted_y_m": f"{ground_truth_y + lateral_error:.3f}",
                        "ground_truth_x_m": f"{ground_truth_x:.3f}",
                        "ground_truth_y_m": f"{ground_truth_y:.3f}",
                        "sample_valid": 0 if position in invalid_positions else 1,
                        "timed_out": 1 if position in invalid_positions and step == 1 else 0,
                        "collision_event_id": (
                            f"{run_id}_collision_{collision_index:02d}"
                            if collision_index
                            else ""
                        ),
                        "takeover_event_id": (
                            f"{run_id}_takeover_{takeover_index:02d}"
                            if takeover_index
                            else ""
                        ),
                        "distance_delta_m": f"{distance_km * 1000 / len(positions):.3f}",
                        "planned_route_m": f"{planned_route_m:.3f}",
                        "completed_route_m": f"{planned_route_m * completion * progress:.3f}",
                    }
                )
    return rows


def main() -> None:
    output = Path(get_abs_path("data/external/records.csv"))
    rows = generate_rows()
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"已生成 {len(rows)} 条逐时刻 Mock 遥测：{output}")


if __name__ == "__main__":
    main()
