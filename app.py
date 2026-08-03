from html import escape

import streamlit as st

from agent.react_agent import ReactAgent
from agent.tools.agent_tools import (
    get_eval_record,
    list_eval_owners,
    list_runs_for_owner,
)


st.set_page_config(
    page_title="DriveMind · E2E Evaluation Lab",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --dm-ink: #14283b;
            --dm-muted: #617487;
            --dm-blue: #285f8f;
            --dm-teal: #2d817d;
            --dm-line: rgba(39, 76, 109, 0.14);
            --dm-paper: #f7fafc;
            --dm-panel: rgba(255, 255, 255, 0.84);
        }

        html, body, [class*="css"] {
            font-family: "IBM Plex Sans", "Noto Sans SC", "Microsoft YaHei UI",
                "Microsoft YaHei", sans-serif;
            color: var(--dm-ink);
        }

        .stApp {
            background-color: var(--dm-paper);
            background-image:
                linear-gradient(rgba(40, 95, 143, 0.035) 1px, transparent 1px),
                linear-gradient(90deg, rgba(40, 95, 143, 0.035) 1px, transparent 1px),
                radial-gradient(circle at 82% 7%, rgba(45, 129, 125, 0.10), transparent 28%),
                radial-gradient(circle at 20% 92%, rgba(40, 95, 143, 0.08), transparent 32%);
            background-size: 32px 32px, 32px 32px, auto, auto;
        }

        [data-testid="stHeader"] {
            background: rgba(247, 250, 252, 0.78);
            backdrop-filter: blur(14px);
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(237, 244, 248, 0.98), rgba(245, 249, 251, 0.98));
            border-right: 1px solid var(--dm-line);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: var(--dm-muted);
        }

        .block-container {
            max-width: 1260px;
            padding-top: 2.2rem;
            padding-bottom: 7rem;
        }

        .dm-sidebar-brand {
            display: flex;
            align-items: center;
            gap: .75rem;
            margin: .25rem 0 1.8rem;
        }

        .dm-mark {
            width: 2.25rem;
            height: 2.25rem;
            display: grid;
            place-items: center;
            color: white;
            background: var(--dm-ink);
            border-radius: 10px;
            box-shadow: 0 8px 20px rgba(20, 40, 59, .18);
            font-family: "Consolas", monospace;
            font-size: 1.1rem;
        }

        .dm-brand-name {
            color: var(--dm-ink);
            font-family: "Georgia", "Noto Serif SC", serif;
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: .02em;
            line-height: 1.15;
        }

        .dm-brand-sub {
            color: var(--dm-muted);
            font-family: "Consolas", monospace;
            font-size: .64rem;
            letter-spacing: .12em;
            text-transform: uppercase;
        }

        .dm-kicker {
            color: var(--dm-blue);
            font-family: "Consolas", "Microsoft YaHei UI", monospace;
            font-size: .7rem;
            font-weight: 700;
            letter-spacing: .14em;
            text-transform: uppercase;
        }

        .dm-hero {
            position: relative;
            overflow: hidden;
            min-height: 210px;
            padding: 2.25rem 2.5rem;
            border: 1px solid var(--dm-line);
            border-radius: 24px;
            background: rgba(255, 255, 255, .82);
            box-shadow: 0 22px 60px rgba(35, 64, 90, .09);
        }

        .dm-hero::after {
            content: "";
            position: absolute;
            right: -70px;
            top: -95px;
            width: 390px;
            height: 390px;
            border: 1px solid rgba(40, 95, 143, .15);
            border-radius: 46% 54% 58% 42%;
            box-shadow:
                0 0 0 34px rgba(40, 95, 143, .035),
                0 0 0 76px rgba(45, 129, 125, .025);
            transform: rotate(18deg);
            pointer-events: none;
        }

        .dm-hero h1 {
            max-width: 760px;
            margin: .65rem 0 .55rem;
            color: var(--dm-ink);
            font-family: "Georgia", "Noto Serif SC", "Songti SC", serif;
            font-size: clamp(2rem, 4vw, 3.25rem);
            font-weight: 600;
            line-height: 1.08;
            letter-spacing: -.035em;
        }

        .dm-hero-copy {
            position: relative;
            z-index: 1;
            max-width: 680px;
            color: var(--dm-muted);
            font-size: .96rem;
            line-height: 1.75;
        }

        .dm-run-line {
            position: relative;
            z-index: 1;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: .55rem;
            margin-top: 1.25rem;
            font-family: "Consolas", monospace;
            font-size: .72rem;
            color: #53697d;
        }

        .dm-chip {
            padding: .32rem .58rem;
            border: 1px solid var(--dm-line);
            border-radius: 999px;
            background: rgba(247, 250, 252, .75);
        }

        .dm-status {
            padding: .32rem .62rem;
            border-radius: 999px;
            font-weight: 700;
            letter-spacing: .06em;
        }

        .dm-status-pass { color: #176761; background: #e5f4f0; }
        .dm-status-fail { color: #9b3b43; background: #fae9ea; }
        .dm-status-warn { color: #8a601e; background: #f8efd9; }
        .dm-status-baseline { color: #405d78; background: #e9f0f6; }

        .dm-section-label {
            display: flex;
            align-items: center;
            gap: .8rem;
            margin: 1.7rem 0 .75rem;
            color: var(--dm-muted);
            font-family: "Consolas", monospace;
            font-size: .68rem;
            font-weight: 700;
            letter-spacing: .14em;
            text-transform: uppercase;
        }

        .dm-section-label::after {
            content: "";
            height: 1px;
            flex: 1;
            background: var(--dm-line);
        }

        [data-testid="stMetric"] {
            min-height: 124px;
            padding: .95rem 1rem .85rem;
            border: 1px solid var(--dm-line);
            border-radius: 16px;
            background: var(--dm-panel);
            box-shadow: 0 10px 28px rgba(35, 64, 90, .045);
            overflow: visible;
        }

        [data-testid="stMetricLabel"] {
            color: var(--dm-muted);
            font-size: .7rem;
            letter-spacing: .015em;
            line-height: 1.35;
            white-space: normal;
            overflow: visible;
        }

        [data-testid="stMetricLabel"] > div,
        [data-testid="stMetricLabel"] p {
            white-space: normal;
            overflow: visible;
            text-overflow: clip;
        }

        [data-testid="stMetricValue"] {
            margin-top: .4rem;
            color: var(--dm-ink);
            font-family: "Georgia", "Noto Serif SC", serif;
            font-size: clamp(1.25rem, 2.1vw, 1.65rem);
            line-height: 1.15;
            white-space: nowrap;
        }

        [data-testid="stMetricDelta"] {
            margin-top: .45rem;
            font-family: "Consolas", monospace;
            font-size: .7rem;
        }

        .dm-telemetry-note {
            display: flex;
            align-items: center;
            gap: .45rem;
            margin-top: .72rem;
            color: #75889a;
            font-size: .72rem;
        }

        .dm-telemetry-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--dm-teal);
            box-shadow: 0 0 0 4px rgba(45, 129, 125, .1);
        }

        .dm-evidence-strip {
            display: flex;
            flex-wrap: wrap;
            gap: .5rem;
            margin-top: .75rem;
        }

        .dm-evidence-item {
            padding: .4rem .65rem;
            border: 1px solid var(--dm-line);
            border-radius: 9px;
            color: #5c7185;
            background: rgba(255, 255, 255, .58);
            font-family: "Consolas", "Microsoft YaHei UI", monospace;
            font-size: .68rem;
        }

        .dm-empty {
            padding: 2rem 2.1rem 1.7rem;
            border: 1px dashed rgba(40, 95, 143, .24);
            border-radius: 20px;
            background:
                linear-gradient(110deg, rgba(255,255,255,.82), rgba(240,247,249,.68));
        }

        .dm-empty-title {
            margin: .45rem 0 .45rem;
            color: var(--dm-ink);
            font-family: "Georgia", "Noto Serif SC", serif;
            font-size: 1.35rem;
        }

        .dm-empty-copy {
            max-width: 720px;
            color: var(--dm-muted);
            font-size: .88rem;
            line-height: 1.7;
        }

        [data-testid="stChatMessage"] {
            margin-bottom: .8rem;
            padding: 1.1rem 1.2rem;
            border: 1px solid var(--dm-line);
            border-radius: 16px;
            background: rgba(255, 255, 255, .82);
            box-shadow: 0 8px 24px rgba(35, 64, 90, .04);
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background: rgba(232, 241, 247, .82);
        }

        [data-testid="stChatInput"] {
            border: 1px solid rgba(40, 95, 143, .22);
            border-radius: 16px;
            background: rgba(255, 255, 255, .94);
            box-shadow: 0 14px 40px rgba(35, 64, 90, .12);
        }

        .stButton > button {
            min-height: 2.6rem;
            border: 1px solid var(--dm-line);
            border-radius: 12px;
            color: var(--dm-ink);
            background: rgba(255, 255, 255, .82);
            font-weight: 600;
            transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
        }

        .stButton > button:hover {
            border-color: rgba(40, 95, 143, .44);
            color: var(--dm-blue);
            box-shadow: 0 8px 22px rgba(35, 64, 90, .08);
            transform: translateY(-1px);
        }

        .stButton > button:focus-visible,
        [data-baseweb="select"] > div:focus-within {
            outline: 2px solid rgba(40, 95, 143, .35);
            outline-offset: 2px;
        }

        [data-baseweb="select"] > div {
            border-color: var(--dm-line);
            border-radius: 10px;
            background: rgba(255,255,255,.78);
        }

        .dm-safety {
            margin-top: 1.25rem;
            padding-top: 1rem;
            border-top: 1px solid var(--dm-line);
            color: #75889a;
            font-size: .7rem;
            line-height: 1.65;
        }

        @media (max-width: 900px) {
            .block-container { padding-top: 1.2rem; }
            .dm-hero { min-height: auto; padding: 1.7rem 1.4rem; }
            .dm-hero::after { opacity: .55; }
        }

        @media (max-width: 560px) {
            .dm-hero h1 { font-size: 2rem; }
        }

        @media (prefers-reduced-motion: reduce) {
            * { scroll-behavior: auto !important; transition: none !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe(value: object) -> str:
    return escape(str(value or "—"))


def status_class(status: str) -> str:
    return {
        "PASS": "pass",
        "FAIL": "fail",
        "WARN": "warn",
        "BASELINE": "baseline",
        "INCONCLUSIVE": "warn",
    }.get(status.upper(), "baseline")


def number(record: dict[str, str], field: str) -> float | None:
    try:
        return float(record[field])
    except (KeyError, TypeError, ValueError):
        return None


def metric_value(value: float | None, unit: str, as_percent: bool = False) -> str:
    if value is None:
        return "—"
    if as_percent:
        return f"{value * 100:.1f}%"
    return f"{value:.3f} {unit}".strip()


def metric_delta(
    current: float | None,
    baseline: float | None,
    unit: str,
    as_percent: bool = False,
) -> str | None:
    if current is None or baseline is None:
        return None
    difference = current - baseline
    if as_percent:
        return f"{difference * 100:+.1f} pp"
    return f"{difference:+.3f} {unit}".strip()


inject_styles()

owners = list_eval_owners()
if not owners:
    st.error("未找到可用评测数据，请检查 data/external/records.csv。")
    st.stop()

with st.sidebar:
    st.markdown(
        """
        <div class="dm-sidebar-brand">
            <div class="dm-mark">DM</div>
            <div>
                <div class="dm-brand-name">DriveMind</div>
                <div class="dm-brand-sub">Evaluation Laboratory</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="dm-kicker">Evaluation context</div>', unsafe_allow_html=True)
    st.caption("锁定本次分析使用的数据身份与对照组。")

    owner_id = st.selectbox("评测负责人", owners, help="仅允许查询该负责人名下的跑次")
    run_ids = list_runs_for_owner(owner_id)
    run_id = st.selectbox("目标跑次", run_ids)
    baseline_options = ["不使用基线"] + [item for item in run_ids if item != run_id]
    baseline_label = st.selectbox("对照基线", baseline_options)
    baseline_run_id = "" if baseline_label == "不使用基线" else baseline_label

    if st.button("清空当前对话", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

    st.markdown(
        """
        <div class="dm-safety">
            <strong>研究用途 · Mock 原始遥测</strong><br>
            分析结果不替代道路测试、安全审查、变更评审或正式发布审批。
        </div>
        """,
        unsafe_allow_html=True,
    )

context_key = (owner_id, run_id, baseline_run_id)
if st.session_state.get("context_key") != context_key:
    st.session_state["context_key"] = context_key
    st.session_state["messages"] = []

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()
if "messages" not in st.session_state:
    st.session_state["messages"] = []

record = get_eval_record(owner_id, run_id) or {}
baseline_record = (
    get_eval_record(owner_id, baseline_run_id) or {} if baseline_run_id else {}
)
gate_status = record.get("gate_status", "UNKNOWN")

st.markdown(
    f"""
    <section class="dm-hero">
        <div class="dm-kicker">E2E Autonomous Driving · Evaluation Intelligence</div>
        <h1>把评测数据转化为<br>可复核的工程判断</h1>
        <div class="dm-hero-copy">
            面向端到端模型回归、ODD 风险切片与门禁复核的研究工作台。
            页面指标由所选跑次的逐时刻车辆与场景遥测确定性计算。
        </div>
        <div class="dm-run-line">
            <span class="dm-status dm-status-{status_class(gate_status)}">{safe(gate_status)}</span>
            <span class="dm-chip">{safe(run_id)}</span>
            <span class="dm-chip">{safe(record.get("model_version"))}</span>
            <span class="dm-chip">{safe(record.get("eval_region"))}</span>
            <span class="dm-chip">{safe(record.get("env_condition")).replace("_", " / ")}</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="dm-section-label">Run telemetry / 当前跑次遥测</div>', unsafe_allow_html=True)
metric_specs = [
    ("ADE", "ade", "m", False, "inverse", "平均位移误差，越低越好"),
    ("FDE", "fde", "m", False, "inverse", "场景末端位移误差，越低越好"),
    ("Miss Rate", "miss_rate", "", True, "inverse", "末端误差超过阈值的场景比例"),
    ("Route Completion", "route_completion", "", True, "normal", "路线完成比例，越高越好"),
]
metric_columns = st.columns(4)
for column, (label, field, unit, as_percent, delta_color, help_text) in zip(
    metric_columns, metric_specs
):
    current_value = number(record, field)
    baseline_value = number(baseline_record, field)
    with column:
        st.metric(
            label=label,
            value=metric_value(current_value, unit, as_percent),
            delta=metric_delta(current_value, baseline_value, unit, as_percent),
            delta_color=delta_color,
            help=help_text,
        )

comparison_note = (
    f"相对基线 {baseline_run_id} 显示差值；绿色表示改善，红色表示退化。"
    if baseline_run_id
    else "当前展示绝对值。若要查看改善或退化幅度，请在左侧选择对照基线。"
)
st.markdown(
    f'<div class="dm-telemetry-note"><span class="dm-telemetry-dot"></span>'
    f"{safe(comparison_note)}</div>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="dm-evidence-strip">'
    f'<span class="dm-evidence-item">SCENARIOS {safe(record.get("scenario_count"))}</span>'
    f'<span class="dm-evidence-item">RAW FRAMES {safe(record.get("raw_frame_count"))}</span>'
    f'<span class="dm-evidence-item">VALID DISTANCE {safe(record.get("valid_distance_km"))} km</span>'
    f'<span class="dm-evidence-item">MISS THRESHOLD {safe(record.get("miss_threshold_m"))} m</span>'
    f'<span class="dm-evidence-item">SOURCE {safe(record.get("source"))}</span>'
    "</div>",
    unsafe_allow_html=True,
)

with st.expander("查看闭环与数据质量指标"):
    secondary_specs = [
        ("Collision Rate", "collision_rate", "", True, "inverse", "发生碰撞的场景占比"),
        (
            "Takeover / 100 km",
            "closed_loop_takeover_per_100km",
            "",
            False,
            "inverse",
            "每百公里接管事件数",
        ),
        (
            "Collision / 100 km",
            "closed_loop_collision_per_100km",
            "",
            False,
            "inverse",
            "每百公里碰撞事件数",
        ),
        ("Invalid Sample", "invalid_sample_rate", "", True, "inverse", "无效或超时帧占比"),
    ]
    secondary_columns = st.columns(4)
    for column, (label, field, unit, as_percent, delta_color, help_text) in zip(
        secondary_columns, secondary_specs
    ):
        current_value = number(record, field)
        baseline_value = number(baseline_record, field)
        with column:
            st.metric(
                label=label,
                value=metric_value(current_value, unit, as_percent),
                delta=metric_delta(current_value, baseline_value, unit, as_percent),
                delta_color=delta_color,
                help=help_text,
            )

st.markdown('<div class="dm-section-label">Analysis dialogue / 研究对话</div>', unsafe_allow_html=True)

suggested_prompt = None
if not st.session_state["messages"]:
    st.markdown(
        """
        <div class="dm-empty">
            <div class="dm-kicker">Ready for inquiry</div>
            <div class="dm-empty-title">从一个可验证的问题开始</div>
            <div class="dm-empty-copy">
                查询指标定义、解释当前跑次，或生成九章节评测报告。
                报告中的事实只引用当前跑次及所选基线，缺失证据不会被推断。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    prompt_columns = st.columns(3)
    prompt_options = [
        ("解释核心指标", "解释 ADE、FDE、Miss Rate 的定义与适用边界"),
        ("分析当前跑次", "分析当前跑次的主要指标、场景风险与数据限制"),
        ("生成评测报告", "为当前跑次生成完整的开环评测报告"),
    ]
    for column, (label, content) in zip(prompt_columns, prompt_options):
        with column:
            if st.button(label, use_container_width=True):
                suggested_prompt = content

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

typed_prompt = st.chat_input("输入评测问题，或要求生成当前跑次报告…")
prompt = suggested_prompt or typed_prompt

if prompt:
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    chunks: list[str] = []

    def capture(stream):
        for chunk in stream:
            chunks.append(chunk)
            yield chunk

    with st.chat_message("assistant"):
        try:
            with st.spinner("正在检索证据并组织分析…"):
                response_stream = st.session_state["agent"].execute_stream(
                    prompt,
                    owner_id=owner_id,
                    run_id=run_id,
                    baseline_run_id=baseline_run_id,
                )
                st.write_stream(capture(response_stream))
            full_response = "".join(chunks).strip()
        except Exception as error:
            full_response = f"处理失败：{error}"
            st.error(full_response)

    st.session_state["messages"].append(
        {"role": "assistant", "content": full_response or "未生成有效回复。"}
    )