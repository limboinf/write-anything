#!/usr/bin/env python3
"""每日内容矩阵管理 — 跟踪多平台文章从选题到发布的状态。

用法:
    daily.py                                  # 查看今日状态
    daily.py plan 小红书:3 头条:2 推特:2       # 设置今日计划
    daily.py add 小红书 "AI工具推荐"           # 添加选题
    daily.py update 1 draft                   # 更新状态
    daily.py update 1 draft -t "标题" -o out/file.md
"""

import argparse
import json
import os
import sys
from datetime import datetime, date

import yaml

# ── 常量 ──────────────────────────────────────────────

DAILY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "daily"
)

PLATFORM_ALIASES = {
    "小红书": "xiaohongshu", "xhs": "xiaohongshu", "xiaohongshu": "xiaohongshu",
    "头条": "toutiao", "今日头条": "toutiao", "toutiao": "toutiao",
    "推特": "twitter", "twitter": "twitter", "x": "twitter",
}

PLATFORM_DISPLAY = {
    "xiaohongshu": "小红书",
    "toutiao": "今日头条",
    "twitter": "Twitter",
}

STATUSES = ["topic", "draft", "reviewed", "ready", "published"]

STATUS_DISPLAY = {
    "topic":     "已选题",
    "draft":     "已生成",
    "reviewed":  "已审核",
    "ready":     "待发布",
    "published": "已发布",
}

STATUS_ICONS = {
    "topic": "1", "draft": "2", "reviewed": "3", "ready": "4", "published": "5",
}

# ── 文件操作 ──────────────────────────────────────────

def daily_path(target_date=None):
    d = target_date or date.today().isoformat()
    return os.path.join(DAILY_DIR, f"{d}.yaml")


def load_daily(target_date=None):
    p = daily_path(target_date)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_daily(data, target_date=None):
    os.makedirs(DAILY_DIR, exist_ok=True)
    with open(daily_path(target_date), "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def ensure_daily(target_date=None):
    """加载或创建当天文件。"""
    d = target_date or date.today().isoformat()
    data = load_daily(d)
    if data is None:
        data = {"date": d, "plan": {}, "articles": []}
    return data, d


def resolve_platform(name):
    key = name.lower().strip()
    if key in PLATFORM_ALIASES:
        return PLATFORM_ALIASES[key]
    print(f"未知平台: {name}", file=sys.stderr)
    print(f"支持: {', '.join(sorted(set(PLATFORM_ALIASES.values())))}", file=sys.stderr)
    sys.exit(1)


def next_id(data):
    articles = data.get("articles", [])
    return max((a["id"] for a in articles), default=0) + 1


# ── 命令 ──────────────────────────────────────────────

def cmd_plan(args):
    data, d = ensure_daily(args.date)
    for item in args.targets:
        if ":" not in item:
            print(f"格式错误: {item}  (应为 平台:数量，如 小红书:3)", file=sys.stderr)
            sys.exit(1)
        platform_raw, count_str = item.rsplit(":", 1)
        platform = resolve_platform(platform_raw)
        try:
            count = int(count_str)
        except ValueError:
            print(f"数量必须是整数: {count_str}", file=sys.stderr)
            sys.exit(1)
        data["plan"][platform] = count

    save_daily(data, d)

    if args.json:
        print(json.dumps(data["plan"], ensure_ascii=False))
        return
    print(f"OK  {d} 计划已设置:")
    for p, c in data["plan"].items():
        print(f"  {PLATFORM_DISPLAY.get(p, p)}: {c} 篇")


def cmd_add(args):
    data, d = ensure_daily(args.date)
    platform = resolve_platform(args.platform)
    now = datetime.now().strftime("%H:%M")

    article = {
        "id": next_id(data),
        "platform": platform,
        "topic": args.topic,
        "title": args.title,
        "status": args.status or "topic",
        "output_file": args.output,
        "notes": args.notes or "",
        "created_at": now,
        "updated_at": now,
    }
    data.setdefault("articles", []).append(article)
    save_daily(data, d)

    if args.json:
        print(json.dumps(article, ensure_ascii=False))
        return
    print(f"OK  #{article['id']} [{PLATFORM_DISPLAY.get(platform, platform)}] {args.topic}")


def cmd_update(args):
    data, d = ensure_daily(args.date)
    if not data:
        print(f"未找到 {d} 的记录", file=sys.stderr)
        sys.exit(1)

    article = next((a for a in data.get("articles", []) if a["id"] == args.id), None)
    if not article:
        print(f"未找到 #{args.id}", file=sys.stderr)
        sys.exit(1)

    if args.status not in STATUSES:
        print(f"无效状态: {args.status}  (可选: {', '.join(STATUSES)})", file=sys.stderr)
        sys.exit(1)

    old = article["status"]
    article["status"] = args.status
    article["updated_at"] = datetime.now().strftime("%H:%M")
    if args.title:
        article["title"] = args.title
    if args.output:
        article["output_file"] = args.output
    if args.notes:
        article["notes"] = args.notes

    save_daily(data, d)

    if args.json:
        print(json.dumps(article, ensure_ascii=False))
        return
    print(f"OK  #{args.id} {STATUS_DISPLAY[old]} -> {STATUS_DISPLAY[args.status]}")


def cmd_status(args):
    d = args.date or date.today().isoformat()
    data = load_daily(d)
    if not data:
        if args.json:
            print(json.dumps({"date": d, "exists": False}, ensure_ascii=False))
        else:
            print(f"未找到 {d} 的计划")
            print(f"  python3 scripts/daily.py plan 小红书:3 头条:2 推特:2")
        return

    plan = data.get("plan", {})
    articles = data.get("articles", [])

    if args.json:
        summary = {
            "date": d,
            "plan": plan,
            "total": len(articles),
            "by_status": {},
            "by_platform": {},
            "articles": articles,
        }
        for s in STATUSES:
            c = sum(1 for a in articles if a["status"] == s)
            if c:
                summary["by_status"][s] = c
        for p in set(a["platform"] for a in articles):
            done = sum(1 for a in articles if a["platform"] == p
                       and STATUSES.index(a["status"]) >= STATUSES.index("draft"))
            summary["by_platform"][p] = {
                "done": done,
                "target": plan.get(p, 0),
                "total": sum(1 for a in articles if a["platform"] == p),
            }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    # ── 文本输出 ──
    sep = "-" * 52
    print(f"\n{sep}")
    print(f"  {d}  每日内容计划")
    print(sep)

    # 平台进度
    if plan:
        print()
        for platform, target in plan.items():
            name = PLATFORM_DISPLAY.get(platform, platform)
            done = sum(1 for a in articles if a["platform"] == platform
                       and STATUSES.index(a["status"]) >= STATUSES.index("draft"))
            total = sum(1 for a in articles if a["platform"] == platform)
            bar_len = 10
            filled = min(int(bar_len * done / target), bar_len) if target > 0 else 0
            bar = "#" * filled + "." * (bar_len - filled)
            print(f"  {name:<8} [{bar}] {done}/{target}  (选题 {total})")

    # 文章列表
    if articles:
        print(f"\n{sep}")
        print(f"  {'ID':<4} {'平台':<10} {'状态':<8} {'选题/标题'}")
        print(sep)
        for a in articles:
            pname = PLATFORM_DISPLAY.get(a["platform"], a["platform"])
            si = STATUS_ICONS.get(a["status"], "?")
            sd = STATUS_DISPLAY.get(a["status"], a["status"])
            title = a.get("title") or a.get("topic", "-")
            print(f"  {a['id']:<4} {pname:<10} [{si}]{sd:<6} {title}")
            if a.get("output_file"):
                print(f"       -> {a['output_file']}")
            if a.get("notes"):
                print(f"       // {a['notes']}")
    else:
        print(f"\n  暂无文章")
        print(f"  python3 scripts/daily.py add 小红书 \"选题\"")

    # 汇总
    print(f"\n{sep}")
    parts = []
    for s in STATUSES:
        c = sum(1 for a in articles if a["status"] == s)
        if c:
            parts.append(f"{STATUS_DISPLAY[s]} {c}")
    total = len(articles)
    line = f"  共 {total} 篇"
    if parts:
        line += "  |  " + " / ".join(parts)
    print(line)
    print()


# ── 入口 ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="每日内容矩阵管理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="状态流转: topic -> draft -> reviewed -> ready -> published",
    )
    parser.add_argument("-d", "--date", help="指定日期 (YYYY-MM-DD)，默认今天")
    parser.add_argument("--json", action="store_true", help="JSON 输出（供 Agent 消费）")

    sub = parser.add_subparsers(dest="command")

    # plan
    p = sub.add_parser("plan", help="设置每日计划 (平台:数量 ...)")
    p.add_argument("targets", nargs="+", help="如 小红书:3 头条:2 推特:2")

    # add
    p = sub.add_parser("add", help="添加文章选题")
    p.add_argument("platform", help="平台")
    p.add_argument("topic", help="选题描述")
    p.add_argument("-t", "--title", help="标题（可后续补充）")
    p.add_argument("-o", "--output", help="输出文件路径")
    p.add_argument("-s", "--status", help="初始状态（默认 topic）")
    p.add_argument("-n", "--notes", help="备注")

    # update
    p = sub.add_parser("update", help="更新文章状态")
    p.add_argument("id", type=int, help="文章 ID")
    p.add_argument("status", help="目标状态")
    p.add_argument("-t", "--title", help="更新标题")
    p.add_argument("-o", "--output", help="更新输出文件")
    p.add_argument("-n", "--notes", help="更新备注")

    # status
    sub.add_parser("status", help="查看状态（默认命令）")

    args = parser.parse_args()

    handlers = {"plan": cmd_plan, "add": cmd_add, "update": cmd_update}
    handlers.get(args.command, cmd_status)(args)


if __name__ == "__main__":
    main()
