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
from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from error_handler import retry_with_backoff, record_error
from poll_prompt_manager import load_poll_prompt

logger = logging.getLogger(__name__)

# 初始化 AI 客户端
logger.info("开始初始化AI客户端...")
logger.debug(f"AI客户端配置: Base URL={LLM_BASE_URL}, Model={LLM_MODEL}, API Key={'***' if LLM_API_KEY else '未设置'}")

client_llm = OpenAI(
    api_key=LLM_API_KEY, 
    base_url=LLM_BASE_URL
)

logger.info("AI客户端初始化完成")

@retry_with_backoff(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_backoff=True,
    retry_on_exceptions=(ConnectionError, TimeoutError, Exception)
)
def analyze_with_ai(messages, current_prompt):
    """调用 AI 进行汇总
    
    Args:
        messages: 要分析的消息列表
        current_prompt: 当前使用的提示词
    """
    logger.info("开始调用AI进行消息汇总")
    
    if not messages:
        logger.info("没有需要分析的消息，返回空结果")
        return "本周无新动态。"

    # 构建AI请求
    prompt = _build_ai_prompt(messages, current_prompt)
    
    # 执行AI分析
    return _execute_ai_analysis(prompt)


def _build_ai_prompt(messages, current_prompt):
    """
    构建AI请求的提示词

    Args:
        messages: 要分析的消息列表
        current_prompt: 当前使用的提示词

    Returns:
        str: 完整的提示词
    """
    context_text = "\n\n---\n\n".join(messages)
    prompt = f"{current_prompt}{context_text}"
    
    logger.debug(f"AI请求配置: 模型={LLM_MODEL}, 提示词长度={len(current_prompt)}字符, 上下文长度={len(context_text)}字符")
    logger.debug(f"AI请求总长度: {len(prompt)}字符")
    
    return prompt


def _execute_ai_analysis(prompt):
    """
    执行AI分析请求

    Args:
        prompt: 完整的提示词

    Returns:
        str: AI分析结果
    """
    try:
        from datetime import datetime
        start_time = datetime.now()
        response = client_llm.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的资讯摘要助手，擅长提取重点并保持客观。"},
                {"role": "user", "content": prompt},
            ]
        )
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        logger.info(f"AI分析完成，处理时间: {processing_time:.2f}秒")
        logger.debug(f"AI响应状态: 成功，选择索引={response.choices[0].index}, 完成原因={response.choices[0].finish_reason}")
        logger.debug(f"AI响应长度: {len(response.choices[0].message.content)}字符")
        
        return response.choices[0].message.content
    except Exception as e:
        record_error(e, "analyze_with_ai")
        logger.error(f"AI分析失败: {type(e).__name__}: {e}", exc_info=True)
        return f"AI 分析失败: {e}"


def _truncate_unicode(text, max_length):
    """
    安全截断文本，避免截断多字节字符
    
    Args:
        text: 要截断的文本
        max_length: 最大长度
    
    Returns:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    # 回退直到找到完整的多字节字符边界
    while truncated and (truncated[-1].encode('utf-8') & 0xC0) == 0x80:
        truncated = truncated[:-1]
    return truncated + '...'


def _validate_and_fix_poll_data(poll_data):
    """
    验证并修复投票数据
    
    Args:
        poll_data: 原始投票数据
    
    Returns:
        dict: 修复后的投票数据
    """
    # 验证投票问题长度（Telegram限制255字符）
    question = poll_data['question'].strip()
    if len(question) > 255:
        logger.warning(f"投票问题超长: {len(question)}字符，将截断")
        poll_data['question'] = _truncate_unicode(question, 255)
        logger.info(f"投票问题已截断为: {poll_data['question']}")
    
    # 验证选项长度（Telegram限制100字符）
    valid_options = []
    for i, option in enumerate(poll_data['options']):
        option_text = str(option).strip()
        if len(option_text) > 100:
            logger.warning(f"投票选项{i+1}超长: {len(option_text)}字符，将截断")
            valid_options.append(_truncate_unicode(option_text, 100))
        else:
            valid_options.append(option_text)
    
    poll_data['options'] = valid_options
    return poll_data


def _extract_poll_json(response_text):
    """
    从AI响应中提取投票JSON数据
    
    Args:
        response_text: AI响应文本
    
    Returns:
        dict: 解析后的投票数据，如果失败返回None
    """
    import json
    import re
    
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            logger.warning("未在响应中找到JSON格式")
            return None
        
        json_str = json_match.group()
        poll_data = json.loads(json_str)
        
        if 'question' not in poll_data or 'options' not in poll_data:
            logger.warning(f"投票数据结构不完整: {poll_data}")
            return None
        
        if not isinstance(poll_data['options'], list) or len(poll_data['options']) < 2:
            logger.warning(f"投票选项格式不正确: {poll_data['options']}")
            return None
        
        return poll_data
    except json.JSONDecodeError as e:
        logger.error(f"解析AI返回的JSON失败: {e}")
        return None


def _get_default_poll():
    """
    获取默认投票选项
    
    Returns:
        dict: 默认投票数据
    """
    return {
        "question": "你对本周总结有什么看法？",
        "options": ["非常满意", "比较满意", "一般", "有待改进"]
    }


@retry_with_backoff(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_backoff=True,
    retry_on_exceptions=(ConnectionError, TimeoutError, Exception)
)
def generate_poll_from_summary(summary_text):
    """根据总结内容生成投票
    
    Args:
        summary_text: 总结文本
    
    Returns:
        dict: 包含question和options的字典，格式为:
            {"question": "投票问题", "options": ["选项1", "选项2", "选项3", "选项4"]}
    """
    logger.info("开始调用AI生成投票")
    
    # 验证输入
    if not _validate_summary_text(summary_text):
        return _get_default_poll()
    
    # 构建提示词
    prompt = _build_poll_prompt(summary_text)
    
    # 执行投票生成
    return _execute_poll_generation(prompt)


def _validate_summary_text(summary_text):
    """
    验证总结文本是否适合生成投票

    Args:
        summary_text: 总结文本

    Returns:
        bool: 是否有效
    """
    if not summary_text or len(summary_text.strip()) < 10:
        logger.warning("总结文本太短，无法生成有意义的投票")
        return False
    return True


def _build_poll_prompt(summary_text):
    """
    构建投票生成的提示词

    Args:
        summary_text: 总结文本

    Returns:
        str: 完整的提示词
    """
    poll_prompt_template = load_poll_prompt()
    prompt = poll_prompt_template.format(summary_text=summary_text)
    logger.debug(f"投票生成请求配置: 模型={LLM_MODEL}, 提示词长度={len(prompt)}字符")
    return prompt


def _execute_poll_generation(prompt):
    """
    执行投票生成请求

    Args:
        prompt: 完整的提示词

    Returns:
        dict: 投票数据
    """
    try:
        # 执行AI请求
        response = _make_ai_poll_request(prompt)
        
        # 处理响应
        return _process_poll_response(response)
        
    except Exception as e:
        record_error(e, "generate_poll_from_summary")
        logger.error(f"AI投票生成失败: {type(e).__name__}: {e}", exc_info=True)
        return _get_default_poll()


def _make_ai_poll_request(prompt):
    """
    执行AI投票请求

    Args:
        prompt: 提示词

    Returns:
        AI响应对象
    """
    from datetime import datetime
    
    start_time = datetime.now()
    response = client_llm.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "你是一个幽默风趣的互动策划专家，擅长从枯燥的文字中挖掘槽点或亮点，创作让人忍不住想投票的双语投票。"},
            {"role": "user", "content": prompt},
        ]
    )
    end_time = datetime.now()
    
    processing_time = (end_time - start_time).total_seconds()
    logger.info(f"AI投票生成完成，处理时间: {processing_time:.2f}秒")
    
    return response


def _process_poll_response(response):
    """
    处理AI投票响应

    Args:
        response: AI响应对象

    Returns:
        dict: 投票数据
    """
    response_text = response.choices[0].message.content
    logger.debug(f"AI投票生成响应: {response_text}")
    
    # 尝试从响应中提取和验证JSON
    poll_data = _extract_and_validate_poll(response_text)
    
    if poll_data:
        logger.info(f"成功生成投票: {poll_data['question']}，选项数: {len(poll_data['options'])}")
        return poll_data
    
    logger.warning("JSON解析失败，使用默认投票")
    return _get_default_poll()


def _extract_and_validate_poll(response_text):
    """
    从AI响应中提取并验证投票数据

    Args:
        response_text: AI响应文本

    Returns:
        dict: 验证后的投票数据，失败返回None
    """
    poll_data = _extract_poll_json(response_text)
    if poll_data:
        return _validate_and_fix_poll_data(poll_data)
    return None
