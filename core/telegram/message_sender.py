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

import logging
from datetime import datetime, timezone
from telethon import TelegramClient

from ..config import (
    API_ID, API_HASH, BOT_TOKEN, ADMIN_LIST, SEND_REPORT_TO_SOURCE,
    SESSION_PATH, LLM_MODEL,
)

from ..telegram_client_utils import split_message_smart, validate_message_entities

logger = logging.getLogger(__name__)

# 全局变量，用于存储活动的Telegram客户端实例
_active_client = None


def set_active_client(client):
    """设置活动的Telegram客户端实例"""
    global _active_client
    _active_client = client
    logger.info("已设置活动的Telegram客户端实例")


def get_active_client():
    """获取活动的Telegram客户端实例"""
    return _active_client


def extract_date_range_from_summary(summary_text):
    """
    从总结文本中提取日期范围

    Args:
        summary_text: 总结文本

    Returns:
        (start_time, end_time): 起始时间和结束时间的datetime对象，解析失败返回(None, None)
    """
    try:
        # 尝试匹配周报日期
        weekly_range = _extract_weekly_date_range(summary_text)
        if weekly_range:
            return weekly_range

        # 尝试匹配日报日期
        daily_range = _extract_daily_date_range(summary_text)
        if daily_range:
            return daily_range

        # 没有匹配到日期模式
        logger.debug("未能从总结文本中提取日期范围")
        return None, None

    except Exception as e:
        logger.warning(f"提取日期范围时出错: {e}")
        return None, None


def _extract_weekly_date_range(summary_text):
    """
    从总结文本中提取周报日期范围

    Args:
        summary_text: 总结文本

    Returns:
        tuple: (start_time, end_time) 或 None
    """
    import re
    
    # 匹配周报日期范围: "**xxx周报 1.8-1.15**"
    weekly_pattern = r"\*\*.*?周报\s*(\d{1,2})\.(\d{1,2})\s*[-—~]\s*(\d{1,2})\.(\d{1,2})\*\*"
    weekly_match = re.search(weekly_pattern, summary_text)

    if not weekly_match:
        return None

    start_month = int(weekly_match.group(1))
    start_day = int(weekly_match.group(2))
    end_month = int(weekly_match.group(3))
    end_day = int(weekly_match.group(4))

    current_year = datetime.now().year

    start_time = datetime(current_year, start_month, start_day, tzinfo=timezone.utc)
    end_time = datetime(current_year, end_month, end_day, 23, 59, 59, tzinfo=timezone.utc)

    # 如果结束时间早于开始时间，说明跨年了
    if end_time < start_time:
        end_time = datetime(current_year + 1, end_month, end_day, 23, 59, 59, tzinfo=timezone.utc)

    return start_time, end_time


def _extract_daily_date_range(summary_text):
    """
    从总结文本中提取日报日期

    Args:
        summary_text: 总结文本

    Returns:
        tuple: (start_time, end_time) 或 None
    """
    import re
    
    # 匹配日报日期: "**xxx日报 1.15**"
    daily_pattern = r"\*\*.*?日报\s*(\d{1,2})\.(\d{1,2})\*\*"
    daily_match = re.search(daily_pattern, summary_text)

    if not daily_match:
        return None

    month = int(daily_match.group(1))
    day = int(daily_match.group(2))
    current_year = datetime.now().year

    start_time = datetime(current_year, month, day, tzinfo=timezone.utc)
    end_time = datetime(current_year, month, day, 23, 59, 59, tzinfo=timezone.utc)

    return start_time, end_time


async def send_long_message(client, chat_id, text, max_length=4000, channel_title=None, show_pagination=True):
    """分段发送长消息
    
    Args:
        client: Telegram客户端实例
        chat_id: 接收者聊天ID
        text: 要发送的文本
        max_length: 最大分段长度，默认4000字符
        channel_title: 频道标题，用于分段消息的标题。如果为None，则使用"更新日志"
        show_pagination: 是否在每条消息显示分页标题（如"1/3"），默认为True。设为False时只在第一条显示标题
    """
    logger.info(f"开始发送长消息，接收者: {chat_id}，消息总长度: {len(text)}字符，最大分段长度: {max_length}字符")
    
    if len(text) <= max_length:
        logger.info(f"消息长度未超过限制，直接发送")
        # 如果消息不超过限制但提供了标题，可以添加标题
        if channel_title and show_pagination:
            text = f"📋 **{channel_title}**\n\n{text}"
        await client.send_message(chat_id, text, link_preview=False)
        return
    
    # 确定标题
    if channel_title is None:
        channel_title = "更新日志"
    
    # 计算标题长度
    if show_pagination:
        # 标题格式：📋 **{channel_title} ({i+1}/{len(parts)})**\n\n
        # 计算最大可能标题长度
        max_title_length = len(f"📋 **{channel_title} (99/99)**\n\n")
    else:
        # 只在第一条消息显示标题，其他条不显示
        # 第一条：📋 **{channel_title}**\n\n
        # 其他：无标题
        max_title_length = len(f"📋 **{channel_title}**\n\n")
    
    # 实际可用于内容的最大长度
    content_max_length = max_length - max_title_length
    
    logger.info(f"消息需要分段发送，开始分段处理，标题长度: {max_title_length}字符，内容最大长度: {content_max_length}字符")
    
    # 使用智能分割算法
    try:
        parts = split_message_smart(text, content_max_length, preserve_md=True)
        logger.info(f"智能分割完成，共分成 {len(parts)} 段")
        
        # 验证每个分段的实体完整性
        for i, part in enumerate(parts):
            is_valid, error_msg = validate_message_entities(part)
            if not is_valid:
                logger.warning(f"第 {i+1} 段实体验证失败: {error_msg}")
                # 尝试修复：移除有问题的格式
                parts[i] = part.replace('**', '').replace('`', '')
                logger.info(f"已修复第 {i+1} 段的格式问题")
    except Exception as e:
        logger.error(f"智能分割失败，使用简单分割: {e}")
        # 回退到简单分割
        parts = []
        text_length = len(text)
        for i in range(0, text_length, content_max_length):
            part = text[i:i+content_max_length]
            if part:
                parts.append(part)
        logger.info(f"简单分割完成，共分成 {len(parts)} 段")
    
    # 验证分段结果
    total_content_length = sum(len(part) for part in parts)
    logger.debug(f"分段后总内容长度: {total_content_length}字符，原始长度: {len(text)}字符")
    
    # 发送所有部分
    for i, part in enumerate(parts):
        # 根据 show_pagination 参数决定标题格式
        if show_pagination:
            # 在每条消息显示分页标题
            full_message = f"📋 **{channel_title} ({i+1}/{len(parts)})**\n\n{part}"
        else:
            # 不显示任何标题，直接发送内容
            full_message = part
        
        full_message_length = len(full_message)
        logger.info(f"正在发送第 {i+1}/{len(parts)} 段，长度: {full_message_length}字符")
        
        # 验证消息长度不超过限制
        if full_message_length > max_length:
            logger.error(f"第 {i+1} 段消息长度 {full_message_length} 超过限制 {max_length}，将进行紧急分割")
            # 紧急分割：直接按字符分割
            for j in range(0, full_message_length, max_length):
                emergency_part = full_message[j:j+max_length]
                await client.send_message(chat_id, emergency_part, link_preview=False)
                logger.warning(f"发送紧急分割段 {j//max_length + 1}")
        else:
            try:
                await client.send_message(chat_id, full_message, link_preview=False)
                logger.debug(f"成功发送第 {i+1}/{len(parts)} 段")
            except Exception as e:
                logger.error(f"发送第 {i+1} 段失败: {e}")
                # 尝试移除格式后重试
                try:
                    plain_message = full_message.replace('**', '').replace('`', '')
                    await client.send_message(chat_id, plain_message, link_preview=False)
                    logger.info(f"已成功发送第 {i+1} 段（移除格式后）")
                except Exception as e2:
                    logger.error(f"即使移除格式后发送第 {i+1} 段仍然失败: {e2}")


async def send_report(summary_text, source_channel=None, client=None, skip_admins=False, message_count=0):
    """发送报告

    Args:
        summary_text: 报告内容
        source_channel: 源频道，可选。如果提供，将向该频道发送报告
        client: 可选。已存在的Telegram客户端实例，如果不提供，将尝试使用活动的客户端实例或创建新实例
        skip_admins: 是否跳过向管理员发送报告，默认为False
        message_count: 消息数量，用于数据库记录，默认为0

    Returns:
        dict: 包含所有消息ID的字典
            {
                "summary_message_ids": [12345, 12346],  # 总结消息ID列表
                "poll_message_id": 12347,                # 投票消息ID(单个)
                "button_message_id": 12348               # 按钮消息ID(单个)
            }
    """
    # 延迟导入避免循环依赖
    from .poll_sender import send_poll
    
    logger.info("开始发送报告")
    logger.debug(f"报告长度: {len(summary_text)}字符")

    # 存储发送到源频道的消息ID
    report_message_ids = []
    poll_message_id = None
    button_message_id = None
    
    try:
        # 确定使用哪个客户端实例
        # 1. 如果提供了客户端实例，直接使用它
        # 2. 否则，尝试使用活动的客户端实例
        # 3. 否则，创建新实例
        if client:
            logger.info("使用提供的客户端实例发送报告")
            use_client = client
            # 如果提供了客户端实例，我们假设它已经启动并连接
            use_existing_client = True
        else:
            # 尝试获取活动的客户端实例
            active_client = get_active_client()
            if active_client:
                logger.info("使用活动的客户端实例发送报告")
                use_client = active_client
                use_existing_client = True
            else:
                logger.info("没有活动的客户端实例，创建新客户端实例发送报告")
                use_client = TelegramClient(SESSION_PATH, int(API_ID), API_HASH)
                use_existing_client = False
        
        if use_existing_client:
            # 使用现有的客户端实例（已经启动并连接）
            
            # 获取频道实际名称（如果提供了源频道）
            channel_actual_name = None
            if source_channel:
                try:
                    channel_entity = await use_client.get_entity(source_channel)
                    channel_actual_name = channel_entity.title
                    logger.info(f"获取到频道实际名称: {channel_actual_name}")
                except Exception as e:
                    logger.warning(f"获取频道实体失败，使用默认名称: {e}")
                    # 使用频道链接的最后部分作为回退
                    channel_actual_name = source_channel.split('/')[-1]
            
            # 提取日期范围和报告类型（从原总结文本中提取）
            date_range = ""
            report_type = ""
            if ("周报" in summary_text or "日报" in summary_text) and "**" in summary_text:
                # 尝试从原总结文本中提取日期范围和类型
                import re
                # 匹配周报或日报的日期范围
                weekly_pattern = r"\*\*.*周报\s*([0-9.]+-[0-9.]+)\*\*"
                daily_pattern = r"\*\*.*日报\s*([0-9.]+)\*\*"
                weekly_match = re.search(weekly_pattern, summary_text)
                daily_match = re.search(daily_pattern, summary_text)
                if weekly_match:
                    date_range = weekly_match.group(1)
                    report_type = "周报"
                elif daily_match:
                    date_range = daily_match.group(1)
                    report_type = "日报"

            # 检查总结文本是否已经有正确的标题格式
            # 如果总结文本已经以 "**" 开头，说明已经有标题，不需要重复添加
            summary_text_for_admins = summary_text  # 管理员接收的文本
            summary_text_for_source = summary_text  # 源频道接收的文本

            # 如果提供了源频道，检查是否需要更新标题
            if source_channel and channel_actual_name:
                # 检查总结文本是否已经有标题（周报或日报）
                if summary_text.startswith("**") and ("周报" in summary_text or "日报" in summary_text):
                    # 已经有标题，检查是否需要更新为频道实际名称
                    # 提取日期范围
                    if date_range:
                        expected_title = f"**{channel_actual_name} {report_type} {date_range}**"
                    else:
                        expected_title = f"**{channel_actual_name} {report_type}**"

                    # 如果当前标题与预期标题不同，则更新
                    if not summary_text.startswith(expected_title):
                        # 找到原标题的结束位置
                        if "** " in summary_text:
                            start_idx = summary_text.index("**")
                            end_idx = summary_text.index("** ", start_idx) + 2
                            # 替换标题
                            summary_text_for_source = expected_title + summary_text[end_idx:]
                            summary_text_for_admins = summary_text_for_source
                else:
                    # 没有标题，添加标题（默认为周报）
                    if not report_type:
                        report_type = "周报"
                    if date_range:
                        new_title = f"**{channel_actual_name} {report_type} {date_range}**"
                    else:
                        new_title = f"**{channel_actual_name} {report_type}**"
                    summary_text_for_source = new_title + "\n\n" + summary_text
                    summary_text_for_admins = summary_text_for_source
            
            # 向所有管理员发送消息（除非跳过）
            if not skip_admins:
                for admin_id in ADMIN_LIST:
                    try:
                        logger.info(f"正在向管理员 {admin_id} 发送报告")
                        await send_long_message(use_client, admin_id, summary_text_for_admins, show_pagination=False)
                        logger.info(f"成功向管理员 {admin_id} 发送报告")
                    except Exception as e:
                        logger.error(f"向管理员 {admin_id} 发送报告失败: {type(e).__name__}: {e}", exc_info=True)
            else:
                logger.info("跳过向管理员发送报告")
            
            # 如果提供了源频道且配置允许，向源频道发送报告
            if source_channel and SEND_REPORT_TO_SOURCE:
                try:
                    logger.info(f"正在向源频道 {source_channel} 发送报告")
                    
                    # 直接调用use_client.send_message并收集消息ID
                    if len(summary_text_for_source) <= 4000:
                        # 短消息直接发送
                        msg = await use_client.send_message(source_channel, summary_text_for_source, link_preview=False)
                        report_message_ids.append(msg.id)
                    else:
                        # 长消息分段发送，收集每个分段的消息ID
                        # 使用频道实际名称作为分段消息标题
                        channel_title = channel_actual_name if channel_actual_name else "频道周报汇总"
                        
                        # 使用send_long_message函数进行智能分割和发送
                        # 但需要收集消息ID，所以需要自定义实现
                        max_length = 4000
                        max_title_length = len(f"📋 **{channel_title} (99/99)**\n\n")
                        content_max_length = max_length - max_title_length
                        
                        # 使用智能分割算法
                        try:
                            parts = split_message_smart(summary_text_for_source, content_max_length, preserve_md=True)
                            logger.info(f"智能分割完成，共分成 {len(parts)} 段")
                            
                            # 验证每个分段的实体完整性
                            for i, part in enumerate(parts):
                                is_valid, error_msg = validate_message_entities(part)
                                if not is_valid:
                                    logger.warning(f"第 {i+1} 段实体验证失败: {error_msg}")
                                    # 尝试修复：移除有问题的格式
                                    parts[i] = part.replace('**', '').replace('`', '')
                                    logger.info(f"已修复第 {i+1} 段的格式问题")
                        except Exception as e:
                            logger.error(f"智能分割失败，使用简单分割: {e}")
                            # 回退到简单分割
                            parts = []
                            text_length = len(summary_text_for_source)
                            for i in range(0, text_length, content_max_length):
                                part = summary_text_for_source[i:i+content_max_length]
                                if part:
                                    parts.append(part)
                            logger.info(f"简单分割完成，共分成 {len(parts)} 段")
                        
                        # 发送所有部分并收集消息ID
                        for i, part in enumerate(parts):
                            # 不显示任何标题，直接发送内容
                            part_text = part
                            try:
                                msg = await use_client.send_message(source_channel, part_text, link_preview=False)
                                report_message_ids.append(msg.id)
                                logger.debug(f"成功发送第 {i+1}/{len(parts)} 段，消息ID: {msg.id}")
                            except Exception as e:
                                logger.error(f"发送第 {i+1} 段失败: {e}")
                                # 尝试移除格式后重试
                                try:
                                    plain_text = part_text.replace('**', '').replace('`', '')
                                    msg = await use_client.send_message(source_channel, plain_text, link_preview=False)
                                    report_message_ids.append(msg.id)
                                    logger.info(f"已成功发送第 {i+1} 段（移除格式后），消息ID: {msg.id}")
                                except Exception as e2:
                                    logger.error(f"即使移除格式后发送第 {i+1} 段仍然失败: {e2}")
                    
                    logger.info(f"成功向源频道 {source_channel} 发送报告，消息ID: {report_message_ids}")
                    
                    # 自动置顶第一条消息
                    if report_message_ids:
                        try:
                            first_message_id = report_message_ids[0]
                            await use_client.pin_message(source_channel, first_message_id)
                            logger.info(f"已成功置顶消息ID: {first_message_id}")
                        except Exception as e:
                            logger.warning(f"置顶消息失败，可能需要管理员权限: {e}")
                    
                    # 如果启用了投票功能，根据频道配置发送投票
                    if report_message_ids:
                        logger.info(f"开始处理投票发送，总结消息ID: {report_message_ids[0]}")
                        # 使用第一个消息ID作为投票回复目标
                        poll_result = await send_poll(
                            use_client, source_channel, report_message_ids[0], summary_text_for_source
                        )
                        if poll_result and poll_result.get("poll_msg_id"):
                            poll_message_id = poll_result.get("poll_msg_id")
                            button_message_id = poll_result.get("button_msg_id")
                            logger.info(f"投票成功发送, poll_msg_id={poll_message_id}, button_msg_id={button_message_id}")
                        else:
                            logger.warning("投票发送失败，但总结消息已成功发送")
                except Exception as e:
                    logger.error(f"向源频道 {source_channel} 发送报告失败: {type(e).__name__}: {e}", exc_info=True)
        
        # 保存到数据库
        # 如果成功发送总结到频道，保存到数据库
        if source_channel and report_message_ids:
            try:
                from ..database import get_db_manager

                # 提取时间范围
                start_time, end_time = extract_date_range_from_summary(summary_text_for_source)

                # 保存到数据库
                db = get_db_manager()
                summary_id = db.save_summary(
                    channel_id=source_channel,
                    channel_name=channel_actual_name,
                    summary_text=summary_text_for_source,
                    message_count=message_count,
                    start_time=start_time,
                    end_time=end_time,
                    summary_message_ids=report_message_ids,
                    poll_message_id=poll_message_id,
                    button_message_id=button_message_id,
                    ai_model=LLM_MODEL,
                    summary_type='manual'  # 手动触发的总结
                )

                if summary_id:
                    logger.info(f"总结已保存到数据库，记录ID: {summary_id}")
                else:
                    logger.warning("保存到数据库失败，但不影响总结发送")

            except Exception as e:
                logger.error(f"保存总结到数据库时出错: {type(e).__name__}: {e}", exc_info=True)
                # 数据库保存失败不影响总结发送，只记录日志

        # 返回包含所有消息ID的字典
        return {
            "summary_message_ids": report_message_ids,
            "poll_message_id": poll_message_id,
            "button_message_id": button_message_id
        }

    except Exception as e:
        logger.error(f"发送报告时发生严重错误: {type(e).__name__}: {e}", exc_info=True)
        # 返回空字典，而不是让程序崩溃
        return {
            "summary_message_ids": [],
            "poll_message_id": None,
            "button_message_id": None
        }
