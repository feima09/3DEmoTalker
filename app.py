"""
AI数字人后端服务

该模块实现了一个数字人助手的后端服务，包括:
- 与GPT模型交互的聊天接口
- 文本到语音(TTS)的转换服务
- 语音识别(ASR)服务
- 与Unreal Engine客户端的实时通信
- 支持唇形同步的音频播放控制

架构设计采用异步处理模式，通过Socket.IO实现与前端的实时通信，
并利用流式处理技术确保对话和语音的自然流畅。

作者: 光明实验室媒体智能团队
版本: 2.0.2
日期: 2025-03-19
"""

import os
import time

import asyncio
from quart import Quart, request, jsonify, Response
from quart_cors import cors
import socketio

from utils import Config, get_logger, atee, sentence_segment
from services.gpt import GPT
from services.tts import TTS
from services.player import Player

logging = get_logger()

CORS_ALLOWED_ORIGINS = "*"

host = Config.get("host", "127.0.0.1")
port = Config.get("port", 5002)


class QuartSIO:
    def __init__(self):
        self._sio = socketio.AsyncServer(
            async_mode='asgi', 
            cors_allowed_origins=CORS_ALLOWED_ORIGINS
        )
        self._quart_app = Quart(__name__)
        self._quart_app = cors(
            self._quart_app, 
            allow_origin=CORS_ALLOWED_ORIGINS
        )
        self._sio_app = socketio.ASGIApp(
            self._sio, 
            self._quart_app
        )
        self.route = self._quart_app.route
        self.on = self._sio.on
        self.emit = self._sio.emit
        
    async def _run(self):
        import hypercorn.asyncio
        try:
            await hypercorn.asyncio.serve(
                    self._sio_app,
                    hypercorn.Config.from_mapping(
                        bind=f"{host}:{port}",
                        workers=1,
                        timeout=300,
                        keep_alive_timeout=300
                    )
                )
        except KeyboardInterrupt:
            logging.info("Shutting down server")
        finally:
            logging.info("Server stopped")
    
    def run(self):
        asyncio.run(self._run())


app = QuartSIO()

home_dir = os.getcwd()


tasks = set()
def tasks_cancel():
    """
    取消并清理所有正在运行的异步任务
    
    该函数遍历全局tasks集合中的所有异步任务,
    对每个任务执行取消操作并标记为完成。
    主要用于在开始新对话或应用关闭时确保没有遗留的任务继续运行。
    """
    global tasks
    task: asyncio.Task
    for task in tasks:
        if not task.done():
            task.cancel()
    tasks.clear()


@app.on('connect', namespace='/ue') # type: ignore
async def connet(sid, environ):
    logging.info(f"Connected: {sid}")
    

@app.on('disconnect', namespace='/ue') # type: ignore
async def disconnect(sid):
    logging.info(f"Disconnected: {sid}")


@app.route('/v1/chat/completions', methods=['POST'])
async def chat():
    """
    处理聊天完成请求的主函数
    
    该函数接收用户消息，调用GPT生成回复，同时将文本转换为语音并播放
    实现了并行处理文本生成和语音合成的流程
    
    Returns:
        Response: 包含生成文本的流式响应
    """
    global tasks
    tasks_cancel()
    
    data: dict = await request.json
    messages: list[dict] = data.get("messages", [])
    if not messages:
        return jsonify({"error": "Message is required"}), 400
    message = messages[0].get("content", "")
    
    start_time = time.time()
    
    async def generate():
        gpt_stream = gpt.generate_stream(message)
        
        stream1, stream2, task = await atee(gpt_stream)
        tasks.add(task)
        
        sentence_stream = sentence_segment(gpt.create_text_stream(stream1))
        
        audio_stream = tts.audio_generate(sentence_stream)
        
        audio_queue = asyncio.Queue()
                        
        audio_gen_task = asyncio.create_task(tts.run(audio_stream, audio_queue))
        tasks.add(audio_gen_task)
        play_task = asyncio.create_task(player.run(audio_queue, start_time))
        tasks.add(play_task)
        
        output_stream = gpt.output_stream(stream2)
                    
        try:
            async for data in output_stream:
                yield data
            
            await audio_gen_task
            await play_task
        except asyncio.CancelledError:
            logging.info("Chat cancelled")
            audio_gen_task.cancel()
            play_task.cancel()
            raise
        else:
            tasks.clear()
    
    try:
        return Response(
            generate(),
            mimetype="text/event-stream"
        )
    except Exception as e:
        logging.error(f"Failed to chat: {e}")
        return jsonify({"error": f"Failed to chat: {e}"}), 500


@app.route('/v1/chat/new', methods=['GET'])
async def new_chat():
    tasks_cancel()
    GPT.reset_body()
    return jsonify({"message": "New chat started"}), 200

                
if __name__ == '__main__':
    gpt = GPT()
    tts = TTS()
    player = Player(app)
    
    asr_task = None
    
    async def main():
        if Config.get("ASR", "").get("enable", False):
            global asr_task
            from services.asr import ASR
            asr = ASR(app, tasks_cancel)
            asr_task = asyncio.create_task(asr.run_forever())
        
        await app._run()
    
    try:
        asyncio.run(main())
    finally:
        if asr_task:
            asr_task.cancel()
