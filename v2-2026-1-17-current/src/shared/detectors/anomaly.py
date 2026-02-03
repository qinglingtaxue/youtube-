"""
异常值检测器

检测知识单元中的异常数据：
- 统计异常：超出正常分布范围
- 逻辑异常：违反常识的数据
- 模式异常：与已知模式不符
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..knowledge_unit import (
    BaseDetector,
    DetectionResult,
    KnowledgeUnit,
    Severity,
)


@dataclass
class AnomalyRule:
    """异常检测规则"""
    name: str
    detector_func: Callable[[KnowledgeUnit], Tuple[bool, float, str]]
    # 返回 (is_anomaly, anomaly_score, description)
    threshold: float = 0.8  # 异常分数阈值
    severity: Severity = Severity.WARNING


class AnomalyDetector(BaseDetector[KnowledgeUnit]):
    """
    异常值检测器

    检测维度：
    1. Z-Score 异常：距离均值超过N个标准差
    2. IQR 异常：超出四分位距范围
    3. 业务异常：违反业务常识
    4. 模式异常：与历史模式不符

    使用示例：
        detector = AnomalyDetector()

        # 添加 Z-Score 规则
        detector.add_zscore_rule(
            field="view_count",
            mean=50000,
            std=30000,
            threshold=3.0
        )

        # 添加业务异常规则
        detector.add_business_rule(
            name="viral_without_engagement",
            checker=lambda ku: (
                ku.metadata.get("view_count", 0) > 1000000 and
                ku.metadata.get("engagement_rate", 0) < 0.1
            ),
            description="百万播放但互动率低于0.1%，可能是刷量"
        )

        result = detector.detect(video_ku)
    """

    def __init__(
        self,
        name: str = "anomaly",
        weight: float = 0.8  # 异常检测权重稍低
    ):
        super().__init__(name, weight)
        self.rules: List[AnomalyRule] = []

    def add_rule(
        self,
        name: str,
        detector_func: Callable[[KnowledgeUnit], Tuple[bool, float, str]],
        threshold: float = 0.8,
        severity: Severity = Severity.WARNING
    ) -> "AnomalyDetector":
        """添加异常检测规则"""
        self.rules.append(AnomalyRule(
            name=name,
            detector_func=detector_func,
            threshold=threshold,
            severity=severity
        ))
        return self

    def add_zscore_rule(
        self,
        field: str,
        mean: float,
        std: float,
        z_threshold: float = 3.0,
        severity: Severity = Severity.WARNING
    ) -> "AnomalyDetector":
        """添加 Z-Score 异常检测规则"""
        def detector_func(ku: KnowledgeUnit) -> Tuple[bool, float, str]:
            value = self._get_field_value(ku, field)
            if value is None or std == 0:
                return False, 0.0, ""

            z_score = abs((value - mean) / std)
            is_anomaly = z_score > z_threshold
            anomaly_score = min(z_score / z_threshold, 1.0) if z_threshold > 0 else 0

            description = f"{field}={value} (z-score={z_score:.2f})"
            return is_anomaly, anomaly_score, description

        self.rules.append(AnomalyRule(
            name=f"{field}_zscore",
            detector_func=detector_func,
            threshold=0.5,
            severity=severity
        ))
        return self

    def add_iqr_rule(
        self,
        field: str,
        q1: float,
        q3: float,
        multiplier: float = 1.5,
        severity: Severity = Severity.WARNING
    ) -> "AnomalyDetector":
        """添加 IQR 异常检测规则"""
        iqr = q3 - q1
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr

        def detector_func(ku: KnowledgeUnit) -> Tuple[bool, float, str]:
            value = self._get_field_value(ku, field)
            if value is None:
                return False, 0.0, ""

            is_anomaly = value < lower_bound or value > upper_bound

            # 计算异常程度
            if value < lower_bound:
                deviation = (lower_bound - value) / iqr if iqr > 0 else 0
            elif value > upper_bound:
                deviation = (value - upper_bound) / iqr if iqr > 0 else 0
            else:
                deviation = 0

            anomaly_score = min(deviation / multiplier, 1.0)
            description = f"{field}={value} (range=[{lower_bound:.0f}, {upper_bound:.0f}])"

            return is_anomaly, anomaly_score, description

        self.rules.append(AnomalyRule(
            name=f"{field}_iqr",
            detector_func=detector_func,
            threshold=0.5,
            severity=severity
        ))
        return self

    def add_business_rule(
        self,
        name: str,
        checker: Callable[[KnowledgeUnit], bool],
        description: str,
        severity: Severity = Severity.WARNING
    ) -> "AnomalyDetector":
        """添加业务异常规则"""
        def detector_func(ku: KnowledgeUnit) -> Tuple[bool, float, str]:
            try:
                is_anomaly = checker(ku)
                return is_anomaly, 1.0 if is_anomaly else 0.0, description
            except Exception:
                return False, 0.0, ""

        self.rules.append(AnomalyRule(
            name=name,
            detector_func=detector_func,
            threshold=0.5,
            severity=severity
        ))
        return self

    def detect(self, ku: KnowledgeUnit) -> DetectionResult:
        """执行异常检测"""
        normal_rules: List[str] = []
        anomaly_rules: List[Tuple[str, str, float, Severity]] = []
        suggestions: List[str] = []

        for rule in self.rules:
            try:
                is_anomaly, anomaly_score, description = rule.detector_func(ku)

                if not is_anomaly or anomaly_score < rule.threshold:
                    normal_rules.append(rule.name)
                else:
                    anomaly_rules.append((
                        rule.name,
                        description,
                        anomaly_score,
                        rule.severity
                    ))
                    suggestions.append(f"检查异常 {rule.name}: {description}")

            except Exception as e:
                # 检测器执行失败不算异常
                normal_rules.append(f"{rule.name} (skipped: {e})")

        # 计算得分 (无异常 = 高分)
        total_rules = len(self.rules)
        score = len(normal_rules) / max(total_rules, 1) if total_rules > 0 else 1.0

        # 判定结果
        if not anomaly_rules:
            return self._pass(
                message=f"异常检测通过 ({total_rules} 规则)",
                score=1.0,
                details={"checked_rules": normal_rules}
            )

        max_severity = max(a[3] for a in anomaly_rules)
        affected_rules = [a[0] for a in anomaly_rules]

        return self._fail(
            message=f"发现 {len(anomaly_rules)} 个异常",
            severity=max_severity,
            score=score,
            affected_fields=affected_rules,
            suggestions=suggestions,
            details={
                "normal_rules": normal_rules,
                "anomalies": [
                    {"rule": a[0], "description": a[1], "score": a[2]}
                    for a in anomaly_rules
                ],
            }
        )

    def _get_field_value(self, ku: KnowledgeUnit, field_name: str) -> Any:
        """获取字段值"""
        if "." in field_name:
            parts = field_name.split(".")
            value = ku
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        return getattr(ku, field_name, None)


# ============================================================
# 预定义检测器
# ============================================================


class VideoAnomalyDetector(AnomalyDetector):
    """视频知识单元的异常检测器"""

    def __init__(
        self,
        view_stats: Optional[Dict[str, float]] = None,
        engagement_stats: Optional[Dict[str, float]] = None
    ):
        super().__init__(name="video_anomaly")

        # 默认统计值 (基于典型 YouTube 视频)
        view_stats = view_stats or {
            "mean": 50000,
            "std": 200000,
            "q1": 1000,
            "q3": 50000,
        }

        engagement_stats = engagement_stats or {
            "mean": 3.0,
            "std": 2.5,
            "q1": 1.0,
            "q3": 5.0,
        }

        # 播放量 Z-Score 异常
        self.add_zscore_rule(
            field="metadata.view_count",
            mean=view_stats["mean"],
            std=view_stats["std"],
            z_threshold=4.0  # 4个标准差
        )

        # 播放量 IQR 异常
        self.add_iqr_rule(
            field="metadata.view_count",
            q1=view_stats["q1"],
            q3=view_stats["q3"],
            multiplier=3.0
        )

        # 业务异常：刷量嫌疑
        self.add_business_rule(
            name="suspected_fake_views",
            checker=lambda ku: (
                ku.metadata.get("view_count", 0) > 1000000 and
                ku.metadata.get("like_count", 0) < 100
            ),
            description="百万播放但点赞不足100，疑似刷量",
            severity=Severity.WARNING
        )

        # 业务异常：超高互动率
        self.add_business_rule(
            name="abnormal_high_engagement",
            checker=lambda ku: (
                ku.metadata.get("engagement_rate", 0) > 30
            ),
            description="互动率超过30%，数据可能有误",
            severity=Severity.WARNING
        )

        # 业务异常：新频道爆款
        self.add_business_rule(
            name="new_channel_viral",
            checker=lambda ku: (
                ku.metadata.get("view_count", 0) > 500000 and
                ku.metadata.get("subscriber_count", 0) < 1000
            ),
            description="订阅不足1000但播放超50万，需核实",
            severity=Severity.INFO
        )


class PatternAnomalyDetector(AnomalyDetector):
    """模式知识单元的异常检测器"""

    def __init__(self):
        super().__init__(name="pattern_anomaly")

        # 小样本高置信度
        self.add_business_rule(
            name="small_sample_high_confidence",
            checker=lambda ku: (
                ku.metadata.get("sample_size", 0) < 30 and
                ku.metadata.get("confidence", 0) > 0.9
            ),
            description="样本量<30但置信度>90%，可能过拟合",
            severity=Severity.WARNING
        )

        # 有趣度异常高
        self.add_business_rule(
            name="extreme_interestingness",
            checker=lambda ku: (
                ku.metadata.get("interestingness", 0) > 4.5
            ),
            description="有趣度>4.5，需人工审核",
            severity=Severity.INFO
        )
