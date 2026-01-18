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
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient

from ..config import (
    API_ID, API_HASH, CHANNELS, SESSION_NAME_PATH
)
from ..error_handler import retry_with_backoff, record_error

logger = logging.getLogger(__name__)


@retry_with_backoff(
    max_retries=3,
    base_delay=2.0,
    max_delay=60.0,
    exponential_backoff=True,
    retry_on_exceptions=(ConnectionError, TimeoutError, Exception)
)
async def fetch_last_week_messages(channels_to_fetch=None, start_time=None, report_message_ids=None):
    """抓取指定时间范围的频道消息
    
    Args:
        channels_to_fetch: 可选，要抓取的频道列表。如果为None，则抓取所有配置的频道。
        start_time: 可选，开始抓取的时间。如果为None，则默认抓取过去一周的消息。
        report_message_ids: 可选，要排除的报告消息ID列表，按频道分组。
    """
    # 确保 API_ID 是整数
    logger.info("开始抓取指定时间范围的频道消息")
    
    async with TelegramClient(SESSION_NAME_PATH, int(API_ID), API_HASH) as client:
        # 如果没有提供开始时间，则默认抓取过去一周的消息
        if start_time is None:
            start_time = datetime.now(timezone.utc) - timedelta(days=7)
            logger.info(f"未提供开始时间，默认抓取过去一周的消息")
        
        messages_by_channel = {}  # 按频道分组的消息字典
        report_message_ids = report_message_ids or {}
        
        # 确定要抓取的频道
        if channels_to_fetch and isinstance(channels_to_fetch, list):
            # 只抓取指定的频道
            channels = channels_to_fetch
            logger.info(f"正在抓取指定的 {len(channels)} 个频道的消息，时间范围: {start_time} 至今")
        else:
            # 抓取所有配置的频道
            if not CHANNELS:
                logger.warning("没有配置任何频道，无法抓取消息")
                return messages_by_channel
            channels = CHANNELS
            logger.info(f"正在抓取所有 {len(channels)} 个频道的消息，时间范围: {start_time} 至今")
        
        total_message_count = 0
        
        # 遍历所有要抓取的频道
        for channel in channels:
            channel_messages = []
            channel_message_count = 0
            skipped_report_count = 0
            logger.info(f"开始抓取频道: {channel}")
            
            # 获取当前频道要排除的报告消息ID列表
            exclude_ids = report_message_ids.get(channel, [])
            logger.info(f"频道 {channel} 要排除的报告消息ID列表: {exclude_ids}")
            
            try:
                async for message in client.iter_messages(channel, offset_date=start_time, reverse=True):
                    total_message_count += 1
                    channel_message_count += 1
                    
                    # 跳过报告消息
                    if message.id in exclude_ids:
                        skipped_report_count += 1
                        logger.debug(f"跳过报告消息，ID: {message.id}")
                        continue
                    
                    if message.text:
                        # 动态获取频道名用于生成链接
                        channel_part = channel.split('/')[-1]
                        msg_link = f"https://t.me/{channel_part}/{message.id}"
                        channel_messages.append(f"内容: {message.text[:500]}\n链接: {msg_link}")
                        
                        # 每抓取10条消息记录一次日志
                        if len(channel_messages) % 10 == 0:
                            logger.debug(f"频道 {channel} 已抓取 {len(channel_messages)} 条有效消息")
            except Exception as e:
                record_error(e, f"fetch_messages_channel_{channel}")
                logger.error(f"抓取频道 {channel} 消息时出错: {e}")
                # 继续处理其他频道
                continue
            
            # 将当前频道的消息添加到字典中
            messages_by_channel[channel] = channel_messages
            logger.info(f"频道 {channel} 抓取完成，共处理 {channel_message_count} 条消息，其中 {len(channel_messages)} 条包含文本内容，跳过了 {skipped_report_count} 条报告消息")
        
        logger.info(f"所有指定频道消息抓取完成，共处理 {total_message_count} 条消息")
        return messages_by_channel
