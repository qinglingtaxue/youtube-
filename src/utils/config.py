#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
提供统一的配置加载和管理功能
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from .logger import setup_logger

logger = setup_logger('config')

class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config = {}
        self._load_config()

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

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'youtube': {
                'api_key': None,
                'max_results': 50,
                'region_code': 'CN',
                'language': 'zh',
                'timeout': 30
            },
            'analysis': {
                'min_pattern_frequency': 3,
                'similarity_threshold': 0.8,
                'sentiment_threshold': 0.6,
                'max_keywords': 20
            },
            'template': {
                'output_dir': 'output',
                'format': 'markdown',
                'max_length': 5000,
                'include_metadata': True
            },
            'workflow': {
                'event1_batch_size': 10,
                'event2_top_patterns': 5,
                'event3_min_templates': 3,
                'save_intermediate': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/youtube_research.log',
                'console': True
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的层级键，如 'youtube.api_key'
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

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

def reload_config(config_path: Optional[str] = None):
    """重新加载配置"""
    global _global_config
    _global_config = Config(config_path)
    return _global_config
