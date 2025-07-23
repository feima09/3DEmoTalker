import copy
import json
import time
import os
import yaml
from utils import httpx_client, Config, get_logger, Prompt

logging = get_logger()
home_dir = os.getcwd()

config = Config.get("GPT", {})
per_config = config.get("pre_config", "")
if per_config is not None:
    with open(f"{home_dir}/configs/gpt/{per_config}", 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)


class OpenAI:
    def __init__(self):
        self.api_endpoint = config.get("api_endpoint", "https://api.openai.com/v1/chat/completions")
        self.headers = config.get("request_header", {
            "Content-Type": "application/json; charset=UTF-8"
        })
        self.reset_body()
        
        self.prompt = Prompt
            
        self.assistant_message = ""
        
    
    def set_body(self, message: str) -> dict:
        messages = self.body.get("messages", [])
        
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
            
        self.body["messages"] = messages
        
        return self.body
    
    
    async def generate_stream(self, message: str):
        try:
            start_time = time.time()
                
            async with httpx_client.stream(
                "POST",
                self.api_endpoint,
                json=self.set_body(message),
                headers=self.headers,
            ) as response:
                first_repsonse_time = time.time()
                logging.info(f"First received response time: {first_repsonse_time - start_time:.2f}s")
                
                response.raise_for_status()
                
                chunk_total = 0
                
                async for chunk in response.aiter_bytes():
                    if chunk:
                        chunk_total += 1
                        yield chunk
            
            end_time = time.time()
            logging.info(f"All data received time: {end_time - first_repsonse_time:.2f}s")
            logging.info(f"Average chunk time: {(end_time - first_repsonse_time) / chunk_total:.2f}s")
            logging.info(f"All response time: {end_time - start_time:.2f}s")
                    
            yield None
        except Exception as e:
            raise Exception(f"Failed to request GPT service: {e}")


    def get_response_content(self, response) -> str:
        try:
            json_data = json.loads(response)
            content = json_data['choices'][0]['delta'].get('content', '')
            return content
        
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON data: {response}")
            return ""
        

    async def create_text_stream(self, gpt_stream):
        buffer = b""
        split_bytes = b""
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
                line: bytes
                line, buffer = buffer.split(split_bytes, 1)
                text = line.decode("utf-8")
                
                if "data:" in text:
                    text = text.split("data:")[1].strip()
                    if text == "[DONE]":
                        yield None
                        break
                    
                    content = self.get_response_content(text)
                    if content:
                        yield content
                        self.assistant_message += content


    @staticmethod
    async def output_stream(gpt_stream):
        chunk: bytes
        async for chunk in gpt_stream:
            if chunk is None:
                break
            yield chunk
            
    
    def reset_body(self):
        self.body = copy.deepcopy(config.get("request_body", {
            "model": "gpt-4",
            "messages": [],
            "temperature": 0.7,
            "top_p": 1,
            "n": 1,
            "stream": True,
            "max_tokens": 10000,
        }))
