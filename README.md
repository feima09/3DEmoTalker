# <img src="doc/logo.png" width="20%"> 3DEmoTalker 虚幻引擎数字人项目

## 项目概述

3DEmoTalker 是一个基于[虚幻引擎5.3](https://www.unrealengine.com/zh-CN/unreal-engine-5)开发的智能数字人项目，集成了语音识别、语音合成、AI对话和3D面部动画驱动技术支持链接本地知识库，语句打断功能。项目包含完整的UE5工程文件、后端服务接口和算法模块，支持本地部署和云端API接入。（本项目完整部署在windows系统上）

<div style="display: flex; justify-content: space-between;">
  <img src="doc/demo.gif" width="40%">
  <img src="doc/demo1.gif" width="40%">
</div>

## 主要特性

🗣️ **多语言语音识别（FunASR）**  
我们选用[Docker](https://www.docker.com/products/docker-desktop/)的方式对FunASR进行快速部署。  
```bash
docker run -p 10096:10095 --name FunASR -it --privileged=true -v $PWD/funasr-runtime-resources/models:/workspace/models registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
```
🔊 高质量语音合成（MeloTTS）
melotts在other目录下，如需本项目音色权重可以联系[贡献者](https://github.com/Calylyli),项目通过uvicorn进行流式推理，时延控制在0.3S内有利于用户的交互体验。
```bash
uvicorn melo.fastapi_server:app --host 0.0.0.0 --port 8001 --reload
```
详细微调+推理可以访问[MeloTTS](https://github.com/myshell-ai/MeloTTS) 

💬 大语言模型对话（支持阿里API/本地部署）

本地部署流程通过xinference

👄 实时面部动画驱动（NVIDIA Audio2Face/ovrlipsync）

[Audio2Face](https://developer.nvidia.cn/omniverse?sortBy=developer_learning_library%2Fsort%2Ffeatured_in.omniverse%3Adesc%2Ctitle%3Aasc&hitsPerPage=6#section-%E5%BC%80%E5%A7%8B%E4%BD%BF%E7%94%A8)由于需要通过VPN下载人物模型并且项目首次加载缓慢，版本选择2023.1.1。

[ovrlipsync](https://developers.meta.com/horizon/documentation/unreal/audio-ovrlipsync-unreal)轻量型嘴型驱动算法时延低但效果稍逊。

🎮 UE5实时渲染数字人

项目基于[UE5.3](https://www.unrealengine.com/zh-CN/unreal-engine-5) 完整UE5项目可以访问[百度网盘](https://pan.baidu.com/s/12xfK-QR10Rt5uYYs-nlnUA)

🌐 WebUI配置面板

双击webui.bat打开后端控制面板启动

```bash
webui.bat
```
