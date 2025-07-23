from utils import Config, get_logger

mode = Config.get("Player", "").get("mode", "local")
logging = get_logger()


def Player(socketio):
    if mode == "local":
        from .localplayer import LocalPlayer
        return LocalPlayer()
    elif mode == "audio2face":
        from .audio2face import Audio2Face
        return Audio2Face(socketio)
    else:
        raise ValueError(f"Invalid Player type: {mode}")
