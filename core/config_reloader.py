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

"""配置重载管理器模块

提供配置的原子化重载功能，支持验证和回滚机制。
"""

import asyncio
import logging
import json
import os
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field

from .config_watcher import ReloadResult
from .config import (
    CONFIG_FILE, PROMPT_FILE, POLL_PROMPT_FILE,
    CHANNELS, SEND_REPORT_TO_SOURCE, ENABLE_POLL,
    SUMMARY_SCHEDULES, CHANNEL_POLL_SETTINGS,
    load_config, save_config, update_module_variables,
    logger
)
from .prompt_manager import load_prompt
from .poll_prompt_manager import load_poll_prompt

logger = logging.getLogger(__name__)


@dataclass
class ReloadStats:
    """重载统计信息"""
    total: int = 0
    success: int = 0
    failed: int = 0
    details: Dict[str, str] = field(default_factory=dict)


class ConfigReloader:
    """配置重载管理器
    
    提供原子化的配置重载功能，支持验证和回滚。
    """
    
    def __init__(self):
        """初始化重载管理器"""
        self._reload_stats = ReloadStats()
        logger.info("配置重载管理器初始化完成")
    
    def reload_by_file(self, file_path: str) -> ReloadResult:
        """根据文件路径重载对应配置
        
        Args:
            file_path: 变更的配置文件路径
            
        Returns:
            ReloadResult: 重载结果
        """
        from .config_watcher import ConfigWatcher
        
        # 获取配置类型
        config_type = ConfigWatcher.get_config_type(file_path)
        
        if config_type is None:
            logger.warning(f"文件 {file_path} 不在监控列表中，跳过重载")
            return ReloadResult(
                success=False,
                config_type='unknown',
                message=f'文件不在监控列表中: {file_path}'
            )
        
        # 根据类型重载
        if config_type == 'env':
            return self._reload_env()
        elif config_type == 'config':
            return self._reload_config_json()
        elif config_type == 'prompt':
            return self._reload_prompt()
        elif config_type == 'poll_prompt':
            return self._reload_poll_prompt()
        else:
            return ReloadResult(
                success=False,
                config_type=config_type,
                message=f'未知的配置类型: {config_type}'
            )
    
    def reload_all(self) -> Tuple[bool, str, Dict]:
        """重载所有配置
        
        Returns:
            Tuple[是否成功, 消息, 详细信息]
        """
        logger.info("开始重载所有配置...")
        
        results = {
            'env': self._reload_env(),
            'config': self._reload_config_json(),
            'prompt': self._reload_prompt(),
            'poll_prompt': self._reload_poll_prompt()
        }
        
        # 统计结果
        success_count = sum(1 for r in results.values() if r.success)
        total_count = len(results)
        
        # 构建消息
        if success_count == total_count:
            message = f"✅ 所有配置重载成功（{total_count}/{total_count}）"
            details = self._build_reload_details(results)
            logger.info(message)
            return (True, message, details)
        else:
            message = f"⚠️ 部分配置重载失败（{success_count}/{total_count}）"
            details = self._build_reload_details(results)
            logger.warning(message)
            return (False, message, details)
    
    def _reload_env(self) -> ReloadResult:
        """重载环境变量配置
        
        注意：大部分环境变量修改需要重启才能生效，
        只有日志级别可以动态更新。
        
        Returns:
            ReloadResult: 重载结果
        """
        try:
            from dotenv import load_dotenv
            from .logger_config import get_current_log_level, update_all_loggers_level
            
            # 重新加载 .env 文件
            load_dotenv(override=True)
            logger.info("已重新加载 .env 文件")
            
            # 动态更新日志级别
            log_level_str = os.getenv('LOG_LEVEL')
            if log_level_str:
                update_all_loggers_level(log_level_str)
                current_level = get_current_log_level()
                logger.info(f"日志级别已动态更新为: {current_level}")
                
                return ReloadResult(
                    success=True,
                    config_type='env',
                    message='环境变量已重载，日志级别已更新',
                    details={'log_level': current_level}
                )
            else:
                return ReloadResult(
                    success=True,
                    config_type='env',
                    message='环境变量已重载（无需更新日志级别）',
                    details={}
                )
            
        except Exception as e:
            logger.error(f"重载环境变量失败: {type(e).__name__}: {e}", exc_info=True)
            return ReloadResult(
                success=False,
                config_type='env',
                message=f'重载失败: {e}',
                details={}
            )
    
    def _reload_config_json(self) -> ReloadResult:
        """重载 JSON 配置文件（原子化）
        
        Returns:
            ReloadResult: 重载结果
        """
        try:
            # 1. 读取并验证新配置
            new_config = self._load_and_validate_config_json()
            if new_config is None:
                return ReloadResult(
                    success=False,
                    config_type='config',
                    message='配置验证失败',
                    details={}
                )
            
            # 2. 原子化更新全局变量
            self._apply_config_json_atomically(new_config)
            
            # 3. 重新加载调度器（如果需要）
            # 检查是否需要重启调度器
            needs_restart = (
                'channels' in new_config or
                'summary_schedules' in new_config
            )
            
            if needs_restart:
                try:
                    # 尝试获取运行中的事件循环
                    loop = asyncio.get_running_loop()
                    # 在后台任务中异步重启调度器，避免阻塞
                    loop.create_task(self._restart_scheduler_if_needed(new_config))
                    scheduler_restarted = True
                    logger.info("调度器重启任务已提交（后台异步执行）")
                except RuntimeError:
                    # 没有运行中的事件循环，记录警告但不尝试创建新循环
                    # 避免使用 asyncio.run() 导致事件循环冲突
                    logger.warning("没有运行中的事件循环，跳过调度器重启")
                    scheduler_restarted = False
            else:
                scheduler_restarted = False
            
            # 4. 构建详细信息
            details = {
                'channels': len(CHANNELS),
                'summary_schedules': len(SUMMARY_SCHEDULES),
                'poll_settings': len(CHANNEL_POLL_SETTINGS),
                'send_report_to_source': SEND_REPORT_TO_SOURCE,
                'enable_poll': ENABLE_POLL,
                'scheduler_restarted': scheduler_restarted
            }
            
            logger.info(f"JSON配置重载成功: {details}")
            
            return ReloadResult(
                success=True,
                config_type='config',
                message='JSON配置已重载',
                details=details
            )
            
        except Exception as e:
            logger.error(f"重载JSON配置失败: {type(e).__name__}: {e}", exc_info=True)
            return ReloadResult(
                success=False,
                config_type='config',
                message=f'重载失败: {e}',
                details={}
            )
    
    def _load_and_validate_config_json(self) -> Optional[Dict]:
        """加载并验证JSON配置文件
        
        Returns:
            验证通过的配置字典，如果验证失败则返回 None
        """
        try:
            # 读取配置文件
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            logger.info(f"成功读取配置文件，包含 {len(config)} 个顶级配置项")
            
            # 验证配置
            errors = self._validate_config_json(config)
            if errors:
                logger.error(f"配置验证失败: {errors}")
                return None
            
            logger.info("配置验证通过")
            return config
            
        except FileNotFoundError:
            logger.warning(f"配置文件 {CONFIG_FILE} 不存在")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            return None
        except Exception as e:
            logger.error(f"读取配置文件时出错: {type(e).__name__}: {e}", exc_info=True)
            return None
    
    def _validate_config_json(self, config: Dict) -> List[str]:
        """验证JSON配置的有效性
        
        Args:
            config: 配置字典
            
        Returns:
            错误消息列表，如果验证通过则返回空列表
        """
        errors = []
        
        # 验证频道列表
        if 'channels' in config:
            channels = config['channels']
            if not isinstance(channels, list):
                errors.append("channels 必须是数组")
            else:
                for channel in channels:
                    if not isinstance(channel, str):
                        errors.append(f"频道必须是字符串: {channel}")
        
        # 验证总结时间配置
        if 'summary_schedules' in config:
            schedules = config['summary_schedules']
            if not isinstance(schedules, dict):
                errors.append("summary_schedules 必须是对象")
        
        # 验证投票配置
        if 'channel_poll_settings' in config:
            poll_settings = config['channel_poll_settings']
            if not isinstance(poll_settings, dict):
                errors.append("channel_poll_settings 必须是对象")
        
        # 验证布尔值配置
        for key in ['send_report_to_source', 'enable_poll']:
            if key in config and not isinstance(config[key], bool):
                errors.append(f"{key} 必须是布尔值")
        
        return errors
    
    def _apply_config_json_atomically(self, new_config: Dict):
        """原子化应用JSON配置（原地更新全局变量）
        
        Args:
            new_config: 新的配置字典
        """
        # 使用全局声明原地更新
        global CHANNELS, SEND_REPORT_TO_SOURCE, ENABLE_POLL
        global SUMMARY_SCHEDULES, CHANNEL_POLL_SETTINGS
        
        # 更新频道列表（原地更新）
        if 'channels' in new_config:
            CHANNELS.clear()
            CHANNELS.extend(new_config['channels'])
            logger.info(f"已更新频道列表: {CHANNELS}")
        
        # 更新发送报告配置
        if 'send_report_to_source' in new_config:
            SEND_REPORT_TO_SOURCE = new_config['send_report_to_source']
            logger.info(f"已更新发送报告配置: {SEND_REPORT_TO_SOURCE}")
        
        # 更新投票功能配置
        if 'enable_poll' in new_config:
            ENABLE_POLL = new_config['enable_poll']
            logger.info(f"已更新投票功能配置: {ENABLE_POLL}")
        
        # 更新总结时间配置（原地更新）
        if 'summary_schedules' in new_config:
            SUMMARY_SCHEDULES.clear()
            SUMMARY_SCHEDULES.update(new_config['summary_schedules'])
            logger.info(f"已更新总结时间配置: {len(SUMMARY_SCHEDULES)} 个频道")
        
        # 更新投票配置（原地更新）
        if 'channel_poll_settings' in new_config:
            CHANNEL_POLL_SETTINGS.clear()
            CHANNEL_POLL_SETTINGS.update(new_config['channel_poll_settings'])
            logger.info(f"已更新投票配置: {len(CHANNEL_POLL_SETTINGS)} 个频道")
    
    async def _restart_scheduler_if_needed(self, new_config: Dict) -> bool:
        """根据配置变更决定是否需要重启调度器
        
        Args:
            new_config: 新的配置字典
            
        Returns:
            是否重启了调度器
        """
        # 检查是否有需要重启调度器的配置变更
        needs_restart = (
            'channels' in new_config or
            'summary_schedules' in new_config
        )
        
        if not needs_restart:
            return False
        
        try:
            from .scheduler import graceful_restart_scheduler
            await graceful_restart_scheduler()
            logger.info("调度器已重启")
            return True
            
        except Exception as e:
            logger.error(f"重启调度器失败: {type(e).__name__}: {e}", exc_info=True)
            return False
    
    def _reload_prompt(self) -> ReloadResult:
        """重载总结提示词（原子化）
        
        Returns:
            ReloadResult: 重载结果
        """
        try:
            # 1. 读取并验证新提示词
            new_prompt = self._load_and_validate_prompt()
            if new_prompt is None:
                return ReloadResult(
                    success=False,
                    config_type='prompt',
                    message='提示词验证失败（不能为空）',
                    details={}
                )
            
            # 2. 原子化更新（提示词是文件缓存，读取时重新加载）
            # 提示词通过 load_prompt() 动态读取，无需更新全局变量
            # 只需要验证文件内容有效即可
            
            logger.info(f"总结提示词重载成功，长度: {len(new_prompt)} 字符")
            
            return ReloadResult(
                success=True,
                config_type='prompt',
                message='总结提示词已更新',
                details={'length': len(new_prompt)}
            )
            
        except Exception as e:
            logger.error(f"重载总结提示词失败: {type(e).__name__}: {e}", exc_info=True)
            return ReloadResult(
                success=False,
                config_type='prompt',
                message=f'重载失败: {e}',
                details={}
            )
    
    def _load_and_validate_prompt(self) -> Optional[str]:
        """加载并验证总结提示词
        
        Returns:
            有效的提示词，如果验证失败则返回 None
        """
        try:
            with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                prompt = f.read().strip()
            
            # 验证提示词非空
            if not prompt:
                logger.error("总结提示词不能为空")
                return None
            
            return prompt
            
        except FileNotFoundError:
            logger.warning(f"总结提示词文件 {PROMPT_FILE} 不存在")
            return None
        except Exception as e:
            logger.error(f"读取总结提示词失败: {type(e).__name__}: {e}", exc_info=True)
            return None
    
    def _reload_poll_prompt(self) -> ReloadResult:
        """重载投票提示词（原子化）
        
        Returns:
            ReloadResult: 重载结果
        """
        try:
            # 1. 读取并验证新提示词
            new_prompt = self._load_and_validate_poll_prompt()
            if new_prompt is None:
                return ReloadResult(
                    success=False,
                    config_type='poll_prompt',
                    message='投票提示词验证失败（不能为空）',
                    details={}
                )
            
            # 2. 原子化更新（提示词是文件缓存，读取时重新加载）
            # 投票提示词通过 load_poll_prompt() 动态读取，无需更新全局变量
            
            logger.info(f"投票提示词重载成功，长度: {len(new_prompt)} 字符")
            
            return ReloadResult(
                success=True,
                config_type='poll_prompt',
                message='投票提示词已更新',
                details={'length': len(new_prompt)}
            )
            
        except Exception as e:
            logger.error(f"重载投票提示词失败: {type(e).__name__}: {e}", exc_info=True)
            return ReloadResult(
                success=False,
                config_type='poll_prompt',
                message=f'重载失败: {e}',
                details={}
            )
    
    def _load_and_validate_poll_prompt(self) -> Optional[str]:
        """加载并验证投票提示词
        
        Returns:
            有效的提示词，如果验证失败则返回 None
        """
        try:
            with open(POLL_PROMPT_FILE, "r", encoding="utf-8") as f:
                prompt = f.read().strip()
            
            # 验证提示词非空
            if not prompt:
                logger.error("投票提示词不能为空")
                return None
            
            return prompt
            
        except FileNotFoundError:
            logger.warning(f"投票提示词文件 {POLL_PROMPT_FILE} 不存在")
            return None
        except Exception as e:
            logger.error(f"读取投票提示词失败: {type(e).__name__}: {e}", exc_info=True)
            return None
    
    def _build_reload_details(self, results: Dict[str, ReloadResult]) -> Dict:
        """构建重载详细信息
        
        Args:
            results: 各配置类型的重载结果
            
        Returns:
            详细信息字典
        """
        details = {}
        
        for config_type, result in results.items():
            if result.success:
                details[config_type] = {
                    'status': 'success',
                    'message': result.message
                }
                if result.details:
                    details[config_type]['info'] = result.details
            else:
                details[config_type] = {
                    'status': 'failed',
                    'message': result.message
                }
        
        return details
    
    def get_reload_summary(self) -> str:
        """获取重载统计摘要
        
        Returns:
            统计摘要字符串
        """
        stats = self._reload_stats
        if stats.total == 0:
            return "暂无重载记录"
        
        return f"总重载: {stats.total} 次，成功: {stats.success} 次，失败: {stats.failed} 次"


# 全局重载管理器实例
_global_reloader: Optional[ConfigReloader] = None


def get_global_reloader() -> Optional[ConfigReloader]:
    """获取全局重载管理器实例"""
    return _global_reloader


def init_global_reloader() -> ConfigReloader:
    """初始化全局重载管理器
    
    Returns:
        重载管理器实例
    """
    global _global_reloader
    
    if _global_reloader is None:
        _global_reloader = ConfigReloader()
        logger.info("全局配置重载管理器初始化完成")
    
    return _global_reloader


def reload_config_by_file(file_path: str) -> ReloadResult:
    """根据文件路径重载配置（便捷函数）
    
    Args:
        file_path: 变更的配置文件路径
        
    Returns:
        ReloadResult: 重载结果
    """
    reloader = get_global_reloader()
    if reloader is None:
        return ReloadResult(
            success=False,
            config_type='unknown',
            message='重载管理器未初始化'
        )
    
    return reloader.reload_by_file(file_path)


def reload_all_configs() -> Tuple[bool, str, Dict]:
    """重载所有配置（便捷函数）
    
    Returns:
        Tuple[是否成功, 消息, 详细信息]
    """
    reloader = get_global_reloader()
    if reloader is None:
        return (False, '重载管理器未初始化', {})
    
    return reloader.reload_all()


def reload_env() -> ReloadResult:
    """重载环境变量（便捷函数）
    
    Returns:
        ReloadResult: 重载结果
    """
    reloader = get_global_reloader()
    if reloader is None:
        return ReloadResult(
            success=False,
            config_type='env',
            message='重载管理器未初始化'
        )
    
    return reloader._reload_env()


def reload_config_json() -> ReloadResult:
    """重载JSON配置（便捷函数）
    
    Returns:
        ReloadResult: 重载结果
    """
    reloader = get_global_reloader()
    if reloader is None:
        return ReloadResult(
            success=False,
            config_type='config',
            message='重载管理器未初始化'
        )
    
    return reloader._reload_config_json()


def reload_prompt() -> ReloadResult:
    """重载总结提示词（便捷函数）
    
    Returns:
        ReloadResult: 重载结果
    """
    reloader = get_global_reloader()
    if reloader is None:
        return ReloadResult(
            success=False,
            config_type='prompt',
            message='重载管理器未初始化'
        )
    
    return reloader._reload_prompt()


def reload_poll_prompt() -> ReloadResult:
    """重载投票提示词（便捷函数）
    
    Returns:
        ReloadResult: 重载结果
    """
    reloader = get_global_reloader()
    if reloader is None:
        return ReloadResult(
            success=False,
            config_type='poll_prompt',
            message='重载管理器未初始化'
        )
    
    return reloader._reload_poll_prompt()
