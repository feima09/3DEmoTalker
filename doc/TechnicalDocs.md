# AI数字人后端系统技术文档

## 1. 系统概览

AI数字人后端系统是一个集成了大语言模型、语音识别、文本转语音和虚拟人物动画的综合服务平台。该系统旨在提供一个流畅的人机交互体验，具有以下特性：

- 基于大语言模型（如OpenAI、阿里通义千问）的对话能力
- 流式文本处理和响应生成
- 实时语音识别与唤醒词检测
- 高质量文本到语音转换
- 支持与NVIDIA Audio2Face集成实现唇形同步
- 可扩展的模块化架构

## 2. 架构设计

系统采用异步编程模式，主要使用Python的asyncio框架实现高并发处理。整体架构如下：

```
                 ┌───────────┐
                 │   客户端   │
                 └─────┬─────┘
                       │
                       ▼
┌───────────────────────────────────────┐
│              Web服务器                 │
│  ┌─────────────┐    ┌─────────────┐   │
│  │   REST API  │    │  Socket.IO  │   │
│  └──────┬──────┘    └──────┬──────┘   │
└─────────┼──────────────────┼──────────┘
          │                  │
┌─────────▼─────────┐  ┌─────▼──────────┐
│    服务组件管理     │  │    事件处理     │
└─────────┬─────────┘  └────────────────┘
          │
┌─────────▼─────────────────────────────┐
│              服务组件                  │
│  ┌────────┐ ┌────────┐ ┌────────────┐ │
│  │  GPT   │ │  TTS   │ │    播放器   │ │
│  └────────┘ └────────┘ └────────────┘ │
│  ┌────────────────────────────────────┤
│  │              ASR                   │ 
│  └────────────────────────────────────┤
└───────────────────────────────────────┘
```

## 3. 核心组件详解

### 3.1 主应用程序 (`app.py`)

主应用程序集成了Quart异步Web框架和Socket.IO，提供HTTP接口和WebSocket通信功能。主要负责：

- 初始化和管理各个服务组件
- 处理聊天API请求
- 协调GPT响应、TTS转换和音频播放的并发处理
- 通过Socket.IO与Unreal Engine客户端通信

关键实现是`chat()`函数，它处理聊天请求并实现三个并行任务：

1. GPT文本生成
2. 文本分割为句子并转换为语音
3. 语音文件的按序播放

### 3.2 GPT服务 (`services/gpt.py`)

提供与大语言模型的交互功能，支持OpenAI API和阿里通义千问等服务。主要功能：

- 向AI模型发送请求并获取流式响应
- 解析不同API格式的响应并提取文本内容
- 将阿里通义千问API响应转换为OpenAI兼容格式

关键函数：

- generate_stream(): 生成模型响应字节流
- create_text_stream(): 将字节流转换为文本流
- output_stream(): 处理不同模型API的响应格式

### 3.3 TTS服务 (`services/tts.py`)

负责文本到语音的转换，支持多种TTS服务。主要功能：

- 接收来自句子分割器的文本流
- 为每个句子生成对应的音频文件
- 通过异步API调用高效处理多个TTS请求

关键函数：

- generate(): 生成单个句子的音频文件
- audio_generate(): 从句子流生成音频文件流

### 3.4 播放器服务 (`services/player.py`)

管理音频文件的播放，支持本地播放和与NVIDIA Audio2Face集成。功能包括：

- 本地音频播放（使用pygame）
- 通过gRPC向Audio2Face发送音频数据
- 管理临时音频文件

- _localplay(): 本地播放音频文件
- _audio2face(): 发送音频到Audio2Face进行播放和面部表情生成

### 3.5 ASR服务 (`services/asr.py`)

提供语音识别功能，支持唤醒词检测和语音转文本。主要特性：

- 使用FunASR作为底层语音识别引擎
- 通过进程间通信实现异步处理
- 支持唤醒词检测和后续语音指令识别

- wake(): 等待检测唤醒词
- speech(): 获取用户语音输入内容

### 3.6 工具模块

- **文本分词** (`utils/tokenizer.py`): 将连续文本流分割为自然句子
- **日志管理** (`utils/logs.py`): 配置日志系统，支持控制台和文件输出
- **配置管理** (`utils/config.py`): 从YAML文件加载和管理系统配置
- **异步迭代工具** (`utils/itertools.py`): 处理异步生成器，实现数据流的分流

## 4. API参考

### 4.1 REST API

#### POST `/v1/chat/completions`

创建一个新的聊天对话，获取AI回复并播放语音。

**请求体**:

```json
{
  "messages": [
    {
      "content": "用户输入文本"
    }
  ]
}
```

**响应**:

- 返回格式: 事件流（text/event-stream）
- 内容: AI回复的流式文本

### 4.2 Socket.IO 事件

#### 发送事件

- `aniplay` (namespace: `/ue`): 通知客户端开始播放动画，参数为 `'play'`
- `question` (namespace: `/ue`): 当通过语音识别获取到用户问题时，将问题文本发送给客户端

#### 接收事件

- `connect` (namespace: `/ue`): 处理客户端连接事件
- `disconnect` (namespace: `/ue`): 处理客户端断开连接事件

## 5. 配置说明

系统配置使用YAML格式，主配置文件为`configs/config.yaml`，支持以下配置项：

### 5.1 系统配置

- `log_level`: 日志级别 (DEBUG, INFO, WARNING, ERROR)
- `host`: 服务绑定地址
- `port`: 服务监听端口

### 5.2 GPT配置

- `pre_config`: 预设配置文件名称，位于configs/gpt/目录下
- `type`: 大语言模型类型 (openai, qwen等)
- `api_endpoint`: API服务地址
- `request_header`: 请求头设置
- `request_body`: 请求体模板，包含系统提示词和用户消息格式

### 5.3 TTS配置

- `pre_config`: 预设配置文件名称，位于configs/tts/目录下
- `type`: TTS服务类型 (gptsovits, chumenwenwen等)
- `api_endpoint`: TTS服务API地址
- `request_header`: 请求头设置
- `request_body`: 请求体模板

### 5.4 ASR配置

- `enable`: 是否启用语音识别
- `wake_words`: 触发词列表，用逗号分隔
- `timeout`: 等待用户输入的超时时间（秒）
- `FunASR`: FunASR服务配置，包括IP、端口、SSL和识别模式

### 5.5 播放器配置

- `mode`: 播放模式 (local, audio2face)
- `Audio2Face`: Audio2Face配置，包括服务地址和播放器路径

## 6. 部署指南

### 6.1 环境要求

- Python 3.11+
- 依赖包：详见`requirements.txt`

### 6.2 部署步骤

1. 使用批处理脚本（Windows）:
    - 运行`app.bat`或`app.ps1`

2. 使用Conda环境:
```shell
conda create -n adhb python=3.11
conda activate adhb
pip install -r requirements.txt
python app.py
```

3. 配置外部服务:
    - 语言模型服务（如OpenAI API或本地部署的模型）
    - TTS服务（如GPTSoVITS或出门问问）
    - FunASR语音识别服务（可选）
    - NVIDIA Audio2Face（可选）

### 6.3 使用本地Python环境

系统自带了预打包的Python环境（位于`python`目录），可以直接使用而不需要额外安装Python

## 7. 开发指南

### 7.1 项目结构

```
.
├── app.py                 # 主应用程序
├── services/              # 服务组件
│   ├── asr.py             # 语音识别服务
│   ├── gpt.py             # GPT模型服务
│   ├── player.py          # 音频播放器服务
│   └── tts.py             # 文本到语音服务
├── utils/                 # 工具模块
│   ├── audio2face_pb2.py  # Audio2Face protobuf生成文件
│   ├── audio2face_pb2_grpc.py # Audio2Face gRPC接口
│   ├── config.py          # 配置管理
│   ├── funasr_wss_client.py # FunASR客户端
│   ├── itertools.py       # 异步迭代工具
│   ├── logs.py            # 日志工具
│   └── tokenizer.py       # 文本分词工具
├── configs/               # 配置文件目录
│   ├── config.yaml        # 主配置文件
│   ├── gpt/               # GPT服务配置
│   └── tts/               # TTS服务配置
├── tmp/                   # 临时文件存储
├── logs/                  # 日志文件目录
└── python/                # 内置Python环境
```

### 7.2 扩展指南

#### 添加新的GPT服务支持

1. 修改`services/gpt.py`中的`generate_stream`和`create_text_stream`函数
2. 为新服务添加适当的请求和响应处理逻辑
3. 在`gpt`中添加新的配置文件

#### 添加新的TTS服务支持

1. 修改`services/tts.py`中的`generate`函数
2. 实现与新TTS API的交互
3. 在`tts`中添加新的配置文件

#### 添加新的播放方式

1. 修改`services/player.py`，添加新的播放函数
2. 更新`play`函数以支持新的播放模式
3. 在`config.yaml`中添加相应配置

## 8. 性能优化

系统已实现的性能优化策略包括：

1. 使用异步编程模型提高并发处理能力
2. 流式处理减少首次响应时间
3. 文本分割以句子为单位，实现更自然的语音合成
4. 并行处理文本生成和语音合成，提高整体响应速度
5. 使用临时文件管理音频数据，避免内存溢出
6. 精细的日志记录，支持性能分析和故障排查

## 9. 故障排除

### 9.1 常见问题

- **无法连接到GPT服务**: 检查API端点和认证信息配置
- **TTS服务无响应**: 验证TTS服务是否正常运行，检查网络连接
- **音频播放失败**: 检查音频格式是否兼容，播放器模式是否正确配置
- **语音识别不工作**: 确认FunASR服务已启动，检查唤醒词配置

### 9.2 日志分析

系统日志存储在`logs`目录下，按日期命名（YYYY-MM-DD.txt格式）。日志包含详细的组件运行信息和性能指标，可用于排查问题。

---

_本文档由光明实验室媒体智能团队制作_  
_更新日期: 2025年5月6日_
