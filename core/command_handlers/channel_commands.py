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
import json
import os
from telethon.events import NewMessage

from ..config import (
    CHANNELS, ADMIN_LIST, RESTART_FLAG_FILE, load_config, save_config, logger,
    get_channel_schedule, set_channel_schedule, set_channel_schedule_v2,
    delete_channel_schedule, validate_schedule, LAST_SUMMARY_FILE,
    SEND_REPORT_TO_SOURCE, ENABLE_POLL, get_channel_poll_config,
    set_channel_poll_config, delete_channel_poll_config
)
from ..prompt_manager import load_prompt
from ..summary_time_manager import load_last_summary_time, save_last_summary_time
from ..ai_client import analyze_with_ai
from ..telegram import fetch_last_week_messages, send_long_message, send_report

logger = logging.getLogger(__name__)


async def handle_show_channels(event):
    """处理/showchannels命令，查看当前频道列表"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    logger.info(f"执行命令 {command} 成功")
    
    if not CHANNELS:
        await event.reply("当前没有配置任何频道")
        return
    
    # 构建频道列表消息
    channels_msg = "当前配置的频道列表：\n\n"
    for i, channel in enumerate(CHANNELS, 1):
        channels_msg += f"{i}. {channel}\n"
    
    await event.reply(channels_msg)


async def handle_add_channel(event):
    """处理/addchannel命令，添加频道"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    try:
        _, channel_url = command.split(maxsplit=1)
        channel_url = channel_url.strip()
        
        if not channel_url:
            await event.reply("请提供有效的频道URL")
            return
        
        # 检查频道是否已存在
        if channel_url in CHANNELS:
            await event.reply(f"频道 {channel_url} 已存在于列表中")
            return
        
        # 添加频道到列表
        CHANNELS.append(channel_url)
        
        # 更新配置文件
        config = load_config()
        config['channels'] = CHANNELS
        save_config(config)
        
        logger.info(f"已添加频道 {channel_url} 到列表")
        await event.reply(f"频道 {channel_url} 已成功添加到列表中\n\n当前频道数量：{len(CHANNELS)}")
        
    except ValueError:
        # 没有提供频道URL
        await event.reply("请提供有效的频道URL，例如：/addchannel https://t.me/examplechannel")
    except Exception as e:
        logger.error(f"添加频道时出错: {type(e).__name__}: {e}", exc_info=True)
        await event.reply(f"添加频道时出错: {e}")


async def handle_delete_channel(event):
    """处理/deletechannel命令，删除频道"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    try:
        _, channel_url = command.split(maxsplit=1)
        channel_url = channel_url.strip()
        
        if not channel_url:
            await event.reply("请提供有效的频道URL")
            return
        
        # 检查频道是否存在
        if channel_url not in CHANNELS:
            await event.reply(f"频道 {channel_url} 不在列表中")
            return
        
        # 从列表中删除频道
        CHANNELS.remove(channel_url)
        
        # 更新配置文件
        config = load_config()
        config['channels'] = CHANNELS
        save_config(config)
        
        logger.info(f"已从列表中删除频道 {channel_url}")
        await event.reply(f"频道 {channel_url} 已成功从列表中删除\n\n当前频道数量：{len(CHANNELS)}")
        
    except ValueError:
        # 没有提供频道URL或频道不存在
        await event.reply("请提供有效的频道URL，例如：/deletechannel https://t.me/examplechannel")
    except Exception as e:
        logger.error(f"删除频道时出错: {type(e).__name__}: {e}", exc_info=True)
        await event.reply(f"删除频道时出错: {e}")


async def handle_show_channel_schedule(event):
    """处理/showchannelschedule命令，查看指定频道的自动总结时间配置"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    try:
        # 解析命令参数
        parts = command.split()
        if len(parts) > 1:
            # 有指定频道参数
            channel_part = parts[1]
            if channel_part.startswith('http'):
                channel = channel_part
            else:
                channel = f"https://t.me/{channel_part}"
            
            # 检查频道是否存在
            if channel not in CHANNELS:
                await event.reply(f"频道 {channel} 不在配置列表中")
                return
        else:
            # 没有指定频道，显示所有频道的配置
            if not CHANNELS:
                await event.reply("当前没有配置任何频道")
                return
            
            # 构建所有频道的配置信息
            schedule_msg = "所有频道的自动总结时间配置：\n\n"
            for i, ch in enumerate(CHANNELS, 1):
                schedule = get_channel_schedule(ch)
                schedule_msg += format_schedule_info(ch, schedule, i)

            await event.reply(schedule_msg)
            return
        
        # 获取指定频道的配置
        schedule = get_channel_schedule(channel)

        schedule_info = format_schedule_info(channel, schedule)
        schedule_info += f"\n使用格式：\n"
        schedule_info += f"每天模式：/setchannelschedule {channel.split('/')[-1]} daily 23 0\n"
        schedule_info += f"每周模式：/setchannelschedule {channel.split('/')[-1]} weekly mon,thu 14 30\n"
        schedule_info += f"旧格式：/setchannelschedule {channel.split('/')[-1]} mon 9 0"

        logger.info(f"执行命令 {command} 成功")
        await event.reply(schedule_info)
        
    except Exception as e:
        logger.error(f"查看频道时间配置时出错: {type(e).__name__}: {e}", exc_info=True)
        await event.reply(f"查看频道时间配置时出错: {e}")


async def handle_set_channel_schedule(event):
    """处理/setchannelschedule命令，设置指定频道的自动总结时间（支持新格式）"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")

    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return

    try:
        # 解析命令参数
        parts = command.split()
        if len(parts) < 4:
            await event.reply(
                "请提供完整的参数。可用格式：\n\n"
                "每天模式：/setchannelschedule <频道> daily <小时> <分钟>\n"
                "  例如：/setchannelschedule channel daily 23 0\n\n"
                "每周模式：/setchannelschedule <频道> weekly <星期> <小时> <分钟>\n"
                "  例如：/setchannelschedule channel weekly mon,thu 23 0\n"
                "  例如：/setchannelschedule channel weekly sun 9 0\n\n"
                "旧格式（向后兼容）：/setchannelschedule <频道> <星期> <小时> <分钟>\n"
                "  例如：/setchannelschedule channel mon 9 0"
            )
            return

        # 解析频道参数
        channel_part = parts[1]
        if channel_part.startswith('http'):
            channel = channel_part
        else:
            channel = f"https://t.me/{channel_part}"

        # 检查频道是否存在
        if channel not in CHANNELS:
            await event.reply(f"频道 {channel} 不在配置列表中，请先使用/addchannel命令添加频道")
            return

        # 判断是新格式还是旧格式
        frequency_or_day = parts[2].lower()

        if frequency_or_day in ['daily', 'weekly']:
            # 新格式
            frequency = frequency_or_day

            if frequency == 'daily':
                # 每天模式：/setchannelschedule channel daily hour minute
                if len(parts) < 5:
                    await event.reply("每天模式需要提供小时和分钟：/setchannelschedule channel daily 23 0")
                    return

                try:
                    hour = int(parts[3])
                    minute = int(parts[4])
                except ValueError:
                    await event.reply("小时和分钟必须是数字")
                    return

                success = set_channel_schedule_v2(channel, frequency='daily', hour=hour, minute=minute)

                if success:
                    success_msg = f"已成功设置频道 {channel.split('/')[-1]} 的自动总结时间：\n\n"
                    success_msg += f"• 频率：每天\n"
                    success_msg += f"• 时间：{hour:02d}:{minute:02d}\n"
                    success_msg += f"\n下次自动总结将在每天 {hour:02d}:{minute:02d} 执行。"
                    await event.reply(success_msg)
                else:
                    await event.reply("设置失败，请检查日志")

            elif frequency == 'weekly':
                # 每周模式：/setchannelschedule channel weekly mon,thu hour minute
                if len(parts) < 6:
                    await event.reply("每周模式需要提供星期、小时和分钟：/setchannelschedule channel weekly mon,thu 23 0")
                    return

                days_str = parts[3]
                try:
                    hour = int(parts[4])
                    minute = int(parts[5])
                except ValueError:
                    await event.reply("小时和分钟必须是数字")
                    return

                # 解析星期几
                days = [d.strip() for d in days_str.split(',')]

                success = set_channel_schedule_v2(channel, frequency='weekly', days=days, hour=hour, minute=minute)

                if success:
                    day_map = {
                        'mon': '周一', 'tue': '周二', 'wed': '周三', 'thu': '周四',
                        'fri': '周五', 'sat': '周六', 'sun': '周日'
                    }
                    days_cn = '、'.join([day_map.get(d, d) for d in days])

                    success_msg = f"已成功设置频道 {channel.split('/')[-1]} 的自动总结时间：\n\n"
                    success_msg += f"• 频率：每周\n"
                    success_msg += f"• 星期：{days_cn}\n"
                    success_msg += f"• 时间：{hour:02d}:{minute:02d}\n"
                    success_msg += f"\n下次自动总结将在每周{days_cn} {hour:02d}:{minute:02d} 执行。"
                    await event.reply(success_msg)
                else:
                    await event.reply("设置失败，请检查日志")
        else:
            # 旧格式（向后兼容）：/setchannelschedule channel day hour minute
            day = frequency_or_day
            try:
                hour = int(parts[3])
                minute = int(parts[4]) if len(parts) > 4 else 0
            except ValueError:
                await event.reply("小时和分钟必须是数字")
                return

            # 验证时间配置
            is_valid, error_msg = validate_schedule(day, hour, minute)
            if not is_valid:
                await event.reply(error_msg)
                return

            # 使用旧函数设置（内部转换为新格式）
            success = set_channel_schedule(channel, day=day, hour=hour, minute=minute)

            if success:
                day_map = {
                    'mon': '周一', 'tue': '周二', 'wed': '周三', 'thu': '周四',
                    'fri': '周五', 'sat': '周六', 'sun': '周日'
                }
                day_cn = day_map.get(day, day)

                success_msg = f"已成功设置频道 {channel.split('/')[-1]} 的自动总结时间：\n\n"
                success_msg += f"• 星期几：{day_cn} ({day})\n"
                success_msg += f"• 时间：{hour:02d}:{minute:02d}\n"
                success_msg += f"\n下次自动总结将在每周{day_cn} {hour:02d}:{minute:02d}执行。"
                await event.reply(success_msg)
            else:
                await event.reply("设置频道时间配置失败，请检查日志")

    except Exception as e:
        logger.error(f"设置频道时间配置时出错: {type(e).__name__}: {e}", exc_info=True)
        await event.reply(f"设置频道时间配置时出错: {e}")


async def handle_delete_channel_schedule(event):
    """处理/deletechannelschedule命令，删除指定频道的自动总结时间配置"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    try:
        # 解析命令参数
        parts = command.split()
        if len(parts) < 2:
            await event.reply("请提供频道参数：/deletechannelschedule 频道\n\n例如：/deletechannelschedule examplechannel")
            return
        
        # 解析频道参数
        channel_part = parts[1]
        if channel_part.startswith('http'):
            channel = channel_part
        else:
            channel = f"https://t.me/{channel_part}"
        
        # 检查频道是否存在
        if channel not in CHANNELS:
            await event.reply(f"频道 {channel} 不在配置列表中")
            return
        
        # 删除频道时间配置
        success = delete_channel_schedule(channel)
        
        if success:
            success_msg = f"已成功删除频道 {channel.split('/')[-1]} 的自动总结时间配置。\n"
            success_msg += f"该频道将使用默认时间配置：每周一 09:00"
            
            logger.info(f"已删除频道 {channel} 的时间配置")
            await event.reply(success_msg)
        else:
            await event.reply("删除频道时间配置失败，请检查日志")
            
    except Exception as e:
        logger.error(f"删除频道时间配置时出错: {type(e).__name__}: {e}", exc_info=True)
        await event.reply(f"删除频道时间配置时出错: {e}")


async def handle_clear_summary_time(event):
    """处理/clearsummarytime命令，清除上次总结时间记录
    支持清除所有频道或特定频道的时间记录
    """
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    try:
        # 解析命令参数
        parts = command.split()
        specific_channel = None
        if len(parts) > 1:
            # 有指定频道参数
            channel_part = parts[1]
            if channel_part.startswith('http'):
                specific_channel = channel_part
            else:
                specific_channel = f"https://t.me/{channel_part}"
        
        if os.path.exists(LAST_SUMMARY_FILE):
            if specific_channel:
                # 清除特定频道的时间记录
                with open(LAST_SUMMARY_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        existing_data = json.loads(content)
                        if specific_channel in existing_data:
                            del existing_data[specific_channel]
                            # 写回文件
                            with open(LAST_SUMMARY_FILE, "w", encoding="utf-8") as f_write:
                                json.dump(existing_data, f_write, ensure_ascii=False, indent=2)
                            logger.info(f"已清除频道 {specific_channel} 的上次总结时间记录")
                            await event.reply(f"已成功清除频道 {specific_channel} 的上次总结时间记录。")
                        else:
                            logger.info(f"频道 {specific_channel} 的上次总结时间记录不存在，无需清除")
                            await event.reply(f"频道 {specific_channel} 的上次总结时间记录不存在，无需清除。")
                    else:
                        logger.info(f"上次总结时间记录文件 {LAST_SUMMARY_FILE} 内容为空，无需清除")
                        await event.reply("上次总结时间记录文件内容为空，无需清除。")
            else:
                # 清除所有频道的时间记录
                os.remove(LAST_SUMMARY_FILE)
                logger.info(f"已清除所有频道的上次总结时间记录，文件 {LAST_SUMMARY_FILE} 已删除")
                await event.reply("已成功清除所有频道的上次总结时间记录。下次总结将重新抓取过去一周的消息。")
        else:
            logger.info(f"上次总结时间记录文件 {LAST_SUMMARY_FILE} 不存在，无需清除")
            await event.reply("上次总结时间记录文件不存在，无需清除。")
    except Exception as e:
        logger.error(f"清除上次总结时间记录时出错: {type(e).__name__}: {e}", exc_info=True)
        await event.reply(f"清除上次总结时间记录时出错: {e}")


async def handle_set_send_to_source(event):
    """处理/setsendtosource命令，设置是否将报告发送回源频道"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    # 解析命令参数
    parts = command.strip().split()
    
    # 处理没有参数的情况：显示当前设置
    if len(parts) == 1:
        current_status = "开启" if SEND_REPORT_TO_SOURCE else "关闭"
        await event.reply(
            f"当前报告发送回源频道的设置：`{SEND_REPORT_TO_SOURCE}`\n"
            f"当前状态：`{current_status}`\n\n"
            f"使用格式：`/setsendtosource true|false`"
        )
        return
    
    # 处理带参数的情况
    try:
        value_str = parts[1].lower()
        
        # 检查值是否有效
        if value_str not in ['true', 'false', '1', '0', 'yes', 'no', 'on', 'off']:
            await event.reply(f"无效的值: `{value_str}`\n\n可用值：true, false, 1, 0, yes, no, on, off")
            return
        
        # 转换为布尔值
        new_value = value_str in ['true', '1', 'yes', 'on']
        
        # 更新配置文件
        config = load_config()
        config['send_report_to_source'] = new_value
        save_config(config)
        
        # save_config 会自动调用 update_module_variables 更新全局变量 SEND_REPORT_TO_SOURCE
        logger.info(f"已将 send_report_to_source 设置为: {new_value}")
        
        current_status = "开启" if new_value else "关闭"
        await event.reply(f"✅ 设置成功！发送回源频道已{current_status}。")
        
    except Exception as e:
        logger.error(f"设置报告发送回源频道选项时出错: {type(e).__name__}: {e}", exc_info=True)
        await event.reply(f"❌ 设置失败，发生错误: `{str(e)}`")


async def handle_channel_poll(event):
    """处理/channelpoll命令，查看频道投票配置"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")

    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return

    try:
        # 解析命令参数
        parts = command.split()
        if len(parts) > 1:
            # 有指定频道参数
            channel_part = parts[1]
            if channel_part.startswith('http'):
                channel = channel_part
            else:
                channel = f"https://t.me/{channel_part}"

            # 检查频道是否存在
            if channel not in CHANNELS:
                await event.reply(f"频道 {channel} 不在配置列表中")
                return
        else:
            # 没有指定频道，显示所有频道的配置
            if not CHANNELS:
                await event.reply("当前没有配置任何频道")
                return

            # 构建所有频道的配置信息
            poll_msg = "所有频道的投票配置：\n\n"
            for i, ch in enumerate(CHANNELS, 1):
                poll_msg += format_poll_info(ch, i)

            # 添加全局配置说明
            poll_msg += f"\n🌐 全局配置：\n"
            poll_msg += f"• 投票功能：{'开启' if ENABLE_POLL else '关闭'}\n"
            poll_msg += f"\n💡 提示：频道独立配置会覆盖全局配置"

            await event.reply(poll_msg)
            return

        # 获取指定频道的配置
        poll_config = get_channel_poll_config(channel)

        channel_name = channel.split('/')[-1]
        poll_info = f"频道 `{channel_name}` 的投票配置：\n\n"

        # 显示启用状态
        enabled = poll_config['enabled']
        if enabled is None:
            poll_info += f"📊 投票启用：使用全局配置（{'开启' if ENABLE_POLL else '关闭'}）\n"
        else:
            poll_info += f"📊 投票启用：{'开启' if enabled else '关闭'}\n"

        # 显示发送位置
        send_to_channel = poll_config['send_to_channel']
        location = "频道" if send_to_channel else "讨论组"
        poll_info += f"📍 发送位置：{location}\n"

        poll_info += f"\n使用格式：\n"
        poll_info += f"/setchannelpoll {channel_name} <on/off> <channel/discussion>\n"
        poll_info += f"  例如：/setchannelpoll {channel_name} on channel\n"
        poll_info += f"  例如：/setchannelpoll {channel_name} off\n"
        poll_info += f"\n/deletechannelpoll {channel_name} - 删除独立配置"

        logger.info(f"执行命令 {command} 成功")
        await event.reply(poll_info)

    except Exception as e:
        logger.error(f"查看频道投票配置时出错: {type(e).__name__}: {e}", exc_info=True)
        await event.reply(f"查看频道投票配置时出错: {e}")


async def handle_set_channel_poll(event):
    """处理/setchannelpoll命令，设置频道投票配置"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")

    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return

    try:
        # 解析命令参数
        parts = command.split()
        if len(parts) < 3:
            await event.reply(
                "请提供完整的参数。\n\n"
                "使用格式：\n"
                "/setchannelpoll <频道> <on/off> [channel/discussion]\n\n"
                "参数说明：\n"
                "• on/off - 启用或禁用投票\n"
                "• channel - 发送到频道（可选，默认讨论组）\n"
                "• discussion - 发送到讨论组（可选）\n\n"
                "示例：\n"
                "/setchannelpoll examplechannel on channel\n"
                "/setchannelpoll examplechannel off"
            )
            return

        # 解析频道参数
        channel_part = parts[1]
        if channel_part.startswith('http'):
            channel = channel_part
        else:
            channel = f"https://t.me/{channel_part}"

        # 检查频道是否存在
        if channel not in CHANNELS:
            await event.reply(f"频道 {channel} 不在配置列表中，请先使用/addchannel命令添加频道")
            return

        # 解析启用参数
        enabled_str = parts[2].lower()
        if enabled_str in ['on', 'true', '1', 'yes', 'enable']:
            enabled = True
        elif enabled_str in ['off', 'false', '0', 'no', 'disable']:
            enabled = False
        else:
            await event.reply(f"无效的启用参数: {enabled_str}，请使用 on/off")
            return

        # 解析发送位置参数（可选）
        send_to_channel = None
        if len(parts) >= 4:
            location_str = parts[3].lower()
            if location_str in ['channel', '频道']:
                send_to_channel = True
            elif location_str in ['discussion', '讨论组']:
                send_to_channel = False
            else:
                await event.reply(f"无效的发送位置参数: {location_str}，请使用 channel/discussion")
                return

        # 设置配置
        success = set_channel_poll_config(channel, enabled=enabled, send_to_channel=send_to_channel)

        if success:
            channel_name = channel.split('/')[-1]
            success_msg = f"✅ 已成功设置频道 `{channel_name}` 的投票配置：\n\n"
            success_msg += f"• 投票启用：{'开启' if enabled else '关闭'}\n"

            if send_to_channel is not None:
                location = "频道" if send_to_channel else "讨论组"
                success_msg += f"• 发送位置：{location}\n"
            else:
                success_msg += f"• 发送位置：保持不变\n"

            if enabled is None:
                success_msg += f"\n该频道将使用全局投票配置（{'开启' if ENABLE_POLL else '关闭'}）"
            else:
                success_msg += f"\n该频道将使用独立配置"

            await event.reply(success_msg)
        else:
            await event.reply("设置失败，请检查日志")

    except Exception as e:
        logger.error(f"设置频道投票配置时出错: {type(e).__name__}: {e}", exc_info=True)
        await event.reply(f"设置频道投票配置时出错: {e}")


async def handle_delete_channel_poll(event):
    """处理/deletechannelpoll命令，删除频道投票配置"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")

    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return

    try:
        # 解析命令参数
        parts = command.split()
        if len(parts) < 2:
            await event.reply("请提供频道参数：/deletechannelpoll <频道>\n\n例如：/deletechannelpoll examplechannel")
            return

        # 解析频道参数
        channel_part = parts[1]
        if channel_part.startswith('http'):
            channel = channel_part
        else:
            channel = f"https://t.me/{channel_part}"

        # 检查频道是否存在
        if channel not in CHANNELS:
            await event.reply(f"频道 {channel} 不在配置列表中")
            return

        # 删除频道投票配置
        success = delete_channel_poll_config(channel)

        if success:
            channel_name = channel.split('/')[-1]
            success_msg = f"✅ 已成功删除频道 `{channel_name}` 的独立投票配置。\n\n"
            success_msg += f"该频道将使用全局投票配置：\n"
            success_msg += f"• 投票功能：{'开启' if ENABLE_POLL else '关闭'}\n"
            success_msg += f"• 默认发送位置：讨论组"

            logger.info(f"已删除频道 {channel} 的投票配置")
            await event.reply(success_msg)
        else:
            await event.reply("删除频道投票配置失败，请检查日志")

    except Exception as e:
        logger.error(f"删除频道投票配置时出错: {type(e).__name__}: {e}", exc_info=True)
        await event.reply(f"删除频道投票配置时出错: {e}")


def format_schedule_info(channel, schedule, index=None):
    """格式化调度配置信息

    Args:
        channel: 频道URL
        schedule: 标准化的调度配置字典
        index: 可选的索引编号

    Returns:
        str: 格式化的配置信息字符串
    """
    day_map = {
        'mon': '周一', 'tue': '周二', 'wed': '周三', 'thu': '周四',
        'fri': '周五', 'sat': '周六', 'sun': '周日'
    }

    channel_name = channel.split('/')[-1]
    frequency = schedule.get('frequency', 'weekly')
    hour = schedule['hour']
    minute = schedule['minute']

    if index is not None:
        prefix = f"{index}. "
    else:
        prefix = ""

    if frequency == 'daily':
        return f"{prefix}{channel_name}: 每天 {hour:02d}:{minute:02d}\n"
    elif frequency == 'weekly':
        days_cn = '、'.join([day_map.get(d, d) for d in schedule.get('days', [])])
        return f"{prefix}{channel_name}: 每周{days_cn} {hour:02d}:{minute:02d}\n"
    else:
        return f"{prefix}{channel_name}: 未知频率 {frequency} {hour:02d}:{minute:02d}\n"


def format_poll_info(channel, index):
    """格式化投票配置信息

    Args:
        channel: 频道URL
        index: 索引编号

    Returns:
        str: 格式化的配置信息字符串
    """
    channel_name = channel.split('/')[-1]
    poll_config = get_channel_poll_config(channel)

    prefix = f"{index}. "

    # 显示启用状态
    enabled = poll_config['enabled']
    if enabled is None:
        enabled_text = "全局"
    elif enabled:
        enabled_text = "✅ 开启"
    else:
        enabled_text = "❌ 关闭"

    # 显示发送位置
    send_to_channel = poll_config['send_to_channel']
    location_text = "频道" if send_to_channel else "讨论组"

    return f"{prefix}{channel_name}: {enabled_text} → {location_text}\n"
