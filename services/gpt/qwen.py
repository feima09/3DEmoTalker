from .openai import OpenAI
import time
import json
from utils import get_logger

logging = get_logger()


class Qwen(OpenAI):
    def set_body(self, message: str) -> dict:
        messages = self.body.get("input", {}).get("messages", [])
        
        if self.body is None:
            messages.append({
                "role": "system",
                "content": self.prompt
            })
            messages.append({
                "role": "user",
                "content": message
            })
        else:
            messages.append({
                "role": "assistant",
                "content": self.assistant_message
            })
            messages.append({
                "role": "user",
                "content": message
            })
            self.assistant_message = ""
            
        self.body["input"]["messages"] = messages
        
        return self.body
    
    
    def get_response_content(self, response) -> str:
        try:
            json_data = json.loads(response)
            content = json_data['output'].get('text', '')
            return content
        
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON data: {response}")
            return ""
                    
                    
    @staticmethod
    async def output_stream(gpt_stream):
        buffer = b""
        async for chunk in gpt_stream:
            if chunk is None:
                break
            buffer += chunk
            if b"\r\n\r\n" in buffer:
                split_bytes = b"\r\n\r\n"
            elif b"\n\n" in buffer:
                split_bytes = b"\n\n"
            else:
                continue
            
            while split_bytes in buffer:
                line, buffer = buffer.split(split_bytes, 1)
                text = line.decode("utf-8")
                if "data:" in text:
                    text = text.split("data:")[1].strip()
                    if text == "[DONE]":
                        yield text + "\n\n"
                        break
                    
                    try:
                        json_data: dict = json.loads(text.strip())
                        yield "data: " + json.dumps({
                            "id": "chat" + json_data.get('request_id', ''),
                            "model": json_data['usage']['models'][0].get('model_id', ''),
                            "create": int(time.time()),
                            "object": "chat.completion.chunk",
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "content": json_data['output'].get('text', '')
                                    },
                                    "finish_reason": json_data['output'].get('finish_reason', '')
                                }
                            ]
                        }) + "\n\n"
                        
                    except json.JSONDecodeError as e:
                        logging.error(f"Failed to parse JSON data: {e}")
                        raise
                    
