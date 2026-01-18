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

import re
import logging

logger = logging.getLogger(__name__)

def _get_md_entities(text):
    """
    获取文本中的所有md实体位置
    
    Args:
        text: 要分析的文本
    
    Returns:
        list: 实体列表，每个实体包含start, end, text, type
    """
    md_patterns = [
        (r'\*\*.*?\*\*', 'bold'),
        (r'`.*?`', 'inline_code'),
        (r'\[.*?\]\(.*?\)', 'link'),
        (r'\*.*?\*', 'italic'),
        (r'_.*?_', 'italic_underscore'),
        (r'~~.*?~~', 'strikethrough'),
        (r'__.*?__', 'bold_underscore'),
    ]
    
    entities = []
    for pattern, entity_type in md_patterns:
        for match in re.finditer(pattern, text, re.DOTALL):
            entities.append({
                'start': match.start(),
                'end': match.end(),
                'text': match.group(),
                'type': entity_type
            })
    
    return entities


def _merge_overlapping_entities(entities, text):
    """
    合并重叠的md实体
    
    Args:
        entities: 实体列表
        text: 原始文本
    
    Returns:
        list: 合并后的实体列表
    """
    entities = sorted(entities, key=lambda x: x['start'])
    merged = []
    
    for entity in entities:
        if not merged or entity['start'] > merged[-1]['end']:
            merged.append(entity)
        else:
            merged[-1]['end'] = max(merged[-1]['end'], entity['end'])
            merged[-1]['text'] = text[merged[-1]['start']:merged[-1]['end']]
    
    return merged


def _find_boundaries(text):
    """
    查找文本中的分割边界（段落和句子边界）
    
    Args:
        text: 要分析的文本
    
    Returns:
        list: 所有分割点位置列表
    """
    paragraph_boundaries = []
    for match in re.finditer(r'\n\s*\n', text):
        paragraph_boundaries.append(match.end())
    
    sentence_boundaries = []
    for match in re.finditer(r'[。.?!]\s+', text):
        sentence_boundaries.append(match.end())
    
    return sorted(set(paragraph_boundaries + sentence_boundaries))


def _find_boundary_split(current_pos, max_end_pos, boundaries, min_segment_length, max_length):
    """
    在边界中查找合适的分割点
    
    Args:
        current_pos: 当前位置
        max_end_pos: 最大结束位置
        boundaries: 分割边界列表
        min_segment_length: 最小分段长度
        max_length: 最大长度
    
    Returns:
        int: 分割位置，如果未找到返回-1
    """
    # 1. 查找第一个在范围内的边界
    for boundary in boundaries:
        if current_pos < boundary <= max_end_pos:
            best_split_pos = boundary
            # 2. 如果太短，尝试找更合适的
            if (best_split_pos - current_pos) < min_segment_length:
                for b in boundaries:
                    if b > best_split_pos and b <= max_end_pos:
                        segment_length = b - current_pos
                        if min_segment_length <= segment_length <= max_length:
                            return b
                        elif segment_length < min_segment_length:
                            best_split_pos = b
                        else:
                            break
            return best_split_pos
    return -1


def _find_entity_split(current_pos, max_end_pos, entities, max_length):
    """
    在实体边界查找分割点
    
    Args:
        current_pos: 当前位置
        max_end_pos: 最大结束位置
        entities: 实体列表
        max_length: 最大长度
    
    Returns:
        int: 分割位置，如果未找到返回-1
    """
    for entity in entities:
        if entity['start'] < max_end_pos < entity['end']:
            if entity['start'] > current_pos:
                return entity['start']
            elif entity['end'] <= current_pos + max_length * 2:
                return entity['end']
    return -1


def _find_char_boundary_split(current_pos, max_end_pos, text):
    """
    在字符边界查找分割点
    
    Args:
        current_pos: 当前位置
        max_end_pos: 最大结束位置
        text: 原始文本
    
    Returns:
        int: 分割位置
    """
    for i in range(max_end_pos - 1, current_pos, -1):
        if text[i].isspace() or text[i] in '，。,.!?;:':
            return i + 1
    return max_end_pos


def _find_best_split_position(current_pos, max_end_pos, text, boundaries, entities, max_length):
    """
    查找最佳分割位置
    
    Args:
        current_pos: 当前位置
        max_end_pos: 最大结束位置
        text: 原始文本
        boundaries: 分割边界列表
        entities: 实体列表
        max_length: 最大长度
    
    Returns:
        int: 最佳分割位置
    """
    min_segment_length = 100
    
    # 1. 尝试在边界分割
    split_pos = _find_boundary_split(current_pos, max_end_pos, boundaries, min_segment_length, max_length)
    if split_pos != -1:
        return split_pos
    
    # 2. 尝试在实体边界分割
    split_pos = _find_entity_split(current_pos, max_end_pos, entities, max_length)
    if split_pos != -1:
        return split_pos
    
    # 3. 使用字符边界
    return _find_char_boundary_split(current_pos, max_end_pos, text)


def _validate_parts_length(parts, max_length):
    """
    验证分段长度，对超长的分段进行二次分割
    
    Args:
        parts: 原始分段列表
        max_length: 最大长度
    
    Returns:
        list: 验证后的分段列表
    """
    validated_parts = []
    for part in parts:
        if len(part) > max_length:
            logger.warning(f"分段长度 {len(part)} 超过最大长度 {max_length}，进行二次分割")
            for i in range(0, len(part), max_length):
                validated_parts.append(part[i:i+max_length])
        else:
            validated_parts.append(part)
    
    return validated_parts


def _validate_entities(parts):
    """
    验证分段中的md实体完整性
    
    Args:
        parts: 分段列表
    """
    for part in parts:
        bold_count = part.count('**')
        if bold_count % 2 != 0:
            logger.warning(f"分段中粗体标记不匹配: {bold_count}个**标记")


def split_message_simple(text, max_length):
    """
    简单分割消息，按字符数分割
    
    Args:
        text: 要分割的文本
        max_length: 每个分段的最大长度
    
    Returns:
        list: 分割后的文本片段列表
    """
    parts = []
    for i in range(0, len(text), max_length):
        parts.append(text[i:i+max_length])
    return parts


def split_message_smart(text, max_length, preserve_md=True):
    """
    智能分割消息，确保md格式实体不被破坏
    
    Args:
        text: 要分割的文本
        max_length: 每个分段的最大长度
        preserve_md: 是否保护md格式
    
    Returns:
        list: 分割后的文本片段列表
    """
    if len(text) <= max_length:
        return [text]
    
    if not preserve_md:
        return split_message_simple(text, max_length)
    
    # 获取并合并实体
    entities = _get_md_entities(text)
    merged_entities = _merge_overlapping_entities(entities, text)
    
    # 查找分割边界
    boundaries = _find_boundaries(text)
    
    # 分割算法
    parts = []
    current_pos = 0
    
    while current_pos < len(text):
        max_end_pos = min(current_pos + max_length, len(text))
        
        if len(text) - current_pos <= max_length:
            parts.append(text[current_pos:])
            break
        
        # 查找最佳分割位置
        best_split_pos = _find_best_split_position(
            current_pos, max_end_pos, text, boundaries, merged_entities, max_length
        )
        
        # 添加分段
        part = text[current_pos:best_split_pos].strip()
        if part:
            parts.append(part)
        
        current_pos = best_split_pos
    
    # 验证分段
    validated_parts = _validate_parts_length(parts, max_length)
    _validate_entities(validated_parts)
    
    logger.debug(f"智能分割完成: {len(text)}字符 -> {len(validated_parts)}个分段")
    return validated_parts


def validate_message_entities(text):
    """
    验证消息中的md实体是否完整
    
    Args:
        text: 要验证的文本
    
    Returns:
        bool: 实体是否完整
        str: 错误信息（如果有）
    """
    # 检查粗体标记 **
    bold_count = text.count('**')
    if bold_count % 2 != 0:
        return False, f"粗体标记不匹配: 找到{bold_count}个**标记"
    
    # 检查粗体标记 __
    bold_underscore_count = text.count('__')
    if bold_underscore_count % 2 != 0:
        return False, f"粗体标记不匹配: 找到{bold_underscore_count}个__标记"
    
    # 检查内联代码标记
    backtick_count = text.count('`')
    if backtick_count % 2 != 0:
        return False, f"内联代码标记不匹配: 找到{backtick_count}个`标记"
    
    # 检查斜体标记 *
    italic_count = text.count('*') - bold_count * 2  # 排除**中的*
    if italic_count % 2 != 0:
        return False, f"斜体标记不匹配: 找到{italic_count}个*标记"
    
    # 检查斜体标记 _
    italic_underscore_count = text.count('_') - bold_underscore_count * 2  # 排除__中的_
    if italic_underscore_count % 2 != 0:
        return False, f"斜体标记不匹配: 找到{italic_underscore_count}个_标记"
    
    # 检查删除线标记 ~~
    strikethrough_count = text.count('~~')
    if strikethrough_count % 2 != 0:
        return False, f"删除线标记不匹配: 找到{strikethrough_count}个~~标记"
    
    # 检查链接格式 [text](url)
    link_pattern = r'\[.*?\]\(.*?\)'
    links = list(re.finditer(link_pattern, text))
    for link in links:
        link_text = link.group()
        if '](' not in link_text or not link_text.endswith(')'):
            return False, f"链接格式错误: {link_text}"
    
    return True, "所有实体完整"


def split_by_lines_smart(text, max_length):
    """
    按行智能分割，确保每行不超过最大长度
    
    Args:
        text: 要分割的文本
        max_length: 每行的最大长度
    
    Returns:
        list: 分割后的行列表
    """
    lines = text.split('\n')
    result_lines = []
    
    for line in lines:
        if len(line) <= max_length:
            result_lines.append(line)
        else:
            # 对超长的行进行智能分割
            words = line.split(' ')
            current_line = ""
            
            for word in words:
                if len(current_line) + len(word) + 1 <= max_length:
                    current_line += (" " if current_line else "") + word
                else:
                    if current_line:
                        result_lines.append(current_line)
                    current_line = word
            
            if current_line:
                result_lines.append(current_line)
    
    return result_lines
