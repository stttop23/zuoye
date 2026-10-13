/**
 * 语音输入（浏览器自带能力）
 * ========================
 * 用的是 Web Speech API（`webkitSpeechRecognition`），不装任何依赖、不花钱。
 *
 * ⚠️ 三件必须知道的事，别把它当成「本机识别」：
 *
 * 1. **只有 Chrome / Edge 有**。Firefox 至今没实现，**Safari 也没实现**
 *    （MDN 兼容性表：Chrome ✅ Edge ✅ Firefox ❌ Safari ❌）。
 *    → 所以【iPhone 上的任何浏览器都用不了语音】，这不是配置问题，是没这个能力；
 *      开 HTTPS 也救不了。Firefox 同理。
 * 2. **它不是离线识别**：音频要发到浏览器厂商的服务器（Edge → 微软，Chrome → Google）。
 *    所以它和「模型跑在本机、数据不出机器」是**两回事**——这一点在答辩时别讲错。
 *    真要做到离线，得另接本地 Whisper，那是另一套东西。
 * 3. **没网就废**。它认不出来时会报 `network` 错误，我们已经翻译成人话提示。
 *
 * ⚠️ 手机上还多一层坑：Chrome for Android 的识别会话会被静音/熄屏打断，
 *    而且**麦克风不是马上释放的** —— 旧会话刚结束就立刻 `start()`，
 *    会直接报 `audio-capture`（用户看到的就是「录音被占用」）。
 *    所以续听必须**隔一小会儿**，且失败要允许重试（见下面的 RESTART_DELAY / 重试逻辑）。
 */
import { onBeforeUnmount, ref } from 'vue'

const ERROR_MESSAGES = {
  'not-allowed': '没有麦克风权限。点地址栏左边的锁图标，把「麦克风」改成允许。',
  'service-not-allowed': '浏览器拒绝了语音服务，检查一下麦克风权限。',
  'audio-capture': '麦克风被占用了（可能有别的 App 在录音，或者刚停就又开了）。',
  network: '语音识别连不上网。注意：它不是本机识别的，需要联网。',
}

/**
 * 续听前等多久（毫秒）。
 * ⚠️ 不能是 0：浏览器（尤其安卓）释放麦克风需要一点点时间，
 * 立刻重启会报 audio-capture。这不是我拍的 —— 安卓实测到的。
 */
const RESTART_DELAY = 400

/** audio-capture / network 这类是「环境抖了一下」，不是致命错误，给它几次机会 */
const RETRYABLE_ERRORS = new Set(['audio-capture', 'network'])
const MAX_RETRY = 3

/**
 * @param {object} options
 * @param {string} [options.lang] 识别语言，默认普通话
 * @param {(text: string) => void} [options.onText] 每识别出一段就回调（含临时结果）
 * @param {(message: string) => void} [options.onError] 出错时回调一句人话
 */
export function useSpeechInput({ lang = 'zh-CN', onText, onError } = {}) {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
  /*
   * ⚠️ 这里必须是 ref，不能写成普通布尔值。
   * 之前写成 `const supported = Boolean(Recognition)`，结果调用方在脚本里
   * 写 `voiceSupported.value` 会取到 `undefined`（布尔值没有 .value），
   * `!undefined` 恒为 true → 每次调用都静默提前返回，功能“点了没反应”。
   * 返回值里三个都是 ref，调用方脚本里统一 `.value`、模板里不用写。
   */
  const supported = ref(Boolean(Recognition))

  const listening = ref(false)

  let recognition = null
  let base = '' // 开始说话时输入框里已有的内容，识别结果接在它后面
  let finalText = '' // 本次已经「确定」的文字
  let fatal = false // 遇到致命错误就不再自动续听，免得死循环
  let retries = 0 // 本次录音里重试了几次
  let restartTimer = null // 续听的定时器，stop() 时要清掉

  function ensure() {
    if (recognition || !supported.value) return recognition

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
      /*
       * audio-capture / network 先重试。
       * 手机上第一次长按经常就是这个错（旧会话还没放开麦克风），
       * 一上来就判死刑的话，用户的感觉是「刚按两下就坏了」。
       */
      if (RETRYABLE_ERRORS.has(event.error) && retries < MAX_RETRY) {
        retries += 1
        return // 交给 onend 里的延迟续听
      }
      fatal = true
      onError?.(ERROR_MESSAGES[event.error] || `语音识别出错：${event.error}`)
    }

    recognition.onend = () => {
      if (!listening.value || fatal) {
        if (fatal) listening.value = false
        return
      }
      /*
       * 就算设了 continuous，浏览器也会因为静默 / 熄屏自己停 → 不致命就接着听。
       * ⚠️ 必须【隔一会儿】再 start：麦克风还没释放就重启，安卓直接报
       * audio-capture（用户看到「录音被占用」）。这个坑是安卓真机实测出来的。
       */
      clearTimeout(restartTimer)
      restartTimer = setTimeout(() => {
        if (!listening.value) return
        try {
          recognition.start()
        } catch {
          listening.value = false
        }
      }, RESTART_DELAY)
    }

    return recognition
  }

  function start(existing = '') {
    if (!supported.value || listening.value) return
    const instance = ensure()
    const prefix = existing.trim()
    base = prefix ? `${prefix}，` : ''
    finalText = ''
    fatal = false
    retries = 0

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
    clearTimeout(restartTimer) // 把排着的「续听」取消掉，否则停止后它又把麦克风打开
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
