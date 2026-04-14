---
name: write-anything
description: |
  内容创作全流程助手，支持今日头条、小红书、Twitter。
  选题 → 框架 → 内容增强 → 写作 → SEO → 视觉AI → 排版输出。
  也支持将内容转化为杂志质感信息卡片（HTML→图片）。
  触发关键词：头条、头条号、今日头条、头条文章、
  小红书、小红书笔记、种草、
  Twitter、X、推特、推文、tweet、发推、
  封面图、配图、写一篇、
  信息卡、信息卡片、做张卡片、做成卡片、make info card。
  也覆盖：个人写作风格管理、文章数据复盘、风格设置。
  不应被通用的"写文章"、blog、邮件、PPT、抖音/短视频、网站 SEO 触发——
  需要有平台明确上下文。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebSearch
  - WebFetch
---

# write-anything — 内容创作全流程

## 行为声明

**角色**：用户的内容编辑 Agent（支持今日头条、小红书、Twitter）。

**模式**：
- **默认全自动**——一口气跑完 Step 1-8，不中途停下。只在出错时停。
- **交互模式**——用户说"交互模式"/"我要自己选"时，在选题/框架/配图处暂停。

**降级原则**：每一步都有降级方案。Step 1 检测到的降级标记（`skip_image_gen`）在后续 Step 自动生效，不重复报错。

**进度追踪**：主管道启动时，用 TaskCreate 为 7 个 Step 创建任务。每开始一个 Step 标记 in_progress，完成后标记 completed。用户可随时看到当前进度。

**完成协议**：
- **DONE** — 全流程完成（含降级完成的情况，降级项在 7.2 回复中列出）
- **BLOCKED** — 关键步骤无法继续且用户无法提供所需信息

**路径约定**：本文档中 `{skill_dir}` 指本 SKILL.md 所在的目录（即 write-anything 的根目录）。

**Onboard 例外**：Onboard 是交互式的（需要问用户问题），不受"全自动"约束。Onboard 完成后回到全自动管道。

**辅助功能**（按需加载，不在主管道内）：
- 用户说"重新设置风格" → `读取: {skill_dir}/references/onboard.md`
- 用户说"调整我的风格"/"更新风格" → 根据用户反馈，读取并更新 `{skill_dir}/my-style/` 下对应平台的风格文件（xiaohongshu.md / toutiao.md / twitter.md）。可以新增规则、修改规则、添加范例片段。
- 用户说"看看文章数据" → `读取: {skill_dir}/references/performance-review.md`
- 用户说"检查一下"/"自检"/"这篇文章怎么样" → 对最近一篇生成的文章（或用户指定的文章）执行质量检查：
  1. 读取：
     - `{skill_dir}/references/writing-guide.md`
     - `{skill_dir}/references/writing-evaluation-phrases.md`
     - `{skill_dir}/references/writing-evaluation-structures.md`
     - `{skill_dir}/references/writing-evaluation-examples.md`
  2. Agent 按规则做自然语言评审，重点检查：
     - 是否有明显套话、空话、讲解腔、总结腔
     - 是否有二元反转、连环否定、设问自答、抽象主语、段尾金句化等结构模板
     - 是否缺少真实锚点、具体细节、节奏变化和个人判断
  3. 输出可操作建议，格式：
     - 每条建议定位到具体段落或句子（"第 3 段第 2 句用了‘不是 X，而是 Y’模板"）
     - 给出具体改法（"直接写结论，不要先搭反转"、"把‘这说明了’删掉，换成具体判断"）
     - 按影响度排序，最多 5 条
  4. 如果整体没明显问题 → "这篇文章整体已经比较自然，优先在编辑锚点处补你的真实经验或判断就可以发。"

  **输出格式**：自然语言报告，不输出 JSON 或分数（用户不需要看数字）
- 用户说"更新"/"更新 write-anything"/"升级" → 在 `{skill_dir}` 执行 `git pull origin main`，完成后告知版本变化
- 用户说"今天计划..."/"每日计划"/"设置计划" → 设置当天各平台发文目标：
  ```bash
  python3 {skill_dir}/scripts/daily.py plan {平台:数量} ...
  # 示例: python3 {skill_dir}/scripts/daily.py plan 小红书:3 头条:2 推特:2
  ```
- 用户说"今日进度"/"看看进度"/"今天状态"/"矩阵状态" → 查看当天文章矩阵状态：
  ```bash
  python3 {skill_dir}/scripts/daily.py --json
  ```
  Agent 解读 JSON 后以自然语言报告：各平台完成进度、每篇文章当前状态、待办建议。
- 用户说"添加选题" → 手动添加一条选题到当天追踪：
  ```bash
  python3 {skill_dir}/scripts/daily.py add {platform} "{topic}"
  ```
- 用户说"生成信息卡"/"做张信息卡"/"信息卡片"/"做成卡片" → `读取: {skill_dir}/references/info-card-design-spec.md`，执行信息卡工作流（见下方独立章节）。
  - 输入来源：用户提供的文本/URL，或刚写完的文章（自动取 `output/` 最新文件）
  - 输出：HTML 源文件 + PNG 截图，保存在 `{skill_dir}/output/info-cards/{YYYYMMDD}-{来源}-{关键词}/`

---

## 主管道（Step 1-7）

主管道启动时，创建以下 7 个任务用于进度追踪：

```
TaskCreate: "Step 1: 环境 + 配置"
TaskCreate: "Step 2: 框架 + 素材"
TaskCreate: "Step 3: 写作"
TaskCreate: "Step 4: SEO + 验证"
TaskCreate: "Step 5: 视觉 AI"
TaskCreate: "Step 6: 排版 + 输出"
TaskCreate: "Step 7: 收尾"
```

每开始一个 Step → TaskUpdate status=in_progress。完成 → TaskUpdate status=completed。

---

### Step 1: 环境 + 配置

**1.1 环境检查**（静默通过或引导修复）：

```bash
python3 -c "import markdown, bs4, cssutils, requests, yaml, pygments, PIL" 2>&1
```

| 检查项 | 通过 | 不通过 |
|--------|------|--------|
| `config.yaml` 存在 | 静默 | 引导创建 |
| Python 依赖 | 静默 | 提供 `pip install -r requirements.txt` |
| 图片 API Key 环境变量已配置 | 静默 | 设 `skip_image_gen = true` |
| `my-style/{平台}.md` | 静默 | 提示："个人风格文件为空。你可以说**'调整我的风格'**添加写作偏好和范例，写出来的文章会更像你。没有也不影响使用。" |

**1.2 加载配置 + 平台参数**：

```
检查: {skill_dir}/config.yaml
```

- 存在 → 继续
- 不存在 → `读取: {skill_dir}/references/onboard.md`，完成后回到 Step 1

```
解析 platform：
- 提到「头条 / 今日头条 / 头条号 / 头条文章」→ `toutiao`
- 提到「小红书 / 小红书笔记 / 种草」→ `xiaohongshu`
- 提到「Twitter / X / 推特 / 推文 / 发推 / tweet」→ `twitter`

本次请求明确提到平台 → 该平台优先
未提到 → 回退到 config.yaml 的 default_platform
都没有 → 默认 toutiao

从 config.yaml 加载：
- 全局配置：industry、blacklist
- 当前平台配置：config.yaml → platforms.{platform}（name、topics、tone、voice、cover_style 等）

读取: {skill_dir}/references/platform-profiles.yaml
加载 platform_profile = platform-profiles.yaml[platform]

读取: {skill_dir}/references/platform-writing-rules.md
记住当前 platform 对应的写作规则，后续 Step 2-6 中使用
```

`default_platform` 是**默认平台偏好**，不是硬绑定。本次自然语言请求优先级更高。

用户必须提供明确选题。

---

### Step 2: 框架 + 素材

**2.1 框架选择**：

```
读取: {skill_dir}/references/frameworks.md
```

7 套框架（痛点/故事/清单/对比/热点解读/纯观点/复盘），自动选推荐指数最高的。框架选择时参考 `platform-writing-rules.md` 中当前平台的框架限制（如小红书不推荐纯观点型和复盘型）。

**2.2 素材采集 + 内容增强**（合并执行，共用搜索结果）：

```
读取: {skill_dir}/references/content-enhance.md
```

根据 2.1 选定的框架类型，一次搜索同时完成素材采集和内容增强。搜索时使用 `platform-writing-rules.md` 中当前平台的推荐搜索源替换 site 限定词：

| 框架 | 搜索策略 | 从结果中提取 |
|------|---------|-------------|
| 热点解读 / 纯观点 | `"{关键词} site:{平台推荐源}"` + `"{关键词} 观点 OR 评论"` | 真实素材（数据/引述）**+** 已有文章的主流观点（供角度发现） |
| 痛点 / 清单 | `"{关键词} 教程 OR 工具 OR 实操"` + `"{关键词} 数据 报告"` | 真实素材 **+** 具体工具名/步骤/参数（供密度强化） |
| 故事 / 复盘 | `"{人物/事件} 采访 OR 专访 OR 细节"` + `"{关键词} 数据 报告"` | 真实素材 **+** 时间锚/数字锚/对话锚/感官锚（供细节锚定） |
| 对比 | `"{方案A} vs {方案B} 评测 OR 体验"` + `"{方案A OR 方案B} 踩坑 OR 缺点 site:{平台补充源}"` | 真实素材 **+** 真实用户评价和踩坑信息（供真实体感） |

每次搜索 2 轮，从结果中**同时**提取：
1. **素材**：5-8 条真实素材（具名来源 + 具体数据/引述/案例）。**禁止编造**。
2. **增强材料**：按 content-enhance.md 对应策略的要求提取（角度/密度要点/细节/用户声音）。

两者并入框架大纲，一起传入 Step 2.3。

**降级**：WebSearch 不可用 → 用 LLM 训练数据中可验证的公开信息。但需告知用户："素材采集未能使用 WebSearch，建议在编辑锚点处多加入你自己的内容。"密度强化不依赖搜索，始终执行。

**2.3 大纲生成与确认**（仅写文章类任务，如头条 / 小红书长文）：

基于 2.1 框架和 2.2 素材，生成**结构化大纲 + 简短摘要**，包含：
- **摘要**：1-2 句话概括文章核心观点和目标读者收益
- **大纲**：各章节标题 + 每节要点（含将嵌入的素材/增强材料标注）

生成后**必须询问用户**：
> 以下是大纲和摘要，请确认是否 OK，或告诉我需要调整的部分：
>
> {大纲 + 摘要}

- 用户要求修改 → 按反馈调整大纲，再次确认，直到用户明确同意
- 用户确认 OK → 进入 Step 3 写作

> **跳过条件**：Twitter 等短文本平台不执行此步，直接进入 Step 3。

---

### Step 3: 写作

```
读取: {skill_dir}/references/writing-guide.md
读取: {skill_dir}/my-style/{当前平台}.md（如果存在，加载风格规则和范例）
```

**3.1 个人风格注入**（有 `my-style/{当前平台}.md` 且非空时执行）：

读取当前平台对应的风格文件，将其中的**风格规则**作为写作约束，**范例片段**作为风格参考注入写作 prompt。

> 以下是用户的个人写作偏好和范例，严格遵循风格规则，模仿范例片段的句长节奏、情绪强度和口语化程度：
>
> {my-style 文件内容}

**Fallback（风格文件为空或不存在时）**：仅依据 writing-guide.md 写作，不注入额外风格。

**3.2 写文章**：
- **头条 / 小红书**：按 Step 2.3 确认的大纲逐节展开。展开时**优先通过 WebSearch 搜索每节要点对应的素材和内容**进行填充，确保信息密度和准确性。H1 标题（≤ `platform_profile.title_max_chars` 字） + 正文结构（按 `platform-writing-rules.md` 当前平台规则执行），字数 `platform_profile.word_count_min` - `platform_profile.word_count_max`
- **Twitter**：不写 H1，直接输出单条短推正文。要求：总长度 `platform_profile.word_count_min` - `platform_profile.word_count_max` 字；3-6 句短句/短行；只保留 1 个核心观点、1 个核心画面或 1 个核心吐槽；默认不拆线程
- **素材 + 增强约束**：头条 / 小红书把 Step 2.2 的素材和增强材料分散嵌入各段落；Twitter 至少包含 1 个真实锚点（具体产品名、功能名、数字或事件），增强策略的核心输出必须在单条短推里可感知，不能只剩空情绪
- **收尾方式**：根据文章内容和情绪弧线自行判断最自然的收尾方式
- **写作规范**：writing-guide.md 中的基础规则（禁用词、句长方差、词汇混用等）在初稿阶段生效
- **头条 / 小红书**：保留 2-3 个编辑锚点：`<!-- ✏️ 编辑建议：在这里加一句你自己的经历/看法 -->`
- **头条 / 小红书 图片占位符**：当正文提及具体产品界面、操作步骤、数据图表、对比截图等**真实图片比 AI 生图更有说服力**的内容时，在对应位置插入占位符：`<!-- 📷 插图：{具体描述，如"ChatGPT 设置页 Memory 开关截图"} -->`。占位符应说明需要什么图、截取哪个画面，让编辑不用猜。每篇不超过 3 个
- **Twitter**：不在正文中插入 HTML 注释或编辑锚点，避免影响自动发布
- 可选容器语法（仅长文平台）：`:::dialogue`、`:::timeline`、`:::callout`、`:::quote`

保存到 `{skill_dir}/output/{date}-{slug}.md`

**3.3 整体审核**（仅写文章类任务，如头条 / 小红书长文）：

填充完成后对全文做一遍整体审核：
- 检查各节是否覆盖大纲所有要点
- 检查素材/数据引用的准确性和一致性
- 检查段落衔接和逻辑连贯性
- 检查字数是否在平台要求范围内

审核通过后进入 Step 4 SEO 流程。

---

### Step 4: SEO + 验证

```
读取: {skill_dir}/references/seo-rules-{platform}.md
```

**4.0 关键词扩展**（头条 / 小红书执行，Twitter 跳过）：

```
读取: {skill_dir}/references/seo-keyword-analysis.md
```

用 WebSearch 快速搜索本文主题关键词（1-2 轮），从结果中提取：
- 3-5 个核心关键词（同义词 / 近义词）
- 2-3 个长尾关键词（具体场景词，优先用于话题标签和标题）
- 热点关联词（如有）

输出「关键词扩展」简表，供 4.1 标签生成和标题优化直接使用。**WebSearch 不可用时**跳过，依靠 LLM 已有知识判断。

**4.1 SEO / 发布优化**：
- **头条**：按"平台可发现性优化"处理。结合 4.0 扩展词，生成 3 个备选标题（≤ `platform_profile.title_max_chars` 字）+ 摘要 + `platform_profile.tags_count` 个标签；核心关键词优先放在**标题 + 前 3 段 + 合适的小标题**，全文自然覆盖，避免机械堆砌
- **小红书**：按"站内搜索可发现性优化"处理。结合 4.0 扩展词，生成 3 个备选标题（≤ `platform_profile.title_max_chars` 字）+ 话题标签列表 + 前 2 行摘要感优化；核心关键词优先放在**标题 + 前 2 行 + 话题标签**，表达口语化、自然、不硬塞
- **Twitter**：按"可发现性 / 传播优化"处理。Twitter 无传统搜索 SEO，跳过关键词扩展；生成 3 个备选推文版本（都满足长度限制）+ 选 1 个最终发布版 + 0-2 个 hashtags；核心词尽量出现在前 2 行，但优先保证可读性、观点强度和转发性

**4.2 质量验证**（两个维度，每项逐一检查）：

**A. 写作质量**（writing-guide.md 基础规则）：

| 检查项 | 标准 | 规则 |
|--------|------|------|
| 句长方差 | 最短与最长句相差 ≥ 30 字 | 1.1 |
| 词汇温度 | 任意 500 字 ≥ 3 种温度 | 1.2 |
| 段落节奏 | 无连续 2 个相近长度段落 | 1.3 |
| 情绪极性 | 负面情绪 ≥ 2 处，无平铺直叙 | 1.4 |
| 禁用词 | 命中数 = 0 | 2.1 |
| 真实锚定 | 长文每个段落组 ≥ 1 条真实素材；Twitter 至少 1 条真实锚点，零编造 | 3.1 |
| 具体性 | 长文每 500 字 ≥ 2 处具体细节；Twitter 至少 1 处具体细节 | 3.2 |

**B. 内容质量**（基于 Step 2.2 的增强策略检查，按框架类型选检）：

| 检查项 | 标准 | 适用框架 |
|--------|------|---------|
| 增强贯穿 | 增强策略的核心输出（角度/密度/细节/体感）在全文可见，不只出现在一段 | 所有 |
| 开头钩子 | 前 3 句能制造悬念、冲突或好奇心（不是背景铺垫） | 所有 |
| 金句密度 | 至少 1 处可独立截图转发的句子 | 所有 |
| 操作密度 | 长文每个 H2 有可操作要点；Twitter 正文至少 1 个可操作点或明确判断 | 仅 痛点/清单 |
| 角度锐度 | 核心观点能引发同意或反对，不是"两面都有道理" | 仅 热点解读/纯观点 |
| 场景感 | 长文至少 2 处有时间/地点/对话等画面细节；Twitter 至少 1 处 | 仅 故事/复盘 |
| 真实声音 | 至少 1 处引用真实用户评价或体验 | 仅 对比 |

> 每篇文章只检查"所有"标记的 3 项 + 当前框架对应的 1 项（如有），不全查。

不通过 → **定向修复**：只替换不达标的具体句子/段落，不动已通过的部分。每轮最多改 3 处，改完立即重新检查该项。2 轮仍不过 → 标注跳过，继续下一项。

**4.3 规则评审辅助验证**（补充 4.2 的逐项检查）：

读取：
- `{skill_dir}/references/writing-guide.md`
- `{skill_dir}/references/writing-evaluation-phrases.md`
- `{skill_dir}/references/writing-evaluation-structures.md`
- `{skill_dir}/references/writing-evaluation-examples.md`

Agent 在 4.2 检查过程中同步完成综合评审：

- **表层表达**：是否有明显套话、空话、开场报幕、提纲讲解腔、总结腔
- **结构推进**：是否反复使用“不是 X，而是 Y”、连环否定、设问后立刻自答、抽象主语代替人、段尾金句化
- **内容扎实度**：是否有真实来源、具体对象、时间/数字/场景，是否只是抽象判断堆叠
- **节奏自然度**：是否长短句有落差、段落不齐整、不是每段都按同一模板展开
- **平台适配**：是否符合当前平台文风，而不是为了“去 AI 味”硬塞口癖或情绪词

输出规则评审结论：
- **通过** → 继续 Step 5
- **建议小修** → 只修最影响自然度的 1-3 处具体句子，不重写整段，修完继续
- **需要定向重写** → 挑最明显的 2-3 个结构性问题逐项改，每项只改最相关的 1-2 处；最多 2 轮，仍不理想则在 7.2 回复中标注降级项，继续

评审输出必须包含：
- `top_issues`：最影响可读性/自然度的 3-5 个问题
- `rewrite_hints`：逐条定位到句子/段落的改写建议
- `quality_review`：一句话总结（如“结构自然，可发”“有明显讲解腔，建议小修后发”）

---

### Step 5: 视觉 AI

**如果 `skip_image_gen = true`** → 只执行 5.1。

```
读取: {skill_dir}/references/visual-prompts.md
```

**5.1 实体提取**：从终稿中提取 3-5 个**具体实体**（人物、产品名、场景、数据点、行业术语）。后续所有提示词必须包含至少 2 个实体。

**5.2 封面生成**：生成封面 3 组创意提示词（按 visual-prompts.md），选最佳 1 组调用 image_gen.py 生成。`--size` 使用 `platform_profile.cover_size_preset`（头条 `article`、小红书 `vertical`、Twitter `article`）。

**5.3 封面验证**：
- **交互模式**：展示封面，问用户"封面效果如何？"。用户 OK → 继续；不满意 → 调整提示词重新生成。
- **全自动模式**：agent 自检——提示词中的实体是否在画面描述中可识别？如果提示词过于泛化（仅含"科技感""未来感"等抽象词，无具体实体），换一组提示词重试 1 次。

**5.4 配图**：分析终稿结构，生成配图提示词（按 visual-prompts.md），总数不超过 `platform_profile.max_images`。`--size` 使用 `platform_profile.article_image_preset`。风格、色调、画风沿用封面，保持视觉一致。头条用作内文配图；小红书的图片作为笔记图片序列，由 Agent 根据内容自动决定数量；Twitter 默认最多 1 张，仅在产品界面、数据点或信息卡能明显提升传播时才生成。

**注**：已有 `<!-- 📷 插图：... -->` 占位符的位置**不生成 AI 配图**——该位置留给编辑插入真实截图。AI 配图只覆盖没有占位符的段落。图片总数（AI 生成 + 占位符）合计不超过 `platform_profile.max_images`。

**降级**：生图失败 → 输出提示词 + 备选图库关键词，继续。

---

### Step 6: 排版 + 输出

**6.1 Metadata 预检**（按 `platform_profile` 对应字段检查）：

| 检查项 | 标准 | 不通过时 |
|--------|------|---------|
| H1 标题（仅头条 / 小红书） | 存在且 ≤ `platform_profile.title_max_chars` 字 | 自动修正或提示用户 |
| 推文正文（仅 Twitter） | 存在且 ≤ `platform_profile.word_count_max` 字 | 自动压缩到长度内 |
| 摘要 | `digest_max_bytes/chars` 非 null 时：存在且不超限 | 自动生成（小红书 / Twitter 跳过此项） |
| 封面图 | 推送模式下需要 | 无封面则警告 |
| 正文字数 | ≥ `platform_profile.word_count_min` | 警告"内容过短" |
| 图片数量 | ≤ `platform_profile.max_images` | 超出则移除末尾多余图片 |

预检全部通过后才进入排版/输出。

**6.2 输出**（按平台分支）：

**今日头条**（`platform = toutiao`）：

直接输出 Markdown 文件到 `output/{date}-{slug}.md`。提示用户：「文章已保存，请复制到头条号后台发布。」

**小红书**（`platform = xiaohongshu`）：

直接输出 Markdown 文件（emoji 分段+话题标签风格）到 `output/{date}-{slug}.md`。图片保存在 `output/{date}-{slug}/` 目录下。提示用户：「笔记文案和图片已保存，请发布到小红书。」

**Twitter**（`platform = twitter`）：

直接输出 Markdown 文件到 `output/{date}-{slug}.md`，正文仅保留最终发布版推文；如生成配图，保存在 `output/{date}-{slug}/` 目录下。如果环境中已安装 Twitter 发布 skill（如 `twitter-publisher`），则直接调用它发布；如果外部 skill 不可用，则降级为保存文案和图片，并提示用户手动发布。

---

### Step 7: 收尾

**7.1 Daily Tracker 联动**（静默执行，不输出）：

如果 `daily/{date}.yaml` 存在，查找当前选题对应的条目并更新为 `draft`：

```bash
python3 {skill_dir}/scripts/daily.py --json
# 从 JSON 中找到 platform 和 topic 匹配的条目 ID
python3 {skill_dir}/scripts/daily.py update {id} draft -t "{标题}" -o "{output_file}"
```

如果 daily 文件不存在 → 跳过。

**7.2 回复用户**：

- **头条 / 小红书**：最终标题 + 2 备选 + 标签 + 摘要（如有）
- **Twitter**：最终发布版 + 2 个备选版本 + hashtags（如有）
- 编辑建议：头条 / 小红书提示用户补个人表达并说**"学习我的修改"**；如果文中有 `📷 插图` 占位符，列出每个占位符的位置和所需图片描述，提醒用户替换为真实截图；Twitter 提示用户如需更口语、更狠一点或更克制，可直接要求改 1 版

**7.3 后续操作**：

| 用户说 | 动作 |
|--------|------|
| 润色/缩写/扩写/换语气 | 编辑文章 |
| 封面换暖色调 | 重新生图 |
| 用框架 B 重写 | 回到 Step 4 |
| 换一个选题 | 回到 Step 2.3 |
| 看看文章数据 | `读取: {skill_dir}/references/performance-review.md` |
| 调整风格 / 更新风格 | 读取并更新 `{skill_dir}/my-style/{平台}.md` |
| 检查一下 / 自检 / 这篇文章怎么样 | 生成报告（生成档案 + 质量检查，见辅助功能） |
| 发布到 Twitter | 调用外部 Twitter 发布 skill（如已安装），否则提示用户手动发布 |
| 做张信息卡 / 信息���片 | 执行信息卡工��流（见下方章节） |

---

## 信息卡工作流（手动触发）

> 触发词："生成信息卡"、"做张信息卡"、"信息卡片"��"做成卡片"、"make info card"。
> 将文本/URL/刚写的文章转化为杂志质感 HTML 信息卡，自动截图输出 PNG。

### IC-0：获取内容

**如果输入是 URL**，先抓取内容：

| URL 类型 | 抓取方式 |
|----------|---------|
| `x.com` / `twitter.com` | `curl -sL "https://r.jina.ai/{url}"` |
| `mp.weixin.qq.com` | WebFetch 抓取 |
| `arxiv.org/abs/` | 抓 HTML 版 `https://arxiv.org/html/{id}v1`，失败则 PDF |
| 其他网页 | `curl -sL "https://r.jina.ai/{url}"`，失败则 WebFetch |

**如果是纯文本** → 直接进入 IC-1。

**如果用户没给内容**（刚写完文章后说"做成卡片"）→ 自动取 `{skill_dir}/output/` 目录下最新的 .md 文件。

### IC-1：提炼核心信息

> **目标**：让读者只看图片就能理解核心信息，不需要点进原文。

**提炼原则**：
1. **找核心论点**：最反直觉、最颠覆认知的 1 个观点，作为主标题
2. **找关键数据**：具体数字（百分比、倍数、年份、金额），数字比文字更有冲击力
3. **找因果链**：A → B → C，每个环节就是一个要点
4. **砍到 4-6 个要点**：只放"删了会损失信息"的
5. **每个要点 ≤ 2 句话**：第一句给事实/数据，第二句给洞察/结论

**主标题写法**（卡片成败关键）：
- 必须是**结论性的**，读者看到就被勾住
- 用数字或动词驱动
- 检验：读者看完想问"为什么？" → 对；反应是"哦" → 错

**要点间的逻辑**：不是随机罗列，推荐叙事弧线：**发现问题 → 分析原因 → 关键证据 → 反转**

**数据准确性（强制）**：引用数字必须忠实原文，不能为冲击力改变含义。

### IC-2：分析布局

```
读取: {skill_dir}/references/info-card-design-spec.md
```

**选择平台模式**：
- 用户说"小红书" → 轮播模式（多张独立图）
- 用户说"Twitter"/"X" → 长图模式（纵向拼接）
- 未指定 → 默认轮播模式

**规划页面**：
1. **封面页**（必选）：按内容主题匹配 6 种配色之一，有核心数据时用数字封面变体
2. **内容页**（按密度选择）：
   - 1-2 个核心观点 → 低密度（金句型 or 数字型）
   - 3-4 个要点 → 中密度（叙事流）
   - 5+ 个要点 → 高密度（编号列表 or 标签交替）
3. **组合**：一套信息卡 = 封面 + 1-3 张内容页

根据内容主题选择配色：

| 配色 | 色值 | 适用场景 |
|------|------|---------|
| 赤陶 | `#c96a4f` | 科技/AI/通用 |
| 暖炭 | `#1c1917` | 警示/数据/严肃 |
| 暖沙 | `#a68b6b` | 商业/财经/深度 |
| 橄榄 | `#5c7a5e` | 生活/自然/健康 |
| 紫藤 | `#7b6b8a` | 创意/哲学/艺术 |
| 深青 | `#2e4a5c` | 政策/社会/国际 |

### IC-3：生成 HTML

按 design-spec.md 的模板生成**多个** HTML 文件。

**硬性约束**：
- **所有页面**（封面 + 内容页）宽度 **540px**，高度 **720px** 固定，输出 1080×1440（3:4）
- 内容放不下时拆成多页，**不要拉高单页**——小红书轮播中高度不一致会导致图片缩小、两侧留白
- `<meta name="viewport" content="width=540">`
- 封面底色用配色满铺，内容页底色 `#faf9f5`
- 正文 ≥ 22px，标签 ≥ 9px（见 design-spec 详细字号表）

保存路径：
```
{skill_dir}/output/info-cards/{YYYYMMDD}-{来源}-{关键词}/
  ├── card-cover.html
  ├── card-1.html
  ├── card-2.html（如有）
  └── ...
```

### IC-4：截图

**单页截图**：
```bash
python3 {skill_dir}/scripts/screenshot.py {html_path} {output_png} --width 540 --wait 3000
```

**批量截图**（推荐）：
```bash
python3 {skill_dir}/scripts/screenshot.py batch {card_dir} --width 540 --wait 3000
```

批量模式自动截图目录下所有 `card-*.html` 文件，输出同名 `.png`。

| 卡片宽度 | deviceScaleFactor | 输出 PNG 宽度 |
|---------|-----------------|-------------|
| 540px | 2x | 1080px |

### IC-5：拼接或分割

**小红书轮播模式**（默认）：
每张 card-*.png 已是独立图片，无需额外处理。

**Twitter 长图模式**：
将所有页面纵向拼接为一张长图：
```bash
python3 {skill_dir}/scripts/card_slice.py stitch {output_dir}/card-full.png {output_dir}/card-cover.png {output_dir}/card-1.png {output_dir}/card-2.png
```

**分割**（用户明确要求时）：
```bash
python3 {skill_dir}/scripts/card_slice.py {png_path} 1200
```

### IC-6：输出

告知用户：
- 图片路径和数量
- 输出模式（轮播 or 长图）
- 各页尺寸信息
- 如果是轮播模式，说明第 1 张是封面，建议作为小红书首图

如果是从 write-anything 主管道写完的文章生成的卡片，提示用户可以用卡片配合原文一起发布。

---

## 错误处理

| 步骤 | 降级 |
|------|------|
| 环境检查 | 逐项引导，设降级标记 |
| 关键词扩展（WebSearch 不可用） | 跳过 4.0，依靠 LLM 已有知识完成 4.1 标签和标题优化 |
| 素材采集（WebSearch） | LLM 训练数据中可验证的公开信息 |
| my-style 为空 | 仅依据 writing-guide.md 写作 |
| 去 AI 验证 | 2 轮定向修复不过则跳过该项 |
| 生图失败 | 输出提示词 |
| Twitter 发布 skill 不存在 | 保存推文文案和配图，提示用户手动发布 |
| 效果数据 | 告知等 24h |
| 信息卡 Playwright 不可用 | 提示用户 `pip install playwright && playwright install chromium` |
| 信息卡分割无断点 | 输出完整长图 |
