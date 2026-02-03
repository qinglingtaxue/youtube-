#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
提供统一的配置加载和管理功能

支持：
- YAML/JSON 配置文件
- 环境变量覆盖
- secrets.yaml 敏感信息分离
- 点号分隔的层级键访问

引用规约：
- sys.spec.md: 共享模块 Config 组件
- data.spec.md: 配置文件格式规约
"""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from .logger import setup_logger

logger = setup_logger('config')


class Config:
    """
    配置管理类

    支持多层配置合并：
    1. 默认配置
    2. settings.yaml 主配置
    3. secrets.yaml 敏感配置
    4. 环境变量覆盖
    """

    def __init__(self, config_path: Optional[str] = None, secrets_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 主配置文件路径
            secrets_path: 敏感信息配置文件路径
        """
        self.config_path = config_path
        self.secrets_path = secrets_path
        self._config: Dict[str, Any] = {}
        self._secrets: Dict[str, Any] = {}
        self._load_config()
        self._load_secrets()
        self._apply_env_overrides()

    def _load_config(self):
        """加载配置文件"""
        if not self.config_path:
            # 默认配置文件路径
            default_path = Path(__file__).parent.parent.parent / 'config' / 'config.yaml'
            if default_path.exists():
                self.config_path = str(default_path)
            else:
                logger.warning(f"未找到配置文件，使用默认配置")
                self._config = self._get_default_config()
                return

        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.warning(f"配置文件不存在: {self.config_path}")
                self._config = self._get_default_config()
                return

            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    self._config = yaml.safe_load(f) or {}
                elif config_file.suffix.lower() == '.json':
                    self._config = json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {config_file.suffix}")

            logger.info(f"成功加载配置文件: {self.config_path}")

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config = self._get_default_config()

    def _load_secrets(self):
        """加载敏感信息配置文件"""
        if not self.secrets_path:
            # 默认 secrets 路径
            default_path = Path(__file__).parent.parent.parent / 'config' / 'secrets.yaml'
            if default_path.exists():
                self.secrets_path = str(default_path)
            else:
                logger.debug("未找到 secrets.yaml，跳过敏感信息加载")
                return

        try:
            secrets_file = Path(self.secrets_path)
            if not secrets_file.exists():
                logger.debug(f"secrets 文件不存在: {self.secrets_path}")
                return

            with open(secrets_file, 'r', encoding='utf-8') as f:
                self._secrets = yaml.safe_load(f) or {}

            logger.info(f"成功加载 secrets 文件: {self.secrets_path}")

        except Exception as e:
            logger.error(f"加载 secrets 文件失败: {e}")

    def _apply_env_overrides(self):
        """应用环境变量覆盖配置

        环境变量命名规则：YTP_{SECTION}_{KEY}
        例如：YTP_YOUTUBE_API_KEY -> youtube.api_key
        """
        prefix = "YTP_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 转换环境变量名为配置键
                # YTP_YOUTUBE_API_KEY -> youtube.api_key
                config_key = key[len(prefix):].lower().replace('_', '.', 1)
                # 后续的下划线保留
                parts = config_key.split('.', 1)
                if len(parts) == 2:
                    config_key = f"{parts[0]}.{parts[1].replace('_', '.')}"

                # 尝试类型转换
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        pass  # 保持字符串

                self.set(config_key, value)
                logger.debug(f"环境变量覆盖配置: {config_key}")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置

        配置结构与 data.spec.md 和 api.spec.md 保持一致
        """
        return {
            # 项目基础配置
            'project': {
                'name': 'youtube-pipeline',
                'version': '1.0.0',
                'data_dir': 'data',
                'config_dir': 'config',
                'logs_dir': 'logs',
            },
            # 数据库配置
            'database': {
                'path': 'data/youtube_pipeline.db',
                'echo': False,  # SQL 日志
                'pool_size': 5,
            },
            # YouTube 相关配置
            'youtube': {
                'api_key': None,
                'max_results': 50,
                'region_code': 'US',
                'language': 'zh',
                'timeout': 30,
                'rate_limit_delay': 2,  # 请求间隔（秒）
            },
            # 调研模块配置
            'research': {
                'max_videos': 100,
                'min_views': 1000,
                'min_likes': 50,
                'max_duration': 3600,
                'patterns': ['cognitive_impact', 'storytelling', 'knowledge_sharing', 'interaction_guide'],
            },
            # 策划模块配置
            'planning': {
                'default_style': 'tutorial',
                'target_duration': 600,
                'seo_min_score': 70,
            },
            # 制作模块配置
            'production': {
                'resolution': '1080p',
                'video_codec': 'libx264',
                'audio_codec': 'aac',
                'audio_bitrate': '192k',
                'thumbnail_width': 1280,
                'thumbnail_height': 720,
            },
            # 发布模块配置
            'publishing': {
                'default_privacy': 'private',
                'upload_timeout': 3600,
                'retry_count': 3,
                'retry_delay': 60,
            },
            # 复盘模块配置
            'analytics': {
                'default_period': '7d',
                'collect_delay_days': 7,
            },
            # 分析模块配置（保持兼容）
            'analysis': {
                'min_pattern_frequency': 3,
                'similarity_threshold': 0.8,
                'sentiment_threshold': 0.6,
                'max_keywords': 20,
            },
            # 模板配置（保持兼容）
            'template': {
                'output_dir': 'output',
                'format': 'markdown',
                'max_length': 5000,
                'include_metadata': True,
            },
            # 工作流配置（保持兼容）
            'workflow': {
                'event1_batch_size': 10,
                'event2_top_patterns': 5,
                'event3_min_templates': 3,
                'save_intermediate': True,
            },
            # 日志配置
            'logging': {
                'level': 'INFO',
                'file': 'logs/youtube_pipeline.log',
                'console': True,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        查找顺序：
        1. 主配置 (_config)
        2. 敏感配置 (_secrets)
        3. 默认值

        Args:
            key: 配置键，支持点号分隔的层级键，如 'youtube.api_key'
            default: 默认值

        Returns:
            配置值
        """
        # 先从主配置查找
        value = self._get_nested(self._config, key)
        if value is not None:
            return value

        # 再从 secrets 查找
        value = self._get_nested(self._secrets, key)
        if value is not None:
            return value

        return default

    def _get_nested(self, data: Dict, key: str) -> Any:
        """从嵌套字典中获取值"""
        keys = key.split('.')
        value = data

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return None

    def get_secret(self, key: str, default: Any = None) -> Any:
        """
        获取敏感配置值（仅从 secrets 中查找）

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        value = self._get_nested(self._secrets, key)
        return value if value is not None else default

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键，支持点号分隔的层级键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config

        # 创建嵌套字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value
        logger.debug(f"设置配置: {key} = {value}")

    def save(self, file_path: Optional[str] = None):
        """
        保存配置到文件

        Args:
            file_path: 保存路径，如果为None则保存到原路径
        """
        save_path = file_path or self.config_path
        if not save_path:
            raise ValueError("未指定保存路径")

        save_file = Path(save_path)
        save_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(save_file, 'w', encoding='utf-8') as f:
                if save_file.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
                elif save_file.suffix.lower() == '.json':
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"不支持的配置文件格式: {save_file.suffix}")

            logger.info(f"配置已保存到: {save_path}")

        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """返回配置的字典副本"""
        return self._config.copy()

    def update(self, config_dict: Dict[str, Any]):
        """
        批量更新配置

        Args:
            config_dict: 配置字典
        """
        self._config.update(config_dict)
        logger.info(f"批量更新配置: {len(config_dict)} 项")

# 全局配置实例
_global_config = None

def get_config() -> Config:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def reload_config(config_path: Optional[str] = None, secrets_path: Optional[str] = None):
    """重新加载配置"""
    global _global_config
    _global_config = Config(config_path, secrets_path)
    return _global_config


def get_project_root() -> Path:
    """获取项目根目录"""
    # 从 src/utils/config.py 向上两级
    return Path(__file__).parent.parent.parent


def get_data_dir() -> Path:
    """获取数据目录"""
    config = get_config()
    data_dir = config.get('project.data_dir', 'data')
    return get_project_root() / data_dir


def get_config_dir() -> Path:
    """获取配置目录"""
    config = get_config()
    config_dir = config.get('project.config_dir', 'config')
    return get_project_root() / config_dir


def get_logs_dir() -> Path:
    """获取日志目录"""
    config = get_config()
    logs_dir = config.get('project.logs_dir', 'logs')
    return get_project_root() / logs_dir
