# Copyright 2026 Sakura-频道总结助手
# 
# 本项目采用 GNU General Public License v3.0 (GPLv3) 许可证
# 
# 您可以自由地：
# - 商业使用：将本软件用于商业目的
# - 修改：修改本软件以满足您的需求
# - 分发：分发本软件的副本
# - 专利使用：明确授予专利许可
# 
# 您必须遵守以下条件：
# - 开源修改：如果修改了代码，必须开源修改后的代码
# - 源代码分发：分发程序时必须同时提供源代码
# - 相同许可证：修改和分发必须使用相同的GPLv3许可证
# - 版权声明：保留原有的版权声明和许可证
# 
# 本项目源代码：https://github.com/Sakura520222/Sakura-Channel-Summary-Assistant-Pro
# 许可证全文：https://www.gnu.org/licenses/gpl-3.0.html

"""配置文件监控器模块

提供配置文件变更监控功能，支持自动重载和手动触发。
当 watchdog 不可用时自动降级为手动模式。
"""

import logging
import os
import threading
import time
from typing import Callable, Dict, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 尝试导入 watchdog，如果失败则禁用自动监控
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # 定义一个空的基类，防止类定义时报错
    class FileSystemEventHandler:
        pass
    class Observer:
        def start(self):
            pass
        def stop(self):
            pass
        def schedule(self, *args, **kwargs):
            pass
        def join(self, *args, **kwargs):
            pass
        def shutdown(self):
            pass
    
    logger.warning("watchdog 模块未安装，自动配置监控功能已禁用")
    logger.warning("请运行: pip install watchdog>=3.0.0")


@dataclass
class FileChangeEvent:
    """文件变更事件"""
    file_path: str
    event_type: str  # 'modified' or 'created'
    timestamp: float = field(default_factory=time.time)


@dataclass
class ReloadResult:
    """重载结果"""
    success: bool
    config_type: str
    message: str
    details: Optional[Dict] = None
    old_values: Optional[Dict] = None  # 变更前的值，用于对比
    error_type: Optional[str] = None   # 错误类型
    error_location: Optional[str] = None  # 错误位置


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件事件处理器
    
    处理配置文件的变更事件，实现防抖机制。
    """
    
    def __init__(self, reload_callback: Callable[[str], ReloadResult], debounce_seconds: float = 2.0):
        """初始化处理器
        
        Args:
            reload_callback: 文件变更时的回调函数
            debounce_seconds: 防抖延迟时间（秒）
        """
        self.reload_callback = reload_callback
        self.debounce_seconds = debounce_seconds
        self._pending_changes: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._debounce_timer: Optional[threading.Timer] = None
    
    def on_modified(self, event):
        """处理文件修改事件"""
        if not event.is_directory:
            self._schedule_reload(event.src_path, 'modified')
    
    def on_created(self, event):
        """处理文件创建事件"""
        if not event.is_directory:
            self._schedule_reload(event.src_path, 'created')
    
    def _schedule_reload(self, file_path: str, event_type: str):
        """调度重载操作（带防抖）"""
        with self._lock:
            # 记录变更时间
            self._pending_changes[file_path] = time.time()
            
            # 取消之前的定时器
            if self._debounce_timer:
                self._debounce_timer.cancel()
            
            # 创建新的定时器
            self._debounce_timer = threading.Timer(
                self.debounce_seconds,
                self._execute_reload
            )
            self._debounce_timer.daemon = True
            self._debounce_timer.start()
            
            logger.debug(f"检测到文件变更（防抖中）: {file_path}, 事件类型: {event_type}")
    
    def _execute_reload(self):
        """执行重载操作"""
        with self._lock:
            # 复制待处理的文件列表
            files_to_reload = list(self._pending_changes.keys())
            self._pending_changes.clear()
            
            # 取消防抖定时器
            if self._debounce_timer:
                self._debounce_timer.cancel()
                self._debounce_timer = None
        
        # 执行重载（在锁外执行，避免阻塞）
        for file_path in files_to_reload:
            try:
                logger.info(f"开始重载配置文件: {file_path}")
                # 传递 is_auto_reload=True 标识这是自动重载
                result = self.reload_callback(file_path, is_auto_reload=True)
                
                if result.success:
                    logger.info(f"配置重载成功: {result.message}")
                    if result.details:
                        logger.info(f"详细信息: {result.details}")
                else:
                    logger.error(f"配置重载失败: {result.message}")
                    
            except Exception as e:
                logger.error(f"重载配置文件时出错 {file_path}: {type(e).__name__}: {e}", exc_info=True)
    
    def stop(self):
        """停止处理器"""
        with self._lock:
            if self._debounce_timer:
                self._debounce_timer.cancel()
                self._debounce_timer = None


class ConfigWatcher:
    """配置文件监控器
    
    监控配置文件的变更，自动触发重载。
    支持降级模式：当 watchdog 不可用时禁用自动监控。
    """
    
    # 监控的配置文件
    WATCHED_FILES = {
        '.env': 'env',
        'data/config/config.json': 'config',
        'data/config/prompt.txt': 'prompt',
        'data/config/poll_prompt.txt': 'poll_prompt'
    }
    
    def __init__(self, reload_callback: Callable[[str], ReloadResult], debounce_seconds: float = 2.0):
        """初始化监控器
        
        Args:
            reload_callback: 文件变更时的回调函数
            debounce_seconds: 防抖延迟时间（秒）
        """
        self.reload_callback = reload_callback
        self.debounce_seconds = debounce_seconds
        self._observer: Optional[Observer] = None
        self._handler: Optional[ConfigFileHandler] = None
        self._enabled = WATCHDOG_AVAILABLE
        self._running = False
        
        logger.info(f"配置监控器初始化完成，自动监控: {'启用' if self._enabled else '禁用'}")
    
    def start(self):
        """启动监控器"""
        if not self._enabled:
            logger.info("自动配置监控已禁用（watchdog 不可用），请使用 /reload 命令手动重载")
            return False
        
        if self._running:
            logger.warning("配置监控器已在运行")
            return False
        
        try:
            # 创建观察者
            self._observer = Observer()
            
            # 创建事件处理器
            self._handler = ConfigFileHandler(self.reload_callback, self.debounce_seconds)
            
            # 为每个监控目录添加观察者
            watched_dirs = set()
            for file_path in self.WATCHED_FILES.keys():
                # 规范化路径
                abs_path = os.path.abspath(file_path)
                dir_path = os.path.dirname(abs_path)
                
                if dir_path not in watched_dirs:
                    # 添加目录观察者
                    self._observer.schedule(self._handler, dir_path, recursive=False)
                    watched_dirs.add(dir_path)
                    logger.info(f"添加监控目录: {dir_path}")
            
            # 启动观察者
            self._observer.start()
            self._running = True
            
            logger.info(f"配置监控器已启动，监控 {len(self.WATCHED_FILES)} 个文件")
            return True
            
        except Exception as e:
            logger.error(f"启动配置监控器失败: {type(e).__name__}: {e}", exc_info=True)
            self._enabled = False
            logger.warning("已自动降级为手动模式，请使用 /reload 命令手动重载")
            return False
    
    def stop(self):
        """停止监控器"""
        if not self._running:
            return
        
        try:
            # 停止事件处理器
            if self._handler:
                self._handler.stop()
            
            # 停止观察者
            if self._observer:
                self._observer.stop()
                self._observer.join(timeout=5.0)
            
            self._running = False
            logger.info("配置监控器已停止")
            
        except Exception as e:
            logger.error(f"停止配置监控器时出错: {type(e).__name__}: {e}", exc_info=True)
    
    def is_enabled(self) -> bool:
        """检查自动监控是否启用"""
        return self._enabled
    
    def is_running(self) -> bool:
        """检查监控器是否正在运行"""
        return self._running
    
    def get_watched_files(self) -> Dict[str, str]:
        """获取监控的文件列表
        
        Returns:
            Dict[文件路径, 配置类型]
        """
        return self.WATCHED_FILES.copy()
    
    @staticmethod
    def get_config_type(file_path: str) -> Optional[str]:
        """根据文件路径获取配置类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            配置类型（env/config/prompt/poll_prompt），如果不是监控的文件则返回 None
        """
        # 规范化路径
        abs_path = os.path.abspath(file_path)
        
        # 检查是否为监控的文件
        for watched_path, config_type in ConfigWatcher.WATCHED_FILES.items():
            if os.path.abspath(watched_path) == abs_path:
                return config_type
        
        return None


# 全局监控器实例
_global_watcher: Optional[ConfigWatcher] = None


def get_global_watcher() -> Optional[ConfigWatcher]:
    """获取全局监控器实例"""
    return _global_watcher


def set_global_watcher(watcher: ConfigWatcher):
    """设置全局监控器实例"""
    global _global_watcher
    _global_watcher = watcher


def init_global_watcher(reload_callback: Callable[[str], ReloadResult], debounce_seconds: float = 2.0) -> Optional[ConfigWatcher]:
    """初始化全局监控器
    
    Args:
        reload_callback: 文件变更时的回调函数
        debounce_seconds: 防抖延迟时间（秒）
        
    Returns:
        配置监控器实例，如果初始化失败则返回 None
    """
    global _global_watcher
    
    if _global_watcher is not None:
        logger.warning("全局监控器已存在，跳过初始化")
        return _global_watcher
    
    try:
        _global_watcher = ConfigWatcher(reload_callback, debounce_seconds)
        logger.info("全局配置监控器初始化完成")
        return _global_watcher
    except Exception as e:
        logger.error(f"初始化全局监控器失败: {type(e).__name__}: {e}", exc_info=True)
        return None


def start_global_watcher() -> bool:
    """启动全局监控器
    
    Returns:
        是否成功启动
    """
    global _global_watcher
    
    if _global_watcher is None:
        logger.error("全局监控器未初始化，无法启动")
        return False
    
    return _global_watcher.start()


def stop_global_watcher():
    """停止全局监控器"""
    global _global_watcher
    
    if _global_watcher:
        _global_watcher.stop()
        _global_watcher = None
        logger.info("全局监控器已停止并清理")
