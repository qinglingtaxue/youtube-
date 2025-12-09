#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作工具模块
提供文件读写、目录管理等工具函数
"""

import json
import csv
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from .logger import setup_logger

logger = setup_logger('file_utils')

def ensure_dir(dir_path: Union[str, Path]):
    """
    确保目录存在

    Args:
        dir_path: 目录路径
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"确保目录存在: {path}")

def read_text(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """
    读取文本文件

    Args:
        file_path: 文件路径
        encoding: 编码格式

    Returns:
        文件内容
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        logger.debug(f"成功读取文本文件: {file_path}")
        return content
    except Exception as e:
        logger.error(f"读取文本文件失败 {file_path}: {e}")
        raise

def write_text(file_path: Union[str, Path], content: str, encoding: str = 'utf-8'):
    """
    写入文本文件

    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 编码格式
    """
    try:
        ensure_dir(Path(file_path).parent)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        logger.debug(f"成功写入文本文件: {file_path}")
    except Exception as e:
        logger.error(f"写入文本文件失败 {file_path}: {e}")
        raise

def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    读取JSON文件

    Args:
        file_path: JSON文件路径

    Returns:
        JSON数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"成功读取JSON文件: {file_path}")
        return data
    except Exception as e:
        logger.error(f"读取JSON文件失败 {file_path}: {e}")
        raise

def write_json(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2):
    """
    写入JSON文件

    Args:
        file_path: JSON文件路径
        data: 要写入的数据
        indent: 缩进空格数
    """
    try:
        ensure_dir(Path(file_path).parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        logger.debug(f"成功写入JSON文件: {file_path}")
    except Exception as e:
        logger.error(f"写入JSON文件失败 {file_path}: {e}")
        raise

def read_csv(file_path: Union[str, Path]) -> List[Dict[str, str]]:
    """
    读取CSV文件

    Args:
        file_path: CSV文件路径

    Returns:
        CSV数据列表（每行一个字典）
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        logger.debug(f"成功读取CSV文件: {file_path}, 共{len(data)}行")
        return data
    except Exception as e:
        logger.error(f"读取CSV文件失败 {file_path}: {e}")
        raise

def write_csv(file_path: Union[str, Path], data: List[Dict[str, str]], fieldnames: Optional[List[str]] = None):
    """
    写入CSV文件

    Args:
        file_path: CSV文件路径
        data: 要写入的数据列表
        fieldnames: 字段名列表，如果为None则自动获取
    """
    try:
        ensure_dir(Path(file_path).parent)

        if not data:
            logger.warning("写入空数据到CSV文件")
            return

        if fieldnames is None:
            fieldnames = list(data[0].keys())

        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        logger.debug(f"成功写入CSV文件: {file_path}, 共{len(data)}行")
    except Exception as e:
        logger.error(f"写入CSV文件失败 {file_path}: {e}")
        raise

def read_pickle(file_path: Union[str, Path]) -> Any:
    """
    读取pickle文件

    Args:
        file_path: pickle文件路径

    Returns:
        pickle数据
    """
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        logger.debug(f"成功读取pickle文件: {file_path}")
        return data
    except Exception as e:
        logger.error(f"读取pickle文件失败 {file_path}: {e}")
        raise

def write_pickle(file_path: Union[str, Path], data: Any):
    """
    写入pickle文件

    Args:
        file_path: pickle文件路径
        data: 要写入的数据
    """
    try:
        ensure_dir(Path(file_path).parent)
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        logger.debug(f"成功写入pickle文件: {file_path}")
    except Exception as e:
        logger.error(f"写入pickle文件失败 {file_path}: {e}")
        raise

def list_files(dir_path: Union[str, Path], pattern: str = '*', recursive: bool = False) -> List[Path]:
    """
    列出目录中的文件

    Args:
        dir_path: 目录路径
        pattern: 文件名匹配模式
        recursive: 是否递归搜索子目录

    Returns:
        文件路径列表
    """
    try:
        path = Path(dir_path)
        if not path.exists():
            logger.warning(f"目录不存在: {path}")
            return []

        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        # 只返回文件，不包括目录
        files = [f for f in files if f.is_file()]
        logger.debug(f"在{path}中找到{len(files)}个文件")
        return files
    except Exception as e:
        logger.error(f"列出文件失败 {dir_path}: {e}")
        raise

def get_file_size(file_path: Union[str, Path]) -> int:
    """
    获取文件大小（字节）

    Args:
        file_path: 文件路径

    Returns:
        文件大小
    """
    try:
        size = Path(file_path).stat().st_size
        return size
    except Exception as e:
        logger.error(f"获取文件大小失败 {file_path}: {e}")
        raise

def get_file_mtime(file_path: Union[str, Path]) -> datetime:
    """
    获取文件修改时间

    Args:
        file_path: 文件路径

    Returns:
        修改时间
    """
    try:
        mtime = Path(file_path).stat().st_mtime
        return datetime.fromtimestamp(mtime)
    except Exception as e:
        logger.error(f"获取文件修改时间失败 {file_path}: {e}")
        raise

def backup_file(file_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    备份文件

    Args:
        file_path: 要备份的文件路径
        backup_dir: 备份目录，如果为None则在文件同目录创建备份

    Returns:
        备份文件路径
    """
    try:
        src_path = Path(file_path)
        if not src_path.exists():
            raise FileNotFoundError(f"文件不存在: {src_path}")

        if backup_dir:
            backup_path = Path(backup_dir)
            ensure_dir(backup_path)
            backup_file = backup_path / f"{src_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{src_path.suffix}"
        else:
            backup_file = src_path.parent / f"{src_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{src_path.suffix}"

        # 复制文件
        import shutil
        shutil.copy2(src_path, backup_file)
        logger.info(f"文件已备份到: {backup_file}")
        return backup_file

    except Exception as e:
        logger.error(f"备份文件失败 {file_path}: {e}")
        raise

def clean_dir(dir_path: Union[str, Path], pattern: str = '*', older_than_days: Optional[int] = None):
    """
    清理目录中的文件

    Args:
        dir_path: 目录路径
        pattern: 文件名匹配模式
        older_than_days: 只删除指定天数之前的文件，None表示删除所有匹配的文件
    """
    try:
        path = Path(dir_path)
        if not path.exists():
            logger.warning(f"目录不存在: {path}")
            return

        files = list(path.glob(pattern))
        files = [f for f in files if f.is_file()]

        deleted_count = 0
        for file_path in files:
            if older_than_days:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if (datetime.now() - file_mtime).days < older_than_days:
                    continue

            file_path.unlink()
            deleted_count += 1

        logger.info(f"清理完成，删除了{deleted_count}个文件")
    except Exception as e:
        logger.error(f"清理目录失败 {dir_path}: {e}")
        raise
