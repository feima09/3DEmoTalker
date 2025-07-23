from utils import Config

gpt = Config.get("GPT", "")
mode = gpt.get("type", "openai")
rag_enable = gpt.get("RAG", "").get("enable", False)


def GPT():
    if rag_enable:
        if mode == "openai":
            from .rag import RAG
            return RAG()
        elif mode == "qwen":
            from .rag import RAG_Qwen
            return RAG_Qwen()
        else:
            raise ValueError(f"Invalid GPT type: {mode}")
    else:
        if mode == "openai":
            from .openai import OpenAI
            return OpenAI()
        elif mode == "qwen":
            from .qwen import Qwen
            return Qwen()
        else:
            raise ValueError(f"Invalid GPT type: {mode}")
