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
import os
import subprocess
import sys
import glob
from telethon.events import NewMessage

from ..config import ADMIN_LIST, RESTART_FLAG_FILE, logger, load_config, save_config
from ..database import get_db_manager

logger = logging.getLogger(__name__)


async def handle_show_log_level(event):
    """处理/showloglevel命令，显示当前日志级别"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    from logger_config import get_current_log_level
    current_level = get_current_log_level()
    logger.info(f"执行命令 {command} 成功")
    await event.reply(f"当前日志级别: {current_level}")


async def handle_set_log_level(event):
    """处理/setloglevel命令，设置日志级别"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    try:
        _, new_level = command.split(maxsplit=1)
        new_level = new_level.upper()
        logger.info(f"尝试设置日志级别为: {new_level}")
        
        # 更新配置文件
        config = load_config()
        config['log_level'] = new_level
        save_config(config)
        
        logger.info(f"已将日志级别设置为: {new_level}")
        await event.reply(f"日志级别已设置为 {new_level}，将在重启后生效。")
        
    except ValueError:
        await event.reply("请提供有效的日志级别。可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL")
    except Exception as e:
        logger.error(f"设置日志级别时出错: {type(e).__name__}: {e}", exc_info=True)
        await event.reply(f"设置日志级别时出错: {e}")


class RestartException(Exception):
    """重启异常，用于触发进程内重启"""
    pass

async def handle_restart(event):
    """处理/restart命令，重启机器人（完全重启整个程序进程）"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    await event.reply("正在重启机器人...")
    logger.info("正在重启机器人（完全重启进程）...")
    
    # 创建重启标志文件（写入用户ID，用于重启后通知）
    with open(RESTART_FLAG_FILE, 'w') as f:
        f.write(str(sender_id))
    
    logger.info("重启标志文件已创建")
    
    # 在后台任务中执行重启操作，避免阻塞事件处理器
    async def restart_process():
        """异步执行进程重启"""
        import asyncio
        import sys
        
        # 等待消息发送完成
        await asyncio.sleep(1)
        
        # 获取客户端和调度器引用
        from core.telegram import get_active_client
        from core.config import get_scheduler_instance
        client = get_active_client()
        scheduler = get_scheduler_instance()
        
        # 停止调度器
        try:
            if scheduler and scheduler.running:
                logger.info("正在停止调度器...")
                scheduler.shutdown(wait=False)
                logger.info("调度器已停止")
        except Exception as e:
            logger.warning(f"停止调度器时出错: {e}")
        
        # 关闭客户端连接
        try:
            if client and client.is_connected():
                logger.info("正在关闭客户端连接...")
                await client.disconnect()
                logger.info("客户端连接已关闭")
        except Exception as e:
            logger.warning(f"关闭客户端连接时出错: {e}")
        
        # 等待一段时间确保资源释放
        await asyncio.sleep(1)
        
        # 使用 subprocess.Popen 在 Windows 上可靠地重启程序
        logger.info("正在完全重启程序进程...")
        try:
            # 刷新输出流，防止缓冲区中的日志在重启时丢失
            sys.stdout.flush()
            sys.stderr.flush()
            
            # 获取当前 Python 解释器的绝对路径和脚本参数
            python = os.path.abspath(sys.executable)
            args = [python] + sys.argv
            
            # 启动新进程（在 Windows 上更可靠）
            logger.info(f"启动新进程: {python} {' '.join(sys.argv)}")
            subprocess.Popen(args)
            
            # 彻底退出当前进程
            logger.info("新进程已启动，正在退出当前进程...")
            os._exit(0)
        except Exception as e:
            logger.critical(f"重启进程失败: {type(e).__name__}: {e}", exc_info=True)
    
    # 创建后台任务
    import asyncio
    asyncio.create_task(restart_process())
    
    logger.info("重启任务已启动，程序将完全重启...")


async def handle_changelog(event):
    """处理/changelog命令，显示更新日志"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    logger.info(f"执行命令 {command} 成功")
    changelog_path = 'CHANGELOG.md'
    
    if os.path.exists(changelog_path):
        with open(changelog_path, 'r', encoding='utf-8') as f:
            changelog_content = f.read()
        await event.reply(f"**更新日志**\n\n{changelog_content}")
    else:
        await event.reply("未找到更新日志文件")


async def handle_shutdown(event):
    """处理/shutdown命令，关闭机器人（彻底退出）"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    await event.reply("正在关闭机器人...")
    logger.info("正在关闭机器人...")
    
    # 删除重启标志文件（如果存在），确保不会重启
    import os
    try:
        if os.path.exists(RESTART_FLAG_FILE):
            os.remove(RESTART_FLAG_FILE)
            logger.info("已删除重启标志文件，准备关机")
    except Exception as e:
        logger.warning(f"删除重启标志文件时出错: {e}")
    
    # 优雅地关闭客户端连接
    try:
        from core.telegram import get_active_client
        client = get_active_client()
        if client and client.is_connected():
            logger.info("正在关闭客户端连接...")
            await client.disconnect()
            logger.info("客户端连接已关闭")
    except Exception as e:
        logger.warning(f"关闭客户端连接时出错: {e}")
    
    # 停止调度器
    try:
        from core.config import get_scheduler_instance
        scheduler = get_scheduler_instance()
        if scheduler and scheduler.running:
            logger.info("正在停止调度器...")
            scheduler.shutdown(wait=False)
            logger.info("调度器已停止")
    except Exception as e:
        logger.warning(f"停止调度器时出错: {e}")
    
    logger.info("关机请求已提交，程序将退出...")


async def handle_pause(event):
    """处理/pause命令，暂停自动总结"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    from ..scheduler import pause_scheduler
    pause_scheduler()
    
    logger.info(f"执行命令 {command} 成功")
    await event.reply("已暂停自动总结。使用/resume命令恢复。")


async def handle_resume(event):
    """处理/resume命令，恢复自动总结"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    from ..scheduler import resume_scheduler
    resume_scheduler()
    
    logger.info(f"执行命令 {command} 成功")
    await event.reply("已恢复自动总结。")


async def handle_clear_cache(event):
    """处理/clearcache命令，清除缓存"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    cache_cleared = False
    cache_paths = [
        'data/last_summary_time.json',
        'data/channel_schedules.json'
    ]
    
    for path in cache_paths:
        if os.path.exists(path):
            os.remove(path)
            cache_cleared = True
            logger.info(f"已删除缓存文件: {path}")
    
    if cache_cleared:
        logger.info(f"执行命令 {command} 成功")
        await event.reply("已清除缓存")
    else:
        await event.reply("没有需要清除的缓存文件")


async def handle_clean_logs(event):
    """处理/cleanlogs命令，清理日志文件"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    # 解析保留天数参数
    parts = command.split()
    if len(parts) > 1:
        try:
            days = int(parts[1])
        except ValueError:
            await event.reply("请输入有效的天数（数字）")
            return
    else:
        days = 30  # 默认保留30天
    
    # 使用 logger_config 中的清理函数
    from ..logger_config import clean_old_logs, get_clean_logs_summary, get_log_statistics
    from datetime import datetime, timedelta
    
    # 先获取日志统计信息
    stats = get_log_statistics()
    logger.info(f"当前日志统计: 总文件 {stats['total_files']} 个，总大小 {stats['total_size_mb']:.2f} MB")
    logger.info(f"会话目录数量: {len(stats['session_dirs'])} 个")
    
    # 输出每个会话目录的信息
    for session_dir in stats['session_dirs']:
        age = (datetime.now() - session_dir['modified']).days
        logger.info(f"会话目录: {session_dir['name']}, 修改时间: {session_dir['modified']}, 年龄: {age} 天, 大小: {session_dir['size_mb']:.2f} MB")
    
    # 先预览会清理什么
    preview_result = clean_old_logs(days, dry_run=True)
    logger.info(f"预览结果: 将删除 {len(preview_result['deleted_dirs'])} 个会话目录，释放 {preview_result['total_freed_mb']:.2f} MB")
    
    if not preview_result['deleted_dirs']:
        logger.info(f"没有需要清理的日志文件（已保留最近 {days} 天）")
        await event.reply(f"没有需要清理的日志文件（已保留最近 {days} 天）")
        return
    
    # 执行清理
    result = clean_old_logs(days, dry_run=False)
    
    logger.info(f"执行命令 {command} 成功，清理了 {len(result['deleted_dirs'])} 个会话目录，释放 {result['total_freed_mb']:.2f} MB")
    
    # 构建回复消息
    reply_msg = f"✅ **日志清理完成**\n\n"
    reply_msg += f"• 已删除会话: {len(result['deleted_dirs'])} 个\n"
    reply_msg += f"• 已删除文件: {len(result['deleted_files'])} 个\n"
    reply_msg += f"• 释放空间: {result['total_freed_mb']:.2f} MB\n"
    reply_msg += f"• 保留天数: {days} 天"
    
    if result['errors']:
        reply_msg += f"\n\n⚠️ **清理错误**: {len(result['errors'])} 个"
        for error in result['errors']:
            reply_msg += f"\n  • {error['path']}: {error['error']}"
    
    await event.reply(reply_msg)


async def handle_help(event):
    """处理/help命令，显示帮助信息"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    help_text = """
**帮助信息**

**频道管理命令：**
/showchannels - 查看当前频道列表
/addchannel <频道URL> - 添加频道
/deletechannel <频道URL> - 删除频道
/showchannelschedule [频道] - 查看频道的自动总结时间配置
/setchannelschedule <频道> daily|weekly <星期> <小时> <分钟> - 设置频道的自动总结时间（支持新格式）
/deletechannelschedule <频道> - 删除频道的自动总结时间配置
/clearsummarytime [频道] - 清除上次总结时间记录

**总结命令：**
/立即总结 - 立即生成总结（支持指定频道）
  例如：/立即总结 channel1 channel2

**提示词管理命令：**
/showprompt - 显示当前提示词
/setprompt - 设置新的提示词
/showpollprompt - 显示当前投票提示词
/setpollprompt - 设置新的投票提示词

**系统管理命令：**
/showloglevel - 显示当前日志级别
/setloglevel <级别> - 设置日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
/restart - 重启机器人
/changelog - 查看更新日志
/shutdown - 关闭机器人
/pause - 暂停自动总结
/resume - 恢复自动总结
/clearcache - 清除缓存
/cleanlogs [天数] - 清理日志文件（默认保留30天）

**黑名单管理命令：**
/blacklist add <用户ID> [原因] - 添加用户到黑名单
/blacklist remove <用户ID> - 从黑名单移除用户
/blacklist list [数量] - 查看黑名单列表
/blacklist check <用户ID> - 检查用户是否在黑名单中
/blacklist clear - 清空黑名单
/blacklist stats - 查看黑名单统计信息

**配置命令：**
/setsendtosource [true|false] - 设置是否将报告发送回源频道

使用示例：
/setchannelschedule channel daily 23 0 - 设置每天23:00总结
/setchannelschedule channel weekly mon,fri 14 30 - 设置每周一和周五14:30总结
/clearsummarytime channel - 清除特定频道的总结时间
/cleanlogs 7 - 清理7天前的日志
"""
    logger.info(f"执行命令 {command} 成功")
    await event.reply(help_text)


async def handle_start(event):
    """处理/start命令，显示欢迎信息"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    welcome_text = """
👋 欢迎使用 Sakura 频道总结助手！

这是一个用于自动抓取 Telegram 频道消息并生成总结的机器人。

**主要功能：**
• 自动定时抓取频道消息并生成总结
• 支持手动触发总结
• 支持多频道管理
• 支持自定义总结时间
• 支持自定义总结提示词
• 支持投票功能

**快速开始：**
使用 /help 查看所有可用命令
使用 /addchannel 添加需要监控的频道
使用 /showchannels 查看已添加的频道

如有问题，请联系管理员。
"""
    logger.info(f"执行命令 {command} 成功")
    await event.reply(welcome_text)


async def handle_blacklist(event):
    """处理/blacklist命令，黑名单管理"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    parts = command.split()
    
    if len(parts) < 2:
        await event.reply("""
**黑名单管理命令**

/blacklist add <用户ID> [原因] - 添加用户到黑名单
/blacklist remove <用户ID> - 从黑名单移除用户
/blacklist list [数量] - 查看黑名单列表
/blacklist check <用户ID> - 检查用户是否在黑名单中
/blacklist clear - 清空黑名单
/blacklist stats - 查看黑名单统计信息
        """)
        return
    
    action = parts[1].lower()
    db = get_db_manager()
    
    if action == 'add':
        if len(parts) < 3:
            await event.reply("请提供用户ID。使用格式：/blacklist add <用户ID> [原因]")
            return
        
        try:
            user_id = int(parts[2])
            reason = ' '.join(parts[3:]) if len(parts) > 3 else None
            
            if db.add_to_blacklist(user_id, reason=reason, added_by=str(sender_id)):
                await event.reply(f"已将用户 {user_id} 添加到黑名单")
            else:
                await event.reply("添加到黑名单失败")
        except ValueError:
            await event.reply("用户ID必须是数字")
    
    elif action == 'remove':
        if len(parts) < 3:
            await event.reply("请提供用户ID。使用格式：/blacklist remove <用户ID>")
            return
        
        try:
            user_id = int(parts[2])
            
            if db.remove_from_blacklist(user_id):
                await event.reply(f"已将用户 {user_id} 从黑名单移除")
            else:
                await event.reply(f"用户 {user_id} 不在黑名单中")
        except ValueError:
            await event.reply("用户ID必须是数字")
    
    elif action == 'list':
        limit = int(parts[2]) if len(parts) > 2 else 50
        blacklist = db.get_blacklist(limit=limit)
        
        if not blacklist:
            await event.reply("黑名单为空")
            return
        
        msg = "黑名单列表：\n\n"
        for i, user in enumerate(blacklist, 1):
            msg += f"{i}. ID: {user['user_id']}, 用户名: {user['username'] or '未知'}\n"
            msg += f"   原因: {user['reason'] or '未指定'}\n"
            msg += f"   添加时间: {user['added_at']}\n"
            msg += f"   违规次数: {user['violation_count']}\n\n"
        
        await event.reply(msg)
    
    elif action == 'check':
        if len(parts) < 3:
            await event.reply("请提供用户ID。使用格式：/blacklist check <用户ID>")
            return
        
        try:
            user_id = int(parts[2])
            
            if db.is_user_blacklisted(user_id):
                await event.reply(f"用户 {user_id} 在黑名单中")
            else:
                await event.reply(f"用户 {user_id} 不在黑名单中")
        except ValueError:
            await event.reply("用户ID必须是数字")
    
    elif action == 'clear':
        count = db.clear_blacklist()
        await event.reply(f"已清空黑名单，共 {count} 条记录")
    
    elif action == 'stats':
        stats = db.get_blacklist_stats()
        msg = f"""
**黑名单统计信息**

活跃黑名单数量: {stats['active_count']}
总黑名单数量: {stats['total_count']}
本周新增: {stats['week_new']}
        """
        await event.reply(msg)
    
    else:
        await event.reply("未知操作。使用 /blacklist 查看帮助")
