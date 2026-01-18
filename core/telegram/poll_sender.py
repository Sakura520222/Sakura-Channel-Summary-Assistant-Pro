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
import asyncio

from ..config import ENABLE_POLL, get_channel_poll_config
from ..error_handler import record_error

logger = logging.getLogger(__name__)


async def send_poll_to_channel(client, channel, summary_message_id, summary_text):
    """发送投票到源频道，直接回复总结消息

    Args:
        client: Telegram客户端实例
        channel: 频道URL或ID
        summary_message_id: 总结消息在频道中的ID
        summary_text: 总结文本，用于生成投票内容

    Returns:
        dict: {"poll_msg_id": 12347, "button_msg_id": 12348} 或 None
    """
    logger.info(f"开始处理投票发送到频道: 频道={channel}, 消息ID={summary_message_id}")

    try:
        # 获取频道实体
        logger.info(f"获取频道实体: {channel}")
        channel_entity = await client.get_entity(channel)
        logger.info(f"成功获取频道实体: {channel_entity.title if hasattr(channel_entity, 'title') else channel}")

        # 生成投票内容
        logger.info("开始生成投票内容")
        from ..ai_client import generate_poll_from_summary
        poll_data = generate_poll_from_summary(summary_text)

        if not poll_data or 'question' not in poll_data or 'options' not in poll_data:
            logger.error("生成投票内容失败，使用默认投票")
            poll_data = {
                "question": "你对本周总结有什么看法？",
                "options": ["非常满意", "比较满意", "一般", "有待改进"]
            }

        # 发送投票，使用 reply_to 参数回复总结消息
        logger.info(f"发送投票到频道: {poll_data['question']}")

        # 使用底层RPC调用发送投票
        from telethon.tl.types import (
            InputMediaPoll, Poll, PollAnswer, TextWithEntities,
            InputReplyToMessage
        )
        from telethon.tl.functions.messages import SendMediaRequest
        from telethon import Button

        try:
            # 清洗并截断问题文本
            question_text = str(poll_data.get('question', '频道调研')).strip()[:250]

            # 构造选项
            poll_answers = []
            for i, opt in enumerate(poll_data.get('options', [])[:10]):
                opt_clean = str(opt).strip()[:100]
                poll_answers.append(PollAnswer(
                    text=TextWithEntities(text=opt_clean, entities=[]),
                    option=bytes([i])
                ))

            # 构造投票对象
            poll_obj = Poll(
                id=0,
                question=TextWithEntities(text=question_text, entities=[]),
                answers=poll_answers,
                closed=False,
                public_voters=False,
                multiple_choice=False,
                quiz=False
            )

            # 构造回复头
            reply_header = InputReplyToMessage(reply_to_msg_id=int(summary_message_id))

            # 发送投票到频道，回复总结消息
            poll_result = await client(SendMediaRequest(
                peer=channel,
                media=InputMediaPoll(poll=poll_obj),
                message='',
                reply_to=reply_header
            ))

            # 从返回结果中提取投票消息ID
            # poll_result是Updates类型,updates[0]可能是UpdateNewMessage或UpdateMessageID
            update = poll_result.updates[0]
            if hasattr(update, 'message'):
                # UpdateNewMessage类型
                poll_msg_id = update.message.id
            elif hasattr(update, 'id'):
                # UpdateMessageID类型
                poll_msg_id = update.id
            else:
                logger.error(f"无法从更新中提取消息ID: {update}")
                return None

            logger.info(f"✅ 成功发送投票到频道并回复消息 {summary_message_id}, 投票消息ID: {poll_msg_id}")

            # 发送重新生成按钮
            logger.info("开始发送重新生成按钮消息")
            try:
                # 使用 Telethon 的高层 Button API
                # 注意：buttons 必须是二维列表 [[...]]
                button_markup = [[Button.inline(
                    "🔄 重新生成投票",
                    data=f"regen_poll_{summary_message_id}".encode('utf-8')
                )]]

                # 发送按钮消息，回复投票
                button_msg = await client.send_message(
                    channel,
                    "💡 投票效果不理想?点击下方按钮重新生成",
                    reply_to=poll_msg_id,
                    buttons=button_markup
                )

                logger.info(f"✅ 成功发送重新生成按钮,消息ID: {button_msg.id}")

                # 保存映射关系到存储
                from ..config import add_poll_regeneration
                channel_name = channel_entity.title if hasattr(channel_entity, 'title') else channel
                add_poll_regeneration(
                    channel=channel,
                    summary_msg_id=summary_message_id,
                    poll_msg_id=poll_msg_id,
                    button_msg_id=button_msg.id,
                    summary_text=summary_text,
                    channel_name=channel_name,
                    send_to_channel=True
                )

                # 返回消息ID
                return {
                    "poll_msg_id": poll_msg_id,
                    "button_msg_id": button_msg.id
                }

            except Exception as e:
                logger.error(f"发送重新生成按钮失败: {e}")
                # 按钮发送失败仍然返回投票ID
                return {
                    "poll_msg_id": poll_msg_id,
                    "button_msg_id": None
                }

        except Exception as e:
            logger.error(f"发送投票到频道失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    except Exception as e:
        record_error(e, "send_poll_to_channel")
        logger.error(f"发送投票到频道时发生错误: {type(e).__name__}: {e}", exc_info=True)
        return None


async def send_poll_to_discussion_group(client, channel, summary_message_id, summary_text):
    """发送投票到频道的讨论组（评论区）

    Args:
        client: Telegram客户端实例
        channel: 频道URL或ID
        summary_message_id: 总结消息在频道中的ID
        summary_text: 总结文本，用于生成投票内容

    Returns:
        dict: {"poll_msg_id": 12347, "button_msg_id": 12348} 或 None
    """
    logger.info(f"开始处理投票发送到讨论组: 频道={channel}, 消息ID={summary_message_id}")

    if not ENABLE_POLL:
        logger.info("投票功能已禁用，跳过投票发送")
        return False

    try:
        # 获取频道实体
        logger.info(f"获取频道实体: {channel}")
        channel_entity = await client.get_entity(channel)
        channel_id = channel_entity.id
        channel_name = channel_entity.title if hasattr(channel_entity, 'title') else channel

        # 检查频道是否有绑定的讨论组(使用缓存版本)
        from ..config import get_discussion_group_id_cached
        discussion_group_id = await get_discussion_group_id_cached(client, channel)

        if not discussion_group_id:
            logger.warning(f"频道 {channel} 没有绑定讨论组，无法发送投票到评论区")
            return False

        logger.info(f"频道 {channel} 绑定的讨论组ID: {discussion_group_id}")

        # 检查机器人是否在讨论组中
        try:
            await client.get_permissions(discussion_group_id)
            logger.info(f"机器人已在讨论组 {discussion_group_id} 中")
        except Exception as e:
            logger.warning(f"机器人未加入讨论组 {discussion_group_id} 或没有权限: {e}")
            logger.warning("请将机器人添加到频道的讨论组（私人群组）中")
            return False

        # 生成投票内容
        logger.info("开始生成投票内容")
        from ..ai_client import generate_poll_from_summary
        poll_data = generate_poll_from_summary(summary_text)

        if not poll_data or 'question' not in poll_data or 'options' not in poll_data:
            logger.error("生成投票内容失败，使用默认投票")
            poll_data = {
                "question": "你对本周总结有什么看法？",
                "options": ["非常满意", "比较满意", "一般", "有待改进"]
            }

        # 使用事件监听方式等待转发消息
        logger.info(f"等待频道消息转发到讨论组...")

        # 创建事件Future来等待转发消息
        from asyncio import Future
        forward_message_future = Future()

        # 定义事件处理器
        from telethon import events

        @client.on(events.NewMessage(chats=discussion_group_id))
        async def on_discussion_message(event):
            msg = event.message

            # 检查是否是转发消息
            if (hasattr(msg, 'fwd_from') and msg.fwd_from and
                hasattr(msg.fwd_from, 'from_id') and msg.fwd_from.from_id and
                hasattr(msg.fwd_from.from_id, 'channel_id') and
                msg.fwd_from.from_id.channel_id == channel_id and
                msg.fwd_from.channel_post == summary_message_id):

                logger.info(f"收到转发消息，讨论组消息ID: {msg.id}")
                forward_message_future.set_result(msg)

                # 移除事件处理器
                client.remove_event_handler(on_discussion_message)

        # 等待转发消息（最多10秒）
        try:
            forward_message = await asyncio.wait_for(forward_message_future, timeout=10)
            logger.info(f"成功收到转发消息，ID: {forward_message.id}")

            # 发送投票作为回复
            logger.info(f"发送投票到讨论组: {poll_data['question']}")

            # 终极解决方案：直接使用底层RPC调用SendMediaRequest
            # 绕过send_message内部可能出错的自动转换逻辑
            from telethon.tl.types import (
                InputMediaPoll, Poll, PollAnswer, TextWithEntities,
                InputReplyToMessage
            )
            from telethon.tl.functions.messages import SendMediaRequest
            from telethon import Button

            try:
                # 1. 严格清洗并截断
                question_text = str(poll_data.get('question', '频道调研')).strip()[:250]

                # 2. 构造选项，确保text字段被显式包装为TextWithEntities
                # 这是为了适配2025/2026年最新的协议层要求
                poll_answers = []
                for i, opt in enumerate(poll_data.get('options', [])[:10]):
                    opt_clean = str(opt).strip()[:100]
                    poll_answers.append(PollAnswer(
                        text=TextWithEntities(text=opt_clean, entities=[]),
                        option=bytes([i])
                    ))

                # 3. 手动构造底层Poll对象
                # 注意：question必须是TextWithEntities对象
                poll_obj = Poll(
                    id=0,  # 这里的id由Telegram分配，发出去时设为0
                    question=TextWithEntities(text=question_text, entities=[]),
                    answers=poll_answers,
                    closed=False,
                    public_voters=False,
                    multiple_choice=False,
                    quiz=False
                )

                # 4. 【关键修复】将reply_to包装为InputReplyToMessage对象
                # 这里的forward_message.id是转发消息ID，例如47
                reply_header = InputReplyToMessage(reply_to_msg_id=int(forward_message.id))

                # 5. 【核心区别】直接通过client(...)发起SendMediaRequest
                # 这会绕过send_message内部那些容易出错的自动转换逻辑
                poll_result = await client(SendMediaRequest(
                    peer=int(discussion_group_id),  # 必须是int, 例如-1003311748800
                    media=InputMediaPoll(poll=poll_obj),
                    message='',  # 不要带任何消息文本，让它纯粹发投票
                    reply_to=reply_header  # 传入包装后的对象，不再是int
                ))

                # 从返回结果中提取投票消息ID
                # poll_result是Updates类型,updates[0]可能是UpdateNewMessage或UpdateMessageID
                update = poll_result.updates[0]
                if hasattr(update, 'message'):
                    # UpdateNewMessage类型
                    poll_msg_id = update.message.id
                elif hasattr(update, 'id'):
                    # UpdateMessageID类型
                    poll_msg_id = update.id
                else:
                    logger.error(f"无法从更新中提取消息ID: {update}")
                    return None

                logger.info(f"✅ [底层RPC模式] 投票发送成功: {question_text}, 消息ID: {poll_msg_id}")

                # 发送重新生成按钮
                logger.info("开始发送重新生成按钮消息到讨论组")
                try:
                    # 使用 Telethon 的高层 Button API
                    # 注意：buttons 必须是二维列表 [[...]]
                    button_markup = [[Button.inline(
                        "🔄 重新生成投票",
                        data=f"regen_poll_{summary_message_id}".encode('utf-8')
                    )]]

                    # 发送按钮消息到讨论组，回复投票
                    button_msg = await client.send_message(
                        discussion_group_id,
                        "💡 投票效果不理想?点击下方按钮重新生成",
                        reply_to=poll_msg_id,
                        buttons=button_markup
                    )

                    logger.info(f"✅ 成功发送重新生成按钮到讨论组,消息ID: {button_msg.id}")

                    # 保存映射关系到存储
                    from ..config import add_poll_regeneration
                    add_poll_regeneration(
                        channel=channel,
                        summary_msg_id=summary_message_id,
                        poll_msg_id=poll_msg_id,
                        button_msg_id=button_msg.id,
                        summary_text=summary_text,
                        channel_name=channel_name,
                        send_to_channel=False,
                        discussion_forward_msg_id=forward_message.id
                    )

                    # 返回消息ID
                    return {
                        "poll_msg_id": poll_msg_id,
                        "button_msg_id": button_msg.id
                    }

                except Exception as e:
                    logger.error(f"发送重新生成按钮失败: {e}")
                    # 按钮发送失败仍然返回投票ID
                    return {
                        "poll_msg_id": poll_msg_id,
                        "button_msg_id": None
                    }

            except Exception as e:
                logger.error(f"❌ 终极尝试依然失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return None

        except asyncio.TimeoutError:
            logger.warning(f"等待转发消息超时（10秒），可能转发延迟或未成功")
            # 移除事件处理器
            client.remove_event_handler(on_discussion_message)

            # 尝试发送独立消息
            try:
                logger.info(f"尝试发送独立投票消息")
                await client.send_message(
                    discussion_group_id,
                    f"📊 **投票：{poll_data['question']}**\n\n" +
                    "\n".join([f"• {opt}" for opt in poll_data['options']])
                )
                logger.info("成功发送独立投票消息")
                return None
            except Exception as e:
                logger.error(f"发送独立投票消息失败: {e}")
                return None

    except Exception as e:
        record_error(e, "send_poll_to_discussion_group")
        logger.error(f"发送投票到讨论组失败: {type(e).__name__}: {e}", exc_info=True)
        return None


async def send_poll(client, channel, summary_message_id, summary_text):
    """根据频道配置发送投票到频道或讨论组

    Args:
        client: Telegram客户端实例
        channel: 频道URL或ID
        summary_message_id: 总结消息在频道中的ID
        summary_text: 总结文本，用于生成投票内容

    Returns:
        dict: {"poll_msg_id": 12347, "button_msg_id": 12348} 或 None
    """
    # 获取频道投票配置
    poll_config = get_channel_poll_config(channel)

    # 检查是否启用投票
    enabled = poll_config['enabled']
    if enabled is None:
        # 没有独立配置，使用全局配置
        enabled = ENABLE_POLL

    if not enabled:
        logger.info(f"频道 {channel} 的投票功能已禁用，跳过投票发送")
        return None

    # 根据配置决定发送位置
    if poll_config['send_to_channel']:
        # 频道模式：直接回复总结消息
        logger.info(f"频道 {channel} 配置为频道模式，投票将发送到频道")
        return await send_poll_to_channel(client, channel, summary_message_id, summary_text)
    else:
        # 讨论组模式：发送到讨论组，回复转发消息
        logger.info(f"频道 {channel} 配置为讨论组模式，投票将发送到讨论组")
        return await send_poll_to_discussion_group(client, channel, summary_message_id, summary_text)
