#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作工具模块
提供文件读写、目录管理等工具函数

引用规约：
- data.spec.md: 文件格式规约、存储路径
- real.md: #4 存储与成本控制（滚动清理策略）
- sys.spec.md: 共享模块 FileUtils 组件
"""

import json
import csv
import pickle
import shutil
import hashlib
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
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


# ==================== YAML 文件操作 ====================

def read_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    读取 YAML 文件

    Args:
        file_path: YAML 文件路径

    Returns:
        YAML 数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        logger.debug(f"成功读取 YAML 文件: {file_path}")
        return data
    except Exception as e:
        logger.error(f"读取 YAML 文件失败 {file_path}: {e}")
        raise


def write_yaml(file_path: Union[str, Path], data: Dict[str, Any]):
    """
    写入 YAML 文件

    Args:
        file_path: YAML 文件路径
        data: 要写入的数据
    """
    try:
        ensure_dir(Path(file_path).parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        logger.debug(f"成功写入 YAML 文件: {file_path}")
    except Exception as e:
        logger.error(f"写入 YAML 文件失败 {file_path}: {e}")
        raise


# ==================== 安全文件名 ====================

def safe_filename(name: str, max_length: int = 200) -> str:
    """
    生成安全的文件名

    Args:
        name: 原始名称
        max_length: 最大长度

    Returns:
        安全的文件名
    """
    # 移除或替换非法字符
    import re
    safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    # 移除首尾空格和点
    safe_name = safe_name.strip(' .')
    # 限制长度
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]
    return safe_name


def generate_unique_filename(base_name: str, extension: str, directory: Union[str, Path] = None) -> str:
    """
    生成唯一文件名

    Args:
        base_name: 基础名称
        extension: 扩展名（不含点）
        directory: 目录路径，用于检查重名

    Returns:
        唯一文件名
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_base = safe_filename(base_name)
    filename = f"{safe_base}_{timestamp}.{extension}"

    if directory:
        dir_path = Path(directory)
        counter = 1
        while (dir_path / filename).exists():
            filename = f"{safe_base}_{timestamp}_{counter}.{extension}"
            counter += 1

    return filename


# ==================== 滚动清理策略（real.md #4） ====================

def cleanup_old_files(
    dir_path: Union[str, Path],
    pattern: str = '*',
    max_age_days: int = 30,
    max_count: int = None,
    max_size_mb: int = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    滚动清理旧文件

    基于 real.md #4 存储与成本控制约束

    Args:
        dir_path: 目录路径
        pattern: 文件匹配模式
        max_age_days: 最大保留天数
        max_count: 最大保留文件数
        max_size_mb: 最大总大小 (MB)
        dry_run: 是否模拟执行

    Returns:
        清理统计信息
    """
    path = Path(dir_path)
    if not path.exists():
        return {'deleted': 0, 'freed_bytes': 0}

    files = list(path.glob(pattern))
    files = [f for f in files if f.is_file()]

    # 按修改时间排序（最新在前）
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    to_delete = []
    cutoff_date = datetime.now() - timedelta(days=max_age_days)

    # 按时间筛选
    for f in files:
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff_date:
            to_delete.append(f)

    # 按数量筛选
    if max_count and len(files) > max_count:
        for f in files[max_count:]:
            if f not in to_delete:
                to_delete.append(f)

    # 按大小筛选
    if max_size_mb:
        max_bytes = max_size_mb * 1024 * 1024
        total_size = sum(f.stat().st_size for f in files)

        if total_size > max_bytes:
            # 从最旧的开始删除
            for f in reversed(files):
                if f not in to_delete and total_size > max_bytes:
                    to_delete.append(f)
                    total_size -= f.stat().st_size

    # 执行删除
    deleted_count = 0
    freed_bytes = 0

    for f in to_delete:
        file_size = f.stat().st_size
        if not dry_run:
            f.unlink()
        deleted_count += 1
        freed_bytes += file_size
        logger.debug(f"{'[DRY RUN] ' if dry_run else ''}删除: {f}")

    result = {
        'deleted': deleted_count,
        'freed_bytes': freed_bytes,
        'freed_mb': freed_bytes / (1024 * 1024),
        'remaining': len(files) - deleted_count
    }

    logger.info(f"清理完成: 删除 {deleted_count} 个文件，释放 {result['freed_mb']:.2f} MB")
    return result


def get_directory_size(dir_path: Union[str, Path]) -> int:
    """
    获取目录总大小

    Args:
        dir_path: 目录路径

    Returns:
        总大小（字节）
    """
    path = Path(dir_path)
    if not path.exists():
        return 0

    total_size = 0
    for f in path.rglob('*'):
        if f.is_file():
            total_size += f.stat().st_size

    return total_size


def check_disk_space(min_free_gb: float = 10.0) -> Dict[str, Any]:
    """
    检查磁盘空间

    基于 real.md #4 约束：磁盘剩余空间 > 指定值

    Args:
        min_free_gb: 最小剩余空间 (GB)

    Returns:
        磁盘空间信息
    """
    import shutil

    total, used, free = shutil.disk_usage('/')

    result = {
        'total_gb': total / (1024 ** 3),
        'used_gb': used / (1024 ** 3),
        'free_gb': free / (1024 ** 3),
        'free_percent': (free / total) * 100,
        'min_required_gb': min_free_gb,
        'sufficient': (free / (1024 ** 3)) >= min_free_gb
    }

    if not result['sufficient']:
        logger.warning(f"磁盘空间不足: {result['free_gb']:.2f} GB < {min_free_gb} GB")

    return result


# ==================== 文件哈希 ====================

def file_hash(file_path: Union[str, Path], algorithm: str = 'md5') -> str:
    """
    计算文件哈希

    Args:
        file_path: 文件路径
        algorithm: 哈希算法 (md5, sha1, sha256)

    Returns:
        哈希值（十六进制）
    """
    hash_func = hashlib.new(algorithm)

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)

    return hash_func.hexdigest()


# ==================== 目录结构初始化 ====================

def init_project_structure(base_dir: Union[str, Path] = None) -> Dict[str, Path]:
    """
    初始化项目目录结构

    基于 sys.spec.md 的目录结构定义

    Args:
        base_dir: 项目根目录

    Returns:
        创建的目录路径映射
    """
    if base_dir is None:
        base_dir = Path.cwd()
    else:
        base_dir = Path(base_dir)

    directories = {
        'data': base_dir / 'data',
        'data_assets': base_dir / 'data' / 'assets',
        'data_videos': base_dir / 'data' / 'videos',
        'data_transcripts': base_dir / 'data' / 'transcripts',
        'data_thumbnails': base_dir / 'data' / 'thumbnails',
        'data_reports': base_dir / 'data' / 'reports',
        'config': base_dir / 'config',
        'logs': base_dir / 'logs',
        'output': base_dir / 'output',
        'scripts': base_dir / 'scripts',
        'specs': base_dir / 'specs',
    }

    for name, path in directories.items():
        ensure_dir(path)
        logger.debug(f"确保目录存在: {path}")

    logger.info(f"项目目录结构初始化完成: {base_dir}")
    return directories


# ==================== 文件监控 ====================

def watch_file(
    file_path: Union[str, Path],
    callback: Callable[[Path], None],
    interval: float = 1.0,
    timeout: float = None
) -> bool:
    """
    监控文件变化

    Args:
        file_path: 要监控的文件路径
        callback: 文件变化时的回调函数
        interval: 检查间隔（秒）
        timeout: 超时时间（秒），None 表示无限等待

    Returns:
        是否检测到变化
    """
    import time

    path = Path(file_path)
    start_time = time.time()
    last_mtime = path.stat().st_mtime if path.exists() else None

    while True:
        if timeout and (time.time() - start_time) > timeout:
            return False

        if path.exists():
            current_mtime = path.stat().st_mtime
            if last_mtime is None or current_mtime != last_mtime:
                callback(path)
                last_mtime = current_mtime
                return True

        time.sleep(interval)


def copy_file(src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False) -> Path:
    """
    复制文件

    Args:
        src: 源文件路径
        dst: 目标路径（文件或目录）
        overwrite: 是否覆盖已存在的文件

    Returns:
        目标文件路径
    """
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        raise FileNotFoundError(f"源文件不存在: {src_path}")

    if dst_path.is_dir():
        dst_path = dst_path / src_path.name

    if dst_path.exists() and not overwrite:
        raise FileExistsError(f"目标文件已存在: {dst_path}")

    ensure_dir(dst_path.parent)
    shutil.copy2(src_path, dst_path)

    logger.debug(f"复制文件: {src_path} -> {dst_path}")
    return dst_path


def move_file(src: Union[str, Path], dst: Union[str, Path], overwrite: bool = False) -> Path:
    """
    移动文件

    Args:
        src: 源文件路径
        dst: 目标路径（文件或目录）
        overwrite: 是否覆盖已存在的文件

    Returns:
        目标文件路径
    """
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        raise FileNotFoundError(f"源文件不存在: {src_path}")

    if dst_path.is_dir():
        dst_path = dst_path / src_path.name

    if dst_path.exists() and not overwrite:
        raise FileExistsError(f"目标文件已存在: {dst_path}")

    ensure_dir(dst_path.parent)
    shutil.move(str(src_path), str(dst_path))

    logger.debug(f"移动文件: {src_path} -> {dst_path}")
    return dst_path
