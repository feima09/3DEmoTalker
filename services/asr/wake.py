from multiprocessing import Process, Pipe
from .funasr_wss_client import one_thread
import socketio
import asyncio
import time
from utils import Config, get_logger

logging = get_logger()
config = Config.get("ASR", "")

class Wake:
    def __init__(self, socketio: socketio.AsyncServer, tasks_cancel_func):
        self.parent_conn = None
        self.child_conn = None
        self.process = None
        self.socketio = socketio
        self.tasks_cancel_func = tasks_cancel_func
        self.wake_words = config.get("wake_words", "光小明,你好,在吗")
        if isinstance(self.wake_words, str):
            self.wake_words = [w.strip() for w in self.wake_words.split(",") if w.strip()]
        self.timeout = config.get("timeout", 5)
        
    
    def process_start(self):
        if self.process is not None and self.process.is_alive():
            self.process_stop()
        if self.parent_conn is not None or self.child_conn is not None:
            self.process_stop()
            
        self.parent_conn, self.child_conn = Pipe()
        self.process = Process(target=one_thread, args=(0, 0, 0, self.child_conn,), daemon=True)
        self.process.start()
        
        
    def process_stop(self):
        if self.parent_conn is not None:
            self.parent_conn.close()
            self.parent_conn = None
        if self.child_conn is not None:
            self.child_conn.close()
            self.child_conn = None
        if self.process is not None and self.process.is_alive():
            self.process.terminate()
            self.process = None
    
    
    async def wake(self) -> str:
        """
        等待唤醒词
        
        持续监听语音输入，直到检测到配置中的唤醒词
        
        Returns:
            str: 检测到的唤醒词
            
        Raises:
            Exception: 当语音识别过程出错时抛出
        """
        try:
            while True:
                if self.parent_conn is not None and self.parent_conn.poll():
                    text: str = self.parent_conn.recv()
                    logging.info(f"ASR: {text}")
                    for word in self.wake_words:
                        if word in text:
                            return word
                await asyncio.sleep(0.01)
        except Exception as e:
            logging.error(f"Wake: {e}")
            raise e
    
    
    async def speech(self, wake_word: str) -> str:
        """
        获取用户语音输入内容
        
        在检测到唤醒词后，持续收集用户语音，直到超时
        
        Args:
            wake_word: 已检测到的唤醒词
            
        Returns:
            str: 用户语音内容（去除唤醒词部分）
            
        Raises:
            Exception: 当语音识别过程出错时抛出
        """
        current_time = time.time()
        text: str = ""
        try:
            while True:
                if self.parent_conn is not None and self.parent_conn.poll():
                    text = self.parent_conn.recv()
                    logging.info(f"ASR: {text}")
                    current_time = time.time()
                    
                if time.time() - current_time > self.timeout and text:
                    index = text.find(wake_word)
                    index += len(wake_word)
                    if index < len(text) and text[index] in "，。！？":
                        index += 1
                    return text[index:]
                await asyncio.sleep(0.01)
        except Exception as e:
            logging.error(f"Speech: {e}")
            raise e

    
    async def run(self) -> str:
        self.process_start()
        
        try:
            wake_word = await self.wake()
            logging.info(f"Wake word detected: {wake_word}")
            
            self.tasks_cancel_func()
            
            text =  await self.speech(wake_word)
            logging.info(f"Recognized text: {text}")
    
            await self.socketio.emit("question", text, namespace="/ue")
            
            return text
        finally:
            self.process_stop()
            
    
    async def run_forever(self):
        while True:
            await self.run()
