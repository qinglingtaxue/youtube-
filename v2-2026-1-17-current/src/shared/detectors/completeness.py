"""
完整性检测器

检测知识单元的字段完整性：
- 必填字段是否存在
- 字段值是否为空
- 关联字段是否完整
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

from ..knowledge_unit import (
    BaseDetector,
    DetectionResult,
    KnowledgeUnit,
    Severity,
)


@dataclass
class FieldRule:
    """字段规则"""
    field_name: str
    required: bool = True
    allow_empty: bool = False
    validator: Optional[Callable[[Any], bool]] = None
    error_message: str = ""


class CompletenessDetector(BaseDetector[KnowledgeUnit]):
    """
    完整性检测器

    检测维度：
    1. 必填字段存在性
    2. 字段值非空
    3. 自定义验证规则

    使用示例：
        detector = CompletenessDetector()
        detector.add_required_field("title")
        detector.add_required_field("view_count", allow_empty=False)

        result = detector.detect(video_ku)
    """

    def __init__(
        self,
        name: str = "completeness",
        weight: float = 1.0,
        strict: bool = False
    ):
        super().__init__(name, weight)
        self.strict = strict
        self.field_rules: List[FieldRule] = []

        # 默认规则
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """设置默认规则"""
        # 所有 KU 都需要的基础字段
        self.add_required_field("ku_id", allow_empty=False)
        self.add_required_field("ku_type", allow_empty=False)

    def add_required_field(
        self,
        field_name: str,
        allow_empty: bool = False,
        validator: Optional[Callable[[Any], bool]] = None,
        error_message: str = ""
    ) -> "CompletenessDetector":
        """添加必填字段规则"""
        self.field_rules.append(FieldRule(
            field_name=field_name,
            required=True,
            allow_empty=allow_empty,
            validator=validator,
            error_message=error_message or f"字段 {field_name} 不完整"
        ))
        return self

    def add_optional_field(
        self,
        field_name: str,
        validator: Optional[Callable[[Any], bool]] = None
    ) -> "CompletenessDetector":
        """添加可选字段规则（有值时验证）"""
        self.field_rules.append(FieldRule(
            field_name=field_name,
            required=False,
            allow_empty=True,
            validator=validator
        ))
        return self

    def detect(self, ku: KnowledgeUnit) -> DetectionResult:
        """执行完整性检测"""
        missing_fields: List[str] = []
        empty_fields: List[str] = []
        invalid_fields: List[str] = []
        suggestions: List[str] = []

        for rule in self.field_rules:
            # 获取字段值
            value = self._get_field_value(ku, rule.field_name)

            # 检查存在性
            if value is None:
                if rule.required:
                    missing_fields.append(rule.field_name)
                    suggestions.append(f"补充必填字段: {rule.field_name}")
                continue

            # 检查空值
            if not rule.allow_empty and self._is_empty(value):
                empty_fields.append(rule.field_name)
                suggestions.append(f"填充空字段: {rule.field_name}")
                continue

            # 自定义验证
            if rule.validator and not rule.validator(value):
                invalid_fields.append(rule.field_name)
                suggestions.append(rule.error_message or f"修正字段: {rule.field_name}")

        # 计算得分
        total_rules = len([r for r in self.field_rules if r.required])
        failed_count = len(missing_fields) + len(empty_fields) + len(invalid_fields)
        score = 1.0 - (failed_count / max(total_rules, 1))

        # 判定结果
        has_critical = len(missing_fields) > 0
        has_issues = failed_count > 0

        if not has_issues:
            return self._pass(
                message=f"完整性检测通过 ({total_rules} 字段)",
                score=1.0
            )

        severity = Severity.CRITICAL if has_critical else Severity.WARNING
        affected = missing_fields + empty_fields + invalid_fields

        return self._fail(
            message=f"完整性检测失败: 缺失={len(missing_fields)}, 空值={len(empty_fields)}, 无效={len(invalid_fields)}",
            severity=severity,
            score=max(0.0, score),
            affected_fields=affected,
            suggestions=suggestions,
            details={
                "missing": missing_fields,
                "empty": empty_fields,
                "invalid": invalid_fields,
            }
        )

    def _get_field_value(self, ku: KnowledgeUnit, field_name: str) -> Any:
        """获取字段值，支持嵌套字段 (如 metadata.tags)"""
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

    def _is_empty(self, value: Any) -> bool:
        """判断值是否为空"""
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, (list, dict, set)) and len(value) == 0:
            return True
        return False


# ============================================================
# 预定义检测器
# ============================================================


class VideoCompletenessDetector(CompletenessDetector):
    """视频知识单元的完整性检测器"""

    def __init__(self, strict: bool = False):
        super().__init__(name="video_completeness", strict=strict)

        # 视频必填字段
        self.add_required_field("metadata.youtube_id", allow_empty=False)
        self.add_required_field("metadata.title", allow_empty=False)
        self.add_required_field("metadata.view_count", allow_empty=False)
        self.add_required_field("metadata.channel_name", allow_empty=False)

        # 严格模式下额外检查
        if strict:
            self.add_required_field("metadata.like_count")
            self.add_required_field("metadata.comment_count")
            self.add_required_field("metadata.duration")
            self.add_required_field("metadata.published_at")
            self.add_required_field("metadata.description")
            self.add_required_field("metadata.tags")


class PatternCompletenessDetector(CompletenessDetector):
    """模式知识单元的完整性检测器"""

    def __init__(self):
        super().__init__(name="pattern_completeness")

        # 模式必填字段
        self.add_required_field("metadata.pattern_id")
        self.add_required_field("metadata.dimension")
        self.add_required_field("metadata.finding")
        self.add_required_field("metadata.sample_size",
                                validator=lambda x: x > 0,
                                error_message="样本量必须大于0")
        self.add_required_field("metadata.confidence",
                                validator=lambda x: 0 <= x <= 1,
                                error_message="置信度必须在0-1之间")


class InsightCompletenessDetector(CompletenessDetector):
    """洞察知识单元的完整性检测器"""

    def __init__(self):
        super().__init__(name="insight_completeness")

        # 洞察必填字段
        self.add_required_field("metadata.insight_id")
        self.add_required_field("metadata.title")
        self.add_required_field("metadata.confidence",
                                validator=lambda x: 0 <= x <= 100,
                                error_message="置信度必须在0-100之间")
        self.add_required_field("metadata.sources")
        self.add_required_field("metadata.reasoning_chain")
