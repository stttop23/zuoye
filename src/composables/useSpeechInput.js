/**
 * 语音输入（浏览器自带能力）
 * ========================
 * 用的是 Web Speech API（`webkitSpeechRecognition`），不装任何依赖、不花钱。
 *
 * ⚠️ 三件必须知道的事，别把它当成「本机识别」：
 *
 * 1. **只有 Chrome / Edge 有**。Firefox 至今没实现，所以不支持时按钮要置灰。
 * 2. **它不是离线识别**：音频要发到浏览器厂商的服务器（Edge → 微软，Chrome → Google）。
 *    所以它和「模型跑在本机、数据不出机器」是**两回事**——这一点在答辩时别讲错。
 *    真要做到离线，得另接本地 Whisper，那是另一套东西。
 * 3. **没网就废**。它认不出来时会报 `network` 错误，我们已经翻译成人话提示。
 */
import { onBeforeUnmount, ref } from 'vue'

const ERROR_MESSAGES = {
  'not-allowed': '没有麦克风权限。点地址栏左边的锁图标，把「麦克风」改成允许。',
  'service-not-allowed': '浏览器拒绝了语音服务，检查一下麦克风权限。',
  'audio-capture': '找不到麦克风设备，看看是不是没插好或被别的程序占用了。',
  network: '语音识别连不上网。注意：它不是本机识别的，需要联网。',
}

/**
 * @param {object} options
 * @param {string} [options.lang] 识别语言，默认普通话
 * @param {(text: string) => void} [options.onText] 每识别出一段就回调（含临时结果）
 * @param {(message: string) => void} [options.onError] 出错时回调一句人话
 */
export function useSpeechInput({ lang = 'zh-CN', onText, onError } = {}) {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
  const supported = Boolean(Recognition)

  const listening = ref(false)

  let recognition = null
  let base = '' // 开始说话时输入框里已有的内容，识别结果接在它后面
  let finalText = '' // 本次已经「确定」的文字
  let fatal = false // 遇到致命错误就不再自动续听，免得死循环

  function ensure() {
    if (recognition || !supported) return recognition

    recognition = new Recognition()
    recognition.lang = lang
    recognition.continuous = true
    recognition.interimResults = true
    recognition.maxAlternatives = 1

    recognition.onresult = (event) => {
      let interim = ''
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i]
        if (result.isFinal) finalText += result[0].transcript
        else interim += result[0].transcript
      }
      onText?.(`${base}${finalText}${interim}`)
    }

    recognition.onerror = (event) => {
      // 这两类是「正常现象」，别弹提示烦用户
      if (event.error === 'no-speech' || event.error === 'aborted') return
      fatal = true
      onError?.(ERROR_MESSAGES[event.error] || `语音识别出错：${event.error}`)
    }

    recognition.onend = () => {
      if (!listening.value) return
      if (fatal) {
        listening.value = false
        return
      }
      // 就算设了 continuous，浏览器也会因为静默超时自己停 → 不致命就接着听
      try {
        recognition.start()
      } catch {
        listening.value = false
      }
    }

    return recognition
  }

  function start(existing = '') {
    if (!supported || listening.value) return
    const instance = ensure()
    const prefix = existing.trim()
    base = prefix ? `${prefix}，` : ''
    finalText = ''
    fatal = false

    try {
      instance.start()
      listening.value = true
    } catch {
      onError?.('麦克风启动失败，可能被别的程序占用了。')
    }
  }

  function stop() {
    if (!listening.value) return
    listening.value = false // 先置 false，onend 就不会再自动续听
    try {
      recognition?.stop()
    } catch {
      // 已经停了就不用管
    }
  }

  /** 点一下开始、再点一下停止 */
  function toggle(existing = '') {
    if (listening.value) stop()
    else start(existing)
  }

  // 组件卸载（或离开页面）时一定要把麦克风关掉，不然浏览器会一直亮着录音图标
  onBeforeUnmount(stop)

  return { supported, listening, start, stop, toggle }
}
