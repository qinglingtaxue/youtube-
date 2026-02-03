#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script 和 Spec 数据模型
脚本和规约实体 - 策划阶段的核心产出

引用规约：
- data.spec.md: 2.2 Script Schema, 2.5 Spec Schema
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import (
    BaseModel,
    ScriptStatus,
    ContentStyle,
    generate_uuid,
    parse_datetime,
    parse_enum,
)


@dataclass
class Spec(BaseModel):
    """
    视频规约实体

    基于 data.spec.md 2.5 Spec Schema
    策划阶段产出，定义视频的内容框架
    """

    # 主键
    spec_id: str = field(default_factory=generate_uuid)

    # 基本信息
    topic: str = ""  # 视频主题
    target_duration: int = 600  # 目标时长（秒）
    style: ContentStyle = ContentStyle.TUTORIAL  # 内容风格

    # 三事件结构
    event_1: Optional[str] = None  # 引入问题
    event_2: Optional[str] = None  # 展示方案
    event_3: Optional[str] = None  # 总结升华

    # 内容定义
    meaning: Optional[str] = None  # 生发意义
    target_audience: Optional[str] = None  # 目标受众
    cta: Optional[str] = None  # 行动号召 (Call To Action)

    # 关联
    research_id: Optional[str] = None  # 关联的调研报告
    file_path: Optional[str] = None  # 规约文件路径 (Markdown)

    # 时间
    created_at: datetime = field(default_factory=datetime.now)

    # ============================================================
    # 验证方法
    # ============================================================

    def validate(self) -> List[str]:
        """验证规约数据"""
        errors = []

        if not self.topic:
            errors.append("主题不能为空")

        if self.target_duration <= 0:
            errors.append("目标时长必须大于0")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    def is_complete(self) -> bool:
        """检查规约是否完整"""
        return all([
            self.topic,
            self.event_1,
            self.event_2,
            self.event_3,
        ])

    # ============================================================
    # 序列化方法
    # ============================================================

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Spec':
        """从字典创建实例"""
        return cls(
            spec_id=data.get('spec_id', generate_uuid()),
            topic=data.get('topic', ''),
            target_duration=data.get('target_duration', 600),
            style=parse_enum(ContentStyle, data.get('style'), ContentStyle.TUTORIAL),
            event_1=data.get('event_1'),
            event_2=data.get('event_2'),
            event_3=data.get('event_3'),
            meaning=data.get('meaning'),
            target_audience=data.get('target_audience'),
            cta=data.get('cta'),
            research_id=data.get('research_id'),
            file_path=data.get('file_path'),
            created_at=parse_datetime(data.get('created_at')) or datetime.now(),
        )

    @property
    def duration_formatted(self) -> str:
        """格式化目标时长"""
        minutes = self.target_duration // 60
        seconds = self.target_duration % 60
        return f"{minutes}:{seconds:02d}"

    def __repr__(self) -> str:
        return f"Spec(id={self.spec_id[:8]}, topic='{self.topic[:20]}...', style={self.style.value})"


@dataclass
class Script(BaseModel):
    """
    脚本实体

    基于 data.spec.md 2.2 Script Schema
    内容的文本形态，从规约生成
    """

    # 主键
    script_id: str = field(default_factory=generate_uuid)

    # 关联
    video_id: Optional[str] = None
    spec_id: Optional[str] = None

    # 版本
    version: int = 1

    # 内容
    title: str = ""
    content: str = ""  # Markdown 格式

    # 统计
    word_count: Optional[int] = None
    estimated_duration: Optional[int] = None  # 秒

    # SEO
    seo_score: Optional[int] = None  # 0-100

    # 状态
    status: ScriptStatus = ScriptStatus.DRAFT

    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # ============================================================
    # 验证方法
    # ============================================================

    def validate(self) -> List[str]:
        """验证脚本数据"""
        errors = []

        if not self.title:
            errors.append("标题不能为空")

        if not self.content:
            errors.append("内容不能为空")

        if self.seo_score is not None:
            if self.seo_score < 0 or self.seo_score > 100:
                errors.append(f"SEO分数应在0-100之间: {self.seo_score}")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    # ============================================================
    # 内容分析方法
    # ============================================================

    def calculate_word_count(self) -> int:
        """计算字数"""
        import re
        # 移除 Markdown 标记
        text = re.sub(r'[#*`\[\]()>-]', '', self.content)
        # 中文按字符计数，英文按单词计数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        self.word_count = chinese_chars + english_words
        return self.word_count

    def estimate_duration(self, words_per_minute: int = 180) -> int:
        """
        估算时长

        Args:
            words_per_minute: 每分钟字数（中文约150-200）

        Returns:
            预估秒数
        """
        if self.word_count is None:
            self.calculate_word_count()

        minutes = (self.word_count or 0) / words_per_minute
        self.estimated_duration = int(minutes * 60)
        return self.estimated_duration

    # ============================================================
    # 状态方法
    # ============================================================

    def submit_for_review(self) -> bool:
        """提交审核"""
        if self.status == ScriptStatus.DRAFT:
            self.status = ScriptStatus.REVIEWING
            self.updated_at = datetime.now()
            return True
        return False

    def approve(self) -> bool:
        """审核通过"""
        if self.status == ScriptStatus.REVIEWING:
            self.status = ScriptStatus.APPROVED
            self.updated_at = datetime.now()
            return True
        return False

    def archive(self) -> None:
        """归档"""
        self.status = ScriptStatus.ARCHIVED
        self.updated_at = datetime.now()

    # ============================================================
    # 序列化方法
    # ============================================================

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Script':
        """从字典创建实例"""
        return cls(
            script_id=data.get('script_id', generate_uuid()),
            video_id=data.get('video_id'),
            spec_id=data.get('spec_id'),
            version=data.get('version', 1),
            title=data.get('title', ''),
            content=data.get('content', ''),
            word_count=data.get('word_count'),
            estimated_duration=data.get('estimated_duration'),
            seo_score=data.get('seo_score'),
            status=parse_enum(ScriptStatus, data.get('status'), ScriptStatus.DRAFT),
            created_at=parse_datetime(data.get('created_at')) or datetime.now(),
            updated_at=parse_datetime(data.get('updated_at')) or datetime.now(),
        )

    @property
    def is_approved(self) -> bool:
        return self.status == ScriptStatus.APPROVED

    @property
    def duration_formatted(self) -> str:
        """格式化预估时长"""
        if not self.estimated_duration:
            return "未估算"

        minutes = self.estimated_duration // 60
        seconds = self.estimated_duration % 60
        return f"{minutes}:{seconds:02d}"

    def __repr__(self) -> str:
        return f"Script(id={self.script_id[:8]}, title='{self.title[:20]}...', status={self.status.value})"


# ============================================================
# 工厂函数
# ============================================================

def create_spec(
    topic: str,
    target_duration: int = 600,
    style: ContentStyle = ContentStyle.TUTORIAL,
    **kwargs
) -> Spec:
    """创建新规约"""
    return Spec(
        topic=topic,
        target_duration=target_duration,
        style=style,
        **kwargs
    )


def create_script(
    title: str,
    content: str,
    spec_id: Optional[str] = None,
    **kwargs
) -> Script:
    """创建新脚本"""
    script = Script(
        title=title,
        content=content,
        spec_id=spec_id,
        **kwargs
    )
    script.calculate_word_count()
    script.estimate_duration()
    return script
