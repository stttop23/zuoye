r"""
本机语音转文字（faster-whisper）
================================

为什么有这个文件：
    项目原来用的是【浏览器自带】的语音识别（Web Speech API）。
    它有个说不圆的地方：**音频要发到 Google / 微软的服务器**去认。
    也就是说「模型跑在本机、数据不出这台机器」这句话，在语音这一环是破的。

    这个文件把语音识别也搬回本机：OpenAI 开源的 Whisper 模型，权重下载到自己电脑上跑。
    接上之后整条链路就闭环了：

        麦克风 → 浏览器录成音频 → 本机 Flask → 本机 Whisper 转文字 → 输入框
                 （不出这台机器）        （不出这台机器）      （不出这台机器）

⚠️ 和浏览器的那个比，有一个体验上的取舍，必须知道：
    浏览器版是**边说边出字**（流式，一个字一个字蹦出来）；
    Whisper 是**说完再转**（整段录完，停 1-2 秒，一次出全部）。
    前者好看，后者私密。我们两个都留着，让用户自己挑。

⚠️ 依赖：`pip install faster-whisper`
    它自带 PyAV（ffmpeg 的 Python 绑定），所以**不需要另外装 ffmpeg**。
    浏览器录出来的是 webm/opus，PyAV 直接能解，不用先转成 wav。

⚠️⚠️ 换台机器时留意一个坑：**模型可能「下载成功」但文件是 0 字节。**
    第一次跑会自动从 HuggingFace 下 medium（1.5GB）。
    实测遇到过一次：`model.bin` 正常，但 `config.json` / `tokenizer.json` /
    `vocabulary.txt` 全是 0 字节（连同缓存里的 blobs 也是 0），
    **而且下载过程不报任何错** —— 直到加载模型才抛一句莫名其妙的
    `json.exception.parse_error ... unexpected end of input`。
    症状：`WhisperModel(...)` 抛 RuntimeError，提到 json parse error。
    救法（model.bin 不用重下）：
        # 先把小文件用普通 HTTP 直接拉下来，覆盖掉那 0 字节的
        $snap = "$env:USERPROFILE\.cache\huggingface\hub\models--Systran--faster-whisper-medium\snapshots\<那串哈希>"
        $base = "https://huggingface.co/Systran/faster-whisper-medium/resolve/main"
        foreach ($f in 'config.json','tokenizer.json','vocabulary.txt') {
          Invoke-WebRequest "$base/$f" -OutFile (Join-Path $snap $f) -MaximumRedirection 8
        }
    缓存目录里没有 `preprocessor_config.json` 是正常的，那个仓库就没有。

⚠️ 设备选择：默认走 CPU + int8。
    没走 GPU 是刻意的 —— ctranslate2 要用上 CUDA，得额外装好几个 GB 的
    CUDA / cuDNN 运行库，而且新显卡（Blackwell 那代）还需要足够新的版本，
    很容易卡在「装了半天跑不起来」。CPU 上 medium 已经够演示用了。
    真要试 GPU：把 ASR_DEVICE 设成 cuda、ASR_COMPUTE_TYPE 设成 float16。
"""

import io
import os
import threading
import time

# 模型档位：tiny / base / small / medium / large-v3。
# 中文别用 tiny / base（基本没法看），small 起步，medium 更稳。
ASR_MODEL = os.getenv("ASR_MODEL", "medium")
ASR_DEVICE = os.getenv("ASR_DEVICE", "cpu")
ASR_COMPUTE_TYPE = os.getenv("ASR_COMPUTE_TYPE", "int8" if ASR_DEVICE == "cpu" else "float16")

# 搜索宽度。5 = 更准但更慢；1 = 贪心解码，快将近一倍，短句子上差别很小。
# 觉得识别慢就把它调成 1（实测数据见 README）。
ASR_BEAM_SIZE = int(os.getenv("ASR_BEAM_SIZE", "5"))

# 给模型一点上下文，让它倾向输出带标点的简体中文。
# ⚠️ 这段文字有被「照着抄出来」的风险（静音时模型会拿提示词当结果），
#    所以下面 _is_prompt_echo() 专门挡这种情况。
INITIAL_PROMPT = "以下是一段普通话的句子，请用简体中文转写。"

# Whisper 只认这个采样率，解码时统一重采样到这里
SAMPLE_RATE = 16000

_model = None
_load_seconds = None
_lock = threading.Lock()


def load_model():
    """
    第一次调用时才加载（懒加载）。

    为什么不写在模块顶层：模型从硬盘读进来要好几秒，
    放在顶层会让 `import` 变慢，而且万一模型文件还没下好，整个服务都起不来。
    懒加载之后：服务秒起，第一次请求慢一点，之后一直快。
    """
    global _model, _load_seconds

    if _model is not None:
        return _model

    # 双检锁：两个请求同时打进来时，别把模型加载两遍（吃内存也吃时间）
    with _lock:
        if _model is not None:
            return _model

        from faster_whisper import WhisperModel  # 放这里：没装这个包也不影响别的接口

        started = time.time()
        _model = WhisperModel(ASR_MODEL, device=ASR_DEVICE, compute_type=ASR_COMPUTE_TYPE)
        _load_seconds = round(time.time() - started, 1)
        print(f"[ASR] 模型已加载：{ASR_MODEL} / {ASR_DEVICE} / {ASR_COMPUTE_TYPE}（{_load_seconds}s）")
        return _model


def model_info():
    """给状态接口用：让前端能显示「现在用的是哪个模型、跑在哪」。"""
    return {
        "model": ASR_MODEL,
        "device": ASR_DEVICE,
        "compute_type": ASR_COMPUTE_TYPE,
        "beam_size": ASR_BEAM_SIZE,
        "loaded": _model is not None,
        "load_seconds": _load_seconds,
    }


def warm_up():
    """
    启动后在后台把模型加载好，并空跑一次。

    为什么要空跑：实测「进程里的第一次推理」特别慢（同一个进程里
    第一遍 19s、之后 4-5s），因为 ctranslate2 要初始化线程池和 int8 的运算内核。
    不预热的话，这个代价正好落在答辩时你说的第一句话上 —— 最不该慢的一刻。

    ⚠️ 这个函数要放在后台线程里调，别阻塞服务启动。
    """
    try:
        import numpy as np  # 只为造一段静音

        model = load_model()
        silence = np.zeros(SAMPLE_RATE, dtype=np.float32)  # 1 秒静音
        segments, _ = model.transcribe(silence, language="zh", beam_size=1, vad_filter=False)
        list(segments)  # 生成器不迭代就什么都没发生
        print("[ASR] 预热完成，模型随时可用")
    except Exception as error:  # noqa: BLE001  预热失败不该影响别的功能
        print(f"[ASR] 预热失败（不影响使用）：{error}")



def _is_prompt_echo(text):
    """
    判断这句是不是把提示词抄回来了。

    踩过的坑：Whisper 在【几乎没声音】的音频上会自己编一段话，而它最常编的
    就是 initial_prompt 里那句。所以结果如果和提示词高度重合，就当没听见。
    （宁可说「没听清」，也不能凭空冒出一句用户没说过的话 —— 后者最伤可信度。）
    """
    if not text:
        return True
    plain = lambda s: "".join(ch for ch in s if ch not in "，。、！？,.!? ")
    return plain(text) in plain(INITIAL_PROMPT)


def decode_audio(data):
    """
    把音频字节解成 16kHz 单声道 float32 数组 —— 这是 Whisper 要的格式。

    ⚠️ 为什么要自己解码，而不是直接把字节丢给 model.transcribe()：
        faster-whisper 内部会调 `av.open(..., metadata_errors="ignore")`，
        但 **PyAV 19 把这个参数去掉了**，于是直接抛
        `TypeError: open() got an unexpected keyword argument 'metadata_errors'`。
        而 PyAV 14 那条老线又没有 Python 3.12 的预编译包（装的时候要现场编译，失败）。

        与其把某个第三方库钉死在某个版本上（以后别人一升级就炸），
        不如自己解码：PyAV 的基础 API（av.open / decode / 重采样）几个大版本都没变过，
        拿在手里稳定。顺带还能自己算出音频时长，不依赖库的内部实现。
    """
    import av
    import numpy as np

    with av.open(io.BytesIO(data), mode="r") as container:
        stream = next((item for item in container.streams if item.type == "audio"), None)
        if stream is None:
            raise ValueError("这段文件里没有音频轨")

        resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
        pieces = []

        for frame in container.decode(stream):
            pieces.extend(_as_list(resampler.resample(frame)))
        # ⚠️ 必须再冲一次：最后几帧还压在重采样器里，不 flush 会丢掉尾音
        pieces.extend(_as_list(resampler.resample(None)))

    if not pieces:
        raise ValueError("没解出音频数据")

    samples = np.concatenate([frame.to_ndarray().reshape(-1) for frame in pieces])
    return samples.astype(np.float32) / 32768.0  # int16 → [-1, 1]


def _as_list(value):
    """PyAV 不同版本里 resample() 可能返回一帧、一个列表或 None，统一成列表。"""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def transcribe(data, language="zh"):
    """
    把一段音频字节转成文字。

    @param data: 音频文件的原始字节（浏览器录的 webm/opus、wav、mp3 都行）
    @returns: {ok, text, seconds, audio_seconds, ...}
    """
    if not data:
        return {"ok": False, "error": "没有收到音频数据"}

    model = load_model()
    pcm = decode_audio(data)
    audio_seconds = round(len(pcm) / SAMPLE_RATE, 2)

    started = time.time()

    # transcribe 返回的是【生成器】—— 真正的识别发生在下面 for 循环里，
    # 所以计时要包住整个循环，不能只包住这一行。
    segments, info = model.transcribe(
        pcm,
        language=language,
        beam_size=ASR_BEAM_SIZE,
        vad_filter=True,  # 先用 VAD 掐掉静音段：又准又省时间
        initial_prompt=INITIAL_PROMPT,
    )
    text = "".join(segment.text for segment in segments).strip()

    if _is_prompt_echo(text):
        text = ""

    return {
        "ok": True,
        "text": text,
        "seconds": round(time.time() - started, 2),  # 识别本身花了多久
        "audio_seconds": audio_seconds,  # 这段音频多长
        "language": getattr(info, "language", language),
        **model_info(),
    }
