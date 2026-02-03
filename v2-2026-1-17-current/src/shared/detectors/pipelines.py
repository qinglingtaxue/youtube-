"""
预定义检测管线

提供开箱即用的检测管线组合：
- 视频管线：完整性 + 一致性 + 有效性 + 异常
- 模式管线：完整性 + 一致性 + 模式有效性
- 洞察管线：完整性 + 一致性 + 有效性

每个管线都包含：
1. 多个检测器并行执行
2. 对齐判定策略
3. 可选的自动修复策略
"""

from typing import Callable, Dict, Optional

from ..knowledge_unit import (
    AlignmentPolicy,
    DetectionPipeline,
    DetectionResult,
    KnowledgeUnit,
    create_pipeline,
)
from .completeness import (
    VideoCompletenessDetector,
    PatternCompletenessDetector,
    InsightCompletenessDetector,
)
from .consistency import (
    VideoConsistencyDetector,
    PatternConsistencyDetector,
)
from .validity import (
    VideoValidityDetector,
    PatternValidityDetector as PatternValidityDetectorBase,
    InsightValidityDetector,
)
from .anomaly import (
    VideoAnomalyDetector,
    PatternAnomalyDetector,
)
from .pattern import PatternValidityDetector


# ============================================================
# 视频检测管线
# ============================================================


def _video_fix_strategy(
    ku: KnowledgeUnit,
    results: Dict[str, DetectionResult]
) -> KnowledgeUnit:
    """
    视频知识单元修复策略

    修复逻辑：
    1. 缺失字段 → 标记为需要重新采集
    2. 异常值 → 标记为需要人工审核
    3. 格式错误 → 尝试自动修正
    """
    meta = ku.metadata

    for name, result in results.items():
        if result.passed:
            continue

        # 完整性问题：标记需要补充
        if "completeness" in name:
            meta["_needs_enrichment"] = True
            meta["_missing_fields"] = result.affected_fields

        # 一致性问题：标记需要审核
        if "consistency" in name:
            meta["_needs_review"] = True
            meta["_consistency_issues"] = result.details.get("failed_rules", [])

        # 异常问题：标记异常
        if "anomaly" in name:
            meta["_has_anomaly"] = True
            meta["_anomalies"] = result.details.get("anomalies", [])

    ku.metadata = meta
    return ku


def create_video_pipeline(
    strict: bool = False,
    min_score: float = 0.6,
    max_iterations: int = 2,
    enable_fix: bool = True
) -> DetectionPipeline[KnowledgeUnit]:
    """
    创建视频检测管线

    检测器组合：
    1. 完整性检测 (权重 1.0)
    2. 一致性检测 (权重 1.0)
    3. 有效性检测 (权重 0.9)
    4. 异常检测 (权重 0.7)

    Args:
        strict: 是否使用严格模式
        min_score: 最低通过分数
        max_iterations: 最大迭代次数
        enable_fix: 是否启用自动修复

    Returns:
        配置好的检测管线

    使用示例：
        pipeline = create_video_pipeline(strict=True)

        video_ku = KnowledgeUnit(
            ku_id="abc123",
            ku_type="video",
            metadata={
                "youtube_id": "dQw4w9WgXcQ",
                "title": "Never Gonna Give You Up",
                "view_count": 1000000,
                ...
            }
        )

        ku, passed, results = pipeline.process(video_ku)

        if passed:
            print("视频数据通过检测")
        else:
            print("检测失败:", results)
    """
    policy = AlignmentPolicy(
        min_score=min_score,
        max_iterations=max_iterations,
        auto_fix=enable_fix,
        allow_warnings=True
    )

    pipeline = DetectionPipeline[KnowledgeUnit](
        name="video_pipeline",
        policy=policy,
        fix_strategy=_video_fix_strategy if enable_fix else None
    )

    # 注册检测器
    completeness = VideoCompletenessDetector(strict=strict)
    completeness.weight = 1.0
    pipeline.register(completeness)

    consistency = VideoConsistencyDetector()
    consistency.weight = 1.0
    pipeline.register(consistency)

    validity = VideoValidityDetector(strict=strict)
    validity.weight = 0.9
    pipeline.register(validity)

    anomaly = VideoAnomalyDetector()
    anomaly.weight = 0.7
    pipeline.register(anomaly)

    return pipeline


# ============================================================
# 模式检测管线
# ============================================================


def _pattern_fix_strategy(
    ku: KnowledgeUnit,
    results: Dict[str, DetectionResult]
) -> KnowledgeUnit:
    """模式知识单元修复策略"""
    meta = ku.metadata

    for name, result in results.items():
        if result.passed:
            continue

        # 样本量不足：标记需要扩大采集
        if "sample_size" in str(result.details):
            meta["_needs_more_samples"] = True

        # 置信度问题：降低置信度
        if "confidence" in name:
            current = meta.get("confidence", 1.0)
            meta["confidence"] = current * 0.8  # 降低20%
            meta["_confidence_adjusted"] = True

    ku.metadata = meta
    return ku


def create_pattern_pipeline(
    min_score: float = 0.7,
    max_iterations: int = 2,
    enable_fix: bool = True
) -> DetectionPipeline[KnowledgeUnit]:
    """
    创建模式检测管线

    检测器组合：
    1. 完整性检测 (权重 1.0)
    2. 一致性检测 (权重 1.0)
    3. 模式有效性检测 (权重 1.2) - 核心
    4. 异常检测 (权重 0.6)

    Args:
        min_score: 最低通过分数
        max_iterations: 最大迭代次数
        enable_fix: 是否启用自动修复

    Returns:
        配置好的检测管线

    使用示例：
        pipeline = create_pattern_pipeline()

        pattern_ku = KnowledgeUnit(
            ku_id="pattern_001",
            ku_type="pattern",
            metadata={
                "pattern_id": 1,
                "dimension": "temporal",
                "finding": "周一发布效果最佳",
                "sample_size": 150,
                "confidence": 0.85,
                "data_sources": ["competitor_videos"],
                "action_items": ["选择周一发布"]
            }
        )

        ku, passed, results = pipeline.process(pattern_ku)
    """
    policy = AlignmentPolicy(
        min_score=min_score,
        max_iterations=max_iterations,
        auto_fix=enable_fix,
        allow_warnings=True
    )

    pipeline = DetectionPipeline[KnowledgeUnit](
        name="pattern_pipeline",
        policy=policy,
        fix_strategy=_pattern_fix_strategy if enable_fix else None
    )

    # 注册检测器
    completeness = PatternCompletenessDetector()
    completeness.weight = 1.0
    pipeline.register(completeness)

    consistency = PatternConsistencyDetector()
    consistency.weight = 1.0
    pipeline.register(consistency)

    # 模式有效性检测器权重更高
    pattern_validity = PatternValidityDetector()
    pattern_validity.weight = 1.2
    pipeline.register(pattern_validity)

    anomaly = PatternAnomalyDetector()
    anomaly.weight = 0.6
    pipeline.register(anomaly)

    return pipeline


# ============================================================
# 洞察检测管线
# ============================================================


def _insight_fix_strategy(
    ku: KnowledgeUnit,
    results: Dict[str, DetectionResult]
) -> KnowledgeUnit:
    """洞察知识单元修复策略"""
    meta = ku.metadata

    for name, result in results.items():
        if result.passed:
            continue

        # 推理链不完整：标记需要补充
        if "reasoning_chain" in str(result.affected_fields):
            meta["_needs_reasoning"] = True

        # 置信度问题
        if "confidence" in name:
            current = meta.get("confidence", 100)
            meta["confidence"] = current * 0.9
            meta["_confidence_adjusted"] = True

    ku.metadata = meta
    return ku


def create_insight_pipeline(
    min_score: float = 0.7,
    max_iterations: int = 2,
    enable_fix: bool = True
) -> DetectionPipeline[KnowledgeUnit]:
    """
    创建洞察检测管线

    检测器组合：
    1. 完整性检测 (权重 1.0)
    2. 一致性检测 (权重 0.9)
    3. 有效性检测 (权重 1.0)

    Args:
        min_score: 最低通过分数
        max_iterations: 最大迭代次数
        enable_fix: 是否启用自动修复

    Returns:
        配置好的检测管线

    使用示例：
        pipeline = create_insight_pipeline()

        insight_ku = KnowledgeUnit(
            ku_id="insight_001",
            ku_type="insight",
            metadata={
                "insight_id": "i001",
                "title": "3-5分钟视频播放最佳",
                "confidence": 78,
                "category": "opportunity",
                "sources": ["competitor_videos", "trend_data"],
                "reasoning_chain": [...]
            }
        )

        ku, passed, results = pipeline.process(insight_ku)
    """
    policy = AlignmentPolicy(
        min_score=min_score,
        max_iterations=max_iterations,
        auto_fix=enable_fix,
        allow_warnings=True
    )

    pipeline = DetectionPipeline[KnowledgeUnit](
        name="insight_pipeline",
        policy=policy,
        fix_strategy=_insight_fix_strategy if enable_fix else None
    )

    # 注册检测器
    completeness = InsightCompletenessDetector()
    completeness.weight = 1.0
    pipeline.register(completeness)

    # 洞察不需要专门的一致性检测器，复用基础版
    from .consistency import ConsistencyDetector
    consistency = ConsistencyDetector(name="insight_consistency")
    consistency.weight = 0.9
    pipeline.register(consistency)

    validity = InsightValidityDetector()
    validity.weight = 1.0
    pipeline.register(validity)

    return pipeline


# ============================================================
# 通用管线工厂
# ============================================================


def create_ku_pipeline(
    ku_type: str,
    **kwargs
) -> DetectionPipeline[KnowledgeUnit]:
    """
    根据知识单元类型创建对应的检测管线

    Args:
        ku_type: 知识单元类型 (video/pattern/insight)
        **kwargs: 传递给具体管线的参数

    Returns:
        配置好的检测管线

    使用示例：
        pipeline = create_ku_pipeline("video", strict=True)
        ku, passed, results = pipeline.process(video_ku)
    """
    factories = {
        "video": create_video_pipeline,
        "pattern": create_pattern_pipeline,
        "insight": create_insight_pipeline,
    }

    factory = factories.get(ku_type)
    if not factory:
        raise ValueError(f"未知的知识单元类型: {ku_type}")

    return factory(**kwargs)
