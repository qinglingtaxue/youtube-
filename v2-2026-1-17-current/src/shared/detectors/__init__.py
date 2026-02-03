"""
多维检测器模块

提供针对不同维度的检测器实现：
- 完整性检测 (Completeness)
- 一致性检测 (Consistency)
- 有效性检测 (Validity)
- 异常值检测 (Anomaly)
- 模式有效性检测 (Pattern)

使用示例：
    from src.shared.detectors import (
        CompletenessDetector,
        ConsistencyDetector,
        ValidityDetector,
        create_video_pipeline,
    )

    # 方式1: 使用预定义管线
    pipeline = create_video_pipeline()
    ku, passed, results = pipeline.process(video_ku)

    # 方式2: 自定义组合
    from src.shared.knowledge_unit import create_pipeline

    pipeline = create_pipeline(
        name="custom",
        detectors=[
            CompletenessDetector(),
            ValidityDetector(strict=True),
        ],
        min_score=0.8
    )
"""

from .completeness import CompletenessDetector
from .consistency import ConsistencyDetector
from .validity import ValidityDetector
from .anomaly import AnomalyDetector
from .pattern import PatternValidityDetector
from .pipelines import (
    create_video_pipeline,
    create_pattern_pipeline,
    create_insight_pipeline,
)

__all__ = [
    # 检测器
    "CompletenessDetector",
    "ConsistencyDetector",
    "ValidityDetector",
    "AnomalyDetector",
    "PatternValidityDetector",
    # 预定义管线
    "create_video_pipeline",
    "create_pattern_pipeline",
    "create_insight_pipeline",
]
