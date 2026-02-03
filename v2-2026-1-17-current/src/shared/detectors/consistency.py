"""
一致性检测器

检测知识单元内部和跨实体的数据一致性：
- 内部一致性：字段间逻辑关系
- 跨实体一致性：关联数据匹配
- 时间一致性：时间戳递增
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..knowledge_unit import (
    BaseDetector,
    DetectionResult,
    KnowledgeUnit,
    Severity,
)


@dataclass
class ConsistencyRule:
    """一致性规则"""
    name: str
    checker: Callable[[KnowledgeUnit], Tuple[bool, str]]  # 返回 (passed, message)
    severity: Severity = Severity.WARNING


class ConsistencyDetector(BaseDetector[KnowledgeUnit]):
    """
    一致性检测器

    检测维度：
    1. 字段间逻辑关系 (如 likes <= views)
    2. 计算字段正确性 (如 engagement_rate 计算)
    3. 时间戳递增关系
    4. 枚举值有效性

    使用示例：
        detector = ConsistencyDetector()

        # 添加自定义规则
        detector.add_rule(
            name="likes_vs_views",
            checker=lambda ku: (
                ku.metadata.get("likes", 0) <= ku.metadata.get("views", 0),
                "点赞数不能超过播放数"
            ),
            severity=Severity.CRITICAL
        )

        result = detector.detect(video_ku)
    """

    def __init__(
        self,
        name: str = "consistency",
        weight: float = 1.0
    ):
        super().__init__(name, weight)
        self.rules: List[ConsistencyRule] = []

        # 设置默认规则
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """设置默认规则"""
        # 版本一致性
        self.add_rule(
            name="version_positive",
            checker=lambda ku: (
                ku.version > 0,
                "版本号必须为正数"
            ),
            severity=Severity.CRITICAL
        )

        # 时间戳一致性
        self.add_rule(
            name="timestamp_order",
            checker=lambda ku: (
                ku.created_at <= ku.updated_at,
                f"创建时间({ku.created_at})不能晚于更新时间({ku.updated_at})"
            ),
            severity=Severity.CRITICAL
        )

        # 迭代次数一致性
        self.add_rule(
            name="iteration_limit",
            checker=lambda ku: (
                ku.iteration_count <= ku.max_iterations,
                f"迭代次数({ku.iteration_count})超过最大限制({ku.max_iterations})"
            ),
            severity=Severity.WARNING
        )

    def add_rule(
        self,
        name: str,
        checker: Callable[[KnowledgeUnit], Tuple[bool, str]],
        severity: Severity = Severity.WARNING
    ) -> "ConsistencyDetector":
        """添加一致性规则"""
        self.rules.append(ConsistencyRule(
            name=name,
            checker=checker,
            severity=severity
        ))
        return self

    def detect(self, ku: KnowledgeUnit) -> DetectionResult:
        """执行一致性检测"""
        passed_rules: List[str] = []
        failed_rules: List[Tuple[str, str, Severity]] = []  # (name, message, severity)
        suggestions: List[str] = []

        for rule in self.rules:
            try:
                passed, message = rule.checker(ku)
                if passed:
                    passed_rules.append(rule.name)
                else:
                    failed_rules.append((rule.name, message, rule.severity))
                    suggestions.append(f"修复 {rule.name}: {message}")
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
                message=f"一致性检测通过 ({total_rules} 规则)",
                score=1.0,
                details={"passed_rules": passed_rules}
            )

        # 找最严重的级别
        max_severity = max(f[2] for f in failed_rules)
        affected_rules = [f[0] for f in failed_rules]

        return self._fail(
            message=f"一致性检测失败: {len(failed_rules)}/{total_rules} 规则未通过",
            severity=max_severity,
            score=score,
            affected_fields=affected_rules,
            suggestions=suggestions,
            details={
                "passed_rules": passed_rules,
                "failed_rules": [(f[0], f[1]) for f in failed_rules],
            }
        )


# ============================================================
# 预定义检测器
# ============================================================


class VideoConsistencyDetector(ConsistencyDetector):
    """视频知识单元的一致性检测器"""

    def __init__(self):
        super().__init__(name="video_consistency")

        # 点赞数 <= 播放数 (正常情况)
        self.add_rule(
            name="likes_vs_views",
            checker=self._check_likes_vs_views,
            severity=Severity.CRITICAL
        )

        # 评论数合理性
        self.add_rule(
            name="comments_vs_views",
            checker=self._check_comments_vs_views,
            severity=Severity.WARNING
        )

        # 互动率计算一致性
        self.add_rule(
            name="engagement_rate_consistency",
            checker=self._check_engagement_rate,
            severity=Severity.WARNING
        )

        # 时长合理性
        self.add_rule(
            name="duration_reasonable",
            checker=self._check_duration,
            severity=Severity.WARNING
        )

    def _check_likes_vs_views(self, ku: KnowledgeUnit) -> Tuple[bool, str]:
        """点赞数不能超过播放数"""
        meta = ku.metadata
        likes = meta.get("like_count", 0) or 0
        views = meta.get("view_count", 0) or 0

        if views == 0:
            return True, ""  # 无法判断

        if likes > views:
            return False, f"点赞数({likes})超过播放数({views})"

        return True, ""

    def _check_comments_vs_views(self, ku: KnowledgeUnit) -> Tuple[bool, str]:
        """评论数/播放数比例合理性"""
        meta = ku.metadata
        comments = meta.get("comment_count", 0) or 0
        views = meta.get("view_count", 0) or 0

        if views == 0:
            return True, ""

        ratio = comments / views
        if ratio > 0.3:  # 30% 评论率极不合理
            return False, f"评论率({ratio:.1%})异常高"

        return True, ""

    def _check_engagement_rate(self, ku: KnowledgeUnit) -> Tuple[bool, str]:
        """互动率计算一致性"""
        meta = ku.metadata
        likes = meta.get("like_count", 0) or 0
        comments = meta.get("comment_count", 0) or 0
        views = meta.get("view_count", 0) or 0
        stored_rate = meta.get("engagement_rate")

        if views == 0 or stored_rate is None:
            return True, ""

        calculated_rate = (likes + comments) / views * 100
        diff = abs(calculated_rate - stored_rate)

        if diff > 0.1:  # 允许 0.1% 误差
            return False, f"存储互动率({stored_rate:.2f}%)与计算值({calculated_rate:.2f}%)不一致"

        return True, ""

    def _check_duration(self, ku: KnowledgeUnit) -> Tuple[bool, str]:
        """时长合理性检查"""
        meta = ku.metadata
        duration = meta.get("duration", 0) or 0

        if duration < 0:
            return False, "时长不能为负"

        if duration > 12 * 3600:  # 12小时
            return False, f"时长({duration}秒)超过12小时，可能是直播录像"

        return True, ""


class PatternConsistencyDetector(ConsistencyDetector):
    """模式知识单元的一致性检测器"""

    def __init__(self):
        super().__init__(name="pattern_consistency")

        # 样本量与置信度关系
        self.add_rule(
            name="sample_confidence_relation",
            checker=self._check_sample_confidence,
            severity=Severity.WARNING
        )

        # 有趣度公式一致性
        self.add_rule(
            name="interestingness_formula",
            checker=self._check_interestingness,
            severity=Severity.WARNING
        )

    def _check_sample_confidence(self, ku: KnowledgeUnit) -> Tuple[bool, str]:
        """样本量与置信度关系"""
        meta = ku.metadata
        sample_size = meta.get("sample_size", 0)
        confidence = meta.get("confidence", 0)

        # 样本量太小但置信度高，不合理
        if sample_size < 30 and confidence > 0.8:
            return False, f"样本量({sample_size})太小，置信度({confidence})不应超过0.8"

        return True, ""

    def _check_interestingness(self, ku: KnowledgeUnit) -> Tuple[bool, str]:
        """有趣度公式一致性"""
        meta = ku.metadata

        betweenness = meta.get("betweenness")
        degree = meta.get("degree")
        interestingness = meta.get("interestingness")

        if None in (betweenness, degree, interestingness):
            return True, ""  # 字段不存在，跳过

        if degree == 0:
            return True, ""  # 避免除零

        calculated = betweenness / degree
        diff = abs(calculated - interestingness)

        if diff > 0.01:
            return False, f"有趣度({interestingness:.3f})与计算值({calculated:.3f})不一致"

        return True, ""
