#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态追踪调度器
定期执行动态追踪任务，与长期模式分析结合
"""

import sys
import schedule
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger
from utils.config import get_config
from utils.file_utils import ensure_dir, write_json
from dynamic_tracker import DynamicTracker
from analysis.pattern_analyzer import PatternAnalyzer

logger = setup_logger('scheduler')

class TrackingScheduler:
    """动态追踪调度器"""

    def __init__(self, config):
        """
        初始化调度器

        Args:
            config: 配置对象
        """
        self.config = config
        self.tracker = DynamicTracker(config)
        self.analyzer = PatternAnalyzer(config)

    def setup_schedule(self):
        """设置调度任务"""
        logger.info("设置动态追踪调度任务")

        # 每小时检查一次热点
        schedule.every().hour.do(self._hourly_trend_check)

        # 每天早上8点生成每日摘要
        schedule.every().day.at("08:00").do(self._daily_digest)

        # 每周一早上9点生成周报
        schedule.every().monday.at("09:00").do(self._weekly_report)

        # 每3天更新一次模式库
        schedule.every(3).days.do(self._update_pattern_library)

        logger.info("调度任务设置完成")

    def _hourly_trend_check(self):
        """每小时趋势检查"""
        logger.info("执行每小时趋势检查")

        try:
            keywords = self.config.get('monitoring.keywords', [])
            if not keywords:
                logger.warning("未配置监控关键词")
                return

            # 快速趋势检查
            trends = self.tracker.track_daily_trends(keywords)

            # 保存趋势数据
            output_dir = Path('output/trends/hourly')
            ensure_dir(output_dir)

            timestamp = datetime.now().strftime('%Y%m%d_%H')
            trend_file = output_dir / f"trends_{timestamp}.json"
            write_json(trend_file, trends)

            # 检查是否发现异常趋势
            self._check_urgent_trends(trends)

            logger.info(f"每小时趋势检查完成: {trend_file}")

        except Exception as e:
            logger.error(f"每小时趋势检查失败: {e}")

    def _daily_digest(self):
        """生成每日摘要"""
        logger.info("生成每日摘要")

        try:
            digest = self.tracker.generate_daily_digest()

            # 保存摘要
            output_dir = Path('output/daily_digest')
            ensure_dir(output_dir)

            digest_file = output_dir / f"digest_{datetime.now().strftime('%Y%m%d')}.md"
            with open(digest_file, 'w', encoding='utf-8') as f:
                f.write(digest)

            logger.info(f"每日摘要已生成: {digest_file}")

        except Exception as e:
            logger.error(f"生成每日摘要失败: {e}")

    def _weekly_report(self):
        """生成周报"""
        logger.info("生成周报")

        try:
            # 获取过去一周的数据
            week_data = self._collect_weekly_data()

            # 生成周报
            report = self._generate_weekly_report(week_data)

            # 保存周报
            output_dir = Path('output/weekly_reports')
            ensure_dir(output_dir)

            week_start = datetime.now() - timedelta(days=7)
            report_file = output_dir / f"weekly_report_{week_start.strftime('%Y%m%d')}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info(f"周报已生成: {report_file}")

        except Exception as e:
            logger.error(f"生成周报失败: {e}")

    def _update_pattern_library(self):
        """更新模式库"""
        logger.info("更新模式库")

        try:
            # 获取最近的数据
            recent_trends = self._load_recent_trends(days=7)
            recent_videos = self._load_recent_videos(days=7)

            # 重新分析模式
            if recent_videos:
                new_patterns = self.analyzer.analyze_videos(recent_videos)

                # 与现有模式对比
                existing_patterns = self._load_existing_patterns()
                updated_patterns = self._merge_patterns(existing_patterns, new_patterns)

                # 保存更新的模式
                output_dir = Path('output/patterns')
                ensure_dir(output_dir)

                pattern_file = output_dir / f"patterns_{datetime.now().strftime('%Y%m%d')}.json"
                write_json(pattern_file, updated_patterns)

                logger.info(f"模式库已更新: {pattern_file}")
                logger.info(f"新增模式: {len(new_patterns)} 个")

        except Exception as e:
            logger.error(f"更新模式库失败: {e}")

    def _check_urgent_trends(self, trends: Dict[str, Any]):
        """检查紧急趋势"""
        urgent_flags = []

        # 检查新兴话题
        for topic in trends.get('emerging_topics', []):
            if topic['growth_rate'] > 5.0:  # 增长率超过500%
                urgent_flags.append(f"🔥 紧急: {topic['keyword']} 增长 {topic['growth_rate']:.1%}")

        # 检查病毒视频
        for video in trends.get('viral_videos', []):
            if video.get('velocity', 0) > 5000:  # 每小时超过5000观看
                urgent_flags.append(f"🚀 病毒视频: {video['title'][:30]}...")

        if urgent_flags:
            logger.warning("发现紧急趋势:")
            for flag in urgent_flags:
                logger.warning(f"  {flag}")

            # 可以在这里添加通知逻辑（如发送邮件、Slack消息等）
            self._send_urgent_alert(urgent_flags)

    def _collect_weekly_data(self) -> Dict[str, Any]:
        """收集周数据"""
        week_data = {
            'start_date': (datetime.now() - timedelta(days=7)).isoformat(),
            'end_date': datetime.now().isoformat(),
            'daily_trends': [],
            'competitor_activity': [],
            'platform_changes': [],
            'summary': {}
        }

        # 加载每日趋势数据
        trend_dir = Path('output/trends/hourly')
        if trend_dir.exists():
            # 获取过去7天的数据文件
            import glob
            pattern = str(trend_dir / "trends_*.json")
            files = glob.glob(pattern)

            for file_path in sorted(files, reverse=True)[:7*24]:  # 最多7天*24小时
                try:
                    import json
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        week_data['daily_trends'].append(data)
                except Exception as e:
                    logger.error(f"加载趋势文件失败 {file_path}: {e}")

        return week_data

    def _generate_weekly_report(self, week_data: Dict[str, Any]) -> str:
        """生成周报"""
        lines = [
            "# YouTube动态追踪周报",
            "",
            f"**报告周期**: {week_data['start_date'][:10]} 至 {week_data['end_date'][:10]}",
            "",
            "## 📊 本周概况",
            ""
        ]

        # 统计概览
        total_trends = len(week_data.get('daily_trends', []))
        if total_trends > 0:
            # 计算平均增长率
            growth_rates = []
            for trend_data in week_data['daily_trends']:
                for keyword, stats in trend_data.get('daily_stats', {}).items():
                    growth_rates.append(stats.get('growth_rate', 0))

            avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0

            lines.extend([
                f"- **追踪天数**: {total_trends // 24} 天",
                f"- **平均增长率**: {avg_growth:.1%}",
                f"- **新兴话题**: {len([t for t in week_data['daily_trends'] for topic in t.get('emerging_topics', [])])} 个",
                f"- **病毒视频**: {len([t for t in week_data['daily_trends'] for video in t.get('viral_videos', [])])} 个",
                ""
            ])

        # 热点话题排行
        lines.extend([
            "## 🔥 本周热点话题",
            ""
        ])

        # 统计各话题出现次数
        topic_counts = {}
        for trend_data in week_data['daily_trends']:
            for topic in trend_data.get('emerging_topics', []):
                keyword = topic['keyword']
                topic_counts[keyword] = topic_counts.get(keyword, 0) + 1

        # 排序并显示
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (topic, count) in enumerate(sorted_topics, 1):
            lines.append(f"{i}. **{topic}**: 出现 {count} 次")

        lines.append("")

        # 模式变化分析
        lines.extend([
            "## 🔄 模式变化分析",
            "",
            "### 长期稳定模式",
            "- 知识付费的核心需求未变",
            "- 用户对"实用技能"内容需求稳定",
            "- 高质量教程仍有持续吸引力",
            "",
            "### 新兴模式",
            "- AI相关话题热度持续上升",
            "- 短视频+长视频组合模式兴起",
            "- 互动式教学内容更受欢迎",
            "",
        ])

        # 下周预测
        lines.extend([
            "## 🔮 下周预测",
            "",
            "### 潜在热点",
            "1. **技术类教程**: 预计持续热度",
            "2. **AI应用分享**: 可能成为新增长点",
            "3. **效率工具**: 可能有小幅增长",
            "",
            "### 风险提示",
            "1. 避免过度依赖单一话题",
            "2. 关注平台政策变化",
            "3. 竞品可能加大投入",
            "",
        ])

        # 行动建议
        lines.extend([
            "## 💡 行动建议",
            "",
            "### 内容创作",
            "- 继续深耕技术教程领域",
            "- 尝试AI+传统技能的组合",
            "- 增加互动式内容比例",
            "",
            "### 策略调整",
            "- 保持每日发布频率",
            "- 关注竞品创新点",
            "- 准备2-3个备用话题",
            "",
            "### 模式优化",
            "- 基于新数据更新内容模板",
            "- 调整发布时间策略",
            "- 优化标签和关键词使用",
            ""
        ])

        return '\n'.join(lines)

    def _load_recent_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """加载最近趋势数据"""
        trends_dir = Path('output/trends/hourly')
        if not trends_dir.exists():
            return []

        import glob
        import json

        pattern = str(trends_dir / "trends_*.json")
        files = glob.glob(pattern)

        # 获取最近N天的文件
        cutoff = datetime.now() - timedelta(days=days)
        recent_files = []

        for file_path in files:
            try:
                # 从文件名提取日期
                filename = Path(file_path).stem  # 如 trends_20241209_14
                date_str = filename.split('_')[1] + '_' + filename.split('_')[2]
                file_date = datetime.strptime(date_str, '%Y%m%d_%H')

                if file_date >= cutoff:
                    recent_files.append(file_path)
            except Exception:
                continue

        # 加载数据
        recent_trends = []
        for file_path in sorted(recent_files, reverse=True):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    recent_trends.append(data)
            except Exception as e:
                logger.error(f"加载趋势文件失败 {file_path}: {e}")

        return recent_trends

    def _load_recent_videos(self, days: int = 7) -> List[Dict[str, Any]]:
        """加载最近视频数据"""
        # 这里应该从数据库或文件中加载
        # 暂时返回空列表
        return []

    def _load_existing_patterns(self) -> List[Dict[str, Any]]:
        """加载现有模式"""
        pattern_dir = Path('output/patterns')
        if not pattern_dir.exists():
            return []

        import glob
        import json

        # 获取最新的模式文件
        pattern_files = glob.glob(str(pattern_dir / "patterns_*.json"))
        if not pattern_files:
            return []

        latest_file = max(pattern_files)
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载现有模式失败: {e}")
            return []

    def _merge_patterns(self, existing: List[Dict[str, Any]], new: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并新旧模式"""
        merged = existing.copy()

        for new_pattern in new:
            # 检查是否已存在相似模式
            found = False
            for existing_pattern in merged:
                if existing_pattern['name'] == new_pattern['name']:
                    # 更新频率和置信度
                    existing_pattern['frequency'] += new_pattern['frequency']
                    existing_pattern['last_updated'] = datetime.now().isoformat()
                    found = True
                    break

            if not found:
                # 添加新模式
                new_pattern['first_seen'] = datetime.now().isoformat()
                new_pattern['last_updated'] = datetime.now().isoformat()
                merged.append(new_pattern)

        # 按频率排序
        merged.sort(key=lambda x: x['frequency'], reverse=True)

        return merged

    def _send_urgent_alert(self, alerts: List[str]):
        """发送紧急通知"""
        logger.warning("紧急趋势通知:")
        for alert in alerts:
            logger.warning(f"  {alert}")

        # 这里可以添加实际的通知逻辑
        # 例如：发送到Slack、邮件、微信等
        # self._send_slack_message(alerts)
        # self._send_email(alerts)

    def run(self):
        """运行调度器"""
        logger.info("启动动态追踪调度器")
        self.setup_schedule()

        # 立即执行一次每日摘要（如果还没执行过）
        now = datetime.now()
        if now.hour >= 8:
            logger.info("今日已过8点，跳过每日摘要执行")
        else:
            logger.info("执行首次每日摘要")
            self._daily_digest()

        # 主循环
        logger.info("调度器运行中，按Ctrl+C停止")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("用户中断，调度器停止")
        except Exception as e:
            logger.error(f"调度器运行出错: {e}")
        finally:
            logger.info("调度器已停止")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("YouTube动态追踪调度器")
    print("=" * 60)
    print("\n功能说明:")
    print("1. 每小时检查趋势变化")
    print("2. 每天早上8点生成摘要")
    print("3. 每周一生成周报")
    print("4. 每3天更新模式库")
    print("\n按 Ctrl+C 停止调度器\n")

    config = get_config()
    scheduler = TrackingScheduler(config)
    scheduler.run()


if __name__ == '__main__':
    main()
