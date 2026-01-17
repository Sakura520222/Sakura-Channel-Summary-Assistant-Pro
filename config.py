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

import os
import logging
from dotenv import load_dotenv
from config_validators import ScheduleValidator, LegacyScheduleValidator

# 导入日志配置模块
try:
    from logger_config import logger, get_log_level, update_all_loggers_level
    LOG_SYSTEM_INITIALIZED = True
except ImportError:
    # 如果logger_config模块导入失败，使用基本配置（向后兼容）
    DEFAULT_LOG_LEVEL = logging.DEBUG
    
    LOG_LEVEL_MAP = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def get_log_level(level_str):
        """将字符串日志级别转换为logging模块对应的级别常量"""
        if not level_str:
            return DEFAULT_LOG_LEVEL
        return LOG_LEVEL_MAP.get(level_str.upper(), DEFAULT_LOG_LEVEL)
    
    logging.basicConfig(
        level=DEFAULT_LOG_LEVEL,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    LOG_SYSTEM_INITIALIZED = False

# 数据目录基础路径
DATA_DIR = "data"

# 配置文件路径（规范化到 data 目录）
PROMPT_FILE = os.path.join(DATA_DIR, "config", "prompt.txt")
POLL_PROMPT_FILE = os.path.join(DATA_DIR, "config", "poll_prompt.txt")
CONFIG_FILE = os.path.join(DATA_DIR, "config", "config.json")
RESTART_FLAG_FILE = os.path.join(DATA_DIR, "temp", "restart_flag")
SHUTDOWN_FLAG_FILE = os.path.join(DATA_DIR, "temp", "shutdown_flag")
LAST_SUMMARY_FILE = os.path.join(DATA_DIR, "data", "last_summary_time.json")

# 会话文件路径
SESSION_PATH = os.path.join(DATA_DIR, "sessions", "bot_session")
SESSION_NAME_PATH = os.path.join(DATA_DIR, "sessions", "session_name")

# 数据库文件路径
DATABASE_PATH = os.path.join(DATA_DIR, "database", "summaries.db")

# 讨论组ID缓存 (频道URL -> 讨论组ID)
# 避免频繁调用GetFullChannelRequest,提升性能
LINKED_CHAT_CACHE = {}

# 默认提示词
DEFAULT_PROMPT = "请总结以下 Telegram 消息，提取核心要点并列出重要消息的链接：\n\n"

# 默认投票生成提示词
DEFAULT_POLL_PROMPT = """根据以下内容生成一个有趣的单选投票。
1. **趣味性**：题目和选项要幽默、有梗，具有互动性，避免平铺直叙。
2. **双语要求**：整体内容中文在上，英文在下。在 JSON 字段内部，中文与英文之间使用 " / " 分隔。
3. **输出格式**：仅输出标准的 JSON 格式，严禁包含任何前言、解释或 Markdown 代码块标识符。
4. **JSON 结构**：
{{
  "question": "中文题目 / English Question",
  "options": [
    "中文选项1 / English Option 1",
    "中文选项2 / English Option 2",
    "中文选项3 / English Option 3",
    "中文选项4 / English Option 4"
  ]
}}

# Input Content
{summary_text}
"""

# 加载 .env 文件中的变量
load_dotenv()
logger.info("已加载 .env 文件中的环境变量")

# 从环境变量中读取配置
logger.info("开始从环境变量加载配置...")
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# AI 配置 - 从环境变量获取默认值
LLM_API_KEY = os.getenv('LLM_API_KEY', os.getenv('DEEPSEEK_API_KEY'))
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.deepseek.com')
LLM_MODEL = os.getenv('LLM_MODEL', 'deepseek-chat')


# 是否将报告发送回源频道的配置，默认为True
SEND_REPORT_TO_SOURCE = True

# 是否启用投票功能，默认为True
ENABLE_POLL = True

# 频道列表 - 初始为空，只能通过命令添加
CHANNELS = []

# 日志级别 - 从环境变量获取默认值
LOG_LEVEL_FROM_ENV = os.getenv('LOG_LEVEL')
logger.debug(f"从环境变量读取的日志级别: {LOG_LEVEL_FROM_ENV}")

logger.debug(f"从环境变量加载的配置: API_ID={'***' if API_ID else '未设置'}, API_HASH={'***' if API_HASH else '未设置'}, BOT_TOKEN={'***' if BOT_TOKEN else '未设置'}")
logger.debug(f"AI配置 - 环境变量默认值: Base URL={LLM_BASE_URL}, Model={LLM_MODEL}")

# 管理员 ID 列表，从环境变量读取后转为整数列表
REPORT_ADMIN_IDS = os.getenv('REPORT_ADMIN_IDS', '')
logger.debug(f"从环境变量读取的管理员ID: {REPORT_ADMIN_IDS}")

# 处理管理员ID列表
ADMIN_LIST = []
if REPORT_ADMIN_IDS:
    # 支持多个管理员ID，用逗号分隔
    ADMIN_LIST = [int(admin_id.strip()) for admin_id in REPORT_ADMIN_IDS.split(',')]
    logger.info(f"已从环境变量加载管理员ID列表: {ADMIN_LIST}")
else:
    # 如果没有配置管理员ID，默认发送给自己
    ADMIN_LIST = ['me']
    logger.info("未配置管理员ID，默认发送给机器人所有者")

# ==================== 黑名单配置 ====================

# 是否启用黑名单功能
BLACKLIST_ENABLED = os.getenv('BLACKLIST_ENABLED', 'true').lower() == 'true'
logger.info(f"黑名单功能: {'启用' if BLACKLIST_ENABLED else '禁用'}")

# 黑名单检测阈值：时间窗口内的违规次数
BLACKLIST_THRESHOLD_COUNT = int(os.getenv('BLACKLIST_THRESHOLD_COUNT', '3'))
logger.info(f"黑名单检测阈值: {BLACKLIST_THRESHOLD_COUNT} 次")

# 黑名单检测时间窗口（小时）
BLACKLIST_THRESHOLD_HOURS = int(os.getenv('BLACKLIST_THRESHOLD_HOURS', '1'))
logger.info(f"黑名单检测时间窗口: {BLACKLIST_THRESHOLD_HOURS} 小时")

# 读取配置文件
def load_config():
    """从配置文件读取配置（不包括AI配置）"""
    import json
    logger.info(f"开始读取配置文件: {CONFIG_FILE}")
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            logger.info(f"成功读取配置文件，配置项数量: {len(config)}")
            return config
    except FileNotFoundError:
        logger.warning(f"配置文件 {CONFIG_FILE} 不存在，返回空配置")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"配置文件 {CONFIG_FILE} 格式错误: {e}", exc_info=True)
        return {}
    except Exception as e:
        logger.error(f"读取配置文件 {CONFIG_FILE} 时出错: {type(e).__name__}: {e}", exc_info=True)
        return {}

# 保存配置文件
def save_config(config):
    """保存配置到文件（不包括AI配置）"""
    import json
    logger.info(f"开始保存配置到文件: {CONFIG_FILE}")
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"成功保存配置到文件，配置项数量: {len(config)}")
        
        # 更新模块变量以保持一致性
        update_module_variables(config)
        
    except Exception as e:
        logger.error(f"保存配置到文件 {CONFIG_FILE} 时出错: {type(e).__name__}: {e}", exc_info=True)

def update_module_variables(config):
    """更新模块变量以匹配配置文件（不包括AI配置）"""
    global CHANNELS, SEND_REPORT_TO_SOURCE, ENABLE_POLL, SUMMARY_SCHEDULES, CHANNEL_POLL_SETTINGS

    # 更新频道列表
    config_channels = config.get('channels')
    if config_channels and isinstance(config_channels, list):
        CHANNELS = config_channels
        logger.info(f"已更新内存中的频道列表: {CHANNELS}")

    # 更新是否将报告发送回源频道的配置
    if 'send_report_to_source' in config:
        SEND_REPORT_TO_SOURCE = config['send_report_to_source']
        logger.info(f"已更新内存中的发送报告到源频道的配置: {SEND_REPORT_TO_SOURCE}")

    # 更新是否启用投票功能的配置
    if 'enable_poll' in config:
        ENABLE_POLL = config['enable_poll']
        logger.info(f"已更新内存中的投票功能配置: {ENABLE_POLL}")

    # 更新频道级时间配置
    summary_schedules_config = config.get('summary_schedules', {})
    if isinstance(summary_schedules_config, dict):
        SUMMARY_SCHEDULES = summary_schedules_config
        logger.info(f"已更新内存中的频道级时间配置: {len(SUMMARY_SCHEDULES)} 个频道")

    # 更新频道级投票配置
    channel_poll_config = config.get('channel_poll_settings', {})
    if isinstance(channel_poll_config, dict):
        CHANNEL_POLL_SETTINGS = channel_poll_config
        logger.info(f"已更新内存中的频道级投票配置: {len(CHANNEL_POLL_SETTINGS)} 个频道")

# 加载配置文件
logger.info("开始加载配置文件...")
config = load_config()
if config:
    logger.debug(f"从配置文件读取的配置: {config}")
    
    # 从配置文件读取频道列表
    config_channels = config.get('channels')
    if config_channels and isinstance(config_channels, list):
        CHANNELS = config_channels
        logger.info(f"已从配置文件加载频道列表: {CHANNELS}")
    
    # 从配置文件读取是否将报告发送回源频道的配置
    SEND_REPORT_TO_SOURCE = config.get('send_report_to_source', SEND_REPORT_TO_SOURCE)
    logger.info(f"已从配置文件加载发送报告到源频道的配置: {SEND_REPORT_TO_SOURCE}")
    
    # 从配置文件读取是否启用投票功能的配置
    ENABLE_POLL = config.get('enable_poll', ENABLE_POLL)
    logger.info(f"已从配置文件加载投票功能配置: {ENABLE_POLL}")
    
    # 从配置文件读取日志级别
    LOG_LEVEL_FROM_CONFIG = config.get('log_level')
else:
    logger.info("未找到配置文件或配置文件为空，使用默认配置")
    LOG_LEVEL_FROM_CONFIG = None

# 确定最终日志级别（配置文件优先于环境变量）
final_log_level_str = LOG_LEVEL_FROM_CONFIG or LOG_LEVEL_FROM_ENV
final_log_level = get_log_level(final_log_level_str)

# 获取根日志记录器并设置级别
root_logger = logging.getLogger()
current_level = root_logger.getEffectiveLevel()
if current_level != final_log_level:
    root_logger.setLevel(final_log_level)
    logger.info(f"日志级别已从 {logging.getLevelName(current_level)} 更改为 {logging.getLevelName(final_log_level)}")
else:
    logger.info(f"当前日志级别: {logging.getLevelName(current_level)}")

# 如果日志系统已正确初始化，动态更新所有logger的处理器级别
if LOG_SYSTEM_INITIALIZED and final_log_level_str:
    try:
        update_all_loggers_level(final_log_level_str)
    except Exception as e:
        logger.warning(f"更新所有logger级别时出错: {e}")

# 机器人状态管理
BOT_STATE_RUNNING = "running"
BOT_STATE_PAUSED = "paused"
BOT_STATE_SHUTTING_DOWN = "shutting_down"

# 全局状态变量
_bot_state = BOT_STATE_RUNNING
_scheduler_instance = None

def get_bot_state():
    """获取当前机器人状态"""
    return _bot_state

def set_bot_state(state):
    """设置机器人状态"""
    global _bot_state
    valid_states = [BOT_STATE_RUNNING, BOT_STATE_PAUSED, BOT_STATE_SHUTTING_DOWN]
    if state in valid_states:
        _bot_state = state
        logger.info(f"机器人状态已更新为: {state}")
        return True
    else:
        logger.error(f"无效的机器人状态: {state}")
        return False

def set_scheduler_instance(scheduler):
    """设置调度器实例，供其他模块访问"""
    global _scheduler_instance
    _scheduler_instance = scheduler
    logger.info("调度器实例已设置")

def get_scheduler_instance():
    """获取调度器实例"""
    return _scheduler_instance

# 自动总结时间配置
# 默认时间：每周一早上9点
DEFAULT_SUMMARY_DAY = 'mon'  # 星期几：mon, tue, wed, thu, fri, sat, sun
DEFAULT_SUMMARY_HOUR = 9     # 小时：0-23
DEFAULT_SUMMARY_MINUTE = 0   # 分钟：0-59

# 从配置文件读取频道级时间配置
SUMMARY_SCHEDULES = {}
if config:
    summary_schedules_config = config.get('summary_schedules', {})
    if isinstance(summary_schedules_config, dict):
        SUMMARY_SCHEDULES = summary_schedules_config
        logger.info(f"已从配置文件加载频道级时间配置: {len(SUMMARY_SCHEDULES)} 个频道")
    else:
        logger.warning("配置文件中的summary_schedules格式不正确，使用默认配置")

# 频道级投票配置
CHANNEL_POLL_SETTINGS = {}
if config:
    channel_poll_config = config.get('channel_poll_settings', {})
    if isinstance(channel_poll_config, dict):
        CHANNEL_POLL_SETTINGS = channel_poll_config
        logger.info(f"已从配置文件加载频道级投票配置: {len(CHANNEL_POLL_SETTINGS)} 个频道")
    else:
        logger.warning("配置文件中的channel_poll_settings格式不正确，使用默认配置")

# 获取频道的时间配置
def get_channel_schedule(channel):
    """获取指定频道的自动总结时间配置（支持新格式）

    Args:
        channel: 频道URL

    Returns:
        dict: 标准化的配置字典，包含 frequency, days, hour, minute
    """
    if channel in SUMMARY_SCHEDULES:
        schedule = SUMMARY_SCHEDULES[channel]
        # 标准化配置（处理向后兼容）
        return normalize_schedule_config(schedule)
    else:
        # 返回默认配置
        return {
            'frequency': 'weekly',
            'days': [DEFAULT_SUMMARY_DAY],
            'hour': DEFAULT_SUMMARY_HOUR,
            'minute': DEFAULT_SUMMARY_MINUTE
        }

# 设置频道的时间配置
def set_channel_schedule(channel, day=None, hour=None, minute=None):
    """设置指定频道的自动总结时间配置（旧格式，保持向后兼容）

    此函数保留以支持旧代码，内部调用 set_channel_schedule_v2

    Args:
        channel: 频道URL
        day: 星期几（mon, tue, wed, thu, fri, sat, sun）
        hour: 小时（0-23）
        minute: 分钟（0-59）

    Returns:
        bool: 是否成功保存配置
    """
    if day is not None:
        # 旧格式，转换为 weekly 模式
        return set_channel_schedule_v2(channel, 'weekly', days=[day], hour=hour, minute=minute)
    else:
        # 仅更新时间，保持默认星期
        return set_channel_schedule_v2(channel, 'weekly', days=[DEFAULT_SUMMARY_DAY], hour=hour, minute=minute)

# 删除频道的时间配置
def delete_channel_schedule(channel):
    """删除指定频道的自动总结时间配置
    
    Args:
        channel: 频道URL
        
    Returns:
        bool: 是否成功删除配置
    """
    try:
        # 加载当前配置
        current_config = load_config()
        
        # 检查是否存在配置
        if 'summary_schedules' in current_config and channel in current_config['summary_schedules']:
            # 删除频道配置
            del current_config['summary_schedules'][channel]
            
            # 保存配置（save_config会自动更新模块变量）
            save_config(current_config)
            
            logger.info(f"已删除频道 {channel} 的时间配置")
            return True
        else:
            logger.info(f"频道 {channel} 没有时间配置，无需删除")
            return True
    except Exception as e:
        logger.error(f"删除频道时间配置时出错: {type(e).__name__}: {e}", exc_info=True)
        return False

# 验证时间配置（旧版格式）
def validate_schedule(day, hour, minute):
    """验证时间配置是否有效（旧版格式）
    
    Args:
        day: 星期几
        hour: 小时
        minute: 分钟
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    return LegacyScheduleValidator.validate_schedule(day, hour, minute)

# ==================== 多频率模式支持函数 ====================

def normalize_schedule_config(schedule_dict):
    """将配置标准化为新格式，处理向后兼容

    Args:
        schedule_dict: 原始配置字典

    Returns:
        dict: 标准化后的配置，包含 frequency, days, hour, minute
    """
    # 如果包含 frequency 字段，已经是新格式
    if 'frequency' in schedule_dict:
        # 确保 days 字段存在（weekly 模式）
        if schedule_dict['frequency'] == 'weekly' and 'days' not in schedule_dict:
            # 如果没有 days 字段但有 day 字段，转换它
            if 'day' in schedule_dict:
                schedule_dict['days'] = [schedule_dict['day']]
            else:
                schedule_dict['days'] = [DEFAULT_SUMMARY_DAY]
        return schedule_dict

    # 向后兼容：旧格式 (day 字段)
    if 'day' in schedule_dict:
        return {
            'frequency': 'weekly',
            'days': [schedule_dict['day']],
            'hour': schedule_dict.get('hour', DEFAULT_SUMMARY_HOUR),
            'minute': schedule_dict.get('minute', DEFAULT_SUMMARY_MINUTE)
        }

    # 默认配置
    return {
        'frequency': 'weekly',
        'days': [DEFAULT_SUMMARY_DAY],
        'hour': schedule_dict.get('hour', DEFAULT_SUMMARY_HOUR),
        'minute': schedule_dict.get('minute', DEFAULT_SUMMARY_MINUTE)
    }


def validate_schedule_v2(config_dict):
    """验证新的时间配置格式

    Args:
        config_dict: 包含 frequency, days, hour, minute 的字典

    Returns:
        tuple: (是否有效, 错误信息)
    """
    return ScheduleValidator.validate_schedule_v2(config_dict)


def set_channel_schedule_v2(channel, frequency, days=None, hour=None, minute=None):
    """设置指定频道的自动总结时间配置（支持新格式）

    Args:
        channel: 频道URL
        frequency: 频率类型（'daily' 或 'weekly'）
        days: 星期几列表（weekly 模式必需）
        hour: 小时（0-23）
        minute: 分钟（0-59）

    Returns:
        bool: 是否成功保存配置
    """
    try:
        # 构建配置字典
        config_dict = _build_schedule_config(frequency, days, hour, minute)
        
        # 验证配置
        if not _validate_schedule_config(config_dict):
            return False
        
        # 保存配置
        return _save_schedule_config(channel, config_dict)
    except Exception as e:
        logger.error(f"设置频道时间配置时出错: {type(e).__name__}: {e}", exc_info=True)
        return False


def _build_schedule_config(frequency, days, hour, minute):
    """
    构建调度配置字典

    Args:
        frequency: 频率类型
        days: 星期几列表
        hour: 小时
        minute: 分钟

    Returns:
        dict: 配置字典
    """
    config_dict = {
        'frequency': frequency,
        'hour': hour if hour is not None else DEFAULT_SUMMARY_HOUR,
        'minute': minute if minute is not None else DEFAULT_SUMMARY_MINUTE
    }
    
    # weekly 模式需要 days 字段
    if frequency == 'weekly':
        if days is None:
            days = [DEFAULT_SUMMARY_DAY]
        config_dict['days'] = days
    
    return config_dict


def _validate_schedule_config(config_dict):
    """
    验证调度配置

    Args:
        config_dict: 配置字典

    Returns:
        bool: 是否有效
    """
    is_valid, error_msg = validate_schedule_v2(config_dict)
    if not is_valid:
        logger.error(f"配置验证失败: {error_msg}")
    return is_valid


def _save_schedule_config(channel, config_dict):
    """
    保存调度配置到文件

    Args:
        channel: 频道URL
        config_dict: 配置字典

    Returns:
        bool: 是否成功
    """
    current_config = load_config()
    
    # 确保summary_schedules字段存在
    if 'summary_schedules' not in current_config:
        current_config['summary_schedules'] = {}
    
    # 更新配置
    current_config['summary_schedules'][channel] = config_dict
    
    # 保存配置
    save_config(current_config)
    
    logger.info(f"已更新频道 {channel} 的时间配置: {config_dict}")
    return True


def build_cron_trigger(schedule_config):
    """根据配置构建 APScheduler cron 触发器参数

    Args:
        schedule_config: 标准化的调度配置字典

    Returns:
        dict: 包含 cron 触发器参数的字典
    """
    frequency = schedule_config.get('frequency', 'weekly')

    if frequency == 'daily':
        # 每天模式
        return {
            'day_of_week': '*',  # 每天
            'hour': schedule_config['hour'],
            'minute': schedule_config['minute']
        }
    elif frequency == 'weekly':
        # 每周模式（支持多天）
        days_str = ','.join(schedule_config['days'])
        return {
            'day_of_week': days_str,
            'hour': schedule_config['hour'],
            'minute': schedule_config['minute']
        }
    else:
        # 默认：每周一
        return {
            'day_of_week': 'mon',
            'hour': schedule_config.get('hour', DEFAULT_SUMMARY_HOUR),
            'minute': schedule_config.get('minute', DEFAULT_SUMMARY_MINUTE)
        }


# ==================== 频道级投票配置管理函数 ====================

def get_channel_poll_config(channel):
    """获取指定频道的投票配置

    Args:
        channel: 频道URL

    Returns:
        dict: 包含 enabled 和 send_to_channel 的配置字典
            - enabled: 是否启用投票（None 表示使用全局配置）
            - send_to_channel: true=频道模式, false=讨论组模式
    """
    if channel in CHANNEL_POLL_SETTINGS:
        config = CHANNEL_POLL_SETTINGS[channel]
        return {
            'enabled': config.get('enabled', None),  # None 表示使用全局配置
            'send_to_channel': config.get('send_to_channel', False)  # 默认讨论组模式
        }
    else:
        # 没有独立配置，返回默认配置
        return {
            'enabled': None,  # 使用全局 ENABLE_POLL
            'send_to_channel': False  # 默认讨论组模式
        }


def set_channel_poll_config(channel, enabled=None, send_to_channel=None):
    """设置指定频道的投票配置

    Args:
        channel: 频道URL
        enabled: 是否启用投票（None 表示不修改）
        send_to_channel: 投票发送位置（None 表示不修改）
            True - 频道模式（直接发送到频道）
            False - 讨论组模式（发送到讨论组）

    Returns:
        bool: 是否成功保存配置
    """
    try:
        # 加载当前配置
        current_config = load_config()
        
        # 确保配置结构存在
        _ensure_poll_settings_structure(current_config, channel)
        
        # 更新配置
        _update_poll_settings(current_config, channel, enabled, send_to_channel)
        
        # 保存配置
        save_config(current_config)
        
        logger.info(f"已更新频道 {channel} 的投票配置")
        return True
    except Exception as e:
        logger.error(f"设置频道投票配置时出错: {type(e).__name__}: {e}", exc_info=True)
        return False


def _ensure_poll_settings_structure(current_config, channel):
    """
    确保投票配置结构存在

    Args:
        current_config: 当前配置字典
        channel: 频道URL
    """
    if 'channel_poll_settings' not in current_config:
        current_config['channel_poll_settings'] = {}
    
    if channel not in current_config['channel_poll_settings']:
        current_config['channel_poll_settings'][channel] = {}


def _update_poll_settings(current_config, channel, enabled, send_to_channel):
    """
    更新投票配置

    Args:
        current_config: 当前配置字典
        channel: 频道URL
        enabled: 是否启用投票
        send_to_channel: 发送位置
    """
    channel_config = current_config['channel_poll_settings'][channel]
    
    if enabled is not None:
        channel_config['enabled'] = enabled
        logger.info(f"设置频道 {channel} 的投票启用状态: {enabled}")
    
    if send_to_channel is not None:
        channel_config['send_to_channel'] = send_to_channel
        logger.info(f"设置频道 {channel} 的投票发送位置: {'频道' if send_to_channel else '讨论组'}")


def delete_channel_poll_config(channel):
    """删除指定频道的投票配置

    删除后，该频道将使用全局投票配置

    Args:
        channel: 频道URL

    Returns:
        bool: 是否成功删除配置
    """
    try:
        # 加载当前配置
        current_config = load_config()

        # 检查是否存在配置
        if 'channel_poll_settings' in current_config and channel in current_config['channel_poll_settings']:
            # 删除频道配置
            del current_config['channel_poll_settings'][channel]

            # 保存配置
            save_config(current_config)

            logger.info(f"已删除频道 {channel} 的投票配置，将使用全局配置")
            return True
        else:
            logger.info(f"频道 {channel} 没有独立的投票配置，无需删除")
            return True
    except Exception as e:
        logger.error(f"删除频道投票配置时出错: {type(e).__name__}: {e}", exc_info=True)
        return False


# 投票重新生成数据存储
POLL_REGENERATIONS_FILE = os.path.join(DATA_DIR, "data", "poll_regenerations.json")

# ==================== 目录管理工具函数 ====================

def ensure_data_directories():
    """确保所有必要的数据目录存在"""
    directories = [
        os.path.join(DATA_DIR, "sessions"),
        os.path.join(DATA_DIR, "config"),
        os.path.join(DATA_DIR, "data"),
        os.path.join(DATA_DIR, "database"),
        os.path.join(DATA_DIR, "temp")
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"确保目录存在: {directory}")
    
    logger.info("所有数据目录已就绪")

def migrate_old_files():
    """迁移旧路径的文件到新路径（向后兼容）"""
    import shutil
    
    # 获取迁移映射
    migrations = _get_migration_mappings()
    
    # 执行迁移
    migrated_count, skipped_count = _execute_migrations(migrations)
    
    # 记录结果
    _log_migration_results(migrated_count, skipped_count)
    
    return migrated_count


def _get_migration_mappings():
    """
    获取文件迁移映射

    Returns:
        list: 旧路径到新路径的映射列表
    """
    return [
        ("prompt.txt", PROMPT_FILE),
        ("poll_prompt.txt", POLL_PROMPT_FILE),
        ("config.json", CONFIG_FILE),
        (".restart_flag", RESTART_FLAG_FILE),
        (".shutdown_flag", SHUTDOWN_FLAG_FILE),
        (".last_summary_time.json", LAST_SUMMARY_FILE),
        (".poll_regenerations.json", POLL_REGENERATIONS_FILE),
        ("bot_session", SESSION_PATH),
        ("bot_session-journal", os.path.join(DATA_DIR, "sessions", "bot_session-journal")),
        ("session_name", SESSION_NAME_PATH),
        ("session_name-journal", os.path.join(DATA_DIR, "sessions", "session_name-journal")),
        ("summaries.db", DATABASE_PATH)
    ]


def _execute_migrations(migrations):
    """
    执行文件迁移

    Args:
        migrations: 迁移映射列表

    Returns:
        tuple: (迁移数量, 跳过数量)
    """
    migrated_count = 0
    skipped_count = 0
    
    for old_path, new_path in migrations:
        if _should_migrate_file(old_path, new_path):
            success = _migrate_single_file(old_path, new_path)
            if success:
                migrated_count += 1
        else:
            skipped_count += 1
    
    return migrated_count, skipped_count


def _should_migrate_file(old_path, new_path):
    """
    判断是否需要迁移文件

    Args:
        old_path: 旧路径
        new_path: 新路径

    Returns:
        bool: 是否需要迁移
    """
    # 旧文件不存在，无需迁移
    if not os.path.exists(old_path):
        return False
    
    # 新文件已存在，跳过迁移
    if os.path.exists(new_path):
        logger.info(f"新路径已存在，跳过迁移: {old_path} -> {new_path}")
        return False
    
    return True


def _migrate_single_file(old_path, new_path):
    """
    迁移单个文件

    Args:
        old_path: 旧路径
        new_path: 新路径

    Returns:
        bool: 是否成功
    """
    try:
        # 确保目标目录存在
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        
        # 复制文件（保留原文件）
        import shutil
        shutil.copy2(old_path, new_path)
        logger.info(f"已迁移文件: {old_path} -> {new_path}")
        return True
    except Exception as e:
        logger.error(f"迁移文件失败 {old_path} -> {new_path}: {e}")
        return False


def _log_migration_results(migrated_count, skipped_count):
    """
    记录迁移结果

    Args:
        migrated_count: 迁移数量
        skipped_count: 跳过数量
    """
    if migrated_count > 0:
        logger.info(f"文件迁移完成: 共迁移 {migrated_count} 个文件，跳过 {skipped_count} 个文件")
        logger.info("旧文件已保留，如需删除请手动清理")
    else:
        logger.debug("没有需要迁移的旧文件")

# ==================== 初始化目录结构 ====================

# 在模块加载时确保目录结构存在
ensure_data_directories()


def load_poll_regenerations():
    """加载投票重新生成数据

    Returns:
        dict: 投票重新生成数据字典
    """
    import json
    if os.path.exists(POLL_REGENERATIONS_FILE):
        try:
            with open(POLL_REGENERATIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载投票重新生成数据失败: {e}")
            return {}
    return {}


def save_poll_regenerations(data):
    """保存投票重新生成数据

    Args:
        data: 要保存的数据字典
    """
    import json
    try:
        with open(POLL_REGENERATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存投票重新生成数据失败: {e}")


def add_poll_regeneration(channel, summary_msg_id, poll_msg_id,
                         button_msg_id, summary_text, channel_name, send_to_channel,
                         discussion_forward_msg_id=None):
    """添加一条投票重新生成记录

    Args:
        channel: 频道URL
        summary_msg_id: 总结消息ID
        poll_msg_id: 投票消息ID
        button_msg_id: 按钮消息ID
        summary_text: 总结文本
        channel_name: 频道名称
        send_to_channel: 是否发送到频道(True=频道, False=讨论组)
        discussion_forward_msg_id: 讨论组中的转发消息ID(仅讨论组模式需要)
    """
    from datetime import datetime, timezone
    data = load_poll_regenerations()
    if channel not in data:
        data[channel] = {}
    record = {
        "poll_message_id": poll_msg_id,
        "button_message_id": button_msg_id,
        "summary_text": summary_text,
        "channel_name": channel_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "send_to_channel": send_to_channel
    }
    # 如果是讨论组模式，保存转发消息ID
    if not send_to_channel and discussion_forward_msg_id is not None:
        record["discussion_forward_msg_id"] = discussion_forward_msg_id
    data[channel][str(summary_msg_id)] = record
    save_poll_regenerations(data)
    logger.info(f"已添加投票重新生成记录: channel={channel}, summary_id={summary_msg_id}")


def get_poll_regeneration(channel, summary_msg_id):
    """获取指定的投票重新生成记录

    Args:
        channel: 频道URL
        summary_msg_id: 总结消息ID

    Returns:
        dict: 投票重新生成记录,如果不存在返回None
    """
    data = load_poll_regenerations()
    return data.get(channel, {}).get(str(summary_msg_id))


def update_poll_regeneration(channel, summary_msg_id, poll_msg_id, button_msg_id):
    """更新投票重新生成记录的消息ID

    Args:
        channel: 频道URL
        summary_msg_id: 总结消息ID
        poll_msg_id: 新的投票消息ID
        button_msg_id: 新的按钮消息ID
    """
    data = load_poll_regenerations()
    if channel in data and str(summary_msg_id) in data[channel]:
        data[channel][str(summary_msg_id)]["poll_message_id"] = poll_msg_id
        data[channel][str(summary_msg_id)]["button_message_id"] = button_msg_id
        save_poll_regenerations(data)
        logger.info(f"已更新投票重新生成记录: channel={channel}, summary_id={summary_msg_id}")


def delete_poll_regeneration(channel, summary_msg_id):
    """删除指定的投票重新生成记录

    Args:
        channel: 频道URL
        summary_msg_id: 总结消息ID
    """
    data = load_poll_regenerations()
    if channel in data and str(summary_msg_id) in data[channel]:
        del data[channel][str(summary_msg_id)]
        save_poll_regenerations(data)
        logger.info(f"已删除投票重新生成记录: channel={channel}, summary_id={summary_msg_id}")


def cleanup_old_regenerations(days=30):
    """清理超过指定天数的旧记录

    Args:
        days: 保留天数,默认30天

    Returns:
        int: 清理的记录数量
    """
    from datetime import datetime, timezone, timedelta
    data = load_poll_regenerations()
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
    count = 0
    for channel in list(data.keys()):
        for summary_id in list(data[channel].keys()):
            record = data[channel][summary_id]
            try:
                record_time = datetime.fromisoformat(record["timestamp"])
                if record_time < cutoff_time:
                    del data[channel][summary_id]
                    count += 1
            except Exception:
                pass
    save_poll_regenerations(data)
    if count > 0:
        logger.info(f"已清理 {count} 条超过 {days} 天的投票重新生成记录")
    return count


# ==================== 讨论组ID缓存管理 ====================

def get_cached_discussion_group_id(channel_url):
    """获取缓存的讨论组ID

    Args:
        channel_url: 频道URL

    Returns:
        int: 讨论组ID,如果不存在则返回None
    """
    return LINKED_CHAT_CACHE.get(channel_url)


def cache_discussion_group_id(channel_url, discussion_group_id):
    """缓存讨论组ID

    Args:
        channel_url: 频道URL
        discussion_group_id: 讨论组ID (已转换为超级群组格式)
    """
    LINKED_CHAT_CACHE[channel_url] = discussion_group_id
    logger.debug(f"已缓存讨论组ID: {channel_url} -> {discussion_group_id}")


def clear_discussion_group_cache(channel_url=None):
    """清除讨论组ID缓存

    Args:
        channel_url: 可选,指定要清除的频道URL。如果为None则清除所有缓存
    """
    if channel_url:
        if channel_url in LINKED_CHAT_CACHE:
            del LINKED_CHAT_CACHE[channel_url]
            logger.info(f"已清除频道 {channel_url} 的讨论组ID缓存")
    else:
        LINKED_CHAT_CACHE.clear()
        logger.info("已清除所有讨论组ID缓存")


async def get_discussion_group_id_cached(client, channel_url):
    """获取频道的讨论组ID(带缓存)

    首先尝试从缓存获取,如果缓存不存在则从Telegram获取并缓存结果

    Args:
        client: Telegram客户端实例
        channel_url: 频道URL

    Returns:
        int: 讨论组ID(已转换为超级群组格式),如果频道没有讨论组则返回None
    """
    # 1. 先尝试从缓存获取
    cached_id = get_cached_discussion_group_id(channel_url)
    if cached_id is not None:
        logger.debug(f"使用缓存的讨论组ID: {channel_url} -> {cached_id}")
        return cached_id

    # 2. 缓存未命中,从Telegram获取
    from telethon.tl.functions.channels import GetFullChannelRequest

    try:
        full_channel = await client.get_entity(channel_url)

        # 获取讨论组ID
        discussion_group_id = None
        if hasattr(full_channel, 'linked_chat_id') and full_channel.linked_chat_id:
            discussion_group_id = full_channel.linked_chat_id
        else:
            # 尝试使用GetFullChannelRequest
            logger.debug(f"频道 {channel_url} 没有linked_chat_id属性,尝试GetFullChannelRequest")
            full_info = await client(GetFullChannelRequest(full_channel))
            if hasattr(full_info.full_chat, 'linked_chat_id') and full_info.full_chat.linked_chat_id:
                discussion_group_id = full_info.full_chat.linked_chat_id

        if discussion_group_id:
            # 转换为超级群组格式
            if discussion_group_id > 0:
                discussion_group_id = -1000000000000 - discussion_group_id

            # 缓存结果
            cache_discussion_group_id(channel_url, discussion_group_id)
            logger.info(f"已获取并缓存讨论组ID: {channel_url} -> {discussion_group_id}")
            return discussion_group_id
        else:
            logger.warning(f"频道 {channel_url} 没有绑定讨论组")
            return None

    except Exception as e:
        logger.error(f"获取频道 {channel_url} 的讨论组ID失败: {e}")
        return None
