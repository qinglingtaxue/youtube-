"""
模式有效性检测器

检测模式知识单元的有效性：
- 公式正确性
- 样本代表性
- 置信度合理性
- 可复现性
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..knowledge_unit import (
    BaseDetector,
    DetectionResult,
    KnowledgeUnit,
    Severity,
)


@dataclass
class PatternRule:
    """模式验证规则"""
    name: str
    checker: Callable[[KnowledgeUnit], Tuple[bool, str, List[str]]]
    # 返回 (passed, message, suggestions)
    severity: Severity = Severity.WARNING


class PatternValidityDetector(BaseDetector[KnowledgeUnit]):
    """
    模式有效性检测器

    检测维度：
    1. 公式正确性：计算逻辑是否正确
    2. 样本代表性：样本是否足够且多样
    3. 置信度合理性：置信度与数据支撑是否匹配
    4. 可复现性：模式是否可重复验证

    使用示例：
        detector = PatternValidityDetector()
        result = detector.detect(pattern_ku)
    """

    # 维度对应的最小样本量要求
    DIMENSION_MIN_SAMPLES = {
        "variable": 100,    # 变量分布需要较大样本
        "temporal": 50,     # 时间模式需要多个时间点
        "spatial": 30,      # 空间模式需要多个地区
        "channel": 20,      # 频道维度相对较少
        "user": 100,        # 用户维度需要较多评论
    }

    def __init__(
        self,
        name: str = "pattern_validity",
        weight: float = 1.0
    ):
        super().__init__(name, weight)
        self.rules: List[PatternRule] = []

        # 设置默认规则
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """设置默认规则"""
        # 样本量检查
        self.add_rule(
            name="sample_size",
            checker=self._check_sample_size
        )

        # 置信度合理性
        self.add_rule(
            name="confidence_validity",
            checker=self._check_confidence,
            severity=Severity.WARNING
        )

        # 数据源完整性
        self.add_rule(
            name="data_sources",
            checker=self._check_data_sources
        )

        # 行动建议存在性
        self.add_rule(
            name="action_items",
            checker=self._check_action_items,
            severity=Severity.INFO
        )

    def add_rule(
        self,
        name: str,
        checker: Callable[[KnowledgeUnit], Tuple[bool, str, List[str]]],
        severity: Severity = Severity.WARNING
    ) -> "PatternValidityDetector":
        """添加验证规则"""
        self.rules.append(PatternRule(
            name=name,
            checker=checker,
            severity=severity
        ))
        return self

    def _check_sample_size(
        self, ku: KnowledgeUnit
    ) -> Tuple[bool, str, List[str]]:
        """检查样本量是否足够"""
        meta = ku.metadata
        dimension = meta.get("dimension", "")
        sample_size = meta.get("sample_size", 0)

        min_required = self.DIMENSION_MIN_SAMPLES.get(dimension, 30)

        if sample_size >= min_required:
            return True, f"样本量充足 ({sample_size} >= {min_required})", []

        suggestions = [
            f"增加样本量到 {min_required} 以上",
            "考虑扩大数据采集范围",
            "或降低该模式的置信度"
        ]
        return False, f"样本量不足 ({sample_size} < {min_required})", suggestions

    def _check_confidence(
        self, ku: KnowledgeUnit
    ) -> Tuple[bool, str, List[str]]:
        """检查置信度合理性"""
        meta = ku.metadata
        confidence = meta.get("confidence", 0)
        sample_size = meta.get("sample_size", 0)

        # 置信度与样本量的关系
        # 样本量 < 30: 置信度不应超过 0.7
        # 样本量 30-100: 置信度不应超过 0.85
        # 样本量 > 100: 置信度可以更高

        if sample_size < 30 and confidence > 0.7:
            return False, "小样本置信度过高", [
                f"样本量仅{sample_size}，建议置信度≤0.7"
            ]

        if sample_size < 100 and confidence > 0.85:
            return False, "中等样本置信度偏高", [
                f"样本量{sample_size}，建议置信度≤0.85"
            ]

        return True, f"置信度合理 ({confidence})", []

    def _check_data_sources(
        self, ku: KnowledgeUnit
    ) -> Tuple[bool, str, List[str]]:
        """检查数据源完整性"""
        meta = ku.metadata
        sources = meta.get("data_sources", [])

        if not sources:
            return False, "缺少数据源", ["添加数据源标注"]

        if len(sources) < 2:
            return True, "数据源单一", [
                "建议增加多个数据源以提高可信度"
            ]

        return True, f"数据源完整 ({len(sources)} 个)", []

    def _check_action_items(
        self, ku: KnowledgeUnit
    ) -> Tuple[bool, str, List[str]]:
        """检查是否有可执行的行动建议"""
        meta = ku.metadata
        action_items = meta.get("action_items", [])

        if not action_items:
            return False, "缺少行动建议", [
                "添加可执行的行动建议",
                "模式应能指导具体决策"
            ]

        return True, f"有 {len(action_items)} 条行动建议", []

    def detect(self, ku: KnowledgeUnit) -> DetectionResult:
        """执行模式有效性检测"""
        passed_rules: List[str] = []
        failed_rules: List[Tuple[str, str, Severity]] = []
        all_suggestions: List[str] = []

        for rule in self.rules:
            try:
                passed, message, suggestions = rule.checker(ku)
                if passed:
                    passed_rules.append(f"{rule.name}: {message}")
                else:
                    failed_rules.append((rule.name, message, rule.severity))
                    all_suggestions.extend(suggestions)
            except Exception as e:
                failed_rules.append((
                    rule.name,
                    f"规则执行异常: {str(e)}",
                    Severity.CRITICAL
                ))

        # 计算得分
        total_rules = len(self.rules)
        score = len(passed_rules) / max(total_rules, 1)

        # 判定结果
        if not failed_rules:
            return self._pass(
                message=f"模式有效性检测通过 ({total_rules} 规则)",
                score=1.0,
                details={"passed_rules": passed_rules}
            )

        max_severity = max(f[2] for f in failed_rules)
        affected_rules = [f[0] for f in failed_rules]

        return self._fail(
            message=f"模式有效性检测失败: {len(failed_rules)}/{total_rules} 规则未通过",
            severity=max_severity,
            score=score,
            affected_fields=affected_rules,
            suggestions=all_suggestions,
            details={
                "passed_rules": passed_rules,
                "failed_rules": [(f[0], f[1]) for f in failed_rules],
            }
        )


# ============================================================
# 特定维度的检测器
# ============================================================


class TemporalPatternDetector(PatternValidityDetector):
    """时间维度模式检测器"""

    def __init__(self):
        super().__init__(name="temporal_pattern_validity")

        # 时间跨度检查
        self.add_rule(
            name="time_span",
            checker=self._check_time_span
        )

        # 周期性检查
        self.add_rule(
            name="periodicity",
            checker=self._check_periodicity,
            severity=Severity.INFO
        )

    def _check_time_span(
        self, ku: KnowledgeUnit
    ) -> Tuple[bool, str, List[str]]:
        """检查时间跨度是否足够"""
        meta = ku.metadata
        time_span_days = meta.get("time_span_days", 0)

        if time_span_days < 7:
            return False, "时间跨度不足7天", [
                "时间模式需要至少7天数据"
            ]

        if time_span_days < 30:
            return True, "时间跨度较短", [
                "建议扩展到30天以上以发现周期性"
            ]

        return True, f"时间跨度充足 ({time_span_days} 天)", []

    def _check_periodicity(
        self, ku: KnowledgeUnit
    ) -> Tuple[bool, str, List[str]]:
        """检查是否识别了周期性"""
        meta = ku.metadata
        has_periodicity = meta.get("periodicity_detected", False)

        if not has_periodicity:
            return True, "未检测周期性", [
                "考虑分析数据的周期性规律"
            ]

        return True, "已识别周期性", []


class SpatialPatternDetector(PatternValidityDetector):
    """空间维度模式检测器"""

    def __init__(self):
        super().__init__(name="spatial_pattern_validity")

        # 地区覆盖检查
        self.add_rule(
            name="region_coverage",
            checker=self._check_region_coverage
        )

    def _check_region_coverage(
        self, ku: KnowledgeUnit
    ) -> Tuple[bool, str, List[str]]:
        """检查地区覆盖是否足够"""
        meta = ku.metadata
        regions = meta.get("regions", [])

        if len(regions) < 2:
            return False, "地区覆盖不足", [
                "空间模式需要至少2个地区的对比数据"
            ]

        return True, f"覆盖 {len(regions)} 个地区", []
