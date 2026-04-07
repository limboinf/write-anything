# 信息卡设计规范

> 本规范信息卡功能的**唯一视觉真相源**。Agent 在生成信息卡 HTML 时**必须参照此文件**，不得自行发挥。
>
> 参考实现见 `{skill_dir}/examples/` 目录下的 8 个 HTML 文件。

---

## 1. 字体引入

使用宋体（系统内置衬线字体），无需本地文件，零网络依赖。

**所有页面（封面 + 内容页）统一字体栈**：标题、正文均用宋体。

```css
font-family: 'SimSun', '宋体', serif;
```

> 宋体为系统字体，无需 `@font-face` 声明，直接在 CSS 中使用即可。

---

## 2. 尺寸规范

| 页面类型 | CSS 宽度 | CSS 高度 | 截图倍率 | 输出图片尺寸 |
|---------|---------|---------|---------|------------|
| 封面页 | 540px | 720px（固定） | 2x | 1080×1440（3:4） |
| 内容页（所有密度） | 540px | 720px（固定） | 2x | 1080×1440（3:4） |

> **为什么全部固定 720px**：小红书轮播模式下，所有图片必须保持相同宽高比（3:4），否则高度不一致的图会被平台缩小显示，导致看起来变窄、两侧留白。固定 720px 确保每张图都能铺满屏幕。内容放不下时拆成多页，不要拉高单页。

所有页面的 viewport meta 标签：

```html
<meta name="viewport" content="width=540">
```

### 2.1 HTML 生成预规划

在写任何 HTML 之前，先做一次**分页规划**，再落文件。

**生成顺序**：

1. 先判断内容密度（低 / 中 / 高）
2. 估算单页是否能装下
3. 装不下就直接拆成多个 HTML，不要先写满一页再依赖裁切

**输出形式**：

- 封面固定输出 `card-cover.html`
- 内容页允许输出 `card-1.html`、`card-2.html`、`card-3.html`...
- 同一套卡片内，所有内容页复用同一配色、同一模板语言、同一页脚样式

**高密度内容的默认策略**：

- 先按“要点组”分页，再写 HTML
- `card-1.html` 放标题 + 第一组要点
- `card-2.html` 及后续页保留同一主标题，标题可简化为“主标题（续）”或加小字 `PART 2`
- 编号列表型建议续页后编号连续，不要每页从 `01` 重新开始
- 标签交替型建议按主题分组，每页只放一组标签密度接近的内容

**建议的分页阈值**：

- 低密度：1 个核心观点 / 1 个数字 / 1 段金句，通常 1 页
- 中密度：每页 2-3 个 section；如果正文总量明显超过单页容量，拆成 2 页
- 高密度：每页优先放 4 个完整要点；只有当每条都很短时才放 5-6 个；超过这个量就拆多个 HTML

> 原则：宁可多一页，也不要把信息硬塞进单页。

---

## 3. 封面页规范

### 3.1 页面结构

封面固定 540×720px，内容垂直 + 水平居中。从底层到顶层：

1. **底色层**：纯色满铺（见配色方案）
2. **渐变叠加层**：增加光影方向感（z-index: 1）
3. **几何装饰层**：每种配色专属几何语言，透明度 4%-12%（z-index: 1）
4. **噪点纹理层**：2.5% 透明度（z-index: 2）
5. **文字层**：标题区居中（z-index: 3）

### 3.2 基础封面 CSS

```css
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  margin: 0;
  padding: 0;
}

.cover {
  position: relative;
  width: 540px;
  height: 720px;
  background-color: {配色色值};
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

/* 噪点纹理 — 所有封面共用 */
.cover::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 2;
  opacity: 0.025;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-size: 200px 200px;
  pointer-events: none;
}

/* 渐变叠加 — 赤陶/暖沙/橄榄/紫藤/深青 使用此渐变 */
.gradient-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(160deg, rgba(255,255,255,0.06) 0%, transparent 50%, rgba(0,0,0,0.1) 100%);
  pointer-events: none;
}
```

### 3.3 文字层

```css
.content {
  position: relative;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  width: 100%;
}

/* 主标题 — 56-64px，宋体，不加粗 */
.title {
  font-family: 'SimSun', '宋体', serif;
  font-size: 58px;        /* 范围 56-64px，按标题长度调整 */
  font-weight: normal;
  line-height: 1.24;
  color: #ffffff;
  letter-spacing: 0.03em;
  white-space: pre-line;   /* 支持手动换行 */
}

/* 分割线 — 固定 32px 宽 */
.sep {
  width: 32px;
  height: 1.5px;
  background-color: rgba(255,255,255,0.3);
  margin: 24px auto;
}

/* 副标题 — 22-24px */
.subtitle {
  font-family: 'SimSun', '宋体', serif;
  font-size: 23px;
  color: rgba(255,255,255,0.55);
  letter-spacing: 0.01em;
}

/* 刊头 — 标题区最后一行 */
.masthead {
  font-family: -apple-system, 'Helvetica Neue', sans-serif;
  font-size: 9px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.3);
  margin-top: 12px;
}
```

**文字层 HTML 结构**：

```html
<div class="content">
  <h1 class="title">主标题文字
可以手动换行</h1>
  <div class="sep"></div>
  <p class="subtitle">副标题一句话</p>
</div>
```

### 3.4 数字封面变体

当内容有核心数据时，可在标题上方增加大数字。参考 `{skill_dir}/examples/cover-charcoal.html`。

```css
.big-number {
  font-family: -apple-system, 'Helvetica Neue', sans-serif;
  font-size: 130px;      /* 范围 120-140px */
  font-weight: 800;
  color: #d97757;         /* 暖炭底时用赤陶暖色高亮 */
  line-height: 1;
  letter-spacing: -0.02em;
}
```

数字封面时标题缩小到 50-56px。分割线颜色改为 accent 暖色（如暖炭底：`rgba(217,119,87,0.35)`）。

### 3.5 封面不包含的元素

- **日期** — 不放
- **页码** — 不放
- **正文内容** — 不放

---

## 4. 内容页规范

### 4.1 共同视觉语言

所有内容页共享以下基础样式：

```css
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  margin: 0;
  padding: 0;
}

/* 噪点纹理 — 所有内容页共用，通过 .page::after 实现 */
/* 见下方各模板中的 .page::after */
```

| 属性 | 值 | 说明 |
|------|------|------|
| 底色 | `#faf9f5`（暖白） | 所有内容页统一 |
| 噪点纹理 | 2.5% 透明度 | 同封面的 SVG filter |
| 页码 | 右下角，9px，`#ccc` | 系统无衬线体 |
| Accent 色 | 沿用封面配色 | 仅用于圆点、编号、引用线等**小面积点缀** |
| 字体 | 宋体（SimSun） | 标题 + 正文统一 |

**噪点纹理 CSS**（所有内容页 `.page::after` 统一）：

```css
.page::after {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  opacity: 0.025;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-size: 200px 200px;
  pointer-events: none;
}
```

**页码 CSS**（所有内容页统一）：

```css
.page-num {
  position: absolute;
  bottom: 28px;
  right: 36px;
  font-family: -apple-system, 'Helvetica Neue', sans-serif;
  font-size: 9px;
  color: #ccc;
  z-index: 1;
}
```

### 4.1.1 反截断规则

内容页允许固定 `540×720px`，但**正文本身禁止靠裁切解决溢出**。

**禁止出现以下做法**：

- 对标题、正文、条目描述、引用使用 `text-overflow: ellipsis`
- 使用 `display: -webkit-box` + `-webkit-line-clamp`
- 对正文容器设置 `max-height` 再配合 `overflow: hidden`
- 用 `white-space: nowrap` 强行压成一行
- 依赖 `.page { overflow: hidden; }` 把超出的正文直接裁掉

`.page` 上的 `overflow: hidden` 仅用于纹理、几何元素、页边装饰的裁切，不用于隐藏正文。

**内容过长时的处理优先级**：

1. 换更合适的模板（例如中密度改高密度）
2. 启用紧凑模式，缩小标题、正文、间距
3. 拆成多个 HTML 页面
4. 只在极端情况下压缩文案表述，但不能删除事实点、数据点、关键判断

**页脚 CSS**（中/高密度页共用，含来源 + 页码）：

```css
.footer {
  position: relative;
  z-index: 1;
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
}

.footer-source {
  font-family: 'SimSun', '宋体', serif;
  font-size: 14px;
  color: #bbb;
}

.footer-page {
  font-family: -apple-system, 'Helvetica Neue', sans-serif;
  font-size: 9px;
  color: #ccc;
}
```

### 4.2 低密度内容页（1-2 个核心观点）

**设计哲学**：留白 > 内容面积，让单个观点/数字/金句拥有整页空间。

**高度**：固定 720px（保持 3:4）。

#### 4.2.1 金句型

参考 `{skill_dir}/examples/content-low-quote.html`。

居中布局，极简元素。

```css
.page {
  position: relative;
  width: 540px;
  height: 720px;
  background-color: #faf9f5;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 60px 48px;
}

/* 短装饰线 */
.deco-line {
  position: relative;
  z-index: 1;
  width: 28px;
  height: 2px;
  background-color: {accent色};
  margin-bottom: 28px;
}

/* 引号装饰 */
.quote-mark {
  position: relative;
  z-index: 1;
  font-family: Georgia, serif;
  font-size: 48px;
  color: {accent色};
  opacity: 0.15;
  margin-bottom: 8px;
  line-height: 1;
}

/* 引言正文 */
.quote-text {
  position: relative;
  z-index: 1;
  font-family: 'SimSun', '宋体', serif;
  font-size: 38px;           /* 范围 36-40px */
  font-style: italic;
  line-height: 1.6;
  color: #1a1a1a;
  max-width: 420px;
  white-space: pre-line;
}

/* 出处 */
.quote-source {
  position: relative;
  z-index: 1;
  font-family: 'SimSun', '宋体', serif;
  font-size: 20px;
  color: #999;
  margin-top: 24px;
}
```

**HTML 结构**：

```html
<div class="page">
  <div class="deco-line"></div>
  <div class="quote-mark">"</div>
  <p class="quote-text">金句文字
可以换行</p>
  <p class="quote-source">— 作者, 来源</p>
  <span class="page-num">02</span>
</div>
```

#### 4.2.2 数字型

参考 `{skill_dir}/examples/content-low-number.html`。

居中布局，核心数字居中突出。

```css
.page {
  /* 同金句型 .page */
}

/* 短装饰线 */
.deco-line {
  /* 同金句型，margin-bottom: 32px */
  position: relative;
  z-index: 1;
  width: 28px;
  height: 2px;
  background-color: {accent色};
  margin-bottom: 32px;
}

/* 大数字 */
.big-number {
  position: relative;
  z-index: 1;
  font-family: -apple-system, 'Helvetica Neue', sans-serif;
  font-size: 130px;           /* 范围 120-140px */
  font-weight: 800;
  color: {accent色};
  line-height: 1;
}

/* 数字标签 */
.number-label {
  position: relative;
  z-index: 1;
  font-family: 'SimSun', '宋体', serif;
  font-size: 26px;
  color: #666;
  margin-top: 16px;
  line-height: 1.5;
}

/* 补充描述 */
.number-desc {
  position: relative;
  z-index: 1;
  font-family: 'SimSun', '宋体', serif;
  font-size: 24px;
  color: #999;
  margin-top: 12px;
  line-height: 1.5;
  max-width: 400px;
  white-space: pre-line;
}
```

**HTML 结构**：

```html
<div class="page">
  <div class="deco-line"></div>
  <div class="big-number">3.7×</div>
  <p class="number-label">核心指标名称</p>
  <p class="number-desc">一两句补充说明
可以换行</p>
  <span class="page-num">02</span>
</div>
```

### 4.3 中密度内容页（3-4 个要点）

**设计哲学**：叙事流，有节奏的阅读体验。

**高度**：固定 720px（保持 3:4，内容超出则拆成多页）。

参考 `{skill_dir}/examples/content-mid-narrative.html`。

```css
.page {
  position: relative;
  width: 540px;
  height: 720px;
  background-color: #faf9f5;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 44px 40px 48px;
}

/* section 头部 — 圆点 + 标题 */
.section {
  position: relative;
  z-index: 1;
}

.section-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.section-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: {accent色};
  flex-shrink: 0;
}

.section-title {
  font-family: 'SimSun', '宋体', serif;
  font-size: 30px;            /* 范围 28-32px */
  font-weight: normal;
  color: #1a1a1a;
  line-height: 1.3;
}

/* 正文 */
.section-body {
  font-family: 'SimSun', '宋体', serif;
  font-size: 22px;            /* 范围 22-24px */
  color: #555;
  line-height: 1.75;
  padding-left: 16px;
}

/* 段落间分隔线 */
.divider {
  position: relative;
  z-index: 1;
  height: 1px;
  background: rgba(0, 0, 0, 0.06);
  margin: 4px 0 24px;
}

/* 拉引语 pull-quote */
.pull-quote {
  border-left: 3px solid {accent色};
  background: rgba({accent色RGB}, 0.05);    /* accent 色的 5% 透明度 */
  padding: 16px 20px;
  margin: 8px 0 0 16px;
  font-family: 'SimSun', '宋体', serif;
  font-size: 21px;
  font-style: italic;
  color: #333;
  line-height: 1.7;
}
```

**HTML 结构**：

```html
<div class="page">
  <!-- Section 1 -->
  <div class="section">
    <div class="section-header">
      <div class="section-dot"></div>
      <h2 class="section-title">章节标题</h2>
    </div>
    <p class="section-body">正文内容。</p>
  </div>

  <div class="divider"></div>

  <!-- Section 2 -->
  <div class="section">
    <div class="section-header">
      <div class="section-dot"></div>
      <h2 class="section-title">章节标题</h2>
    </div>
    <p class="section-body">正文内容。</p>
    <blockquote class="pull-quote">拉引语，原文中最有冲击力的一句话。</blockquote>
  </div>

  <div class="divider"></div>

  <!-- Section 3 -->
  <div class="section">
    <div class="section-header">
      <div class="section-dot"></div>
      <h2 class="section-title">章节标题</h2>
    </div>
    <p class="section-body">正文内容。</p>
  </div>

  <!-- 页脚 -->
  <div class="footer">
    <span class="footer-source">来源：XXX</span>
    <span class="footer-page">03</span>
  </div>
</div>
```

#### 4.3.1 中密度紧凑模式

当 section 标题偏长、正文段落偏密，或单页接近装不下时，优先启用紧凑模式，而不是截断正文。

```css
.page.compact {
  padding: 36px 32px 40px;
}

.page.compact .section-header {
  gap: 8px;
  margin-bottom: 8px;
}

.page.compact .section-title {
  font-size: 26px;
  line-height: 1.28;
}

.page.compact .section-body {
  font-size: 20px;
  line-height: 1.62;
  padding-left: 14px;
}

.page.compact .divider {
  margin: 2px 0 18px;
}

.page.compact .pull-quote {
  padding: 12px 16px;
  margin: 6px 0 0 14px;
  font-size: 19px;
  line-height: 1.58;
}
```

**使用建议**：

- 正常版仍是首选
- 如果 3 个 section 已接近底部，优先改成 `.page.compact`
- 如果紧凑模式后仍明显拥挤，直接拆成 `card-2.html`

### 4.4 高密度内容页（5+ 个要点）

**设计哲学**：紧凑但有序，扫读友好。

**高度**：固定 720px（保持 3:4，内容超出则拆成多页）。

#### 4.4.1 编号列表型

参考 `{skill_dir}/examples/content-high-numbered.html`。

```css
.page {
  position: relative;
  width: 540px;
  height: 720px;
  background-color: #faf9f5;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 40px 40px 48px;
}

/* 标题区 */
.header {
  position: relative;
  z-index: 1;
}

.title {
  font-family: 'SimSun', '宋体', serif;
  font-size: 28px;
  font-weight: normal;
  color: #1a1a1a;
}

/* 强调线 — accent 色 */
.accent-line {
  height: 2px;
  background: {accent色};
  margin-top: 12px;
  margin-bottom: 24px;
}

/* 列表容器 */
.items {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
}

/* 每个条目 — 序号 + 内容 水平排列 */
.item {
  display: flex;
  flex-direction: row;
  gap: 16px;
  padding: 16px 0;
}

.item + .item {
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

/* 序号 */
.item-number {
  font-family: -apple-system, 'Helvetica Neue', sans-serif;
  font-size: 36px;
  font-weight: 700;
  color: {accent色};
  opacity: 0.7;
  line-height: 1;
  flex-shrink: 0;
  width: 44px;
}

/* 条目内容 */
.item-content {
  flex: 1;
}

.item-title {
  font-family: 'SimSun', '宋体', serif;
  font-size: 24px;
  color: #1a1a1a;
  line-height: 1.4;
  margin-bottom: 6px;
}

.item-desc {
  font-family: 'SimSun', '宋体', serif;
  font-size: 20px;
  color: #888;
  line-height: 1.6;
}
```

**HTML 结构**：

```html
<div class="page">
  <div class="header">
    <h1 class="title">列表标题</h1>
    <div class="accent-line"></div>
  </div>

  <div class="items">
    <div class="item">
      <span class="item-number">01</span>
      <div class="item-content">
        <p class="item-title">条目标题</p>
        <p class="item-desc">条目描述，1-2 句话</p>
      </div>
    </div>
    <!-- 更多 item... -->
  </div>

  <div class="footer">
    <span class="footer-source">来源：XXX</span>
    <span class="footer-page">04</span>
  </div>
</div>
```

#### 4.4.1.1 编号列表型紧凑模式

适用于条目多、每条描述 2 行左右的场景。先收紧排版，再考虑拆页。

```css
.page.compact {
  padding: 34px 32px 40px;
}

.page.compact .title {
  font-size: 24px;
  line-height: 1.3;
}

.page.compact .accent-line {
  margin-top: 10px;
  margin-bottom: 18px;
}

.page.compact .item {
  gap: 12px;
  padding: 12px 0;
}

.page.compact .item-number {
  font-size: 32px;
  width: 38px;
}

.page.compact .item-title {
  font-size: 21px;
  line-height: 1.35;
  margin-bottom: 4px;
}

.page.compact .item-desc {
  font-size: 18px;
  line-height: 1.5;
  color: #777;
}
```

**分页建议**：

- 标准版：每页 4 个条目最稳妥
- 紧凑版：每页 5 个短条目可接受
- 如果有 6 个以上条目，或任一条描述明显偏长，直接拆成多个 HTML

#### 4.4.2 标签交替型

参考 `{skill_dir}/examples/content-high-tagged.html`。

与编号型的关键区别：条目用分类标签替代序号，奇偶行交替底色，`.page` 水平 padding 为 0（由 `.item` 内部负责 padding）。

```css
.page {
  position: relative;
  width: 540px;
  height: 720px;
  background-color: #faf9f5;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 40px 0 48px;       /* 注意：左右 padding 为 0 */
}

/* 标题区 — 内部自带水平 padding */
.header {
  position: relative;
  z-index: 1;
  padding: 0 40px;
}

.title {
  font-family: 'SimSun', '宋体', serif;
  font-size: 28px;
  font-weight: normal;
  color: #1a1a1a;
}

/* 强调线 — 有自己的水平 margin */
.accent-line {
  height: 2px;
  background: {accent色};
  margin: 12px 40px 0;
}

/* 列表容器 */
.items {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-top: 20px;
}

/* 每个条目 — 全宽，内含 padding */
.item {
  padding: 18px 40px;
}

.item:nth-child(odd) {
  background: rgba(0, 0, 0, 0.025);
}

.item:nth-child(even) {
  background: transparent;
}

/* 分类标签 */
.item-tag {
  font-family: -apple-system, 'Helvetica Neue', sans-serif;
  font-size: 9px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: {accent色};
  margin-bottom: 6px;
  font-weight: 600;
}

/* 标题 */
.item-title {
  font-family: 'SimSun', '宋体', serif;
  font-size: 23px;
  color: #1a1a1a;
  line-height: 1.4;
  margin-bottom: 4px;
}

/* 描述 */
.item-desc {
  font-family: 'SimSun', '宋体', serif;
  font-size: 19px;
  color: #888;
  line-height: 1.6;
}

/* 页脚 — 自带水平 padding */
.footer {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 40px 0;
}
```

**HTML 结构**：

```html
<div class="page">
  <div class="header">
    <h1 class="title">列表标题</h1>
  </div>
  <div class="accent-line"></div>

  <div class="items">
    <div class="item">
      <p class="item-tag">分类名称</p>
      <p class="item-title">条目标题</p>
      <p class="item-desc">条目描述</p>
    </div>
    <!-- 更多 item... -->
  </div>

  <div class="footer">
    <span class="footer-source">来源名称</span>
    <span class="footer-page">05</span>
  </div>
</div>
```

#### 4.4.2.1 标签交替型紧凑模式

```css
.page.compact {
  padding: 34px 0 40px;
}

.page.compact .header {
  padding: 0 32px;
}

.page.compact .title {
  font-size: 24px;
  line-height: 1.3;
}

.page.compact .accent-line {
  margin: 10px 32px 0;
}

.page.compact .items {
  margin-top: 16px;
}

.page.compact .item {
  padding: 14px 32px;
}

.page.compact .item-tag {
  font-size: 8px;
  margin-bottom: 4px;
}

.page.compact .item-title {
  font-size: 21px;
  line-height: 1.35;
}

.page.compact .item-desc {
  font-size: 18px;
  line-height: 1.5;
  color: #777;
}

.page.compact .footer {
  padding: 12px 32px 0;
}
```

**分页建议**：

- 标准版：每页 5 个条目以内
- 紧凑版：每页 6 个短条目以内
- 如果条目超过 6 个，或者标题 + 描述合计明显偏长，拆成 `card-2.html`、`card-3.html`

#### 4.4.3 高密度多 HTML 设计规则

当高密度内容已经超出单页容量时，不要继续压缩到失真，直接拆多个 HTML。

**推荐结构**：

- `card-1.html`：主标题 + 4-5 个最重要条目
- `card-2.html`：同一主标题续页，补完剩余条目
- `card-3.html`：只在总条目非常多时使用，避免单页超过 6 个条目

**续页标题设计**：

- 主标题不变，后缀可写 `（续）`
- 或在标题下方加一行 10-12px 的英文小字：`PART 2 / PART 3`
- 续页不需要重复封面式大标题排场，重点是阅读连续性

**拆分原则**：

- 按语义分组拆，不按字数生硬腰斩
- 不要把同一条目标题放在上一页、描述放在下一页
- 一页内部的密度要均匀，避免第一页太满、第二页只有一条

---

## 5. 配色方案

Agent 根据内容主题从 6 种配色中选择 1 种。同一套信息卡（封面 + 所有内容页）使用同一配色。

| 名称 | 色值 | 适用场景 | 封面几何装饰 |
|------|------|---------|------------|
| 赤陶 | `#c96a4f` | 科技/AI/通用 | 弧形圆环（右上 + 左下双环溢出边界） |
| 暖炭 | `#1c1917` | 警示/数据/严肃 | 赤陶色点阵网格 + 斜向光线 |
| 暖沙 | `#a68b6b` | 商业/财经/深度 | 三角切面 + 水平参考线 + 菱形 |
| 橄榄 | `#5c7a5e` | 生活/自然/健康 | 同心圆弧 |
| 紫藤 | `#7b6b8a` | 创意/哲学/艺术 | 交叉细线网格 |
| 深青 | `#2e4a5c` | 政策/社会/国际 | 水平平行线 |

### 5.1 各配色几何装饰 CSS

**赤陶 `#c96a4f`** — 弧形圆环（参考 `{skill_dir}/examples/cover-terracotta.html`）：

```css
/* 大圆环 — 右上角溢出 */
.ring-large {
  position: absolute;
  z-index: 1;
  width: 420px;
  height: 420px;
  top: -160px;
  right: -130px;
  border-radius: 50%;
  border: 1.5px solid rgba(255,255,255,0.1);
  pointer-events: none;
}

/* 小圆环 — 左下角溢出 */
.ring-small {
  position: absolute;
  z-index: 1;
  width: 200px;
  height: 200px;
  bottom: -50px;
  left: -60px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.07);
  pointer-events: none;
}
```

**暖炭 `#1c1917`** — 点阵网格 + 斜向光线（参考 `{skill_dir}/examples/cover-charcoal.html`）：

```css
/* 点阵网格 */
.dot-grid {
  position: absolute;
  inset: 0;
  z-index: 1;
  background-image: radial-gradient(circle, rgba(217,119,87,0.12) 1px, transparent 1px);
  background-size: 24px 24px;
  pointer-events: none;
}

/* 对角线 — 30% 高度处 */
.diag-line-1 {
  position: absolute;
  z-index: 1;
  width: 140%;
  height: 1px;
  background-color: rgba(217,119,87,0.15);
  top: 30%;
  left: -20%;
  transform: rotate(-12deg);
  pointer-events: none;
}

/* 对角线 — 70% 高度处 */
.diag-line-2 {
  position: absolute;
  z-index: 1;
  width: 140%;
  height: 1px;
  background-color: rgba(217,119,87,0.08);
  top: 70%;
  left: -20%;
  transform: rotate(-12deg);
  pointer-events: none;
}
```

> 暖炭配色特殊处理：文字色用 `#faf9f5`（暖白）而非纯白；分割线色用 `rgba(217,119,87,0.35)`；刊头色用 `rgba(217,119,87,0.3)`。

**暖沙 `#a68b6b`** — 三角切面 + 水平线 + 菱形（参考 `{skill_dir}/examples/cover-sand.html`）：

```css
/* 左上角三角切面 */
.triangle {
  position: absolute;
  z-index: 1;
  top: 0;
  left: 0;
  width: 0;
  height: 0;
  border-left: 260px solid rgba(255,255,255,0.04);
  border-bottom: 360px solid transparent;
  pointer-events: none;
}

/* 水平参考线 — 25% */
.h-line-1 {
  position: absolute;
  z-index: 1;
  top: 25%;
  left: 0;
  right: 0;
  height: 1px;
  background-color: rgba(255,255,255,0.12);
  pointer-events: none;
}

/* 水平参考线 — 75% */
.h-line-2 {
  position: absolute;
  z-index: 1;
  top: 75%;
  left: 0;
  right: 0;
  height: 1px;
  background-color: rgba(255,255,255,0.12);
  pointer-events: none;
}

/* 右下角菱形 */
.diamond {
  position: absolute;
  z-index: 1;
  bottom: 48px;
  right: 48px;
  width: 40px;
  height: 40px;
  border: 1px solid rgba(255,255,255,0.2);
  transform: rotate(45deg);
  pointer-events: none;
}
```

**橄榄 `#5c7a5e`** — 同心圆弧：

```css
/* 同心圆弧 — 居中偏右上 */
.arc-1 {
  position: absolute;
  z-index: 1;
  width: 500px;
  height: 500px;
  top: -120px;
  right: -100px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.06);
  pointer-events: none;
}

.arc-2 {
  position: absolute;
  z-index: 1;
  width: 340px;
  height: 340px;
  top: -40px;
  right: -20px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.08);
  pointer-events: none;
}

.arc-3 {
  position: absolute;
  z-index: 1;
  width: 180px;
  height: 180px;
  top: 40px;
  right: 60px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.1);
  pointer-events: none;
}
```

**紫藤 `#7b6b8a`** — 交叉细线网格：

```css
/* 交叉细线网格 */
.grid-lines {
  position: absolute;
  inset: 0;
  z-index: 1;
  background-image:
    linear-gradient(0deg, rgba(255,255,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
}
```

**深青 `#2e4a5c`** — 水平平行线：

```css
/* 水平平行线 */
.h-lines {
  position: absolute;
  inset: 0;
  z-index: 1;
  background-image: linear-gradient(0deg, rgba(255,255,255,0.05) 1px, transparent 1px);
  background-size: 100% 32px;
  pointer-events: none;
}
```

### 5.2 几何装饰规则

- 所有几何元素透明度 4%-12%，**绝不抢标题注意力**
- 每种配色的几何语言固定，保证同一配色的封面视觉一致性
- 几何元素允许溢出画布边界（`overflow: hidden` 裁切）
- 非暖炭配色的封面叠加渐变 `.gradient-overlay`；暖炭配色不叠加渐变（深色底自带层次）

---

## 6. 双模式输出

### 6.1 小红书轮播模式

每页独立截图，独立保存为 PNG。**所有页面必须统一为 1080×1440（3:4）**，确保在小红书轮播中铺满屏幕、宽度一致。内容放不下时拆成更多页，不要拉高单页。

```
输入内容 → Agent 提炼 → 选择密度模板
                      ↓
              card-cover.png (1080×1440)
              card-1.png     (1080×1440)
              card-2.png     (1080×1440)
              ...
```

> 关键约束：轮播模式下，内容页数量可以增加，但单页尺寸不能变；解决超长内容的办法是“多 HTML 分页”，不是“超出后截断”。

### 6.2 Twitter 长图模式

所有页纵向拼接为一张长图，页面之间**无间距**。

```
输入内容 → Agent 提炼 → 选择密度模板
                      ↓
              card-full.png (1080×按内容总高)
```

### 6.3 模式选择逻辑

| 用户说 | 输出模式 |
|--------|---------|
| "小红书" | 轮播模式 |
| "Twitter" / "X" / "推特" | 长图模式 |
| 未指定平台 | 默认轮播模式（更通用） |

---

## 7. 输出规则

### 7.1 目录结构

```
{skill_dir}/output/info-cards/{YYYYMMDD}-{来源}-{关键词}/
  ├── card-cover.html      # 封面 HTML 源文件
  ├── card-cover.png       # 封面截图
  ├── card-1.html          # 内容页 1
  ├── card-1.png
  ├── card-2.html          # 内容页 2
  ├── card-2.png
  └── card-full.png        # Twitter 长图（纵向拼接，仅长图模式）
```

### 7.2 截图命令

单页截图：

```bash
python3 {skill_dir}/scripts/screenshot.py {html_path} {output_png} --width 540 --wait 3000
```

批量截图（对目录下所有 HTML 文件）：

```bash
python3 {skill_dir}/scripts/screenshot.py batch {目录路径} --width 540
```

### 7.3 拼接命令（Twitter 长图）

```bash
python3 {skill_dir}/scripts/card_slice.py stitch {output_png} {img1} {img2} ...
```

### 7.4 分割命令（用户要求时才执行）

```bash
python3 {skill_dir}/scripts/card_slice.py {png_path} 1200
```

---

## 8. 布局速查表

| 密度 | 适用内容量 | 模板 | 子变体 | 标题字号 | 正文字号 | 高度 |
|------|-----------|------|--------|---------|---------|------|
| 封面 | — | 封面页 | 标准 / 数字 | 56-64px / 50-56px | — | 720px 固定 |
| 低 | 1-2 个核心观点 | 内容页 · 低密度 | 金句型 / 数字型 | — | 38px / 130px | 720px 固定 |
| 中 | 3-4 个要点 | 内容页 · 中密度 | 叙事流 | 28-32px（紧凑 26px） | 22-24px（紧凑 20px） | 720px 固定 |
| 高 | 5+ 个要点 | 内容页 · 高密度 | 编号列表 / 标签交替 | 28px（紧凑 24px） | 20-23px（紧凑 18-21px） | 720px 固定 |

> 所有页面统一 540×720px → 输出 1080×1440（3:4）。内容超出单页容量时，先启用紧凑模式，再拆成多页；不要截断正文。
