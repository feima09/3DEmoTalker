import os
import yaml
import gradio as gr
import json

home_dir = os.getcwd()
CONFIG_PATH = f"{home_dir}/configs/config.yaml"


def load_config():
    """从配置文件加载配置"""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def save_config(config_data):
    """保存配置到文件"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
        yaml.dump(config_data, file, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return "配置已保存！"


def update_nested_dict(original, updates, path=None):
    """更新嵌套字典"""
    if path is None:
        path = []
    
    for k, v in updates.items():
        if isinstance(v, dict) and k in original and isinstance(original[k], dict):
            update_nested_dict(original[k], v, path + [k])
        else:
            original[k] = v
    
    return original


def get_preset_configs(config_type):
    """获取指定类型的预设配置文件列表"""
    config_dir = f"{home_dir}/configs/{config_type}"
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    preset_files = [f for f in os.listdir(config_dir) if f.endswith(".yaml")]
    return preset_files


def load_preset_config(config_type, preset_file):
    """加载预设配置"""
    if not preset_file:
        return None, "请选择预设配置文件"
    
    preset_path = f"{home_dir}/configs/{config_type}/{preset_file}"
    if not os.path.exists(preset_path):
        return None, f"预设配置文件 {preset_file} 不存在"
    
    try:
        with open(preset_path, 'r', encoding='utf-8') as file:
            preset_config = yaml.safe_load(file)
            return preset_config, f"成功加载预设配置：{preset_file}"
    except Exception as e:
        return None, f"加载预设配置失败：{str(e)}"


def save_preset_config(config_type, config_data, file_name):
    """保存预设配置"""
    if not file_name:
        return "请输入预设配置文件名"
    
    if not file_name.endswith(".yaml"):
        file_name += ".yaml"
    
    preset_dir = f"{home_dir}/configs/{config_type}"
    if not os.path.exists(preset_dir):
        os.makedirs(preset_dir)
    
    preset_path = f"{preset_dir}/{file_name}"
    
    try:
        with open(preset_path, 'w', encoding='utf-8') as file:
            yaml.dump(config_data, file, default_flow_style=False, sort_keys=False, allow_unicode=True)
        return f"预设配置已保存为 {file_name}"
    except Exception as e:
        return f"保存预设配置失败：{str(e)}"


def save_all_configs(
    # 基本配置
    log_level, host, port,
    # GPT配置
    gpt_type, gpt_api, gpt_preset_file, gpt_request_header_json, gpt_request_body_json,
    rag_enable, embedding_api, embedding_model, embedding_api_key, top_k,
    # TTS配置
    tts_type, tts_api, tts_preset_file, tts_request_header_json, tts_request_body_json,
    # ASR配置
    asr_enable, asr_mode, wake_words, timeout,
    funasr_ip, funasr_port, funasr_ssl, funasr_mode,
    # 播放器配置
    player_mode, a2f_url, a2f_player
):
    """统一保存所有配置"""
    config = load_config()
    
    # 更新基本配置
    config['log_level'] = log_level
    config['host'] = host
    config['port'] = int(port)
    
    # 更新GPT配置
    config['GPT']['type'] = gpt_type
    config['GPT']['api_endpoint'] = gpt_api
    config['GPT']['pre_config'] = gpt_preset_file if gpt_preset_file else None
    
    try:
        gpt_request_header = json.loads(gpt_request_header_json)
        config['GPT']['request_header'] = gpt_request_header
        gpt_request_body = json.loads(gpt_request_body_json)
        config['GPT']['request_body'] = gpt_request_body
    except json.JSONDecodeError:
        return "GPT请求体JSON格式错误，配置未保存！"
    
    # 更新RAG配置
    config['GPT']['RAG']['enable'] = rag_enable
    config['GPT']['RAG']['embedding']['api_endpoint'] = embedding_api
    config['GPT']['RAG']['embedding']['model'] = embedding_model
    config['GPT']['RAG']['embedding']['api_key'] = embedding_api_key
    config['GPT']['RAG']['top_k'] = int(top_k)
    
    # 更新TTS配置
    config['TTS']['type'] = tts_type
    config['TTS']['api_endpoint'] = tts_api
    config['TTS']['pre_config'] = tts_preset_file if tts_preset_file else None
    
    try:
        tts_request_header = json.loads(tts_request_header_json)
        config['TTS']['request_header'] = tts_request_header
        tts_request_body = json.loads(tts_request_body_json)
        config['TTS']['request_body'] = tts_request_body
    except json.JSONDecodeError:
        return "TTS请求体JSON格式错误，配置未保存！"
    
    # 更新ASR配置
    config['ASR']['enable'] = asr_enable
    config['ASR']['mode'] = asr_mode
    config['ASR']['wake_words'] = wake_words
    config['ASR']['timeout'] = float(timeout)
    config['ASR']['FunASR']['ip'] = funasr_ip
    config['ASR']['FunASR']['port'] = funasr_port
    config['ASR']['FunASR']['ssl'] = int(funasr_ssl)
    config['ASR']['FunASR']['mode'] = funasr_mode
    
    # 更新播放器配置
    config['Player']['mode'] = player_mode
    config['Player']['Audio2Face']['url'] = a2f_url
    config['Player']['Audio2Face']['player'] = a2f_player
    
    # 保存所有配置
    save_config(config)
    return "所有配置已保存！"


# 刷新预设配置下拉列表
def refresh_preset_configs(config_type):
    preset_files = get_preset_configs(config_type)
    return gr.Dropdown(choices=preset_files)


# 加载GPT预设配置
def load_gpt_preset(preset_file):
    preset_config, message = load_preset_config("gpt", preset_file)
    if preset_config:
        # 加载基本GPT配置
        gpt_type = preset_config.get('type', 'openai')
        api_endpoint = preset_config.get('api_endpoint', '')
        header_json = json.dumps(preset_config.get('request_header', {}), indent=2, ensure_ascii=False)
        body_json = json.dumps(preset_config.get('request_body', {}), indent=2, ensure_ascii=False)
        
        # 加载RAG配置
        rag_config = preset_config.get('RAG', {})
        rag_enable = rag_config.get('enable', False)
        embedding_config = rag_config.get('embedding', {})
        embedding_api = embedding_config.get('api_endpoint', '')
        embedding_model = embedding_config.get('model', '')
        embedding_api_key = embedding_config.get('api_key', '')
        top_k = rag_config.get('top_k', 3)
        
        return gpt_type, api_endpoint, header_json, body_json, rag_enable, embedding_api, embedding_model, embedding_api_key, top_k, message
    return None, None, None, None, False, '', '', '', 3, message


# 保存GPT预设配置
def save_gpt_preset(gpt_type, api_endpoint, header_json, body_json, rag_enable, embedding_api, embedding_model, embedding_api_key, top_k, file_name):
    try:
        header = json.loads(header_json)
        body = json.loads(body_json)
        config_data = {
            "type": gpt_type,
            "api_endpoint": api_endpoint,
            "request_header": header,
            "request_body": body,
            "RAG": {
                "enable": rag_enable,
                "embedding": {
                    "api_endpoint": embedding_api,
                    "model": embedding_model,
                    "api_key": embedding_api_key
                },
                "top_k": int(top_k)
            }
        }
        result = save_preset_config("gpt", config_data, file_name)
        return result, refresh_preset_configs("gpt")
    except json.JSONDecodeError:
        return "GPT请求体JSON格式错误，配置未保存！", gr.Dropdown()


# 加载TTS预设配置
def load_tts_preset(preset_file):
    preset_config, message = load_preset_config("tts", preset_file)
    if preset_config:
        # 加载整个TTS配置
        tts_type = preset_config.get('type', 'gptsovits')
        api_endpoint = preset_config.get('api_endpoint', '')
        header_json = json.dumps(preset_config.get('request_header', {}), indent=2, ensure_ascii=False)
        body_json = json.dumps(preset_config.get('request_body', {}), indent=2, ensure_ascii=False)
        return tts_type, api_endpoint, header_json, body_json, message
    return None, None, None, None, message


# 保存TTS预设配置
def save_tts_preset(tts_type, api_endpoint, header_json, body_json, file_name):
    try:
        header = json.loads(header_json)
        body = json.loads(body_json)
        config_data = {
            "type": tts_type,
            "api_endpoint": api_endpoint,
            "request_header": header,
            "request_body": body
        }
        result = save_preset_config("tts", config_data, file_name)
        return result, refresh_preset_configs("tts")
    except json.JSONDecodeError:
        return "TTS请求体JSON格式错误，配置未保存！", gr.Dropdown()


def create_ui():
    config = load_config()
    
    gr.Markdown("# AI数字人后端配置")
    
    with gr.Tabs():
        # 基本配置
        with gr.TabItem("基本配置"):
            with gr.Group():
                log_level = gr.Dropdown(
                    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                    value=config['log_level'],
                    label="日志等级"
                )
                host = gr.Textbox(value=config['host'], label="服务器主机")
                port = gr.Number(value=config['port'], label="服务器端口", precision=0)
        
        # GPT配置
        with gr.TabItem("GPT配置"):
            with gr.Group():
                # 预设配置管理
                with gr.Accordion("预设配置管理", open=True):
                    with gr.Row():
                        gpt_preset_files = get_preset_configs("gpt")
                        gpt_preset_dropdown = gr.Dropdown(
                            choices=gpt_preset_files,
                            value=config['GPT'].get('pre_config', None),
                            label="预设配置文件"
                        )
                        
                        gpt_preset_name = gr.Textbox(label="保存为")
                        
                    with gr.Row():
                        gpt_preset_refresh = gr.Button("刷新", variant="primary", size="lg")
                        gpt_preset_load = gr.Button("加载预设", variant="primary", size="lg")
                        gpt_preset_save = gr.Button("保存预设", variant="primary", size="lg")
                    
                    gpt_preset_message = gr.Textbox(label="预设操作结果")
                
                # 其他GPT配置
                gpt_type = gr.Radio(
                    choices=["openai", "qwen"],
                    value=config['GPT']['type'],
                    label="GPT类型"
                )
                gpt_api = gr.Textbox(
                    value=config['GPT']['api_endpoint'],
                    label="API端点"
                )
                
                gpt_request_header = gr.Code(
                    value=json.dumps(config['GPT']['request_header'], indent=2, ensure_ascii=False),
                    language="json",
                    label="请求头配置(JSON)"
                )
                
                gpt_request_body = gr.Code(
                    value=json.dumps(config['GPT']['request_body'], indent=2, ensure_ascii=False),
                    language="json",
                    label="请求体配置(JSON)"
                )
                
                with gr.Accordion("RAG配置"):
                    rag_enable = gr.Checkbox(
                        value=config['GPT']['RAG']['enable'],
                        label="启用RAG"
                    )
                    
                    with gr.Group(visible=config['GPT']['RAG']['enable']) as rag_group:
                        embedding_api = gr.Textbox(
                            value=config['GPT']['RAG']['embedding']['api_endpoint'],
                            label="Embedding API端点"
                        )
                        embedding_model = gr.Textbox(
                            value=config['GPT']['RAG']['embedding']['model'],
                            label="Embedding模型"
                        )
                        embedding_api_key = gr.Textbox(
                            value=config['GPT']['RAG']['embedding']['api_key'],
                            label="API密钥"
                        )
                        top_k = gr.Number(
                            value=config['GPT']['RAG']['top_k'],
                            label="检索文档数量",
                            precision=0
                        )
                    
                    rag_enable.change(
                        fn=lambda x: gr.Group(visible=x),
                        inputs=rag_enable,
                        outputs=rag_group
                    )
                
                # 绑定GPT预设配置相关事件
                gpt_preset_refresh.click(
                    fn=lambda: refresh_preset_configs("gpt"),
                    outputs=gpt_preset_dropdown
                )
                
                gpt_preset_load.click(
                    fn=load_gpt_preset,
                    inputs=gpt_preset_dropdown,
                    outputs=[gpt_type, gpt_api, gpt_request_header, gpt_request_body, 
                             rag_enable, embedding_api, embedding_model, embedding_api_key, 
                             top_k, gpt_preset_message]
                )
                
                gpt_preset_save.click(
                    fn=save_gpt_preset,
                    inputs=[gpt_type, gpt_api, gpt_request_header, gpt_request_body,
                            rag_enable, embedding_api, embedding_model, embedding_api_key,
                            top_k, gpt_preset_name],
                    outputs=[gpt_preset_message, gpt_preset_dropdown]
                )
                
        # TTS配置
        with gr.TabItem("TTS配置"):
            with gr.Group():
                # 预设配置管理
                with gr.Accordion("预设配置管理", open=True):
                    with gr.Row():
                        tts_preset_files = get_preset_configs("tts")
                        tts_preset_dropdown = gr.Dropdown(
                            choices=tts_preset_files,
                            value=config['TTS'].get('pre_config', None),
                            label="预设配置文件"
                        )
                        tts_preset_name = gr.Textbox(label="保存为")
                    
                    with gr.Row():
                        tts_preset_refresh = gr.Button("刷新", variant="primary", size="lg")
                        tts_preset_load = gr.Button("加载预设", variant="primary", size="lg")
                        tts_preset_save = gr.Button("保存预设", variant="primary", size="lg")
                    
                    tts_preset_message = gr.Textbox(label="预设操作结果")
                
                # 其他TTS配置
                tts_type = gr.Radio(
                    choices=["gptsovits", "chumenwenwen"],
                    value=config['TTS']['type'],
                    label="TTS类型"
                )
                tts_api = gr.Textbox(
                    value=config['TTS']['api_endpoint'],
                    label="API端点"
                )
                tts_request_header = gr.Code(
                    value=json.dumps(config['TTS']['request_header'], indent=2, ensure_ascii=False),
                    language="json",
                    label="请求头配置(JSON)"
                )
                tts_request_body = gr.Code(
                    value=json.dumps(config['TTS']['request_body'], indent=2, ensure_ascii=False),
                    language="json",
                    label="请求体配置(JSON)"
                )
                
                # 绑定TTS预设配置相关事件
                tts_preset_refresh.click(
                    fn=lambda: refresh_preset_configs("tts"),
                    outputs=tts_preset_dropdown
                )
                
                tts_preset_load.click(
                    fn=load_tts_preset,
                    inputs=tts_preset_dropdown,
                    outputs=[tts_type, tts_api, tts_request_header, tts_request_body, tts_preset_message]
                )
                
                tts_preset_save.click(
                    fn=save_tts_preset,
                    inputs=[tts_type, tts_api, tts_request_header, tts_request_body, tts_preset_name],
                    outputs=[tts_preset_message, tts_preset_dropdown]
                )
        
        # ASR配置
        with gr.TabItem("语音识别配置"):
            with gr.Group():
                asr_enable = gr.Checkbox(
                    value=config['ASR']['enable'],
                    label="启用语音识别"
                )
                
                with gr.Group(visible=config['ASR']['enable']) as asr_settings_group:
                    asr_mode = gr.Radio(
                        choices=["wake", "realtime"],
                        value=config['ASR']['mode'],
                        label="识别模式"
                    )
                    
                    with gr.Group(visible=config['ASR']['mode'] == "wake") as wake_words_group:
                        wake_words = gr.Textbox(
                            value=config['ASR']['wake_words'],
                            label="唤醒词（用逗号分隔）"
                        )
                    asr_mode.change(
                        fn=lambda x: gr.Group(visible=(x == "wake")),
                        inputs=asr_mode,
                        outputs=wake_words_group
                    )
                    
                    timeout = gr.Number(
                        value=config['ASR']['timeout'],
                        label="超时时间（秒）"
                    )
                    
                    with gr.Accordion("FunASR配置"):
                        funasr_ip = gr.Textbox(
                            value=config['ASR']['FunASR']['ip'],
                            label="IP"
                        )
                        funasr_port = gr.Number(
                            value=config['ASR']['FunASR']['port'],
                            label="Port",
                            precision=0
                        )
                        funasr_ssl = gr.Checkbox(
                            value=bool(config['ASR']['FunASR']['ssl']),
                            label="启用SSL"
                        )
                        funasr_mode = gr.Textbox(
                            value=config['ASR']['FunASR']['mode'],
                            label="模式"
                        )
                
                asr_enable.change(
                    fn=lambda x: gr.Group(visible=x),
                    inputs=asr_enable,
                    outputs=asr_settings_group
                )
        
        # 播放器配置
        with gr.TabItem("播放器配置"):
            with gr.Group():
                player_mode = gr.Radio(
                    choices=["local", "audio2face"],
                    value=config['Player']['mode'],
                    label="播放器模式"
                )

                with gr.Accordion("Audio2Face配置", visible=config['Player']['mode'] == "audio2face") as a2f_config_group:
                    a2f_url = gr.Textbox(
                        value=config['Player']['Audio2Face']['url'],
                        label="Audio2Face URL"
                    )
                    a2f_player = gr.Textbox(
                        value=config['Player']['Audio2Face']['player'],
                        label="Audio2Face播放器路径"
                    )
                player_mode.change(
                    fn=lambda x: gr.update(visible=(x == "audio2face")),
                    inputs=player_mode,
                    outputs=a2f_config_group
                )
    
    # 单一保存按钮
    save_button = gr.Button("保存所有配置", variant="primary", size="lg")
    save_output = gr.Textbox(label="保存结果")
    
    save_button.click(
        fn=save_all_configs,
        inputs=[
            # 基本配置
            log_level, host, port,
            # GPT配置
            gpt_type, gpt_api, gpt_preset_dropdown, gpt_request_header, gpt_request_body,
            rag_enable, embedding_api, embedding_model, embedding_api_key, top_k,
            # TTS配置
            tts_type, tts_api, tts_preset_dropdown, tts_request_header, tts_request_body,
            # ASR配置
            asr_enable, asr_mode, wake_words, timeout,
            funasr_ip, funasr_port, funasr_ssl, funasr_mode,
            # 播放器配置
            player_mode, a2f_url, a2f_player
        ],
        outputs=save_output
    )
