# 风格配置说明

## 快速开始

首次使用时 Agent 会通过对话引导你自动生成 `config.yaml`。也可以手动创建——参考下方完整示例。

## 配置结构

```yaml
# 全局配置
default_platform: "toutiao"    # 默认目标平台
industry: "行业"
blacklist:                     # 全局禁用（可选）
  words: ["禁忌词1"]
  topics: ["禁忌话题1"]

# 每个平台独立配置
platforms:
  toutiao:
    name: "账号名称"           # 必填
    topics: ["方向1"]          # 必填
    tone: "写作风格描述"        # 必填
    voice: "写作人称和语感"     # 可选，默认"第一人称"
    target_audience: "受众描述" # 可选
    cover_style: "封面风格"     # 可选
    reference_accounts: []     # 可选
    author: "署名"             # 可选，默认同 name
```

## 完整示例

```yaml
default_platform: "toutiao"
industry: "科技/互联网"
blacklist:
  words: ["震惊", "必看", "不转不是中国人", "赶紧收藏"]
  topics: ["政治敏感", "宗教"]

platforms:
  toutiao:
    name: "Demo科技"
    topics:
      - AI/人工智能
      - 产品设计
      - 效率工具
    tone: "专业但不学术，有观点但不偏激，偶尔幽默"
    voice: "第一人称，像一个懂行的朋友在分享见解"
    target_audience: "25-40岁互联网从业者、科技爱好者"
    cover_style: "简洁科技感，蓝色调，扁平化设计"
    reference_accounts: ["36氪", "虎嗅", "少数派"]

  xiaohongshu:
    name: "Demo酱"
    topics:
      - AI 工具推荐
      - 效率提升
    tone: "轻松口语化，像朋友在种草"
    voice: "第一人称"

  twitter:
    name: "DemoAI"
    topics:
      - AI/人工智能
      - 产品观察
    tone: "轻松专业，偶尔犀利"
    voice: "第一人称"

image:
  provider: "ark"
```
