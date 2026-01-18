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
from telethon.events import NewMessage

from ..config import ADMIN_LIST, logger
from ..prompt_manager import load_prompt, save_prompt
from ..poll_prompt_manager import load_poll_prompt, save_poll_prompt

logger = logging.getLogger(__name__)

# 全局变量，用于跟踪正在设置提示词的用户
setting_prompt_users = set()
# 全局变量，用于跟踪正在设置投票提示词的用户
setting_poll_prompt_users = set()


async def handle_show_prompt(event):
    """处理/showprompt命令，显示当前提示词"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    logger.info(f"执行命令 {command} 成功")
    current_prompt = load_prompt()
    await event.reply(f"当前提示词：\n\n{current_prompt}")


async def handle_set_prompt(event):
    """处理/setprompt命令，触发提示词设置流程"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")
    
    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return
    
    # 添加用户到正在设置提示词的集合中
    setting_prompt_users.add(sender_id)
    logger.info(f"添加用户 {sender_id} 到提示词设置集合")
    current_prompt = load_prompt()
    await event.reply("请发送新的提示词，我将使用它来生成总结。\n\n当前提示词：\n" + current_prompt)


async def handle_prompt_input(event):
    """处理用户输入的新提示词"""
    sender_id = event.sender_id
    input_text = event.text
    
    # 检查发送者是否在设置提示词的集合中
    if sender_id not in setting_prompt_users:
        return
    
    logger.info(f"收到用户 {sender_id} 的提示词输入")
    
    # 检查是否是命令消息，如果是则不处理
    if input_text.startswith('/'):
        logger.warning(f"用户 {sender_id} 发送了命令而非提示词内容: {input_text}")
        await event.reply("请发送提示词内容，不要发送命令。如果要取消设置，请重新发送命令。")
        return
    
    # 获取新提示词
    new_prompt = input_text.strip()
    logger.debug(f"用户 {sender_id} 设置的新提示词: {new_prompt[:100]}..." if len(new_prompt) > 100 else f"用户 {sender_id} 设置的新提示词: {new_prompt}")
    
    # 更新提示词
    save_prompt(new_prompt)
    logger.info(f"已更新提示词，长度: {len(new_prompt)}字符")
    
    # 从集合中移除用户
    setting_prompt_users.remove(sender_id)
    logger.info(f"从提示词设置集合中移除用户 {sender_id}")
    
    await event.reply(f"提示词已更新为：\n\n{new_prompt}")


async def handle_show_poll_prompt(event):
    """处理/showpollprompt命令，显示当前投票提示词"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")

    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return

    logger.info(f"执行命令 {command} 成功")
    current_poll_prompt = load_poll_prompt()
    await event.reply(f"当前投票提示词：\n\n{current_poll_prompt}")


async def handle_set_poll_prompt(event):
    """处理/setpollprompt命令，触发投票提示词设置流程"""
    sender_id = event.sender_id
    command = event.text
    logger.info(f"收到命令: {command}，发送者: {sender_id}")

    # 检查发送者是否为管理员
    if sender_id not in ADMIN_LIST and ADMIN_LIST != ['me']:
        logger.warning(f"发送者 {sender_id} 没有权限执行命令 {command}")
        await event.reply("您没有权限执行此命令")
        return

    # 添加用户到正在设置投票提示词的集合中
    setting_poll_prompt_users.add(sender_id)
    logger.info(f"添加用户 {sender_id} 到投票提示词设置集合")
    current_poll_prompt = load_poll_prompt()
    await event.reply("请发送新的投票提示词，我将使用它来生成投票。\n\n当前投票提示词：\n" + current_poll_prompt)


async def handle_poll_prompt_input(event):
    """处理用户输入的新投票提示词"""
    sender_id = event.sender_id
    input_text = event.text

    # 检查发送者是否在设置投票提示词的集合中
    if sender_id not in setting_poll_prompt_users:
        return

    logger.info(f"收到用户 {sender_id} 的投票提示词输入")

    # 检查是否是命令消息，如果是则不处理
    if input_text.startswith('/'):
        logger.warning(f"用户 {sender_id} 发送了命令而非提示词内容: {input_text}")
        await event.reply("请发送提示词内容，不要发送命令。如果要取消设置，请重新发送命令。")
        return

    # 获取新提示词
    new_poll_prompt = input_text.strip()
    logger.debug(f"用户 {sender_id} 设置的新投票提示词: {new_poll_prompt[:100]}..." if len(new_poll_prompt) > 100 else f"用户 {sender_id} 设置的新投票提示词: {new_poll_prompt}")

    # 更新投票提示词
    save_poll_prompt(new_poll_prompt)
    logger.info(f"已更新投票提示词，长度: {len(new_poll_prompt)}字符")

    # 从集合中移除用户
    setting_poll_prompt_users.remove(sender_id)
    logger.info(f"从投票提示词设置集合中移除用户 {sender_id}")

    await event.reply(f"投票提示词已更新为：\n\n{new_poll_prompt}")
