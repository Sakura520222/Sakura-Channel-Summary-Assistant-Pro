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
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def _convert_channel_data(channel_data, include_report_ids):
    """
    转换单个频道数据
    
    Args:
        channel_data: 原始频道数据
        include_report_ids: 是否包含消息ID
    
    Returns:
        转换后的数据
    """
    time_obj = datetime.fromisoformat(channel_data["time"])
    
    if not include_report_ids:
        return time_obj
    
    # 兼容旧格式: report_message_ids
    summary_ids = channel_data.get("report_message_ids", [])
    if "summary_message_ids" in channel_data:
        summary_ids = channel_data.get("summary_message_ids", [])
    
    return {
        "time": time_obj,
        "summary_message_ids": summary_ids,
        "poll_message_ids": channel_data.get("poll_message_ids", []),
        "button_message_ids": channel_data.get("button_message_ids", [])
    }


def _load_summary_file():
    """
    从文件加载总结数据
    
    Returns:
        dict: 总结数据字典，如果失败返回None
    """
    from config import LAST_SUMMARY_FILE
    
    logger.info(f"开始读取上次总结时间文件: {LAST_SUMMARY_FILE}")
    
    try:
        with open(LAST_SUMMARY_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                last_data = json.loads(content)
                logger.info(f"成功读取所有频道的上次总结数据: {last_data}")
                return last_data
            else:
                logger.warning(f"上次总结时间文件 {LAST_SUMMARY_FILE} 内容为空")
                return None
    except FileNotFoundError:
        logger.warning(f"上次总结时间文件 {LAST_SUMMARY_FILE} 不存在")
        return None
    except Exception as e:
        logger.error(f"读取上次总结时间文件 {LAST_SUMMARY_FILE} 时出错: {type(e).__name__}: {e}", exc_info=True)
        return None


def load_last_summary_time(channel=None, include_report_ids=False):
    """从文件中读取上次总结的时间和报告消息ID

    Args:
        channel: 可选，指定频道。如果提供，只返回该频道的信息；
                如果不提供，返回所有频道的信息字典
        include_report_ids: 可选，是否包含报告消息ID。默认False只返回时间，True返回包含时间和消息ID的字典
                                新版: 返回summary_message_ids, poll_message_ids, button_message_ids三类ID
    """
    last_data = _load_summary_file()
    
    if last_data is None:
        return None if channel else {}
    
    if channel:
        channel_data = last_data.get(channel)
        if channel_data:
            result = _convert_channel_data(channel_data, include_report_ids)
            if not include_report_ids:
                logger.info(f"成功读取频道 {channel} 的上次总结时间: {result}")
            return result
        else:
            logger.warning(f"频道 {channel} 的上次总结时间不存在")
            return None
    else:
        converted_data = {}
        for ch, data in last_data.items():
            converted_data[ch] = _convert_channel_data(data, include_report_ids)
        return converted_data

def _validate_and_convert_ids(ids, name):
    """
    验证并转换消息ID列表
    
    Args:
        ids: 消息ID，可以是列表、字典或其他类型
        name: 参数名称，用于日志
    
    Returns:
        list: 验证后的消息ID列表
    """
    if ids is None:
        return []
    
    if isinstance(ids, list):
        return ids
    
    if isinstance(ids, dict):
        logger.warning(f"检测到{name}是字典格式,自动提取: {ids}")
        return ids.get(name, [])
    
    logger.error(f"{name}类型错误: {type(ids)}, 使用空列表")
    return []


def _load_existing_summary_data():
    """
    加载现有的总结数据
    
    Returns:
        dict: 现有数据，如果文件不存在返回空字典
    """
    from config import LAST_SUMMARY_FILE
    
    if not os.path.exists(LAST_SUMMARY_FILE):
        return {}
    
    try:
        with open(LAST_SUMMARY_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except Exception as e:
        logger.error(f"读取现有数据时出错: {type(e).__name__}: {e}")
        return {}


def save_last_summary_time(channel, time_to_save, summary_message_ids=None, poll_message_ids=None, button_message_ids=None, report_message_ids=None):
    """将指定频道的上次总结时间和报告消息ID保存到文件中

    Args:
        channel: 频道标识
        time_to_save: 要保存的时间对象
        summary_message_ids: 总结消息ID列表(新格式)
        poll_message_ids: 投票消息ID列表(新格式)
        button_message_ids: 按钮消息ID列表(新格式)
        report_message_ids: 发送到源频道的报告消息ID列表(旧格式,兼容参数)
    """
    from config import LAST_SUMMARY_FILE

    logger.info(f"开始保存频道 {channel} 的上次总结时间到文件: {LAST_SUMMARY_FILE}")
    
    try:
        # 读取现有数据
        existing_data = _load_existing_summary_data()
        
        # 兼容旧格式: 如果提供report_message_ids,将其作为summary_message_ids
        if report_message_ids is not None and summary_message_ids is None:
            summary_message_ids = report_message_ids
        
        # 验证并转换所有ID列表
        summary_ids = _validate_and_convert_ids(summary_message_ids, "summary_message_ids")
        poll_ids = _validate_and_convert_ids(poll_message_ids, "poll_message_ids")
        button_ids = _validate_and_convert_ids(button_message_ids, "button_message_ids")
        
        # 更新频道数据
        existing_data[channel] = {
            "time": time_to_save.isoformat(),
            "summary_message_ids": summary_ids,
            "poll_message_ids": poll_ids,
            "button_message_ids": button_ids
        }
        
        # 写入文件
        with open(LAST_SUMMARY_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)

        logger.info(f"成功保存频道 {channel} 的上次总结时间: {time_to_save}")
        logger.debug(f"总结消息ID: {summary_ids}, 投票消息ID: {poll_ids}, 按钮消息ID: {button_ids}")
    except Exception as e:
        logger.error(f"保存上次总结时间到文件 {LAST_SUMMARY_FILE} 时出错: {type(e).__name__}: {e}", exc_info=True)
