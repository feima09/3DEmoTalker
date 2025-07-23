from .wake import Wake
import time
import asyncio
from utils import get_logger

logging = get_logger()


class Realtime(Wake):
    async def speech(self):
        current_time = time.time()
        text: str = ""
        try:
            while True:
                if self.parent_conn is not None and self.parent_conn.poll():
                    self.tasks_cancel_func()
                    text = self.parent_conn.recv()
                    logging.info(f"ASR: {text}")
                    current_time = time.time()
                    
                if time.time() - current_time > self.timeout and text:
                    return text
                await asyncio.sleep(0.01)
        except Exception as e:
            logging.error(f"Speech: {e}")
            raise e
    
    
    async def run(self):
        self.process_start()
        
        try:
            text = await self.speech()
            logging.info(f"Recognized text: {text}")
            
            await self.socketio.emit("question", text, namespace="/ue")
            return text
        finally:
            self.process_stop()
        