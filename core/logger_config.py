# Copyright 2026 Sakura-频道总结助手
# 
# 本项目采用 GNU General Public License v3.0 (GPLv3) 许可证
# 
# 本项目源代码：https://github.com/Sakura520222/Sakura-Channel-Summary-Assistant-Pro
# 许可证全文：https://www.gnu.org/licenses/gpl-3.0.html

import os
import logging
import logging.handlers
import glob
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# 日志配置
LOG_DIR = os.getenv('LOG_DIR', 'log')
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '30'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# 创建基于时间戳的日志目录（每次启动）
SESSION_DIR = os.path.join(LOG_DIR, datetime.now().strftime('%Y%m%d_%H%M%S'))
os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(os.path.join(LOG_DIR, 'archive'), exist_ok=True)

# 日志级别映射
LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# 获取日志级别
def get_log_level(level_str: str) -> int:
    """将字符串日志级别转换为logging模块对应的级别常量"""
    return LOG_LEVEL_MAP.get(level_str.upper(), logging.INFO)

# 详细的日志格式
DETAILED_FORMAT = (
    '%(asctime)s - %(name)s - [%(levelname)s] - '
    '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s'
)

SIMPLE_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """配置一个logger实例
    
    Args:
        name: logger名称
        log_file: 日志文件名（不含路径），如果为None则只输出到控制台
        level: 日志级别
    
    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name)
    
    # 如果logger已经配置过，直接返回
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 避免日志传播到根logger
    logger.propagate = False
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(SIMPLE_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件）
    if log_file:
        log_path = os.path.join(SESSION_DIR, log_file)
        
        # 使用FileHandler（每次启动都是新文件）
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(DETAILED_FORMAT, DATE_FORMAT))
        logger.addHandler(file_handler)
    
    return logger

def setup_error_logger(name: str, log_file: str = None) -> logging.Logger:
    """配置错误日志logger（只记录ERROR及以上级别）
    
    Args:
        name: logger名称
        log_file: 日志文件名（不含路径）
    
    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name)
    
    if log_file:
        log_path = os.path.join(SESSION_DIR, log_file)
        
        # 使用FileHandler（每次启动都是新文件）
        error_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(DETAILED_FORMAT, DATE_FORMAT))
        logger.addHandler(error_handler)
    
    return logger


# 配置各个模块的logger
main_logger = setup_logger('main', 'main.log', get_log_level(LOG_LEVEL))
telegram_logger = setup_logger('telegram_client', 'telegram.log', get_log_level(LOG_LEVEL))
ai_logger = setup_logger('ai_client', 'ai_client.log', get_log_level(LOG_LEVEL))
database_logger = setup_logger('database', 'database.log', get_log_level(LOG_LEVEL))
scheduler_logger = setup_logger('scheduler', 'scheduler.log', get_log_level(LOG_LEVEL))
command_logger = setup_logger('command_handlers', 'command_handlers.log', get_log_level(LOG_LEVEL))

# 配置错误日志
setup_error_logger('main', 'error.log')
setup_error_logger('telegram_client', 'telegram_error.log')
setup_error_logger('ai_client', 'ai_error.log')
setup_error_logger('database', 'database_error.log')

# 创建控制台日志logger（记录所有输出到console.log）
console_logger = logging.getLogger('console')
console_logger.setLevel(logging.INFO)
console_logger.propagate = False

# 控制台日志文件
console_file_handler = logging.FileHandler(
    os.path.join(SESSION_DIR, 'console.log'),
    mode='a',
    encoding='utf-8'
)
console_file_handler.setLevel(logging.INFO)
console_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', DATE_FORMAT))
console_logger.addHandler(console_file_handler)

# 创建控制台输出捕获器
class ConsoleCapture:
    """捕获控制台输出并记录到console.log"""
    
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        
    def write(self, text):
        """写入数据"""
        # 先记录到console.log
        if text and text.strip():
            try:
                console_logger.info(text.strip())
            except Exception:
                pass
        
        # 再输出到原始stdout
        if self.original_stdout:
            try:
                self.original_stdout.write(text)
                self.original_stdout.flush()
            except Exception:
                pass
    
    def flush(self):
        """刷新缓冲区"""
        if self.original_stdout:
            try:
                self.original_stdout.flush()
            except Exception:
                pass

# 创建并设置控制台捕获器
console_capture = ConsoleCapture(sys.stdout)
sys.stdout = console_capture

# 向后兼容：创建根logger供模块使用
root_logger = logging.getLogger()
root_logger.setLevel(get_log_level(LOG_LEVEL))

# 移除根logger的所有默认handler
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# 添加控制台handler（使用被重定向后的sys.stdout）
console_handler = logging.StreamHandler()
console_handler.setLevel(get_log_level(LOG_LEVEL))
console_handler.setFormatter(logging.Formatter(SIMPLE_FORMAT, DATE_FORMAT))
root_logger.addHandler(console_handler)

logger = setup_logger(__name__, None, get_log_level(LOG_LEVEL))


def get_current_log_level() -> str:
    """获取当前日志级别
    
    Returns:
        str: 当前日志级别字符串 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    # 获取根 logger 的级别
    root_logger = logging.getLogger()
    level_num = root_logger.getEffectiveLevel()
    
    # 将数字级别转换为字符串
    level_str = None
    for name, num in LOG_LEVEL_MAP.items():
        if num == level_num:
            level_str = name
            break
    
    return level_str or 'INFO'


def update_all_loggers_level(level_str: str):
    """动态更新所有已创建的 logger 及其处理器的级别
    
    Args:
        level_str: 日志级别字符串 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    level = get_log_level(level_str)
    
    # 需要更新的 logger 列表
    logger_names = [
        'main',
        'telegram_client',
        'ai_client',
        'database',
        'scheduler',
        'command_handlers',
        __name__,
        'console'
    ]
    
    # 更新每个 logger 及其处理器
    for logger_name in logger_names:
        try:
            logger_obj = logging.getLogger(logger_name)
            logger_obj.setLevel(level)
            
            # 更新所有处理器的级别
            for handler in logger_obj.handlers:
                handler.setLevel(level)
        except Exception as e:
            print(f"更新 logger '{logger_name}' 级别时出错: {e}")
    
    # 更新根 logger 及其处理器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setLevel(level)
    
    print(f"已将所有日志级别更新为: {level_str}")


def _get_dir_size(dir_path: str) -> int:
    """
    计算目录的总大小
    
    Args:
        dir_path: 目录路径
    
    Returns:
        int: 目录大小（字节）
    """
    return sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, dirnames, filenames in os.walk(dir_path)
        for filename in filenames
    )


def _get_session_info(session_path: str, session_name: str) -> dict:
    """
    获取会话目录信息
    
    Args:
        session_path: 会话目录路径
        session_name: 会话目录名称
    
    Returns:
        dict: 会话信息字典
    """
    dir_mtime = datetime.fromtimestamp(os.path.getmtime(session_path))
    dir_size = _get_dir_size(session_path)
    return {
        'path': session_path,
        'name': session_name,
        'modified': dir_mtime,
        'size': dir_size,
        'size_mb': dir_size / (1024 * 1024)
    }


def _get_file_info(log_file: str, session_name: str) -> dict:
    """
    获取日志文件信息
    
    Args:
        log_file: 日志文件路径
        session_name: 所属会话名称
    
    Returns:
        dict: 文件信息字典
    """
    file_size = os.path.getsize(log_file)
    file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
    file_age = (datetime.now() - file_mtime).days
    return {
        'path': log_file,
        'size': file_size,
        'size_mb': file_size / (1024 * 1024),
        'modified': file_mtime,
        'age_days': file_age,
        'session': session_name
    }


def get_log_statistics() -> Dict:
    """获取日志统计信息
    
    Returns:
        包含日志统计信息的字典
    """
    stats = {
        'total_files': 0,
        'total_size': 0,
        'files': [],
        'session_dirs': []
    }
    
    # 遍历日志目录下的所有会话目录
    for item in os.listdir(LOG_DIR):
        item_path = os.path.join(LOG_DIR, item)
        if not (os.path.isdir(item_path) and '_' in item):
            continue
        
        try:
            # 获取会话信息
            session_info = _get_session_info(item_path, item)
            stats['session_dirs'].append(session_info)
            
            # 获取目录中的日志文件信息
            for log_file in glob.glob(os.path.join(item_path, '*.log')):
                file_info = _get_file_info(log_file, item)
                stats['total_files'] += 1
                stats['total_size'] += file_info['size']
                stats['files'].append(file_info)
        except Exception:
            pass
    
    # 按修改时间排序会话目录
    stats['session_dirs'].sort(key=lambda x: x['modified'], reverse=True)
    
    # 按文件大小排序
    stats['files'].sort(key=lambda x: x['size'], reverse=True)
    
    # 格式化总大小
    stats['total_size_mb'] = stats['total_size'] / (1024 * 1024)
    stats['total_size_gb'] = stats['total_size'] / (1024 * 1024 * 1024)
    
    return stats


def _find_old_session_dirs(cutoff_date: datetime) -> List[Dict]:
    """
    查找需要清理的旧会话目录
    
    Args:
        cutoff_date: 截止日期（会删除早于或等于此日期的目录）
    
    Returns:
        list: 旧会话目录列表
    """
    session_dirs = []
    for item in os.listdir(LOG_DIR):
        item_path = os.path.join(LOG_DIR, item)
        if not (os.path.isdir(item_path) and '_' in item):
            continue
        
        try:
            # 获取目录的修改时间
            dir_mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
            
            # 使用 <= 而不是 <，这样可以删除早于或等于截止日期的目录
            if dir_mtime <= cutoff_date:
                dir_size = _get_dir_size(item_path)
                session_dirs.append({
                    'path': item_path,
                    'name': item,
                    'modified': dir_mtime,
                    'size': dir_size
                })
        except Exception:
            pass
    
    return session_dirs


def _delete_session_dir(session_dir: Dict) -> tuple:
    """
    删除会话目录及其所有文件
    
    Args:
        session_dir: 会话目录信息
    
    Returns:
        tuple: (deleted_files列表, total_freed大小, error或None)
    """
    deleted_files = []
    total_freed = 0
    error = None
    
    try:
        # 删除目录中的所有文件
        for log_file in glob.glob(os.path.join(session_dir['path'], '*.log')):
            file_size = os.path.getsize(log_file)
            os.remove(log_file)
            deleted_files.append({
                'path': log_file,
                'size': file_size
            })
            total_freed += file_size
        
        # 删除空目录
        os.rmdir(session_dir['path'])
    except Exception as e:
        error = str(e)
    
    return deleted_files, total_freed, error


def clean_old_logs(days: int = 30, dry_run: bool = False) -> Dict:
    """清理旧日志文件
    
    Args:
        days: 保留最近多少天的日志
        dry_run: 是否只预览不删除
    
    Returns:
        清理结果字典
    """
    result = {
        'deleted_files': [],
        'deleted_dirs': [],
        'total_freed': 0,
        'errors': []
    }
    
    cutoff_date = datetime.now() - timedelta(days=days)
    session_dirs = _find_old_session_dirs(cutoff_date)
    
    # 处理每个会话目录
    for session_dir in session_dirs:
        if dry_run:
            # 预览模式，只记录不删除
            result['deleted_dirs'].append({
                'path': session_dir['path'],
                'name': session_dir['name'],
                'size': session_dir['size'],
                'modified': session_dir['modified']
            })
            result['total_freed'] += session_dir['size']
        else:
            # 执行删除
            deleted_files, freed_size, error = _delete_session_dir(session_dir)
            result['deleted_files'].extend(deleted_files)
            result['total_freed'] += freed_size
            
            if error:
                result['errors'].append({
                    'path': session_dir['path'],
                    'error': error
                })
            else:
                result['deleted_dirs'].append({
                    'path': session_dir['path'],
                    'name': session_dir['name'],
                    'size': session_dir['size'],
                    'modified': session_dir['modified']
                })
    
    # 格式化释放的空间
    result['total_freed_mb'] = result['total_freed'] / (1024 * 1024)
    
    return result


def get_clean_logs_summary(days: int = 30, dry_run: bool = False) -> str:
    """生成日志清理的摘要信息
    
    Args:
        days: 保留最近多少天的日志
        dry_run: 是否只预览不删除
    
    Returns:
        摘要信息字符串
    """
    stats = get_log_statistics()
    
    summary = f"""📊 **日志统计信息**

**当前日志状态**
• 日志文件总数: {stats['total_files']} 个
• 日志总大小: {stats['total_size_mb']:.2f} MB ({stats['total_size_gb']:.3f} GB)
• 日志目录: {LOG_DIR}
• 当前会话: {os.path.basename(SESSION_DIR)}
• 保留天数: {days} 天

**最近的会话目录**
"""
    
    for i, session_dir in enumerate(stats['session_dirs'][:5], 1):
        summary += f"{i}. `{session_dir['name']}` - {session_dir['size_mb']:.2f} MB\n"
    
    summary += f"\n**前5大日志文件**\n"
    for i, file_info in enumerate(stats['files'][:5], 1):
        summary += f"{i}. `{os.path.basename(file_info['path'])}` ({file_info['session']}) - {file_info['size_mb']:.2f} MB\n"
    
    if dry_run:
        result = clean_old_logs(days, dry_run=True)
        summary += f"""
**预计清理结果**
• 将删除会话: {len(result['deleted_dirs'])} 个
• 将删除文件: {len(result['deleted_files'])} 个
• 预计释放空间: {result['total_freed_mb']:.2f} MB
"""
    else:
        summary += "\n执行清理命令后，将删除指定天数之前的所有会话目录。\n"
    
    return summary
