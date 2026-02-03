"""
有效性检测器

检测知识单元的业务有效性：
- 值域有效性：值在合理范围内
- 格式有效性：URL、ID等格式正确
- 业务规则有效性：符合业务逻辑
"""

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union

from ..knowledge_unit import (
    BaseDetector,
    DetectionResult,
    KnowledgeUnit,
    Severity,
)


@dataclass
class ValidationRule:
    """验证规则"""
    name: str
    field: str
    validator: Callable[[Any], bool]
    error_message: str
    severity: Severity = Severity.WARNING


class ValidityDetector(BaseDetector[KnowledgeUnit]):
    """
    有效性检测器

    检测维度：
    1. 值域范围 (如 view_count >= 0)
    2. 格式校验 (如 YouTube URL/ID)
    3. 枚举约束 (如 quadrant in [star, niche, viral, dog])
    4. 正则匹配

    使用示例：
        detector = ValidityDetector()

        # 添加值域规则
        detector.add_range_rule("view_count", min_val=0)
        detector.add_range_rule("engagement_rate", min_val=0, max_val=100)

        # 添加格式规则
        detector.add_pattern_rule(
            "youtube_id",
            r"^[a-zA-Z0-9_-]{11}$",
            "YouTube ID 格式错误"
        )

        result = detector.detect(video_ku)
    """

    # 常用正则模式
    YOUTUBE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{11}$")
    YOUTUBE_URL_PATTERN = re.compile(
        r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]{11}"
    )
    CHANNEL_ID_PATTERN = re.compile(r"^UC[a-zA-Z0-9_-]{22}$")

    def __init__(
        self,
        name: str = "validity",
        weight: float = 1.0,
        strict: bool = False
    ):
        super().__init__(name, weight)
        self.strict = strict
        self.rules: List[ValidationRule] = []

    def add_rule(
        self,
        name: str,
        field: str,
        validator: Callable[[Any], bool],
        error_message: str,
        severity: Severity = Severity.WARNING
    ) -> "ValidityDetector":
        """添加自定义验证规则"""
        self.rules.append(ValidationRule(
            name=name,
            field=field,
            validator=validator,
            error_message=error_message,
            severity=severity
        ))
        return self

    def add_range_rule(
        self,
        field: str,
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        severity: Severity = Severity.WARNING
    ) -> "ValidityDetector":
        """添加值域范围规则"""
        def validator(value: Any) -> bool:
            if value is None:
                return True  # 空值由完整性检测器处理

            try:
                num_value = float(value)
                if min_val is not None and num_value < min_val:
                    return False
                if max_val is not None and num_value > max_val:
                    return False
                return True
            except (TypeError, ValueError):
                return False

        range_desc = []
        if min_val is not None:
            range_desc.append(f">= {min_val}")
        if max_val is not None:
            range_desc.append(f"<= {max_val}")

        self.rules.append(ValidationRule(
            name=f"{field}_range",
            field=field,
            validator=validator,
            error_message=f"{field} 应在范围 {' 且 '.join(range_desc)}",
            severity=severity
        ))
        return self

    def add_pattern_rule(
        self,
        field: str,
        pattern: Union[str, Pattern],
        error_message: str,
        severity: Severity = Severity.WARNING
    ) -> "ValidityDetector":
        """添加正则匹配规则"""
        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        def validator(value: Any) -> bool:
            if value is None:
                return True
            if not isinstance(value, str):
                return False
            return bool(pattern.match(value))

        self.rules.append(ValidationRule(
            name=f"{field}_pattern",
            field=field,
            validator=validator,
            error_message=error_message,
            severity=severity
        ))
        return self

    def add_enum_rule(
        self,
        field: str,
        allowed_values: List[Any],
        severity: Severity = Severity.WARNING
    ) -> "ValidityDetector":
        """添加枚举约束规则"""
        def validator(value: Any) -> bool:
            if value is None:
                return True
            return value in allowed_values

        self.rules.append(ValidationRule(
            name=f"{field}_enum",
            field=field,
            validator=validator,
            error_message=f"{field} 必须是 {allowed_values} 之一",
            severity=severity
        ))
        return self

    def add_length_rule(
        self,
        field: str,
        min_len: Optional[int] = None,
        max_len: Optional[int] = None,
        severity: Severity = Severity.WARNING
    ) -> "ValidityDetector":
        """添加长度规则"""
        def validator(value: Any) -> bool:
            if value is None:
                return True
            try:
                length = len(value)
                if min_len is not None and length < min_len:
                    return False
                if max_len is not None and length > max_len:
                    return False
                return True
            except TypeError:
                return False

        len_desc = []
        if min_len is not None:
            len_desc.append(f">= {min_len}")
        if max_len is not None:
            len_desc.append(f"<= {max_len}")

        self.rules.append(ValidationRule(
            name=f"{field}_length",
            field=field,
            validator=validator,
            error_message=f"{field} 长度应 {' 且 '.join(len_desc)}",
            severity=severity
        ))
        return self

    def detect(self, ku: KnowledgeUnit) -> DetectionResult:
        """执行有效性检测"""
        passed_rules: List[str] = []
        failed_rules: List[Tuple[str, str, Severity]] = []
        suggestions: List[str] = []
        affected_fields: List[str] = []

        for rule in self.rules:
            value = self._get_field_value(ku, rule.field)

            try:
                if rule.validator(value):
                    passed_rules.append(rule.name)
                else:
                    failed_rules.append((rule.name, rule.error_message, rule.severity))
                    suggestions.append(f"修正 {rule.field}: {rule.error_message}")
                    affected_fields.append(rule.field)
            except Exception as e:
                failed_rules.append((
                    rule.name,
                    f"验证器执行异常: {str(e)}",
                    Severity.CRITICAL
                ))

        # 计算得分
        total_rules = len(self.rules)
        score = len(passed_rules) / max(total_rules, 1) if total_rules > 0 else 1.0

        # 判定结果
        if not failed_rules:
            return self._pass(
                message=f"有效性检测通过 ({total_rules} 规则)",
                score=1.0,
                details={"passed_rules": passed_rules}
            )

        max_severity = max(f[2] for f in failed_rules)

        return self._fail(
            message=f"有效性检测失败: {len(failed_rules)}/{total_rules} 规则未通过",
            severity=max_severity,
            score=score,
            affected_fields=list(set(affected_fields)),
            suggestions=suggestions,
            details={
                "passed_rules": passed_rules,
                "failed_rules": [(f[0], f[1]) for f in failed_rules],
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
        else:
            return getattr(ku, field_name, None)


# ============================================================
# 预定义检测器
# ============================================================


class VideoValidityDetector(ValidityDetector):
    """视频知识单元的有效性检测器"""

    def __init__(self, strict: bool = False):
        super().__init__(name="video_validity", strict=strict)

        # YouTube ID 格式
        self.add_pattern_rule(
            "metadata.youtube_id",
            self.YOUTUBE_ID_PATTERN,
            "YouTube ID 格式错误 (应为11位字母数字)",
            severity=Severity.CRITICAL
        )

        # 值域范围
        self.add_range_rule("metadata.view_count", min_val=0)
        self.add_range_rule("metadata.like_count", min_val=0)
        self.add_range_rule("metadata.comment_count", min_val=0)
        self.add_range_rule("metadata.duration", min_val=0, max_val=43200)  # 最长12小时

        # 标题长度 (YouTube 限制)
        self.add_length_rule("metadata.title", min_len=1, max_len=100)

        # 四象限枚举
        self.add_enum_rule(
            "metadata.quadrant",
            ["star", "niche", "viral", "dog", None],
            severity=Severity.WARNING
        )

        # 严格模式额外检查
        if strict:
            self.add_pattern_rule(
                "metadata.channel_id",
                self.CHANNEL_ID_PATTERN,
                "Channel ID 格式错误"
            )
            self.add_range_rule(
                "metadata.engagement_rate",
                min_val=0,
                max_val=50,  # 50% 已经非常高
                severity=Severity.WARNING
            )


class PatternValidityDetector(ValidityDetector):
    """模式知识单元的有效性检测器"""

    def __init__(self):
        super().__init__(name="pattern_validity")

        # 维度枚举
        self.add_enum_rule(
            "metadata.dimension",
            ["variable", "temporal", "spatial", "channel", "user"],
            severity=Severity.CRITICAL
        )

        # 置信度范围
        self.add_range_rule("metadata.confidence", min_val=0, max_val=1)

        # 有趣度范围
        self.add_range_rule("metadata.interestingness", min_val=1, max_val=5)

        # 样本量
        self.add_range_rule("metadata.sample_size", min_val=1)


class InsightValidityDetector(ValidityDetector):
    """洞察知识单元的有效性检测器"""

    def __init__(self):
        super().__init__(name="insight_validity")

        # 置信度范围
        self.add_range_rule("metadata.confidence", min_val=0, max_val=100)

        # 分类枚举
        self.add_enum_rule(
            "metadata.category",
            ["market", "opportunity", "warning", None],
            severity=Severity.WARNING
        )
