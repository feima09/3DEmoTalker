from .gptsovits import GPTSoVits
from utils import Config, get_logger

mode = Config.get("TTS", "").get("mode", "gptsovits")
logging = get_logger()


def TTS():
    if mode == "gptsovits":
        return GPTSoVits()
    else:
        raise ValueError(f"Invalid TTS type: {mode}")
