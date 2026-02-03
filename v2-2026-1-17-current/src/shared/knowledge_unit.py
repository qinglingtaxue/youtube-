"""
知识单元基础设施

核心理念：以知识单元为原子，多维并行检测，对齐标准，不达标就迭代，直到收敛

架构：
    KnowledgeUnit (知识单元)
        ↓
    ┌───┴───┐───┐
    检测器1  检测器2  检测器N  (并行检测)
    ↓       ↓       ↓
    结果1   结果2   结果N
        ↓
    AlignmentJudge (对齐判定器)
        ↓
    通过 → 输出 / 失败 → 迭代修复
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    TypeVar,
)
import asyncio
import logging

logger = logging.getLogger(__name__)


# ============================================================
# 1. 知识单元定义
# ============================================================


class KnowledgeUnitStatus(Enum):
    """知识单元状态"""
    DRAFT = "draft"          # 草稿，未经检测
    CHECKING = "checking"    # 检测中
    PASSED = "passed"        # 通过所有检测
    FAILED = "failed"        # 检测失败
    ITERATING = "iterating"  # 迭代修复中
    ARCHIVED = "archived"    # 已归档


@dataclass
class KnowledgeUnit:
    """
    知识单元基类

    每个知识单元是系统中最小的可独立处理单元，包括：
    - CompetitorVideo (竞品视频)
    - Pattern (模式)
    - Insight (洞察)
    - Report (报告)

    原则：
    1. 来源分离：记录数据来源
    2. 唯一编码：全局唯一ID
    3. 版本追踪：每次修改记录版本
    4. 状态流转：draft → checking → passed/failed → iterating → ...
    """

    # 核心标识
    ku_id: str                              # 唯一编码
    ku_type: str                            # 类型 (video/pattern/insight/report)

    # 来源追踪 (原则1)
    source: str = ""                        # 数据来源 (yt-dlp/manual/derived)
    source_id: Optional[str] = None         # 来源原始ID

    # 版本管理 (原则3)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 状态流转
    status: KnowledgeUnitStatus = KnowledgeUnitStatus.DRAFT

    # 质量评分
    quality_score: float = 0.0              # 综合质量分 0-1
    confidence: float = 0.0                 # 置信度 0-1

    # 检测结果记录
    detection_results: Dict[str, "DetectionResult"] = field(default_factory=dict)
    iteration_count: int = 0                # 迭代次数
    max_iterations: int = 3                 # 最大迭代次数

    # 可选元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def bump_version(self) -> None:
        """版本递增"""
        self.version += 1
        self.updated_at = datetime.now()

    def start_iteration(self) -> bool:
        """开始新一轮迭代，返回是否允许继续迭代"""
        if self.iteration_count >= self.max_iterations:
            logger.warning(f"KU {self.ku_id} 达到最大迭代次数 {self.max_iterations}")
            return False

        self.iteration_count += 1
        self.status = KnowledgeUnitStatus.ITERATING
        self.bump_version()
        return True

    def mark_passed(self, score: float, confidence: float) -> None:
        """标记为通过"""
        self.status = KnowledgeUnitStatus.PASSED
        self.quality_score = score
        self.confidence = confidence
        self.bump_version()

    def mark_failed(self, results: Dict[str, "DetectionResult"]) -> None:
        """标记为失败"""
        self.status = KnowledgeUnitStatus.FAILED
        self.detection_results = results
        self.bump_version()


# ============================================================
# 2. 检测结果定义
# ============================================================


class Severity(Enum):
    """严重程度"""
    CRITICAL = "critical"    # 致命，必须修复
    WARNING = "warning"      # 警告，建议修复
    INFO = "info"            # 信息，可忽略


@dataclass
class DetectionResult:
    """单个检测器的检测结果"""

    detector_name: str                      # 检测器名称
    passed: bool                            # 是否通过
    severity: Severity = Severity.INFO      # 严重程度
    score: float = 1.0                      # 该维度得分 0-1
    message: str = ""                       # 结果描述
    affected_fields: List[str] = field(default_factory=list)  # 受影响字段
    suggestions: List[str] = field(default_factory=list)      # 修复建议
    details: Dict[str, Any] = field(default_factory=dict)     # 详细数据
    checked_at: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        status = "✅" if self.passed else "❌"
        return f"{status} {self.detector_name}: {self.message} (score={self.score:.2f})"


# ============================================================
# 3. 检测器协议
# ============================================================

T = TypeVar("T", bound=KnowledgeUnit)


class Detector(Protocol[T]):
    """
    检测器协议

    每个检测器负责一个维度的检测，返回 DetectionResult
    """

    name: str

    def detect(self, ku: T) -> DetectionResult:
        """执行检测"""
        ...


class AsyncDetector(Protocol[T]):
    """异步检测器协议"""

    name: str

    async def detect(self, ku: T) -> DetectionResult:
        """异步执行检测"""
        ...


# ============================================================
# 4. 基础检测器实现
# ============================================================


class BaseDetector(ABC, Generic[T]):
    """检测器基类"""

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight  # 权重，用于计算综合分数

    @abstractmethod
    def detect(self, ku: T) -> DetectionResult:
        """执行检测，子类实现"""
        pass

    def _pass(
        self,
        message: str = "检测通过",
        score: float = 1.0,
        **kwargs
    ) -> DetectionResult:
        """快捷方法：返回通过结果"""
        return DetectionResult(
            detector_name=self.name,
            passed=True,
            severity=Severity.INFO,
            score=score,
            message=message,
            **kwargs
        )

    def _fail(
        self,
        message: str,
        severity: Severity = Severity.WARNING,
        score: float = 0.0,
        suggestions: Optional[List[str]] = None,
        **kwargs
    ) -> DetectionResult:
        """快捷方法：返回失败结果"""
        return DetectionResult(
            detector_name=self.name,
            passed=False,
            severity=severity,
            score=score,
            message=message,
            suggestions=suggestions or [],
            **kwargs
        )


# ============================================================
# 5. 对齐判定器
# ============================================================


@dataclass
class AlignmentPolicy:
    """对齐策略"""

    # 通过条件
    min_pass_rate: float = 1.0              # 最低通过率 (1.0 = 全部通过)
    min_score: float = 0.6                  # 最低综合分
    allow_warnings: bool = True             # 是否允许警告级别的失败

    # 迭代策略
    max_iterations: int = 3                 # 最大迭代次数
    auto_fix: bool = True                   # 是否自动修复


class AlignmentJudge:
    """
    对齐判定器

    职责：
    1. 汇总多个检测器的结果
    2. 根据策略判定是否通过
    3. 决定是输出还是迭代
    """

    def __init__(self, policy: Optional[AlignmentPolicy] = None):
        self.policy = policy or AlignmentPolicy()

    def judge(
        self,
        results: Dict[str, DetectionResult],
        weights: Optional[Dict[str, float]] = None
    ) -> tuple[bool, float, float, List[str]]:
        """
        判定是否通过

        Returns:
            (passed, score, confidence, failure_reasons)
        """
        if not results:
            return True, 1.0, 1.0, []

        weights = weights or {name: 1.0 for name in results}

        # 计算通过率
        passed_count = sum(1 for r in results.values() if r.passed)
        pass_rate = passed_count / len(results)

        # 计算加权分数
        total_weight = sum(weights.get(name, 1.0) for name in results)
        weighted_score = sum(
            r.score * weights.get(r.detector_name, 1.0)
            for r in results.values()
        ) / total_weight if total_weight > 0 else 0

        # 计算置信度 (基于通过率和分数的组合)
        confidence = (pass_rate + weighted_score) / 2

        # 收集失败原因
        failure_reasons = []
        for r in results.values():
            if not r.passed:
                if r.severity == Severity.CRITICAL:
                    failure_reasons.append(f"[CRITICAL] {r.message}")
                elif r.severity == Severity.WARNING and not self.policy.allow_warnings:
                    failure_reasons.append(f"[WARNING] {r.message}")

        # 判定
        passed = (
            pass_rate >= self.policy.min_pass_rate
            and weighted_score >= self.policy.min_score
            and (self.policy.allow_warnings or not any(
                r.severity == Severity.WARNING and not r.passed
                for r in results.values()
            ))
        )

        # 检查是否有 CRITICAL 失败
        has_critical_failure = any(
            r.severity == Severity.CRITICAL and not r.passed
            for r in results.values()
        )
        if has_critical_failure:
            passed = False

        return passed, weighted_score, confidence, failure_reasons


# ============================================================
# 6. 检测管线
# ============================================================


class DetectionPipeline(Generic[T]):
    """
    检测管线

    核心功能：
    1. 注册多个检测器
    2. 并行执行检测
    3. 汇总结果
    4. 判定是否通过
    5. 不通过则迭代
    """

    def __init__(
        self,
        name: str = "default",
        policy: Optional[AlignmentPolicy] = None,
        fix_strategy: Optional[Callable[[T, Dict[str, DetectionResult]], T]] = None
    ):
        self.name = name
        self.detectors: List[BaseDetector[T]] = []
        self.judge = AlignmentJudge(policy)
        self.fix_strategy = fix_strategy
        self.policy = policy or AlignmentPolicy()

    def register(self, detector: BaseDetector[T]) -> "DetectionPipeline[T]":
        """注册检测器"""
        self.detectors.append(detector)
        return self

    def detect(self, ku: T) -> Dict[str, DetectionResult]:
        """
        执行所有检测（同步）
        """
        results = {}
        for detector in self.detectors:
            try:
                result = detector.detect(ku)
                results[detector.name] = result
            except Exception as e:
                logger.error(f"检测器 {detector.name} 执行失败: {e}")
                results[detector.name] = DetectionResult(
                    detector_name=detector.name,
                    passed=False,
                    severity=Severity.CRITICAL,
                    score=0.0,
                    message=f"检测器执行异常: {str(e)}"
                )
        return results

    async def detect_async(self, ku: T) -> Dict[str, DetectionResult]:
        """
        并行执行所有检测（异步）
        """
        async def run_detector(detector: BaseDetector[T]) -> tuple[str, DetectionResult]:
            try:
                # 在线程池中执行同步检测器
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, detector.detect, ku)
                return detector.name, result
            except Exception as e:
                logger.error(f"检测器 {detector.name} 执行失败: {e}")
                return detector.name, DetectionResult(
                    detector_name=detector.name,
                    passed=False,
                    severity=Severity.CRITICAL,
                    score=0.0,
                    message=f"检测器执行异常: {str(e)}"
                )

        # 并行执行所有检测器
        tasks = [run_detector(d) for d in self.detectors]
        results_list = await asyncio.gather(*tasks)

        return dict(results_list)

    def process(self, ku: T) -> tuple[T, bool, Dict[str, DetectionResult]]:
        """
        处理知识单元：检测 + 判定 + 迭代

        Returns:
            (processed_ku, passed, final_results)
        """
        ku.status = KnowledgeUnitStatus.CHECKING

        for iteration in range(self.policy.max_iterations):
            # 执行检测
            results = self.detect(ku)

            # 获取权重
            weights = {d.name: d.weight for d in self.detectors}

            # 判定
            passed, score, confidence, reasons = self.judge.judge(results, weights)

            if passed:
                ku.mark_passed(score, confidence)
                logger.info(f"KU {ku.ku_id} 通过检测 (iteration={iteration+1}, score={score:.2f})")
                return ku, True, results

            # 未通过，尝试迭代修复
            if not ku.start_iteration():
                ku.mark_failed(results)
                logger.warning(f"KU {ku.ku_id} 达到最大迭代次数，检测失败")
                return ku, False, results

            # 执行修复策略
            if self.fix_strategy and self.policy.auto_fix:
                try:
                    ku = self.fix_strategy(ku, results)
                    logger.info(f"KU {ku.ku_id} 执行修复策略 (iteration={iteration+1})")
                except Exception as e:
                    logger.error(f"修复策略执行失败: {e}")
            else:
                # 无修复策略，直接失败
                ku.mark_failed(results)
                return ku, False, results

        # 超出迭代次数
        ku.mark_failed(results)
        return ku, False, results

    async def process_async(self, ku: T) -> tuple[T, bool, Dict[str, DetectionResult]]:
        """异步处理知识单元"""
        ku.status = KnowledgeUnitStatus.CHECKING

        for iteration in range(self.policy.max_iterations):
            results = await self.detect_async(ku)
            weights = {d.name: d.weight for d in self.detectors}
            passed, score, confidence, reasons = self.judge.judge(results, weights)

            if passed:
                ku.mark_passed(score, confidence)
                return ku, True, results

            if not ku.start_iteration():
                ku.mark_failed(results)
                return ku, False, results

            if self.fix_strategy and self.policy.auto_fix:
                try:
                    ku = self.fix_strategy(ku, results)
                except Exception as e:
                    logger.error(f"修复策略执行失败: {e}")
                    ku.mark_failed(results)
                    return ku, False, results

        ku.mark_failed(results)
        return ku, False, results


# ============================================================
# 7. 便捷工厂函数
# ============================================================


def create_pipeline(
    name: str,
    detectors: List[BaseDetector],
    min_score: float = 0.6,
    max_iterations: int = 3,
    fix_strategy: Optional[Callable] = None
) -> DetectionPipeline:
    """
    快速创建检测管线

    Example:
        pipeline = create_pipeline(
            name="video_quality",
            detectors=[
                CompletenessDetector(),
                ConsistencyDetector(),
                ValidityDetector(),
            ],
            min_score=0.7,
            max_iterations=2
        )

        ku, passed, results = pipeline.process(video_ku)
    """
    policy = AlignmentPolicy(
        min_score=min_score,
        max_iterations=max_iterations,
        auto_fix=fix_strategy is not None
    )

    pipeline = DetectionPipeline(name=name, policy=policy, fix_strategy=fix_strategy)

    for detector in detectors:
        pipeline.register(detector)

    return pipeline
