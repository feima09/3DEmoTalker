import pygame
import os
import asyncio
from utils import get_logger
import time

logging = get_logger()


class LocalPlayer:
    def __init__(self):
        pygame.mixer.init()
        
    
    @staticmethod
    def remove_audio(filename: str):
        """
        删除音频文件
        
        Args:
            filename: 要删除的音频文件路径
        """
        try:
            os.remove(filename)
        except Exception as e:
            pass
        
    
    async def play(self, filename: str):
        """
        本地播放音频文件
        
        使用pygame加载并播放音频，播放完成后删除文件
        
        Args:
            filename: 要播放的音频文件路径
        """
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            # 等待当前音频播放完成
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
        except Exception as e:
            logging.error(f"Failed to play audio: {e}")
            return
        
        finally:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            await asyncio.sleep(0.1)
            self.remove_audio(filename)
            
    
    async def run(self, audio_queue: asyncio.Queue, start_time):
        first_play = True
        
        try:
            while True:
                audio_file = await audio_queue.get()
                if audio_file is None:
                    break
                if first_play:
                    logging.info(f"First playing audio time: {time.time() - start_time:.2f}s")
                    first_play = False
                await self.play(audio_file)
        except asyncio.CancelledError:
            logging.info("Audio player cancelled")
            raise
        finally:
            while not audio_queue.empty():
                filename = audio_queue.get_nowait()
                if filename is not None:
                    self.remove_audio(filename)
