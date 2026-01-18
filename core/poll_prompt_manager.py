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
from .config import POLL_PROMPT_FILE, DEFAULT_POLL_PROMPT

logger = logging.getLogger(__name__)

def load_poll_prompt():
    """从文件中读取投票提示词，如果文件不存在则使用默认提示词

    Returns:
        str: 投票提示词
    """
    logger.info(f"开始读取投票提示词文件: {POLL_PROMPT_FILE}")
    try:
        with open(POLL_PROMPT_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            logger.info(f"成功读取投票提示词文件，长度: {len(content)}字符")
            return content
    except FileNotFoundError:
        logger.warning(f"投票提示词文件 {POLL_PROMPT_FILE} 不存在，将使用默认提示词并创建文件")
        # 如果文件不存在，使用默认提示词并创建文件
        save_poll_prompt(DEFAULT_POLL_PROMPT)
        return DEFAULT_POLL_PROMPT
    except Exception as e:
        logger.error(f"读取投票提示词文件 {POLL_PROMPT_FILE} 时出错: {type(e).__name__}: {e}", exc_info=True)
        # 如果读取失败，使用默认提示词
        return DEFAULT_POLL_PROMPT

def save_poll_prompt(prompt):
    """将投票提示词保存到文件中

    Args:
        prompt: 要保存的投票提示词
    """
    logger.info(f"开始保存投票提示词到文件: {POLL_PROMPT_FILE}")
    try:
        with open(POLL_PROMPT_FILE, "w", encoding="utf-8") as f:
            f.write(prompt)
        logger.info(f"成功保存投票提示词到文件，长度: {len(prompt)}字符")
    except Exception as e:
        logger.error(f"保存投票提示词到文件 {POLL_PROMPT_FILE} 时出错: {type(e).__name__}: {e}", exc_info=True)
