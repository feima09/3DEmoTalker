from .localplayer import LocalPlayer
import grpc
import time
import soundfile
from . import audio2face_pb2, audio2face_pb2_grpc
import asyncio
from utils import get_logger, Config

logging = get_logger()
config = Config.get("Player", "").get("Audio2Face", "")


class Audio2Face(LocalPlayer):
    def __init__(self, socketio):
        self.socketio = socketio
        self.BLOCK_UNTIL_PLAYBACK_IS_FINISHED = True
        self.SLEEP_BETWEEN_CHUNKS = 0.09
        
        self.url = config.get("url", "localhost:50051")
        self.player = config.get("player", "default")
        
        
    async def play(self, filename: str, stub: audio2face_pb2_grpc.Audio2FaceStub):
        try:
            # 记录开始时间
            start_time = time.time()
            
            audio_data, samplerate = soundfile.read(filename, dtype="float32")
            duration = len(audio_data) / samplerate
            logging.info(f"Audio duration: {duration:.2f}s")

            async def make_generator():
                """创建发送音频数据的异步生成器"""
                start_marker = audio2face_pb2.PushAudioRequestStart(
                    samplerate=samplerate, # type: ignore
                    instance_name=self.player, # type: ignore
                    block_until_playback_is_finished=self.BLOCK_UNTIL_PLAYBACK_IS_FINISHED, # type: ignore
                )
                CHUNK_SIZE = samplerate // 10
                
                yield audio2face_pb2.PushAudioStreamRequest(start_marker=start_marker) # type: ignore
                
                for i in range(len(audio_data) // CHUNK_SIZE + 1):
                    await asyncio.sleep(self.SLEEP_BETWEEN_CHUNKS)
                    chunk = audio_data[i * CHUNK_SIZE: i * CHUNK_SIZE + CHUNK_SIZE]
                    yield audio2face_pb2.PushAudioStreamRequest(audio_data=chunk.tobytes()) # type: ignore

            logging.info(f"Sending audio to audio2face")
            await stub.PushAudioStream(make_generator())
            
        except Exception as e:
            logging.error(f"Failed to send audio to audio2face: {e}")
            return
        else:
            logging.info(f"Successfully sent audio to audio2face")
            
            # 记录结束时间
            end_time = time.time()
            logging.info(f"Excluding the time consumed by the audio duration: {end_time - start_time - duration:.2f}s")
            logging.info(f"Audio playback time: {end_time - start_time:.2f}s")
        finally:
            self.remove_audio(filename)


    async def run(self, audio_queue: asyncio.Queue, start_time):
        first_play = True
        
        try:
            channel = grpc.aio.insecure_channel(self.url)
            logging.info(f"Connecting to audio2face at {self.url}")
            
            stub = audio2face_pb2_grpc.Audio2FaceStub(channel)
            
            while True:
                audio_file = await audio_queue.get()
                if audio_file is None:
                    break
                
                if first_play:
                    logging.info(f"First playing audio time: {time.time() - start_time:.2f}s")
                    first_play = False
                    
                await self.socketio.emit(
                        'aniplay', 
                        'play',
                        namespace='/ue'
                    )
                
                await self.play(audio_file, stub)
        except asyncio.CancelledError:
            logging.info("Audio player cancelled")
            raise
        finally:
            await channel.close()
            while not audio_queue.empty():
                filename = audio_queue.get_nowait()
                if filename is not None:
                    self.remove_audio(filename)
