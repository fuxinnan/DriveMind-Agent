from pathlib import Path

import yaml

from utils.path_tools import get_abs_path


EXPECTED_SECTIONS = [
    "## 1. 评测范围与身份",
    "## 2. 数据完整性与可比性",
    "## 3. 执行摘要",
    "## 4. 开环指标分析",
    "## 5. 闭环指标补充",
    "## 6. ODD 与场景切片",
    "## 7. 失效模式与安全风险",
    "## 8. 门禁结论",
    "## 9. 建议、限制与后续动作",
]


def test_eval_cases_cover_core_behaviors():
    path = Path(get_abs_path("eval/cases.yaml"))
    cases = yaml.safe_load(path.read_text(encoding="utf-8"))["cases"]

    assert {case["type"] for case in cases} >= {"knowledge_qa", "report", "negative"}
    report_case = next(case for case in cases if case["type"] == "report")
    assert report_case["expected_tools"] == [
        "fill_context_for_report",
        "get_eval_owner_id",
        "get_run_id",
        "fetch_external_data",
    ]


def test_golden_report_has_all_sections_in_order():
    path = Path(
        get_abs_path("eval/golden_reports/owner_alpha_run_20260722_01.md")
    )
    report = path.read_text(encoding="utf-8")

    positions = [report.index(section) for section in EXPECTED_SECTIONS]
    assert positions == sorted(positions)
    assert "run_20260722_01" in report
    assert "run_20260701_01" in report
