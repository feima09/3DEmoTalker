from .wake import Wake
from utils import Config

mode = Config.get("ASR", "").get("mode", "wake")
player_mode = Config.get("Player", "").get("mode", "local")


def ASR(socketio, tasks_cancel_func):
    if mode == "wake":
        if player_mode == "local":
            from .local import WakeLocal
            return WakeLocal(socketio=socketio, tasks_cancel_func=tasks_cancel_func)
        else:
            return Wake(socketio=socketio, tasks_cancel_func=tasks_cancel_func)
    elif mode == "realtime":
        if player_mode == "local":
            from .local import RealtimeLocal
            return RealtimeLocal(socketio=socketio, tasks_cancel_func=tasks_cancel_func)
        else:
            from .realtime import Realtime
            return Realtime(socketio=socketio, tasks_cancel_func=tasks_cancel_func)
    else:
        raise ValueError(f"Invalid ASR mode: {mode}")
