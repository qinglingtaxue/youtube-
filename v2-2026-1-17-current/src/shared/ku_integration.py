"""
知识单元检测集成示例

展示如何将多维检测管线集成到现有的数据采集流程中

使用方式：
    # 1. 在采集后立即检测
    from src.shared.ku_integration import VideoKUProcessor

    processor = VideoKUProcessor()
    results = processor.process_videos(videos)

    # 2. 批量处理
    passed, failed = processor.process_batch(videos)

    # 3. 查看检测报告
    report = processor.generate_report()
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.shared.knowledge_unit import (
    KnowledgeUnit,
    KnowledgeUnitStatus,
    DetectionResult,
)
from src.shared.detectors import (
    create_video_pipeline,
    create_pattern_pipeline,
    create_insight_pipeline,
)
from src.shared.models import CompetitorVideo

logger = logging.getLogger(__name__)


# ============================================================
# 转换器：将现有模型转换为知识单元
# ============================================================


def video_to_ku(video: CompetitorVideo) -> KnowledgeUnit:
    """
    将 CompetitorVideo 转换为知识单元

    Args:
        video: CompetitorVideo 实例

    Returns:
        KnowledgeUnit 实例
    """
    # 计算互动率
    views = video.view_count or 0
    likes = video.like_count or 0
    comments = video.comment_count or 0
    engagement_rate = (likes + comments) / views * 100 if views > 0 else 0

    return KnowledgeUnit(
        ku_id=video.youtube_id or f"video_{id(video)}",
        ku_type="video",
        source="yt-dlp",
        source_id=video.youtube_id,
        metadata={
            "youtube_id": video.youtube_id,
            "title": video.title,
            "description": video.description,
            "channel_name": video.channel_name,
            "channel_id": video.channel_id,
            "view_count": video.view_count,
            "like_count": video.like_count,
            "comment_count": video.comment_count,
            "duration": video.duration,
            "published_at": video.published_at,
            "subscriber_count": video.subscriber_count,
            "engagement_rate": engagement_rate,
            "keyword_source": video.keyword_source,
            "theme": video.theme,
            "quadrant": None,  # 待分析填充
        }
    )


def ku_to_video(ku: KnowledgeUnit) -> CompetitorVideo:
    """
    将知识单元转换回 CompetitorVideo

    Args:
        ku: KnowledgeUnit 实例

    Returns:
        CompetitorVideo 实例
    """
    meta = ku.metadata

    video = CompetitorVideo(
        youtube_id=meta.get("youtube_id", ""),
        title=meta.get("title", ""),
        description=meta.get("description"),
        channel_name=meta.get("channel_name", ""),
        channel_id=meta.get("channel_id"),
        view_count=meta.get("view_count", 0),
        like_count=meta.get("like_count"),
        comment_count=meta.get("comment_count"),
        duration=meta.get("duration"),
        published_at=meta.get("published_at"),
        subscriber_count=meta.get("subscriber_count"),
        keyword_source=meta.get("keyword_source", ""),
        theme=meta.get("theme"),
    )

    # 附加检测结果
    video._quality_score = ku.quality_score
    video._confidence = ku.confidence
    video._detection_status = ku.status.value
    video._detection_results = ku.detection_results

    return video


# ============================================================
# 处理器：集成检测管线
# ============================================================


@dataclass
class ProcessingStats:
    """处理统计"""
    total: int = 0
    passed: int = 0
    failed: int = 0
    iterated: int = 0
    by_detector: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def add_result(self, results: Dict[str, DetectionResult]) -> None:
        """添加检测结果统计"""
        for name, result in results.items():
            if name not in self.by_detector:
                self.by_detector[name] = {"passed": 0, "failed": 0}

            if result.passed:
                self.by_detector[name]["passed"] += 1
            else:
                self.by_detector[name]["failed"] += 1


class VideoKUProcessor:
    """
    视频知识单元处理器

    集成检测管线到视频采集流程

    使用示例：
        processor = VideoKUProcessor(strict=True)

        # 处理单个视频
        video, passed, results = processor.process_video(competitor_video)

        # 批量处理
        passed_videos, failed_videos = processor.process_batch(videos)

        # 生成报告
        report = processor.generate_report()
    """

    def __init__(
        self,
        strict: bool = False,
        min_score: float = 0.6,
        max_iterations: int = 2,
        enable_fix: bool = True
    ):
        """
        初始化处理器

        Args:
            strict: 是否使用严格模式
            min_score: 最低通过分数
            max_iterations: 最大迭代次数
            enable_fix: 是否启用自动修复
        """
        self.pipeline = create_video_pipeline(
            strict=strict,
            min_score=min_score,
            max_iterations=max_iterations,
            enable_fix=enable_fix
        )
        self.stats = ProcessingStats()
        self.failed_videos: List[Tuple[CompetitorVideo, Dict[str, DetectionResult]]] = []

    def process_video(
        self,
        video: CompetitorVideo
    ) -> Tuple[CompetitorVideo, bool, Dict[str, DetectionResult]]:
        """
        处理单个视频

        Args:
            video: CompetitorVideo 实例

        Returns:
            (processed_video, passed, detection_results)
        """
        # 转换为知识单元
        ku = video_to_ku(video)

        # 执行检测管线
        processed_ku, passed, results = self.pipeline.process(ku)

        # 更新统计
        self.stats.total += 1
        if passed:
            self.stats.passed += 1
        else:
            self.stats.failed += 1
        if processed_ku.iteration_count > 0:
            self.stats.iterated += 1
        self.stats.add_result(results)

        # 转换回视频
        processed_video = ku_to_video(processed_ku)

        # 记录失败
        if not passed:
            self.failed_videos.append((video, results))

        return processed_video, passed, results

    def process_batch(
        self,
        videos: List[CompetitorVideo],
        on_progress: Optional[callable] = None
    ) -> Tuple[List[CompetitorVideo], List[CompetitorVideo]]:
        """
        批量处理视频

        Args:
            videos: 视频列表
            on_progress: 进度回调 (current, total, video_id, passed)

        Returns:
            (passed_videos, failed_videos)
        """
        passed_videos = []
        failed_videos = []

        for i, video in enumerate(videos):
            processed, passed, results = self.process_video(video)

            if passed:
                passed_videos.append(processed)
            else:
                failed_videos.append(processed)

            if on_progress:
                on_progress(i + 1, len(videos), video.youtube_id, passed)

        return passed_videos, failed_videos

    def generate_report(self) -> Dict[str, Any]:
        """
        生成检测报告

        Returns:
            检测报告字典
        """
        return {
            "summary": {
                "total": self.stats.total,
                "passed": self.stats.passed,
                "failed": self.stats.failed,
                "iterated": self.stats.iterated,
                "pass_rate": f"{self.stats.passed / max(self.stats.total, 1) * 100:.1f}%",
            },
            "by_detector": self.stats.by_detector,
            "common_failures": self._analyze_common_failures(),
            "recommendations": self._generate_recommendations(),
        }

    def _analyze_common_failures(self) -> List[Dict[str, Any]]:
        """分析常见失败原因"""
        if not self.failed_videos:
            return []

        failure_counts: Dict[str, int] = {}

        for video, results in self.failed_videos:
            for name, result in results.items():
                if not result.passed:
                    key = f"{name}: {result.message}"
                    failure_counts[key] = failure_counts.get(key, 0) + 1

        # 排序返回 Top 5
        sorted_failures = sorted(
            failure_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return [
            {"reason": reason, "count": count}
            for reason, count in sorted_failures
        ]

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 根据统计生成建议
        if self.stats.total > 0:
            pass_rate = self.stats.passed / self.stats.total

            if pass_rate < 0.5:
                recommendations.append("通过率较低，建议检查数据源质量")

            if self.stats.iterated > self.stats.total * 0.3:
                recommendations.append("迭代次数较多，建议优化采集策略")

        # 根据检测器失败率生成建议
        for detector, stats in self.stats.by_detector.items():
            total = stats["passed"] + stats["failed"]
            if total > 0 and stats["failed"] / total > 0.3:
                if "completeness" in detector:
                    recommendations.append(f"数据完整性问题较多，建议启用详情采集")
                elif "consistency" in detector:
                    recommendations.append(f"数据一致性问题较多，建议检查数据转换逻辑")
                elif "validity" in detector:
                    recommendations.append(f"数据有效性问题较多，建议加强格式校验")
                elif "anomaly" in detector:
                    recommendations.append(f"异常数据较多，建议人工审核")

        return recommendations

    def reset_stats(self) -> None:
        """重置统计"""
        self.stats = ProcessingStats()
        self.failed_videos = []


# ============================================================
# 集成到 DataCollector 的示例
# ============================================================


class EnhancedDataCollector:
    """
    增强版数据收集器

    在原有 DataCollector 基础上集成知识单元检测

    使用示例：
        collector = EnhancedDataCollector()

        # 采集并检测
        results = collector.collect_and_validate(
            keyword="养生",
            max_results=100
        )

        print(f"通过: {len(results['passed'])}")
        print(f"失败: {len(results['failed'])}")
        print(f"报告: {results['report']}")
    """

    def __init__(
        self,
        config=None,
        db_path: Optional[str] = None,
        strict: bool = False,
        min_quality_score: float = 0.6
    ):
        """
        初始化增强版收集器

        Args:
            config: 配置对象
            db_path: 数据库路径
            strict: 是否使用严格检测模式
            min_quality_score: 最低质量分数
        """
        # 延迟导入避免循环依赖
        from src.research.data_collector import DataCollector

        self.collector = DataCollector(config, db_path)
        self.processor = VideoKUProcessor(
            strict=strict,
            min_score=min_quality_score
        )
        self.logger = logging.getLogger(__name__)

    def collect_and_validate(
        self,
        keyword: str,
        max_results: int = 50,
        time_range: str = "month",
        save_passed_only: bool = True
    ) -> Dict[str, Any]:
        """
        采集并验证视频

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            time_range: 时间范围
            save_passed_only: 是否只保存通过检测的视频

        Returns:
            {
                "passed": List[CompetitorVideo],
                "failed": List[CompetitorVideo],
                "report": Dict
            }
        """
        self.logger.info(f"开始采集并验证: keyword={keyword}")

        # 1. 采集视频
        videos_data = self.collector.search_videos(
            keyword=keyword,
            max_results=max_results,
            time_range=time_range
        )

        # 2. 转换为 CompetitorVideo
        videos = []
        for data in videos_data:
            video = CompetitorVideo(
                youtube_id=data.get("youtube_id") or data.get("id", ""),
                title=data.get("title", ""),
                description=data.get("description"),
                channel_name=data.get("channel") or data.get("channel_name", ""),
                channel_id=data.get("channel_id"),
                view_count=data.get("view_count", 0),
                like_count=data.get("like_count"),
                comment_count=data.get("comment_count"),
                duration=data.get("duration"),
                keyword_source=keyword,
            )
            videos.append(video)

        self.logger.info(f"采集到 {len(videos)} 个视频，开始检测...")

        # 3. 批量检测
        passed, failed = self.processor.process_batch(
            videos,
            on_progress=lambda c, t, vid, p: self.logger.debug(
                f"[{c}/{t}] {vid}: {'✓' if p else '✗'}"
            )
        )

        # 4. 可选：只保存通过的
        if save_passed_only and passed:
            # 这里可以调用 repository 保存
            self.logger.info(f"保存 {len(passed)} 个通过检测的视频")

        # 5. 生成报告
        report = self.processor.generate_report()

        self.logger.info(
            f"检测完成: 通过 {len(passed)}, 失败 {len(failed)}, "
            f"通过率 {report['summary']['pass_rate']}"
        )

        return {
            "passed": passed,
            "failed": failed,
            "report": report,
        }

    def collect_large_scale_validated(
        self,
        theme: str,
        target_count: int = 500,
        time_range: str = "month"
    ) -> Dict[str, Any]:
        """
        大规模采集并验证

        Args:
            theme: 主题
            target_count: 目标数量
            time_range: 时间范围

        Returns:
            采集和验证结果
        """
        # 1. 大规模采集
        collect_result = self.collector.collect_large_scale(
            theme=theme,
            target_count=target_count,
            time_range=time_range
        )

        # 2. 从数据库获取采集的视频
        videos = self.collector.get_videos_from_db(
            theme=theme,
            limit=target_count
        )

        # 3. 批量验证
        passed, failed = self.processor.process_batch(videos)

        # 4. 生成报告
        report = self.processor.generate_report()

        return {
            "collection": collect_result,
            "validation": {
                "passed": len(passed),
                "failed": len(failed),
                "report": report,
            }
        }


# ============================================================
# 便捷函数
# ============================================================


def validate_video(video: CompetitorVideo, strict: bool = False) -> Tuple[bool, Dict]:
    """
    快速验证单个视频

    Args:
        video: CompetitorVideo 实例
        strict: 是否严格模式

    Returns:
        (passed, results)
    """
    processor = VideoKUProcessor(strict=strict)
    _, passed, results = processor.process_video(video)
    return passed, {
        name: {"passed": r.passed, "message": r.message, "score": r.score}
        for name, r in results.items()
    }


def validate_videos_batch(
    videos: List[CompetitorVideo],
    strict: bool = False
) -> Dict[str, Any]:
    """
    快速批量验证视频

    Args:
        videos: 视频列表
        strict: 是否严格模式

    Returns:
        验证报告
    """
    processor = VideoKUProcessor(strict=strict)
    passed, failed = processor.process_batch(videos)
    return {
        "passed_count": len(passed),
        "failed_count": len(failed),
        "report": processor.generate_report(),
    }


# ============================================================
# 使用示例
# ============================================================

if __name__ == "__main__":
    # 示例：验证单个视频
    test_video = CompetitorVideo(
        youtube_id="dQw4w9WgXcQ",
        title="Never Gonna Give You Up",
        channel_name="Rick Astley",
        view_count=1500000000,
        like_count=15000000,
        comment_count=3000000,
        duration=213,
    )

    passed, results = validate_video(test_video)
    print(f"视频验证: {'通过' if passed else '失败'}")
    for name, info in results.items():
        status = "✓" if info["passed"] else "✗"
        print(f"  {status} {name}: {info['message']} (score={info['score']:.2f})")
