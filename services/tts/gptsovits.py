import os
import copy
import time
from utils.httpx_client import httpx_client
import aiofiles
import random
import string
import asyncio
from utils import get_logger, Config
import yaml

logging = get_logger()
home_dir = os.getcwd()
config = Config.get("TTS", {})
per_config = config.get("pre_config", "")
if per_config is not None:
    with open(f"{home_dir}/configs/tts/{per_config}", 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)


class GPTSoVits:
    def __init__(self):
        tmp_dir = f"{home_dir}/tmp"
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
            
        self.body = copy.deepcopy(config.get("request_body", {
            "ref_audio_path": "test.wav",
            "prompt_text": "test",
            "prompt_lang": "zh",
            "text": "",
            "text_lang": "zh",
            "batch_size": 8,
            "split_bucket": False,
            "parallel_infer": True,
            "streaming_mode": False
        }))
        self.url = config.get("api_endpoint", "http://127.0.0.1:9880")
        self.headers = config.get("request_header", {
            "Content-Type": "application/json"
        })
            
    
    async def generate(self, sentence: str, filename: str):
        """
        生成单个句子的音频文件
        
        Args:
            sentence: 需要转换为语音的文本内容
            filename: 保存音频文件的路径
            
        Raises:
            Exception: 当TTS服务请求失败时抛出
        """
        self.body['text'] = sentence
        
        try: 
            # 记录开始时间
            start_time = time.time()
                
            async with httpx_client.stream(
                "POST",
                self.url,
                json=self.body,
                headers=self.headers,
                timeout=30
            ) as response:
                # 记录首次收到响应时间
                first_repsonse_time = time.time()
                logging.info(f"First received response time: {first_repsonse_time - start_time:.2f}s")
                
                response.raise_for_status()
                
                async with aiofiles.open(filename, "wb") as afp:
                    async for chunk in response.aiter_bytes():
                        await afp.write(chunk)
                    
            # 记录所有数据接收完毕时间
            end_time = time.time()
            logging.info(f"All data received time: {end_time - first_repsonse_time:.2f}s")
            logging.info(f"All response time: {end_time - start_time:.2f}s")    
            
            logging.info(f"Successfully generated audio file: {filename}")
                        
        except Exception as e:
            raise Exception(f"Failed to request TTS service: {e}")
        
        
    async def audio_generate(self, sentence_stream):
        """
        从句子流中生成音频文件流
        
        为每个输入句子生成对应的音频文件，并返回文件路径
        
        Args:
            sentence_stream: 输入句子的异步生成器
            
        Returns:
            AsyncGenerator: 音频文件路径的异步生成器
        """
        index = 0
        async for sentence in sentence_stream:
            if sentence is None:
                break
            index += 1
            filename = ''.join(random.sample(string.ascii_letters + string.digits, 16))
            full_path = f"{home_dir}/tmp/" + filename + ".wav"
            await self.generate(sentence, full_path)
            yield full_path
            
        yield None


    async def run(self, audio_stream, audio_queue: asyncio.Queue):
        """
        音频生成器函数
        
        从TTS服务获取生成的音频文件并放入队列中
        """
        try:
            async for audio_file in audio_stream:
                if audio_file is None:
                    break
                await audio_queue.put(audio_file)
            await audio_queue.put(None)
        except asyncio.CancelledError:
            logging.info("Audio generator cancelled")
            await audio_queue.put(None)
            raise
