# DriveMind E2E Eval Agent

本项目基于 LangChain 架构重构开发，聚焦智能驾驶垂直领域，面向车企智驾研发与评测团队打造专属的评测智能 Agent。依托检索增强生成（RAG）与智能代理自主交互能力，实现评测指标答疑、开闭环结果解读、场景与 ODD 风险梳理、失效模式分析、示例门禁与复测策略咨询等全链路智能化服务，替代传统通用问答与人工翻表流程，提升智能驾驶评测场景下的专业交互体验与分析效率。

## 核心能力

### 评测知识问答

DriveMind 可以通过本地 RAG 知识库回答下列领域问题：

- ADE、FDE、Miss Rate、Collision Rate 等开环指标的定义与适用边界；
- 开环评测与闭环评测的差异、联系及联合解读原则；
- ODD、道路类型、天气、光照、交通密度和行为场景切片；
- 端到端模型常见失效模式及证据要求；
- 示例门禁、数据质量检查和回归复测策略；
- 跑次字段、工具调用约定与报告安全边界。

知识回答严格依据检索资料。资料缺失或相互冲突时，助手应明确说明无法判定，不使用模型常识补造项目事实或指标阈值。

### 跑次查询与对比

用户可在 Streamlit 侧边栏中选择：

- `owner_id`：评测负责人；
- `run_id`：目标评测跑次；
- `baseline_run_id`：可选基线跑次。

选择结果会作为当前请求的 runtime context 注入 Agent。工具只能读取当前上下文中的负责人和跑次，不会随机选择身份，也不会跨负责人查询数据。

### 科研评测工作台

Streamlit 首页直接展示当前跑次的计算摘要：

- 核心指标：ADE、FDE、Miss Rate、Route Completion；
- 闭环与质量指标：Collision Rate、每百公里接管、每百公里碰撞、Invalid Sample；
- 证据口径：场景数、原始帧数、有效里程、Miss 阈值和指标来源；
- 选择 baseline 后显示目标跑次相对基线的差值，误差与事件类指标下降显示为改善，Route Completion 上升显示为改善；
- 指标名称保持短标签以避免小屏截断，完整定义可通过标签旁的提示查看。

### 自动生成评测报告

报告以开环分析为主，闭环结果作为补充证据，固定包含以下九个章节：

1. 评测范围与身份；
2. 数据完整性与可比性；
3. 执行摘要；
4. 开环指标分析；
5. 闭环指标补充；
6. ODD 与场景切片；
7. 失效模式与安全风险；
8. 门禁结论；
9. 建议、限制与后续动作。

报告场景采用固定工具链：

```text
fill_context_for_report
→ get_eval_owner_id
→ get_run_id
→ fetch_external_data
```

如需补充指标定义或门禁说明，Agent 只能在上述链路完成后调用 `rag_summarize`。报告不得估算缺失值；未经数据或实验支持的原因必须标记为“假设”，并说明后续验证所需证据。

## 技术架构

项目保留轻量、可替换的分层结构：

- 表现层：Streamlit 提供聊天界面、跑次选择和流式响应；
- Agent 层：LangChain `create_agent` 负责模型调用、工具编排和 ReAct 执行；
- Middleware 层：记录工具调用，并根据报告上下文动态切换系统提示词；
- Tool 层：读取 runtime context、查询 CSV 跑次数据并调用 RAG；
- RAG 层：Chroma 完成知识向量存储和检索，摘要链仅基于召回资料生成回答；
- Model 层：通过 OpenAI 兼容接口调用聊天模型，通过 DashScope 调用嵌入模型；
- Evaluation 层：校验逐时刻车辆/场景遥测，并确定性计算跑次指标；
- Data 层：分别维护结构化 Mock 原始遥测和领域知识源。

主要数据流如下：

```text
Streamlit 侧边栏
    → owner_id / run_id / baseline_run_id
    → records.csv 原始车辆与场景遥测
    → 字段校验 / 场景聚合 / 跑次指标计算
    → Agent runtime context
    → 评测工具或知识检索
    → 动态提示词
    → 流式回答或九节评测报告
```

## 项目结构

```text
DriveMind-Agent/
├─ app.py                         # Streamlit 应用入口
├─ agent/
│  ├─ context.py                 # 请求级 AgentContext
│  ├─ react_agent.py             # Agent 组装与流式执行
│  └─ tools/
│     ├─ agent_tools.py          # 跑次、环境与 RAG 工具
│     └─ middleware.py           # 日志与动态报告提示词
├─ config/
│  ├─ agent.yml                  # 外部数据路径
│  ├─ chroma.yml                 # 向量库与分片配置
│  ├─ metrics.yml                # 原始遥测字段与指标口径
│  ├─ prompts.yml                # 提示词路径
│  └─ rag.yml                    # 模型名称与服务地址
├─ data/
│  ├─ external/records.csv       # 逐时刻 Mock 车辆与场景遥测
│  └─ knowledge/                 # DriveMind 领域知识
├─ evaluation/metrics.py         # 场景级与跑次级指标计算
├─ eval/
│  ├─ cases.yaml                 # 行为验收样例
│  └─ golden_reports/            # 参考报告
├─ model/factory.py              # 聊天与嵌入模型工厂
├─ prompts/                      # 主提示词、报告提示词和 RAG 提示词
├─ rag/                          # Chroma 入库、检索与摘要链
├─ scripts/
│  ├─ generate_mock_telemetry.py # 重建本地 Mock 原始遥测
│  └─ rebuild_kb.py              # 知识源校验与向量库重建
├─ tests/                        # 确定性自动化测试
├─ utils/                        # 配置、路径、日志与文件工具
├─ .env.example                  # 环境变量模板
└─ requirements.txt              # Python 依赖
```

## 环境要求

- Python 3.10 或更高版本；
- 可访问配置中模型服务地址的网络环境；
- 有效的 DashScope 或兼容服务 API Key；
- Windows PowerShell、Linux 或 macOS 终端。

为避免与系统环境中的 NumPy、SciPy、PyTorch 等依赖发生冲突，建议始终使用独立虚拟环境。

## 安装

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux 或 macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 环境变量与密钥管理

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

Linux 或 macOS 可执行：

```bash
cp .env.example .env
```

在 `.env` 中填写密钥：

```dotenv
DASHSCOPE_API_KEY=replace_with_your_key
```

程序优先读取 `DASHSCOPE_API_KEY`；未设置时兼容读取 `OPENAI_API_KEY`。两者均不存在时，模型工厂会在启动阶段返回明确错误。

安全要求：

- 不要把 `.env`、API Key 或访问令牌提交到版本库；
- `.env.example` 只能保留变量名称和占位值；
- 已经出现在代码、日志或聊天记录中的密钥应立即撤销并轮换；
- 生产环境应使用组织统一的密钥管理服务，而不是本地明文文件。

## 原始车辆与场景数据

输入位于 `data/external/records.csv`。该文件不再直接填写 ADE、FDE 等结果；每行表示一个场景采样时刻，主要包含：

- 身份：`owner_id`、`run_id`、`baseline_run_id`、`scenario_id`、`timestamp_ms`；
- 版本：`model_version`、`dataset`、`eval_region`；
- 环境：`road_type`、`weather`、`light_condition`、`traffic_density`；
- 车辆：位置、速度、加速度、横摆角速度和转向角；
- 轨迹：预测位置 `predicted_x_m/predicted_y_m` 与真实位置 `ground_truth_x_m/ground_truth_y_m`；
- 事件：有效性、超时、碰撞事件 ID、接管事件 ID；
- 里程：增量里程、计划路线长度和完成路线长度。

应用按跑次实时聚合：ADE 使用所有有效轨迹点，FDE 使用各场景末端有效点；Miss Rate 的默认阈值为 2.0 m；碰撞和接管按事件 ID 去重后再按场景或有效里程归一化。完整字段和口径见 `config/metrics.yml` 与 `data/knowledge/06_字段约定.md`。

聚合结果会附带 `source=computed_from_raw_telemetry`、原始帧数、场景数、有效轨迹点和有效里程。当前 MVP 不根据这些指标自动作正式门禁判断，`gate_status` 固定为 `INCONCLUSIVE`，不等同于 PASS 或 FAIL。

`run_id` 必须符合 `run_YYYYMMDD_xx` 格式，baseline 必须属于同一 owner。真实数据需保持 UTF-8 和现有表头；更新后重启 Streamlit 以清除缓存。要恢复仓库自带示例数据，可执行：

```powershell
python -m scripts.generate_mock_telemetry
```

## 知识库维护与重建

知识源位于 `data/knowledge/`。当前知识范围包括：

1. 指标字典；
2. 开环与闭环关系；
3. 场景和 ODD 切片；
4. E2E 失效模式；
5. 示例门禁与发布策略；
6. 评测字段和工具约定；
7. 安全边界与免责声明；
8. 工程师 FAQ。

修改知识文件后，先执行离线检查：

```powershell
python -m scripts.rebuild_kb --check
```

该命令只检查知识目录、允许的文件类型、UTF-8 编码和空文件，不调用外部模型。

检查通过后执行正式重建：

```powershell
python -m scripts.rebuild_kb
```

正式重建会：

1. 校验知识源；
2. 删除旧 Chroma 持久化目录和 MD5 状态；
3. 使用嵌入模型处理知识分片；
4. 写入 `drivemind_eval` collection；
5. 在任一文件入库失败时返回非成功结果。

正式重建需要有效 API Key 和网络连接。不要在应用运行并占用 Chroma 文件时同时重建知识库；建议停止 Streamlit，完成重建后再启动。

## 启动应用

确认已配置环境变量并完成知识库重建：

```powershell
streamlit run app.py
```

启动后终端会显示本地访问地址，默认通常为：

```text
http://localhost:8501
```

推荐的人工验收流程：

1. 在侧边栏选择负责人、目标跑次和可选基线；
2. 询问“ADE 是什么”以验证知识检索；
3. 输入“为当前跑次生成开环评测报告”；
4. 检查报告是否包含九个固定章节；
5. 核对报告中的版本、run_id、样本规模和计算指标是否与原始 CSV 一致；
6. 切换负责人或跑次，确认会话上下文随之重置。

## 测试与质量检查

运行全部自动化测试：

```powershell
python -m pytest -q
```

测试范围包括：

- 原始遥测字段、数值范围、跑次格式和 baseline 引用完整性；
- ADE/FDE/Miss Rate、事件去重、每百公里归一化和无效样本计算；
- owner/run context 的确定性读取；
- 非当前上下文数据的拒绝查询；
- 可选基线加载；
- 主提示词与报告提示词切换；
- Chroma 知识目录边界；
- 旧领域词残留检查；
- 行为评测资产和 Golden Report 九节顺序。

执行 Python 编译检查：

```powershell
python -m compileall -q agent evaluation model rag utils scripts tests app.py
```

行为验收样例位于 `eval/cases.yaml`，包括知识问答、正常报告、缺失数据拒答和门禁边界问题。`eval/golden_reports/` 提供人工核对用参考报告。它们用于行为回归，不替代确定性单元测试，也不表示模型措辞必须逐字一致。

## 日志与问题排查

运行日志写入 `logs/agent_YYYYMMDD.log`，包含模型调用前状态、工具名称、工具参数和异常信息。日志用于排查工具顺序、数据命中和运行错误，不应写入 API Key 或敏感生产数据。

常见问题：

### 启动时提示缺少 API Key

确认项目根目录存在 `.env`，变量名为 `DASHSCOPE_API_KEY` 或 `OPENAI_API_KEY`，并重新启动终端或 Streamlit。

### 知识问答没有召回内容

确认已经执行正式的 `python -m scripts.rebuild_kb`，并检查 `config/chroma.yml` 中的 `data_path` 和 `collection_name`。

### 重建知识库失败

先运行 `python -m scripts.rebuild_kb --check`。如本地校验通过，再检查 API Key、网络、模型名称和服务地址。正式重建失败时不会把失败文件标记为已成功处理。

Windows 下如果出现 `WinError 32`，说明 Streamlit 或其他 Python 进程仍占用 `chroma_db`，应完全停止应用后重试。如果出现 `SSL: UNEXPECTED_EOF_WHILE_READING`，表示到 DashScope 的 HTTPS 连接中途断开；不要使用本次不完整向量库，待网络稳定后重新执行完整重建：

```powershell
python -m scripts.rebuild_kb
```

### 侧边栏没有 owner 或 run

检查 `data/external/records.csv` 是否存在、是否使用 UTF-8 编码，以及是否包含 `config/metrics.yml` 中声明的全部原始遥测字段。

### 报告未使用选中的跑次

工具层会拒绝与当前 runtime context 不一致的 owner/run 请求。可检查日志中的 `get_eval_owner_id`、`get_run_id` 和 `fetch_external_data` 调用参数。

## 安全边界与非目标

DriveMind 当前明确不提供以下能力：

- 不控制车辆或向车辆下发指令；
- 不训练、微调或发布自动驾驶模型；
- 不替代仿真器、数据平台或真实评测系统；
- 不生成缺失跑次、虚构指标或伪造事故结论；
- 不将示例门禁解释为法规、行业标准或量产准入条件；
- 不替代道路测试、安全审查、变更评审和正式发布审批；
- 当前 MVP 不提供 Top Failures 自动聚合。

所有报告仅基于本地 Mock 原始遥测的计算结果、当前知识库和模型生成结果。安全关键结论必须由具备授权和领域责任的人员结合完整证据复核。

## 后续扩展方向

在保持现有安全边界的前提下，可进一步扩展：

- 接入真实评测平台 API 和权限系统；
- 使用结构化响应模型生成可机器解析的报告；
- 增加场景级失败案例索引和 Top Failures；
- 引入更严格的离线 Agent 行为评测与 CI 门禁；
- 增加指标趋势图、版本对比和报告导出；
- 对接组织内部的 ODD、门禁和发布策略知识库。
