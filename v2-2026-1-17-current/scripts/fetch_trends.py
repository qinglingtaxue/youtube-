#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势数据采集脚本
从 Google Trends 获取搜索热度，与 YouTube 数据对比分析

功能：
1. 采集 Google Trends 搜索趋势
2. 与 YouTube 视频数据对比
3. 发现内容缺口（搜索热但视频少）
4. 发现潜在机会（搜索上升趋势）
5. 多语言/多地区搜索热度对比

使用方法:
    python3 scripts/fetch_trends.py                    # 分析预设话题
    python3 scripts/fetch_trends.py --keywords 减肥 健身  # 自定义话题
    python3 scripts/fetch_trends.py --geo CN           # 指定地区（CN/TW/HK）
    python3 scripts/fetch_trends.py --multilang        # 多语言对比分析
"""

import argparse
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import json

try:
    from pytrends.request import TrendReq
    import pandas as pd
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    pd = None  # type: ignore
    print("警告: pytrends 未安装，运行 'pip install pytrends' 安装")

# 路径配置
DB_PATH = Path(__file__).parent.parent / "data" / "youtube_pipeline.db"

# 预设话题（基于 YouTube 数据库中的热门话题）
DEFAULT_TOPICS = [
    # 养生相关
    "八段锦", "太极拳", "食疗", "穴位按摩", "中医养生",
    "糖尿病", "高血压", "睡眠", "护肝", "补肾",
    # 通用健康
    "减肥", "健身", "瑜伽",
]

# 地区配置
GEO_CONFIG = {
    "TW": {"name": "台湾", "hl": "zh-TW"},
    "HK": {"name": "香港", "hl": "zh-TW"},
    "CN": {"name": "中国大陆", "hl": "zh-CN"},
    "US": {"name": "美国", "hl": "en-US"},
    "JP": {"name": "日本", "hl": "ja"},
    "KR": {"name": "韩国", "hl": "ko"},
    "VN": {"name": "越南", "hl": "vi"},
    "MY": {"name": "马来西亚", "hl": "zh-TW"},
    "SG": {"name": "新加坡", "hl": "en"},
}

# 多语言关键词映射（话题 -> 各语言版本）
MULTILANG_KEYWORDS = {
    "太极": {
        "TW": "太極",
        "US": "Tai Chi",
        "JP": "太極拳",
        "KR": "태극권",
    },
    "八段锦": {
        "TW": "八段錦",
        "US": "Baduanjin",
        "JP": "八段錦",
    },
    "气功": {
        "TW": "氣功",
        "US": "Qigong",
        "JP": "気功",
    },
    "穴位按摩": {
        "TW": "穴位按摩",
        "US": "Acupressure",
        "JP": "ツボ押し",
    },
    "冥想": {
        "TW": "冥想",
        "US": "Meditation",
        "JP": "瞑想",
        "KR": "명상",
    },
}


def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(str(DB_PATH), timeout=30)


def init_trends_table():
    """创建趋势数据表"""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS search_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            geo TEXT NOT NULL,              -- 地区代码
            date TEXT NOT NULL,             -- 日期
            interest INTEGER,               -- 搜索热度 (0-100)

            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(keyword, geo, date)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS trend_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            geo TEXT NOT NULL,

            -- Google Trends 指标
            avg_interest REAL,              -- 平均搜索热度
            trend_direction TEXT,           -- rising/stable/falling
            trend_change_pct REAL,          -- 趋势变化百分比

            -- YouTube 数据对比
            yt_video_count INTEGER,         -- YouTube 视频数
            yt_total_views INTEGER,         -- YouTube 总播放
            yt_avg_views INTEGER,           -- YouTube 均播放

            -- 机会评分
            opportunity_score REAL,         -- 内容缺口评分
            opportunity_reason TEXT,        -- 机会原因

            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(keyword, geo)
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_trends_keyword ON search_trends(keyword)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_trends_date ON search_trends(date)")

    conn.commit()
    conn.close()


def get_youtube_stats(keyword: str) -> Dict:
    """从 YouTube 数据库获取关键词统计"""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*), COALESCE(SUM(view_count), 0), COALESCE(AVG(view_count), 0)
        FROM competitor_videos
        WHERE title LIKE ?
    """, (f"%{keyword}%",))

    row = c.fetchone()
    conn.close()

    return {
        "video_count": row[0],
        "total_views": int(row[1]),
        "avg_views": int(row[2]),
    }


def fetch_google_trends(keywords: List[str], geo: str = "TW",
                        timeframe: str = "today 12-m") -> Optional[pd.DataFrame]:
    """
    获取 Google Trends 数据

    Args:
        keywords: 关键词列表（最多5个）
        geo: 地区代码
        timeframe: 时间范围

    Returns:
        DataFrame with interest over time
    """
    if not PYTRENDS_AVAILABLE:
        return None

    try:
        config = GEO_CONFIG.get(geo, GEO_CONFIG["TW"])
        pytrends = TrendReq(hl=config["hl"], tz=480, timeout=(10, 25))
        pytrends.build_payload(keywords[:5], cat=0, timeframe=timeframe, geo=geo)

        df = pytrends.interest_over_time()
        return df if not df.empty else None

    except Exception as e:
        print(f"  获取 Google Trends 失败: {e}")
        return None


def fetch_related_queries(keyword: str, geo: str = "TW") -> Dict:
    """获取相关搜索词"""
    if not PYTRENDS_AVAILABLE:
        return {"top": [], "rising": []}

    try:
        config = GEO_CONFIG.get(geo, GEO_CONFIG["TW"])
        pytrends = TrendReq(hl=config["hl"], tz=480, timeout=(10, 25))
        pytrends.build_payload([keyword], cat=0, timeframe="today 3-m", geo=geo)

        related = pytrends.related_queries()

        result = {"top": [], "rising": []}

        if related.get(keyword):
            if related[keyword].get("top") is not None:
                result["top"] = related[keyword]["top"].head(10).to_dict("records")
            if related[keyword].get("rising") is not None:
                result["rising"] = related[keyword]["rising"].head(10).to_dict("records")

        return result

    except Exception:
        return {"top": [], "rising": []}


def analyze_trend(df: pd.DataFrame, keyword: str) -> Dict:
    """分析趋势方向和变化"""
    if df is None or keyword not in df.columns:
        return {"avg": 0, "direction": "unknown", "change_pct": 0}

    series = df[keyword]
    avg = series.mean()

    # 计算趋势（最近4周 vs 之前4周）
    recent = series.tail(4).mean()
    earlier = series.head(4).mean()

    if earlier > 0:
        change_pct = (recent - earlier) / earlier * 100
    else:
        change_pct = 100 if recent > 0 else 0

    if change_pct > 20:
        direction = "rising"
    elif change_pct < -20:
        direction = "falling"
    else:
        direction = "stable"

    return {
        "avg": round(avg, 1),
        "direction": direction,
        "change_pct": round(change_pct, 1),
    }


def calculate_opportunity_score(trend_data: Dict, yt_data: Dict) -> tuple:
    """
    计算内容缺口机会评分

    评分逻辑：
    - 搜索热度高 + 视频少 = 高机会
    - 搜索上升 + 视频少 = 高机会
    - 搜索热度高 + 视频均播低 = 中机会
    """
    score = 0
    reasons = []

    avg_interest = trend_data.get("avg", 0)
    direction = trend_data.get("direction", "unknown")
    change_pct = trend_data.get("change_pct", 0)

    video_count = yt_data.get("video_count", 0)
    avg_views = yt_data.get("avg_views", 0)

    # 搜索热度评分 (0-40分)
    if avg_interest >= 50:
        score += 40
        reasons.append(f"搜索热度高({avg_interest})")
    elif avg_interest >= 20:
        score += 20
        reasons.append(f"搜索热度中({avg_interest})")

    # 趋势方向评分 (0-30分)
    if direction == "rising" and change_pct > 50:
        score += 30
        reasons.append(f"快速上升({change_pct:+.0f}%)")
    elif direction == "rising":
        score += 20
        reasons.append(f"上升趋势({change_pct:+.0f}%)")
    elif direction == "falling":
        score -= 10
        reasons.append(f"下降趋势({change_pct:+.0f}%)")

    # 内容缺口评分 (0-30分)
    if video_count < 10 and avg_interest > 10:
        score += 30
        reasons.append(f"视频稀缺({video_count}条)")
    elif video_count < 50 and avg_interest > 20:
        score += 15
        reasons.append(f"视频较少({video_count}条)")

    # 竞争强度惩罚
    if video_count > 100 and avg_views < 10000:
        score -= 20
        reasons.append("竞争激烈但表现一般")

    return max(0, min(100, score)), "; ".join(reasons) if reasons else "无明显机会"


def save_analysis(keyword: str, geo: str, trend_data: Dict,
                  yt_data: Dict, score: float, reason: str):
    """保存分析结果"""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO trend_analysis
        (keyword, geo, avg_interest, trend_direction, trend_change_pct,
         yt_video_count, yt_total_views, yt_avg_views,
         opportunity_score, opportunity_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(keyword, geo) DO UPDATE SET
            avg_interest = excluded.avg_interest,
            trend_direction = excluded.trend_direction,
            trend_change_pct = excluded.trend_change_pct,
            yt_video_count = excluded.yt_video_count,
            yt_total_views = excluded.yt_total_views,
            yt_avg_views = excluded.yt_avg_views,
            opportunity_score = excluded.opportunity_score,
            opportunity_reason = excluded.opportunity_reason,
            analyzed_at = CURRENT_TIMESTAMP
    """, (
        keyword, geo,
        trend_data.get("avg", 0),
        trend_data.get("direction", "unknown"),
        trend_data.get("change_pct", 0),
        yt_data.get("video_count", 0),
        yt_data.get("total_views", 0),
        yt_data.get("avg_views", 0),
        score, reason,
    ))

    conn.commit()
    conn.close()


def analyze_multilang_trends():
    """多语言搜索热度对比分析"""
    print("=" * 70)
    print("多语言 Google Trends 搜索热度对比")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    results = []

    for topic_zh, lang_keywords in MULTILANG_KEYWORDS.items():
        print(f"\n【{topic_zh}】")
        print("-" * 50)

        topic_results = {"topic": topic_zh, "regions": {}}

        for geo, keyword in lang_keywords.items():
            if geo not in GEO_CONFIG:
                continue

            config = GEO_CONFIG[geo]
            try:
                pytrends = TrendReq(hl=config["hl"], tz=480, timeout=(10, 25))
                pytrends.build_payload([keyword], cat=0, timeframe="today 12-m", geo=geo)
                df = pytrends.interest_over_time()

                if not df.empty and keyword in df.columns:
                    avg = df[keyword].mean()
                    recent = df[keyword].tail(4).mean()
                    earlier = df[keyword].head(4).mean()
                    change = ((recent - earlier) / earlier * 100) if earlier > 0 else 0
                    trend = "↑" if change > 20 else ("↓" if change < -20 else "→")

                    print(f"  {config['name']}: \"{keyword}\" = {avg:.1f} ({trend}{change:+.0f}%)")

                    topic_results["regions"][geo] = {
                        "keyword": keyword,
                        "interest": round(avg, 1),
                        "change_pct": round(change, 1),
                        "trend": trend,
                    }
                else:
                    print(f"  {config['name']}: \"{keyword}\" = 无数据")

                time.sleep(2)
            except Exception as e:
                print(f"  {config['name']}: 获取失败 - {str(e)[:30]}")
                time.sleep(3)

        results.append(topic_results)

    # 输出汇总表格
    print("\n" + "=" * 70)
    print("多语言搜索热度汇总")
    print("=" * 70)
    print(f"\n{'话题':<10} {'台湾':<15} {'美国':<15} {'日本':<15} {'韩国':<15}")
    print("-" * 70)

    for r in results:
        row = [r["topic"]]
        for geo in ["TW", "US", "JP", "KR"]:
            if geo in r["regions"]:
                data = r["regions"][geo]
                row.append(f"{data['interest']:.0f} {data['trend']}{data['change_pct']:+.0f}%")
            else:
                row.append("-")
        print(f"{row[0]:<10} {row[1]:<15} {row[2]:<15} {row[3]:<15} {row[4]:<15}")

    # 识别跨语言机会
    print("\n" + "=" * 70)
    print("跨语言内容机会")
    print("=" * 70)

    for r in results:
        regions = r["regions"]
        if len(regions) < 2:
            continue

        # 找出热度最高和最低的地区
        sorted_regions = sorted(regions.items(), key=lambda x: x[1]["interest"], reverse=True)
        top = sorted_regions[0]
        bottom = sorted_regions[-1]

        if top[1]["interest"] > 50 and bottom[1]["interest"] < 20:
            print(f"\n  {r['topic']}:")
            print(f"    高需求市场: {GEO_CONFIG[top[0]]['name']} ({top[1]['interest']:.0f})")
            print(f"    低竞争市场: {GEO_CONFIG[bottom[0]]['name']} ({bottom[1]['interest']:.0f})")

        # 找出上升最快的市场
        rising = [(geo, data) for geo, data in regions.items() if data["change_pct"] > 50]
        if rising:
            for geo, data in rising:
                print(f"    快速上升: {GEO_CONFIG[geo]['name']} ({data['trend']}{data['change_pct']:+.0f}%)")

    print("\n" + "=" * 70)
    return results


def main():
    parser = argparse.ArgumentParser(description="Google Trends 趋势分析")
    parser.add_argument("--keywords", nargs="+", default=None,
                        help="自定义关键词（默认使用预设话题）")
    parser.add_argument("--geo", default="TW", choices=list(GEO_CONFIG.keys()),
                        help="地区代码（默认 TW）")
    parser.add_argument("--timeframe", default="today 12-m",
                        help="时间范围（默认 today 12-m）")
    parser.add_argument("--multilang", action="store_true",
                        help="多语言搜索热度对比分析")
    args = parser.parse_args()

    if not PYTRENDS_AVAILABLE:
        print("错误: 请先安装 pytrends")
        print("运行: pip install pytrends")
        return

    # 多语言模式
    if args.multilang:
        analyze_multilang_trends()
        return

    if not PYTRENDS_AVAILABLE:
        print("错误: 请先安装 pytrends")
        print("运行: pip install pytrends")
        return

    keywords = args.keywords or DEFAULT_TOPICS
    geo = args.geo
    region_name = GEO_CONFIG[geo]["name"]

    print("=" * 70)
    print("Google Trends vs YouTube 数据对比分析")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"地区: {region_name} ({geo})")
    print("=" * 70)

    # 初始化表
    init_trends_table()

    print(f"\n分析话题: {len(keywords)} 个")
    print(f"话题列表: {', '.join(keywords[:5])}...")

    # 分批获取 Google Trends（每批最多5个）
    all_results = []

    for i in range(0, len(keywords), 5):
        batch = keywords[i:i+5]
        print(f"\n正在获取批次 {i//5 + 1}: {batch}")

        df = fetch_google_trends(batch, geo, args.timeframe)

        for kw in batch:
            # Google Trends 数据
            trend_data = analyze_trend(df, kw)

            # YouTube 数据
            yt_data = get_youtube_stats(kw)

            # 计算机会评分
            score, reason = calculate_opportunity_score(trend_data, yt_data)

            # 保存
            save_analysis(kw, geo, trend_data, yt_data, score, reason)

            all_results.append({
                "keyword": kw,
                "google_interest": trend_data["avg"],
                "google_trend": trend_data["direction"],
                "google_change": trend_data["change_pct"],
                "yt_videos": yt_data["video_count"],
                "yt_avg_views": yt_data["avg_views"],
                "opportunity": score,
                "reason": reason,
            })

        if i + 5 < len(keywords):
            time.sleep(2)  # 避免请求过快

    # 输出结果
    print("\n" + "=" * 70)
    print("分析结果")
    print("=" * 70)

    # 按机会评分排序
    all_results.sort(key=lambda x: x["opportunity"], reverse=True)

    print(f"\n{'话题':<12} {'搜索热度':<10} {'趋势':<10} {'YT视频':<10} {'YT均播':<12} {'机会':<6} {'原因'}")
    print("-" * 90)

    for r in all_results:
        trend_icon = {"rising": "↑", "falling": "↓", "stable": "→"}.get(r["google_trend"], "?")
        opp_level = "★★★" if r["opportunity"] >= 60 else ("★★" if r["opportunity"] >= 30 else "★")

        print(f"{r['keyword']:<12} {r['google_interest']:<10.1f} "
              f"{trend_icon} {r['google_change']:+.0f}%{'':4} "
              f"{r['yt_videos']:<10} {r['yt_avg_views']:<12,} "
              f"{opp_level:<6} {r['reason'][:30]}")

    # 输出机会汇总
    high_opp = [r for r in all_results if r["opportunity"] >= 60]
    if high_opp:
        print(f"\n{'='*70}")
        print("高机会话题（评分≥60）")
        print("="*70)
        for r in high_opp:
            print(f"\n  {r['keyword']}")
            print(f"    搜索热度: {r['google_interest']} ({r['google_trend']} {r['google_change']:+.0f}%)")
            print(f"    YouTube: {r['yt_videos']}条视频, 均播{r['yt_avg_views']:,}")
            print(f"    机会原因: {r['reason']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
