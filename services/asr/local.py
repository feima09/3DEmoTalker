from .wake import Wake
from .realtime import Realtime
import requests
import threading
from utils import Config, get_logger

logging = get_logger()

host = Config.get("host", "127.0.0.1")
port = Config.get("port", 5002)


def send_request(text):
    try:
        response = requests.post(
            f"http://{host}:{port}/v1/chat/completions",
            json={"messages": [{"content": text}]},
            timeout=30,
            stream=True
        )
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=1024):
            pass
    except Exception as e:
        pass


class WakeLocal(Wake):
    async def run(self):
        text = await super().run()
        
        try:
            thread = threading.Thread(target=send_request, args=(text,))
            thread.daemon = True
            thread.start()
        except Exception as e:
            logging.error(f"Failed to create request thread: {e}")
            

class RealtimeLocal(Realtime):
    async def run(self):
        text = await super().run()
        
        try:
            thread = threading.Thread(target=send_request, args=(text,))
            thread.daemon = True
            thread.start()
        except Exception as e:
            logging.error(f"Failed to create request thread: {e}")

