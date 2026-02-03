#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多语言/跨地区视频采集脚本
采集同一话题在不同语言市场的表现，发现跨境内容机会

设计思路：
1. 定义话题的多语言关键词映射
2. 按语言+地区组合采集
3. 保存时标记语言和地区
4. 支持对比分析

使用方法:
    python3 scripts/collect_multilang.py                    # 采集所有语言
    python3 scripts/collect_multilang.py --lang en ja       # 只采集英语和日语
    python3 scripts/collect_multilang.py --topic 太极       # 只采集太极相关
    python3 scripts/collect_multilang.py --analyze          # 分析已采集数据
"""

import argparse
import json
import sqlite3
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 路径配置
DB_PATH = Path(__file__).parent.parent / "data" / "youtube_pipeline.db"

# ============================================================
# 多语言关键词映射表
# ============================================================
TOPIC_TRANSLATIONS = {
    "八段锦": {
        "zh": ["八段锦", "8段锦"],
        "en": ["Baduanjin", "Eight Brocades", "Eight Silk Movements", "Ba Duan Jin"],
        "ja": ["八段錦", "バドゥアンジン", "はちだんきん"],
        "ko": ["팔단금", "8단금"],
        "vi": ["Bát Đoạn Cẩm", "bat doan cam"],
    },
    "太极": {
        "zh": ["太极", "太極", "太极拳", "太極拳"],
        "en": ["Tai Chi", "Taiji", "Tai Chi Chuan", "Taijiquan"],
        "ja": ["太極拳", "タイチー", "たいきょくけん"],
        "ko": ["태극권", "타이치"],
        "vi": ["Thái Cực Quyền", "thai cuc quyen"],
    },
    "气功": {
        "zh": ["气功", "氣功"],
        "en": ["Qigong", "Chi Kung", "Qi Gong"],
        "ja": ["気功", "きこう"],
        "ko": ["기공", "치공"],
        "vi": ["Khí công", "khi cong"],
    },
    "穴位按摩": {
        "zh": ["穴位按摩", "穴位", "按摩穴位"],
        "en": ["Acupressure", "Pressure Points Massage", "Acupoint Massage"],
        "ja": ["ツボ押し", "指圧", "つぼ押し", "経穴マッサージ"],
        "ko": ["지압", "경혈 마사지", "혈자리 마사지"],
        "vi": ["bấm huyệt", "massage huyệt đạo"],
    },
    "中医养生": {
        "zh": ["中医养生", "中醫養生", "中医"],
        "en": ["Traditional Chinese Medicine", "TCM Health", "Chinese Medicine"],
        "ja": ["中医学", "漢方", "東洋医学"],
        "ko": ["한의학", "중의학", "한방"],
        "vi": ["Đông y", "y học cổ truyền Trung Quốc"],
    },
    "冥想": {
        "zh": ["冥想", "打坐", "静坐"],
        "en": ["Meditation", "Mindfulness", "Guided Meditation"],
        "ja": ["瞑想", "めいそう", "マインドフルネス"],
        "ko": ["명상", "마음챙김"],
        "vi": ["thiền", "thiền định"],
    },
}

# 语言配置（语言代码 -> 搜索配置）
LANGUAGE_CONFIG = {
    "zh": {
        "name": "中文",
        "geo": "TW",  # 默认台湾
        "relevance_language": "zh-Hant",
    },
    "en": {
        "name": "英语",
        "geo": "US",
        "relevance_language": "en",
    },
    "ja": {
        "name": "日语",
        "geo": "JP",
        "relevance_language": "ja",
    },
    "ko": {
        "name": "韩语",
        "geo": "KR",
        "relevance_language": "ko",
    },
    "vi": {
        "name": "越南语",
        "geo": "VN",
        "relevance_language": "vi",
    },
}


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_multilang_table():
    """创建多语言视频表"""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS multilang_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            youtube_id TEXT NOT NULL,

            -- 基础信息
            title TEXT,
            channel_name TEXT,
            channel_id TEXT,

            -- 统计数据
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            duration INTEGER,

            -- 多语言标记
            language TEXT NOT NULL,          -- 语言代码 (en/ja/ko/vi/zh)
            geo TEXT,                        -- 地区代码 (US/JP/KR/VN/TW)
            topic TEXT NOT NULL,             -- 原始话题 (八段锦/太极/etc)
            search_keyword TEXT,             -- 实际搜索词

            -- 时间
            published_at TIMESTAMP,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(youtube_id, language)
        )
    """)

    # 索引
    c.execute("CREATE INDEX IF NOT EXISTS idx_ml_language ON multilang_videos(language)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ml_topic ON multilang_videos(topic)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ml_views ON multilang_videos(view_count DESC)")

    conn.commit()
    conn.close()
    print("✓ multilang_videos 表已初始化")


def search_videos(keyword: str, lang: str, geo: str, max_results: int = 50) -> List[Dict]:
    """
    使用 yt-dlp 搜索视频

    Args:
        keyword: 搜索关键词
        lang: 语言代码
        geo: 地区代码
        max_results: 最大结果数

    Returns:
        视频列表
    """
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--no-warnings",
            "--geo-bypass-country", geo,
            f"ytsearch{max_results}:{keyword}"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            return []

        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                data = json.loads(line)
                videos.append({
                    "youtube_id": data.get("id"),
                    "title": data.get("title"),
                    "channel_name": data.get("channel") or data.get("uploader"),
                    "channel_id": data.get("channel_id") or data.get("uploader_id"),
                    "view_count": data.get("view_count") or 0,
                    "like_count": data.get("like_count") or 0,
                    "duration": data.get("duration") or 0,
                })
            except json.JSONDecodeError:
                continue

        return videos

    except subprocess.TimeoutExpired:
        return []
    except Exception as e:
        print(f"  搜索失败: {e}")
        return []


def save_videos(videos: List[Dict], language: str, geo: str,
                topic: str, search_keyword: str):
    """保存视频到数据库"""
    if not videos:
        return 0

    conn = get_connection()
    c = conn.cursor()

    saved = 0
    for v in videos:
        try:
            c.execute("""
                INSERT INTO multilang_videos
                (youtube_id, title, channel_name, channel_id, view_count,
                 like_count, duration, language, geo, topic, search_keyword)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(youtube_id, language) DO UPDATE SET
                    view_count = excluded.view_count,
                    like_count = excluded.like_count
            """, (
                v["youtube_id"], v["title"], v["channel_name"], v["channel_id"],
                v["view_count"], v["like_count"], v["duration"],
                language, geo, topic, search_keyword
            ))
            saved += 1
        except sqlite3.Error:
            continue

    conn.commit()
    conn.close()
    return saved


def collect_topic_multilang(topic: str, languages: List[str],
                            max_per_keyword: int = 30) -> Dict:
    """
    采集单个话题的多语言数据

    Args:
        topic: 话题名称（中文）
        languages: 要采集的语言列表
        max_per_keyword: 每个关键词最大采集数

    Returns:
        采集统计
    """
    if topic not in TOPIC_TRANSLATIONS:
        print(f"  未知话题: {topic}")
        return {"error": "unknown topic"}

    translations = TOPIC_TRANSLATIONS[topic]
    stats = {"topic": topic, "languages": {}}

    for lang in languages:
        if lang not in translations:
            continue

        config = LANGUAGE_CONFIG.get(lang, {"name": lang, "geo": "US"})
        keywords = translations[lang]
        geo = config["geo"]

        lang_total = 0

        for keyword in keywords[:3]:  # 每种语言最多3个关键词
            print(f"  搜索: [{lang}] {keyword} (geo={geo})")

            videos = search_videos(keyword, lang, geo, max_per_keyword)
            saved = save_videos(videos, lang, geo, topic, keyword)

            lang_total += saved
            time.sleep(2)  # 请求间隔

        stats["languages"][lang] = lang_total
        print(f"  [{config['name']}] 保存 {lang_total} 条")

    return stats


def analyze_multilang_data():
    """分析多语言数据"""
    conn = get_connection()
    c = conn.cursor()

    print("\n" + "=" * 70)
    print("多语言数据分析")
    print("=" * 70)

    # 1. 各语言数据量
    print("\n一、各语言数据量")
    c.execute("""
        SELECT language, COUNT(*) as videos,
               ROUND(AVG(view_count)) as avg_views,
               MAX(view_count) as max_views
        FROM multilang_videos
        GROUP BY language
        ORDER BY avg_views DESC
    """)

    print(f"{'语言':<8} {'视频数':<10} {'均播放':<15} {'最高播放':<15}")
    print("-" * 50)
    for row in c.fetchall():
        lang_name = LANGUAGE_CONFIG.get(row[0], {}).get("name", row[0])
        print(f"{lang_name:<8} {row[1]:<10} {row[2] or 0:<15,.0f} {row[3] or 0:<15,}")

    # 2. 各话题跨语言表现
    print("\n二、各话题跨语言表现")
    c.execute("""
        SELECT topic, language, COUNT(*) as videos,
               ROUND(AVG(view_count)) as avg_views
        FROM multilang_videos
        GROUP BY topic, language
        ORDER BY topic, avg_views DESC
    """)

    current_topic = None
    for row in c.fetchall():
        if row[0] != current_topic:
            current_topic = row[0]
            print(f"\n【{current_topic}】")
        lang_name = LANGUAGE_CONFIG.get(row[1], {}).get("name", row[1])
        print(f"  {lang_name}: {row[2]}条, 均播{row[3] or 0:,.0f}")

    # 3. 跨语言内容缺口
    print("\n三、跨语言内容缺口机会")
    c.execute("""
        SELECT topic,
               SUM(CASE WHEN language = 'zh' THEN view_count ELSE 0 END) as zh_views,
               SUM(CASE WHEN language = 'en' THEN view_count ELSE 0 END) as en_views,
               SUM(CASE WHEN language = 'ja' THEN view_count ELSE 0 END) as ja_views,
               COUNT(DISTINCT CASE WHEN language = 'zh' THEN youtube_id END) as zh_count,
               COUNT(DISTINCT CASE WHEN language = 'en' THEN youtube_id END) as en_count,
               COUNT(DISTINCT CASE WHEN language = 'ja' THEN youtube_id END) as ja_count
        FROM multilang_videos
        GROUP BY topic
    """)

    print(f"{'话题':<12} {'中文':<15} {'英语':<15} {'日语':<15}")
    print("-" * 60)
    for row in c.fetchall():
        zh = f"{row[4]}条/{row[1] or 0:,.0f}播"
        en = f"{row[5]}条/{row[2] or 0:,.0f}播"
        ja = f"{row[6]}条/{row[3] or 0:,.0f}播"
        print(f"{row[0]:<12} {zh:<15} {en:<15} {ja:<15}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="多语言视频采集")
    parser.add_argument("--lang", nargs="+", default=None,
                        help="指定语言 (en ja ko vi zh)")
    parser.add_argument("--topic", nargs="+", default=None,
                        help="指定话题 (八段锦 太极 气功 穴位按摩 中医养生 冥想)")
    parser.add_argument("--max", type=int, default=30,
                        help="每关键词最大采集数 (默认30)")
    parser.add_argument("--analyze", action="store_true",
                        help="分析已采集数据")
    parser.add_argument("--list", action="store_true",
                        help="列出支持的语言和话题")
    args = parser.parse_args()

    # 列出配置
    if args.list:
        print("支持的语言:")
        for code, config in LANGUAGE_CONFIG.items():
            print(f"  {code}: {config['name']} (geo={config['geo']})")
        print("\n支持的话题:")
        for topic in TOPIC_TRANSLATIONS.keys():
            print(f"  {topic}")
        return

    # 分析模式
    if args.analyze:
        analyze_multilang_data()
        return

    # 初始化
    init_multilang_table()

    # 确定采集范围
    languages = args.lang or ["en", "ja"]  # 默认英语和日语
    topics = args.topic or list(TOPIC_TRANSLATIONS.keys())

    print("=" * 70)
    print("多语言视频采集")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"\n语言: {', '.join(languages)}")
    print(f"话题: {', '.join(topics)}")
    print(f"每关键词最大: {args.max} 条")

    # 开始采集
    all_stats = []
    for topic in topics:
        print(f"\n{'='*60}")
        print(f"采集话题: {topic}")
        print("=" * 60)

        stats = collect_topic_multilang(topic, languages, args.max)
        all_stats.append(stats)

        time.sleep(3)  # 话题间休息

    # 输出汇总
    print("\n" + "=" * 70)
    print("采集完成汇总")
    print("=" * 70)

    for s in all_stats:
        if "error" in s:
            continue
        print(f"\n{s['topic']}:")
        for lang, count in s.get("languages", {}).items():
            lang_name = LANGUAGE_CONFIG.get(lang, {}).get("name", lang)
            print(f"  {lang_name}: {count} 条")

    print("\n下一步:")
    print("  分析数据: python3 scripts/collect_multilang.py --analyze")


if __name__ == "__main__":
    main()
