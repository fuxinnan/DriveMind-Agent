# DriveMind E2E 评测助手 · 改造计划

---

## 1. 产品目标

把现有「扫地机智能客服」改造成 **DriveMind**：

面向 **E2E 自动驾驶大模型** 团队的评测分析 Agent。

**核心能力：**

1. 评测知识问答（指标、开环/闭环、场景、失效模式、门禁）
2. 按跑次查询 Mock 评测数据
3. 自动生成 **开环为主** 的评测报告（闭环指标附带）
4. 给出复测/行动建议（不编造无数据结论）

**不做：** 控车、训模型、替代仿真器；MVP 不做 Top Failures。

---

## 2. 已定决策

| 项 | 结论 |
|----|------|
| 数据主键 | `run_id`，格式 `run_YYYYMMDD_xx` |
| 报告形态 | 开环为主，闭环附带 |
| 用户身份 | 侧边栏选择 `owner_id` + `run_id`（禁止随机） |
| 门禁 | 示例阈值（可写进知识库） |
| 知识文风 | FAQ 通俗 + 指标/门禁文档严谨 |
| 原天气/位置工具 | 改为「评测域」「评测环境条件」 |
| 品牌 | 仅 DriveMind |

---

## 3. 总体策略

```
基础设施（少动）          领域层（大改）
─────────────────        ─────────────────
create_agent             prompts 三份重写
middleware 动态提示词     data 知识库全换
Chroma RAG 管线          records.csv 按 run_id
Streamlit 会话/流式      工具语义 + 侧边栏
model factory            UI 文案
```

原则：**复用 Agent 骨架，替换领域内容与入参模型（月份 → run_id）。**

---

## 4. 代码改造框架



### 4.2 各文件改什么

| 文件 | 改动要点 |
|------|----------|
| `app.py` | 标题改 DriveMind；侧边栏选 owner/run/baseline；context 传给 agent；免责声明 |
| `main_prompt.txt` | 角色改为评测助手；工具说明改为 run_id；报告流程约束；开环主报告 |
| `report_prompt.txt` | 按开环报告章节重写（见 §7） |
| `rag_summarize.txt` | 保留「只基于资料」；补安全/不编造 |
| `agent_tools.py` | 工具重命名/改语义；CSV 按 run_id 解析；读 context 不随机 |
| `middleware.py` | 保留 `fill_context_for_report` → 切报告提示词 |
| `react_agent.py` | 更新 tools 导入；`context` 含 report + owner_id + run_id |
| `records.csv` | 全新 Mock 数据 |
| `data/knowledge/*` | 新知识文件；删除旧扫地机文档 |
| `chroma.yml` | 适当增大 chunk_size / k；collection 可改 `drivemind_eval` |
| `vector_store.py` | 修复 Document import；入库前清旧库；不扫 external |

---

## 5. 工具映射

| 旧工具 | 新工具 | 行为 |
|--------|--------|------|
| `get_user_id` | `get_eval_owner_id` | 返回侧边栏 owner_id |
| `get_current_month` | `get_run_id` | 返回侧边栏 run_id |
| `fetch_external_data(user, month)` | `fetch_external_data(owner_id, run_id)` | 读 CSV 汇总 |
| `get_user_location` | `get_eval_region` | 返回评测地图/域 |
| `get_weather(city)` | `get_env_condition(region)` | 返回光照/气象等评测环境 |
| `rag_summarize` | 同名 | 检索评测知识 |
| `fill_context_for_report` | 同名 | 触发报告提示词 |

**报告调用顺序（保持）：**

`fill_context_for_report` → `get_eval_owner_id` / `get_run_id` → `fetch_external_data` → 生成报告

---

## 6. 数据与知识（框架级）

### 6.1 `records.csv` 语义（可用 6 列兼容）

| 列（可暂用旧表头） | 含义 | 示例 |
|--------------------|------|------|
| 用户ID | owner_id | `1001` |
| 特征 | 跑次画像 | `e2e-v0.3.2 \| 开环主评 \| val集` |
| 清洁效率 | 指标（开环主） | `ADE:1.21\nFDE:2.05\n…\n闭环接管:3.2` |
| 耗材 | 健康/环境 | `评测域:CityHD\n超时:12` |
| 对比 | 相对基线 | `较 run_xxx：ADE↓8%` |
| 时间 | **run_id** | `run_20250618_01` |

建议：每 owner 准备 8～12 条不同 run，供侧边栏下拉。

### 6.2 知识库文件（建议）

```
data/knowledge/
  01_metrics_dictionary.txt       # 指标（严谨，开环加厚）
  02_openloop_vs_closedloop.txt   # 开环/闭环关系
  03_scenario_odd_slices.txt      # 场景切片
  04_e2e_failure_modes.txt        # 失效模式
  05_gate_and_release_policy.txt  # 示例门禁
  06_eval_toolchain_fields.txt    # 字段/run_id 约定
  07_safety_and_disclaimer.txt    # 安全边界
  08_faq_engineer_onboarding.txt  # 新人 FAQ（通俗）
```

入库前：删旧扫地机文件；清空 `chroma_db/` 与 `md5.text`；再 `load_document`。


## 7. 开环报告骨架

```markdown
# DriveMind E2E 开环评测报告
1. 跑次概览（run_id / 版本 / 负责人 / 评测域）
2. 开环门禁结论（主）
3. 开环核心指标解读
4. 闭环附带观察
5. 场景/风险摘要（若有）
6. 跑次健康与评测环境
7. 可能原因（标为假设）
8. 行动项
9. 免责声明（仅 DriveMind）
```

---

## 8. UI 框架

```
主聊天区
侧边栏
  ├─ 负责人 owner_id（必选）
  ├─ 跑次 run_id（必选）
  ├─ 基线 baseline_run_id（可选）
  └─ 免责声明
```

文案：标题 `DriveMind`；副标题「E2E 评测与闭环分析助手」；去掉智扫通等旧文案。

开工回复：「开始实施 MVP」。
