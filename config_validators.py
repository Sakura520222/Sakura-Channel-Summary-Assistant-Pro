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

"""
配置验证模块
提供统一的配置验证逻辑，减少代码重复
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class ScheduleValidator:
    """时间配置验证器"""

    # 有效的频率类型
    VALID_FREQUENCIES = ['daily', 'weekly']
    
    # 有效的星期几
    VALID_DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    @staticmethod
    def validate_frequency(frequency: str) -> Tuple[bool, str]:
        """
        验证频率配置
        
        Args:
            frequency: 频率类型
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        if frequency not in ScheduleValidator.VALID_FREQUENCIES:
            return False, f"无效的频率: {frequency}，有效值: {', '.join(ScheduleValidator.VALID_FREQUENCIES)}"
        return True, ""

    @staticmethod
    def validate_weekly_days(days: list) -> Tuple[bool, str]:
        """
        验证weekly模式的days配置
        
        Args:
            days: 星期几列表
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        if not isinstance(days, list) or not days:
            return False, "weekly 模式必须提供 days 字段（非空数组）"
        
        for day in days:
            if day not in ScheduleValidator.VALID_DAYS:
                return False, f"无效的星期几: {day}，有效值: {', '.join(ScheduleValidator.VALID_DAYS)}"
        return True, ""

    @staticmethod
    def validate_time(hour: int, minute: int) -> Tuple[bool, str]:
        """
        验证时间配置
        
        Args:
            hour: 小时（0-23）
            minute: 分钟（0-59）
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        if not isinstance(hour, int) or hour < 0 or hour > 23:
            return False, f"无效的小时: {hour}，有效范围: 0-23"
        if not isinstance(minute, int) or minute < 0 or minute > 59:
            return False, f"无效的分钟: {minute}，有效范围: 0-59"
        return True, ""

    @staticmethod
    def validate_schedule_v2(config_dict: dict) -> Tuple[bool, str]:
        """
        验证新的时间配置格式
        
        Args:
            config_dict: 包含 frequency, days, hour, minute 的字典
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        frequency = config_dict.get('frequency')
        is_valid, error_msg = ScheduleValidator.validate_frequency(frequency)
        if not is_valid:
            return False, error_msg

        if frequency == 'weekly':
            days = config_dict.get('days', [])
            is_valid, error_msg = ScheduleValidator.validate_weekly_days(days)
            if not is_valid:
                return False, error_msg

        hour = config_dict.get('hour')
        minute = config_dict.get('minute')
        is_valid, error_msg = ScheduleValidator.validate_time(hour, minute)
        if not is_valid:
            return False, error_msg

        return True, "配置有效"


class LegacyScheduleValidator:
    """旧版时间配置验证器（向后兼容）"""

    @staticmethod
    def validate_schedule(day: str, hour: int, minute: int) -> Tuple[bool, str]:
        """
        验证旧版时间配置格式
        
        Args:
            day: 星期几
            hour: 小时（0-23）
            minute: 分钟（0-59）
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        valid_days = ScheduleValidator.VALID_DAYS
        
        if day not in valid_days:
            return False, f"无效的星期几: {day}，有效值: {', '.join(valid_days)}"
        
        return ScheduleValidator.validate_time(hour, minute)
