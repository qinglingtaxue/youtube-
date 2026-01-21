#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 数据模型
工作流任务实体 - 贯穿五个阶段的任务调度

引用规约：
- data.spec.md: 2.8 Task Schema
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import (
    BaseModel,
    Stage,
    TaskStatus,
    generate_uuid,
    parse_datetime,
    parse_enum,
    parse_json_field,
)


@dataclass
class Task(BaseModel):
    """
    工作流任务实体

    基于 data.spec.md 2.8 Task Schema
    用于跟踪各阶段的执行任务
    """

    # 主键
    task_id: str = field(default_factory=generate_uuid)

    # 关联
    video_id: Optional[str] = None

    # 任务定义
    stage: Stage = Stage.RESEARCH
    type: str = ""  # 任务类型，如 collect_videos, generate_script

    # 状态
    status: TaskStatus = TaskStatus.PENDING

    # 数据
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    # 重试
    retry_count: int = 0
    max_retries: int = 3

    # 时间
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    # ============================================================
    # 验证方法
    # ============================================================

    def validate(self) -> List[str]:
        """验证任务数据"""
        errors = []

        if not self.type:
            errors.append("任务类型不能为空")

        if self.retry_count < 0:
            errors.append("重试次数不能为负数")

        return errors

    def is_valid(self) -> bool:
        return len(self.validate()) == 0

    # ============================================================
    # 状态方法
    # ============================================================

    def start(self) -> bool:
        """
        开始执行任务

        Returns:
            是否成功启动
        """
        if self.status != TaskStatus.PENDING:
            return False

        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        return True

    def complete(self, output: Optional[Dict[str, Any]] = None) -> None:
        """
        完成任务

        Args:
            output: 任务输出数据
        """
        self.status = TaskStatus.COMPLETED
        self.output_data = output
        self.completed_at = datetime.now()

    def fail(self, error: str) -> None:
        """
        任务失败

        Args:
            error: 错误信息
        """
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now()

    def cancel(self) -> bool:
        """
        取消任务

        Returns:
            是否成功取消
        """
        if self.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return False

        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
        return True

    def retry(self) -> bool:
        """
        重试任务

        Returns:
            是否可以重试
        """
        if self.status != TaskStatus.FAILED:
            return False

        if self.retry_count >= self.max_retries:
            return False

        self.retry_count += 1
        self.status = TaskStatus.PENDING
        self.error_message = None
        self.started_at = None
        self.completed_at = None
        return True

    def reset(self) -> None:
        """重置任务状态"""
        self.status = TaskStatus.PENDING
        self.output_data = None
        self.error_message = None
        self.retry_count = 0
        self.started_at = None
        self.completed_at = None

    # ============================================================
    # 状态检查
    # ============================================================

    @property
    def is_pending(self) -> bool:
        return self.status == TaskStatus.PENDING

    @property
    def is_running(self) -> bool:
        return self.status == TaskStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status == TaskStatus.FAILED

    @property
    def is_cancelled(self) -> bool:
        return self.status == TaskStatus.CANCELLED

    @property
    def is_finished(self) -> bool:
        """任务是否已结束（无论成功或失败）"""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED
        ]

    @property
    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.is_failed and self.retry_count < self.max_retries

    # ============================================================
    # 时间计算
    # ============================================================

    @property
    def duration_seconds(self) -> Optional[float]:
        """
        任务执行时长（秒）

        Returns:
            时长秒数，未完成返回 None
        """
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    @property
    def duration_formatted(self) -> str:
        """格式化执行时长"""
        seconds = self.duration_seconds
        if seconds is None:
            return "N/A"

        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    @property
    def stage_name(self) -> str:
        """阶段中文名"""
        names = {
            Stage.RESEARCH: "调研",
            Stage.PLANNING: "策划",
            Stage.PRODUCTION: "制作",
            Stage.PUBLISHING: "发布",
            Stage.ANALYTICS: "复盘",
        }
        return names.get(self.stage, "未知")

    @property
    def status_name(self) -> str:
        """状态中文名"""
        names = {
            TaskStatus.PENDING: "待执行",
            TaskStatus.RUNNING: "执行中",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "失败",
            TaskStatus.CANCELLED: "已取消",
        }
        return names.get(self.status, "未知")

    # ============================================================
    # 序列化方法
    # ============================================================

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建实例"""
        return cls(
            task_id=data.get('task_id', generate_uuid()),
            video_id=data.get('video_id'),
            stage=parse_enum(Stage, data.get('stage'), Stage.RESEARCH),
            type=data.get('type', ''),
            status=parse_enum(TaskStatus, data.get('status'), TaskStatus.PENDING),
            input_data=parse_json_field(data.get('input_data')),
            output_data=parse_json_field(data.get('output_data')),
            error_message=data.get('error_message'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            started_at=parse_datetime(data.get('started_at')),
            completed_at=parse_datetime(data.get('completed_at')),
            created_at=parse_datetime(data.get('created_at')) or datetime.now(),
        )

    def __repr__(self) -> str:
        return f"Task(id={self.task_id[:8]}, stage={self.stage.value}, type='{self.type}', status={self.status.value})"


# ============================================================
# 工厂函数
# ============================================================

def create_task(
    stage: Stage,
    task_type: str,
    video_id: Optional[str] = None,
    input_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Task:
    """
    创建新任务

    Args:
        stage: 所属阶段
        task_type: 任务类型
        video_id: 关联视频 ID
        input_data: 输入数据
    """
    return Task(
        stage=stage,
        type=task_type,
        video_id=video_id,
        input_data=input_data,
        **kwargs
    )


# ============================================================
# 预定义任务类型
# ============================================================

class TaskTypes:
    """任务类型常量"""

    # 调研阶段
    COLLECT_VIDEOS = "collect_videos"
    ANALYZE_PATTERNS = "analyze_patterns"
    GENERATE_REPORT = "generate_report"

    # 策划阶段
    CREATE_SPEC = "create_spec"
    GENERATE_SCRIPT = "generate_script"
    SEO_ANALYSIS = "seo_analysis"

    # 制作阶段
    GENERATE_AUDIO = "generate_audio"
    CREATE_VIDEO = "create_video"
    GENERATE_SUBTITLE = "generate_subtitle"
    CREATE_THUMBNAIL = "create_thumbnail"

    # 发布阶段
    UPLOAD_VIDEO = "upload_video"
    UPLOAD_THUMBNAIL = "upload_thumbnail"
    UPLOAD_SUBTITLE = "upload_subtitle"
    SCHEDULE_PUBLISH = "schedule_publish"

    # 复盘阶段
    COLLECT_ANALYTICS = "collect_analytics"
    GENERATE_ANALYTICS_REPORT = "generate_analytics_report"
