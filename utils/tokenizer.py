"""
文本分词和句子分割模块

该模块提供文本处理功能，主要用于将连续文本流按照标点符号分割成自然句子，
以便进行后续的文本到语音转换处理。支持中英文标点符号识别。

作者: 光明实验室媒体智能团队
"""

from utils import get_logger

logging = get_logger()


async def sentence_segment(text_stream):
    """
    句子分割器
    
    将连续的文本流按照标点符号分割成自然句子，支持中英文标点。
    当累积的文本中含有标点且长度适中时，产生一个新的句子。
    
    Args:
        text_stream: 输入的文本流，异步生成器格式
        
    Returns:
        AsyncGenerator: 分割后的句子流，每个元素是一个自然句子
        
    Yields:
        str: 分割出的完整句子
        None: 当所有文本处理完毕时
    """
    buffer = ""
    punctuations = ',.?!:-，。？！：、'
    async for chunk in text_stream:
        if chunk is None:
            break
        buffer += chunk
        last_punctuation = max(
            (buffer.rfind(p) for p in punctuations),
            default=-1
        )
        if not last_punctuation == -1 and len(buffer[:last_punctuation + 1]) > 20:
            logging.info(f"tokenizer: {buffer[:last_punctuation + 1]}")
            yield buffer[:last_punctuation + 1]
            buffer = buffer[last_punctuation + 1:]
    
    if buffer:
        logging.info(f"tokenizer: {buffer}")
        yield buffer
        
    yield None
