<!--
  MiMo TTS 语音合成页面

  功能概述：
  - 支持三个 TTS 模型切换（内置音色 / 声音设计 / 声音克隆）
  - 通过后端代理调用 MiMo API，解决浏览器跨域限制
  - API Key 存放在后端 .env 中，前端无需暴露

  API 调用流程：
  前端 -> POST /api/tts -> Express 代理 -> MiMo API -> 返回 Base64 音频 -> 前端播放
-->
<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import lamejs from 'lamejs'

// ========================================
// 主题切换逻辑
// ========================================
const themes = [
  { id: 'neo-brutalism', name: 'Neo-Brutalism', icon: '🔥' },
  { id: 'soft-ui', name: 'Soft UI', icon: '☁️' },
  { id: 'claymorphism', name: 'Claymorphism', icon: '🎨' },
  { id: 'cyber-neon', name: 'Cyber Neon', icon: '⚡' }
]
const currentTheme = ref('neo-brutalism')

onMounted(() => {
  const savedTheme = localStorage.getItem('mimo-theme')
  if (savedTheme && themes.some(t => t.id === savedTheme)) {
    currentTheme.value = savedTheme
  }
})

watch(currentTheme, (newTheme) => {
  document.documentElement.setAttribute('data-theme', newTheme)
  localStorage.setItem('mimo-theme', newTheme)
}, { immediate: true })

// ========================================
// 模型配置数据
// 根据 MiMo TTS V2.5 文档定义的三个模型
// ========================================
const models = [
  {
    id: 'mimo-v2.5-tts',
    name: 'MiMo-V2.5-TTS',
    desc: '使用内置高品质音色进行语音合成，支持唱歌模式',
    hasVoiceSelect: true,       // 需要选择内置音色
    hasVoiceDesign: false,
    hasVoiceClone: false
  },
  {
    id: 'mimo-v2.5-tts-voicedesign',
    name: 'VoiceDesign',
    desc: '通过文字描述自定义音色，无需预设或音频样本',
    hasVoiceSelect: false,
    hasVoiceDesign: true,       // 需要输入音色描述
    hasVoiceClone: false
  },
  {
    id: 'mimo-v2.5-tts-voiceclone',
    name: 'VoiceClone',
    desc: '从音频样本精准复制音色，实现任意声音的语音合成',
    hasVoiceSelect: false,
    hasVoiceDesign: false,
    hasVoiceClone: true          // 需要上传音频样本
  }
]

// ========================================
// 内置音色列表
// 来自 MiMo TTS V2.5 文档的内置音色
// ========================================
const voices = [
  { id: 'mimo_default', name: 'MiMo-默认', lang: '中文', gender: '' },
  { id: '冰糖', name: '冰糖', lang: '中文', gender: '女声' },
  { id: '茉莉', name: '茉莉', lang: '中文', gender: '女声' },
  { id: '苏打', name: '苏打', lang: '中文', gender: '男声' },
  { id: '白桦', name: '白桦', lang: '中文', gender: '男声' },
  { id: 'Mia', name: 'Mia', lang: 'English', gender: 'Female' },
  { id: 'Chloe', name: 'Chloe', lang: 'English', gender: 'Female' },
  { id: 'Milo', name: 'Milo', lang: 'English', gender: 'Male' },
  { id: 'Dean', name: 'Dean', lang: 'English', gender: 'Male' }
]

// ========================================
// API Key 管理
// 页面输入的 key 存 localStorage，优先于环境变量
// ========================================
const apiKey = ref('')
const showApiKey = ref(false)

onMounted(() => {
  const savedKey = localStorage.getItem('mimo-api-key')
  if (savedKey) {
    apiKey.value = savedKey
  }
})

watch(apiKey, (val) => {
  localStorage.setItem('mimo-api-key', val)
})

// ========================================
// 响应式状态
// ========================================
const currentModel = ref('mimo-v2.5-tts')       // 当前选中的模型 ID
const selectedVoice = ref('苏打')                // 当前选中的内置音色 ID
const voiceDesignPrompt = ref('')                // VoiceDesign 的音色描述文本
const voiceCloneFile = ref(null)                 // VoiceClone 上传的音频文件
const voiceCloneBase64 = ref('')                 // VoiceClone 音频的 Base64 编码
const styleInstruction = ref('用春晚主持人那种热情洋溢、喜庆祥和的语调，声音洪亮饱满，充满感染力和节日氛围，语速适中偏快，情绪层层递进，最后达到高潮')
const synthesisText = ref('亲爱的观众朋友们，大家过年好！在这辞旧迎新的美好时刻，我们欢聚一堂，共同迎接新年的到来！回首过去的一年，我们风雨同舟、砥砺前行；展望新的一年，我们满怀信心、豪情万丈！让我们一起倒计时，十、九、八、七、六、五、四、三、二、一！新年快乐！祝大家万事如意、阖家幸福、龙马精神、大吉大利！')
const loading = ref(false)                       // 是否正在合成中
const errorMsg = ref('')                         // 错误信息
const audioUrl = ref('')                         // 合成后的音频 Blob URL
const wavBlob = ref(null)                        // 原始 WAV Blob（用于下载）
const converting = ref(false)                    // MP3 转换中

// 计算属性：当前模型的配置对象
const currentModelConfig = computed(() => {
  return models.find(m => m.id === currentModel.value)
})

// ========================================
// 选择模型
// 更新当前模型并重置相关状态
// ========================================
function selectModel(modelId) {
  currentModel.value = modelId
  // 切换模型时清除错误信息
  errorMsg.value = ''
}

// ========================================
// 处理 VoiceClone 音频文件上传
// 支持 mp3/wav 直接读取，mp4 自动提取音频转为 wav
// ========================================
function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) {
    voiceCloneFile.value = null
    voiceCloneBase64.value = ''
    return
  }

  voiceCloneFile.value = file

  const isVideo = file.type.startsWith('video/')

  if (isVideo) {
    // mp4 等视频格式：提取音频转为 wav
    convertVideoToWav(file)
  } else {
    // mp3/wav 等音频格式：直接读取
    console.log('[VoiceClone] 音频文件:', file.name, '类型:', file.type, '大小:', (file.size / 1024 / 1024).toFixed(2), 'MB')
    const reader = new FileReader()
    reader.onload = (e) => {
      console.log('[VoiceClone] 音频读取完成, Base64 长度:', e.target.result.length)
      voiceCloneBase64.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

// ========================================
// 将视频文件（mp4）转为 WAV Base64
// 直接用 AudioContext.decodeAudioData 解码，无需实时播放
// ========================================
async function convertVideoToWav(file) {
  loading.value = true
  errorMsg.value = ''
  console.log('[VoiceClone] 开始处理视频文件:', file.name, '大小:', (file.size / 1024 / 1024).toFixed(2), 'MB')

  try {
    const arrayBuffer = await file.arrayBuffer()
    console.log('[VoiceClone] 文件读取完成, 大小:', arrayBuffer.byteLength, 'bytes')

    const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    console.log('[VoiceClone] AudioContext 创建成功, 开始解码...')

    let audioBuffer
    try {
      audioBuffer = await audioCtx.decodeAudioData(arrayBuffer)
      console.log('[VoiceClone] 直接解码成功, 采样率:', audioBuffer.sampleRate, '时长:', audioBuffer.duration.toFixed(2), 's')
    } catch (decodeErr) {
      console.warn('[VoiceClone] 直接解码失败, 尝试用 video 元素提取:', decodeErr.message)
      audioCtx.close()
      audioBuffer = await extractAudioViaVideoElement(file)
    }
    if (audioCtx.state !== 'closed') audioCtx.close()

    const wavBase64 = audioBufferToWavBase64(audioBuffer)
    console.log('[VoiceClone] WAV 转换完成, Base64 长度:', wavBase64.length)
    voiceCloneBase64.value = wavBase64

  } catch (err) {
    console.error('[VoiceClone] 失败:', err)
    errorMsg.value = '视频音频提取失败: ' + err.message
    voiceCloneBase64.value = ''
  } finally {
    loading.value = false
  }
}

// ========================================
// AudioBuffer 转 WAV Base64
// ========================================
// ========================================
// Fallback: 用 video 元素实时播放提取音频
// 当 decodeAudioData 无法直接解码视频容器时使用
// ========================================
function extractAudioViaVideoElement(file) {
  return new Promise((resolve, reject) => {
    console.log('[VoiceClone] 使用 video 元素提取音频...')
    const videoUrl = URL.createObjectURL(file)
    const video = document.createElement('video')
    video.src = videoUrl
    video.muted = false
    video.crossOrigin = 'anonymous'

    video.onloadedmetadata = () => {
      console.log('[VoiceClone] 视频时长:', video.duration.toFixed(2), 's')
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      const source = audioCtx.createMediaElementSource(video)
      const destination = audioCtx.createMediaStreamDestination()
      source.connect(destination)
      source.connect(audioCtx.destination)

      const mediaRecorder = new MediaRecorder(destination.stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm'
      })
      const chunks = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data)
      }

      mediaRecorder.onstop = async () => {
        console.log('[VoiceClone] 录制完成, 解码中...')
        URL.revokeObjectURL(videoUrl)
        try {
          const webmBlob = new Blob(chunks, { type: 'audio/webm' })
          const buf = await webmBlob.arrayBuffer()
          const decodeCtx = new (window.AudioContext || window.webkitAudioContext)()
          const ab = await decodeCtx.decodeAudioData(buf)
          decodeCtx.close()
          console.log('[VoiceClone] 解码完成, 时长:', ab.duration.toFixed(2), 's')
          resolve(ab)
        } catch (e) {
          reject(e)
        }
      }

      video.onended = () => {
        console.log('[VoiceClone] 播放结束, 停止录制')
        mediaRecorder.stop()
        audioCtx.close()
      }

      mediaRecorder.start()
      video.play().catch(reject)
    }

    video.onerror = () => reject(new Error('无法加载视频文件'))
    setTimeout(() => reject(new Error('视频加载超时')), 30000)
  })
}

function audioBufferToWavBase64(audioBuffer) {
  const numChannels = 1 // 单声道
  const sampleRate = audioBuffer.sampleRate
  const format = 1 // PCM
  const bitDepth = 16

  // 取第一个声道的数据
  const samples = audioBuffer.getChannelData(0)
  const dataLength = samples.length * (bitDepth / 8)
  const buffer = new ArrayBuffer(44 + dataLength)
  const view = new DataView(buffer)

  // WAV 文件头
  writeString(view, 0, 'RIFF')
  view.setUint32(4, 36 + dataLength, true)
  writeString(view, 8, 'WAVE')
  writeString(view, 12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, format, true)
  view.setUint16(22, numChannels, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * numChannels * (bitDepth / 8), true)
  view.setUint16(32, numChannels * (bitDepth / 8), true)
  view.setUint16(34, bitDepth, true)
  writeString(view, 36, 'data')
  view.setUint32(40, dataLength, true)

  // 写入 PCM 数据
  let offset = 44
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]))
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
    offset += 2
  }

  // 转为 Base64
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return 'data:audio/wav;base64,' + btoa(binary)
}

function writeString(view, offset, str) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i))
  }
}

// ========================================
// 核心函数：调用 TTS API 进行语音合成
//
// 请求流程：
// 1. 前端构建请求体（与 MiMo API 格式一致）
// 2. POST 到 /api/tts（Vite 代理 -> Express 后端）
// 3. Express 后端附加 API Key，转发到 MiMo API
// 4. MiMo API 返回 Base64 音频数据
// 5. 前端解码并播放
// ========================================
async function synthesize() {
  errorMsg.value = ''
  audioUrl.value = ''

  // --- 1. 校验合成文本 ---
  if (!synthesisText.value.trim()) {
    errorMsg.value = '请输入要合成的文本'
    return
  }

  // --- 2. 校验 VoiceDesign 的音色描述 ---
  if (currentModel.value === 'mimo-v2.5-tts-voicedesign' && !voiceDesignPrompt.value.trim()) {
    errorMsg.value = 'VoiceDesign 模型需要输入音色描述'
    return
  }

  // --- 3. 校验 VoiceClone 的音频文件 ---
  if (currentModel.value === 'mimo-v2.5-tts-voiceclone' && !voiceCloneBase64.value) {
    errorMsg.value = '请上传音频样本用于声音克隆'
    return
  }

  // --- 4. 构建请求体 ---
  // 请求体格式与 MiMo API 一致：{ model, messages, audio }
  const body = {
    model: currentModel.value,
    messages: [],
    audio: { format: 'wav' }
  }

  // 4a. 添加 user 角色消息（风格指令 / 音色描述）
  // - VoiceDesign: user 消息是音色描述（必填）
  // - 其他模型: user 消息是风格控制指令（可选）
  if (currentModel.value === 'mimo-v2.5-tts-voicedesign') {
    body.messages.push({
      role: 'user',
      content: voiceDesignPrompt.value.trim()
    })
  } else if (styleInstruction.value.trim()) {
    body.messages.push({
      role: 'user',
      content: styleInstruction.value.trim()
    })
  }

  // 4b. 添加 assistant 角色消息（要合成的文本，必填）
  body.messages.push({
    role: 'assistant',
    content: synthesisText.value.trim()
  })

  // 4c. 根据模型类型设置 voice 参数
  if (currentModel.value === 'mimo-v2.5-tts') {
    // 内置音色模型：voice 为音色 ID 字符串
    body.audio.voice = selectedVoice.value
  } else if (currentModel.value === 'mimo-v2.5-tts-voiceclone') {
    // 声音克隆模型：voice 为 data:audio/xxx;base64,... 格式的音频数据
    body.audio.voice = voiceCloneBase64.value
  }
  // VoiceDesign 模型不需要 voice 参数

  // --- 5. 调用后端代理接口 ---
  loading.value = true
  console.log('[TTS] 发送请求, 模型:', body.model, 'voice:', body.audio.voice?.substring(0, 50) + '...')

  try {
    console.log('[TTS] 请求中...')
    const headers = { 'Content-Type': 'application/json' }
    if (apiKey.value.trim()) {
      headers['X-Api-Key'] = apiKey.value.trim()
    }
    const response = await fetch('/api/tts', {
      method: 'POST',
      headers,
      body: JSON.stringify(body)
    })

    const data = await response.json()
    console.log('[TTS] 响应状态:', response.status)

    // --- 6. 处理错误响应 ---
    if (!response.ok) {
      console.error('[TTS] 请求失败:', data)
      throw new Error(data.error?.message || `请求失败 (${response.status})`)
    }

    // --- 7. 提取 Base64 音频数据 ---
    // MiMo API 响应格式：completion.choices[0].message.audio.data
    const audioData = data.choices?.[0]?.message?.audio?.data
    console.log('[TTS] 音频数据长度:', audioData?.length || 0)
    if (!audioData) {
      throw new Error('响应中未包含音频数据')
    }

    // --- 8. Base64 解码并创建音频 Blob URL ---
    const binaryString = atob(audioData)
    const bytes = new Uint8Array(binaryString.length)
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i)
    }
    const blob = new Blob([bytes], { type: 'audio/wav' })

    // 释放旧的 Blob URL 避免内存泄漏
    if (audioUrl.value) {
      URL.revokeObjectURL(audioUrl.value)
    }
    wavBlob.value = blob
    audioUrl.value = URL.createObjectURL(blob)

  } catch (err) {
    errorMsg.value = err.message
  } finally {
    loading.value = false
  }
}

// ========================================
// 下载 WAV 文件
// ========================================
function downloadWav() {
  if (!wavBlob.value) return
  const a = document.createElement('a')
  a.href = URL.createObjectURL(wavBlob.value)
  a.download = 'mimo-tts-output.wav'
  a.click()
  URL.revokeObjectURL(a.href)
}

// ========================================
// 将 WAV 转换为 MP3 并下载
// 使用 lamejs 进行客户端编码
// ========================================
async function downloadMp3() {
  if (!wavBlob.value) return
  converting.value = true

  try {
    // 1. 用 Web Audio API 解码 WAV
    const arrayBuffer = await wavBlob.value.arrayBuffer()
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer)
    audioCtx.close()

    // 2. 提取 PCM 数据（取第一个声道）
    const sampleRate = audioBuffer.sampleRate
    const samples = audioBuffer.getChannelData(0) // Float32 [-1, 1]

    // 3. 转换为 Int16 PCM
    const pcm = new Int16Array(samples.length)
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]))
      pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
    }

    // 4. 用 lamejs 编码 MP3
    const mp3Encoder = new lamejs.Mp3Encoder(1, sampleRate, 128) // 单声道, 128kbps
    const mp3Data = []
    const blockSize = 1152

    for (let i = 0; i < pcm.length; i += blockSize) {
      const chunk = pcm.subarray(i, i + blockSize)
      const mp3buf = mp3Encoder.encodeBuffer(chunk)
      if (mp3buf.length > 0) mp3Data.push(mp3buf)
    }

    const end = mp3Encoder.flush()
    if (end.length > 0) mp3Data.push(end)

    // 5. 创建 MP3 Blob 并下载
    const mp3Blob = new Blob(mp3Data, { type: 'audio/mp3' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(mp3Blob)
    a.download = 'mimo-tts-output.mp3'
    a.click()
    URL.revokeObjectURL(a.href)

  } catch (err) {
    errorMsg.value = 'MP3 转换失败: ' + err.message
  } finally {
    converting.value = false
  }
}
</script>

<template>
  <!-- ========================================
       顶部导航栏
       ======================================== -->
  <header class="header">
    <div class="header-left">
      <h1 class="header-title">MiMo TTS</h1>
      <span class="header-badge">V2.5</span>
      <span class="header-subtitle">小米 MiMo 语音合成</span>
    </div>
    <div class="header-right">
      <div class="api-key-wrapper">
        <input
          :type="showApiKey ? 'text' : 'password'"
          class="api-key-input"
          v-model="apiKey"
          placeholder="API Key（选填）"
        />
        <button class="api-key-toggle" @click="showApiKey = !showApiKey" :title="showApiKey ? '隐藏' : '显示'">
          {{ showApiKey ? '🙈' : '👁️' }}
        </button>
      </div>
      <div class="theme-switcher-wrapper">
        <select class="theme-switcher" v-model="currentTheme">
          <option v-for="theme in themes" :key="theme.id" :value="theme.id">
            {{ theme.icon }} {{ theme.name }}
          </option>
        </select>
      </div>
    </div>
  </header>

  <div class="container">

    <!-- ========================================
         模型选择区域
         三个模型卡片：内置音色 / 声音设计 / 声音克隆
         ======================================== -->
    <section class="card">
      <h2 class="card-title">
        <span class="icon">🤖</span> 选择模型
      </h2>

      <div class="model-grid">
        <div
          v-for="model in models"
          :key="model.id"
          class="model-option"
          :class="{ active: currentModel === model.id }"
          @click="selectModel(model.id)"
        >
          <div class="model-check" v-if="currentModel === model.id">✓</div>
          <div class="model-name">{{ model.name }}</div>
          <div class="model-id">{{ model.id }}</div>
          <div class="model-desc">{{ model.desc }}</div>
        </div>
      </div>

      <!-- 内置音色选择（仅 mimo-v2.5-tts 模型显示） -->
      <div v-if="currentModelConfig.hasVoiceSelect" class="section-divider">
        <label for="voice">内置音色</label>
        <select id="voice" v-model="selectedVoice">
          <optgroup label="中文">
            <option
              v-for="v in voices.filter(v => v.lang === '中文')"
              :key="v.id"
              :value="v.id"
            >
              {{ v.name }}{{ v.gender ? ' - ' + v.gender : '' }}
            </option>
          </optgroup>
          <optgroup label="English">
            <option
              v-for="v in voices.filter(v => v.lang === 'English')"
              :key="v.id"
              :value="v.id"
            >
              {{ v.name }} - {{ v.gender }}
            </option>
          </optgroup>
        </select>
      </div>

      <!-- 声音设计描述输入（仅 VoiceDesign 模型显示） -->
      <div v-if="currentModelConfig.hasVoiceDesign" class="section-divider">
        <label for="voiceDesign">音色描述</label>
        <textarea
          id="voiceDesign"
          v-model="voiceDesignPrompt"
          rows="3"
          placeholder="例如：一个温柔的年轻女声，语速稍慢，带有磁性的低语感，像是在耳边轻声细语"
        ></textarea>
        <p class="hint">
          描述越具体，生成的音色越贴近期望。建议涵盖：性别与年龄、音色质感、情绪语调、语速节奏等维度。
        </p>
      </div>

      <!-- 声音克隆音频上传（仅 VoiceClone 模型显示） -->
      <div v-if="currentModelConfig.hasVoiceClone" class="section-divider">
        <label for="voiceClone">上传音频样本</label>
        <input
          id="voiceClone"
          type="file"
          accept=".mp3,.wav,.mp4,.mov,.avi,.webm"
          class="file-input"
          @change="handleFileUpload"
        />
        <p class="hint">
          上传参考音频或视频（mp3/wav/mp4），模型将克隆该音色来合成语音。视频文件会自动提取音频，Base64 编码后不超过 10MB。
        </p>
      </div>
    </section>

    <!-- ========================================
         文本输入区域
         风格指令（user 角色）+ 合成文本（assistant 角色）
         ======================================== -->
    <section class="card">
      <h2 class="card-title">
        <span class="icon">✍️</span> 输入文本
      </h2>

      <!-- 风格指令（user 角色消息，可选） -->
      <div class="form-group">
        <label for="style">风格指令（可选）</label>
        <textarea
          id="style"
          v-model="styleInstruction"
          rows="2"
          placeholder="例如：用欢快、跳跃的语调，语速稍快，像在分享一个天大的好消息"
        ></textarea>
        <p class="hint">
          通过自然语言描述期望的语音风格，内容会作为 <code>role: user</code> 消息发送。支持"导演模式"详细描述角色、场景和指导。
        </p>
      </div>

      <!-- 合成文本（assistant 角色消息，必填） -->
      <div class="form-group">
        <label for="text">
          合成文本 <span class="required">*</span>
        </label>
        <textarea
          id="text"
          v-model="synthesisText"
          rows="4"
          placeholder="请输入要转换为语音的文字内容..."
        ></textarea>
        <p class="hint">
          此内容会作为 <code>role: assistant</code> 消息发送，是实际被合成为语音的文本。
          支持音频标签如 <code>(叹气)</code>、<code>(笑)</code>、<code>(唱歌)</code> 等。
        </p>
      </div>
    </section>

    <!-- ========================================
         合成按钮 & 输出区域
         ======================================== -->
    <section class="card card-center">
      <button
        class="btn btn-primary"
        :disabled="loading"
        @click="synthesize"
      >
        <span v-if="loading" class="spinner"></span>
        <span v-else>🎙️</span>
        {{ loading ? '合成中...' : '开始合成' }}
      </button>

      <!-- 错误信息 -->
      <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

      <!-- 音频播放器（合成完成后显示） -->
      <div v-if="audioUrl" class="audio-player">
        <p class="audio-label">合成完成，点击播放</p>
        <audio controls :src="audioUrl"></audio>
        <div class="download-btns">
          <button class="btn btn-download" @click="downloadWav">
            下载 WAV
          </button>
          <button class="btn btn-download" :disabled="converting" @click="downloadMp3">
            <span v-if="converting" class="spinner"></span>
            {{ converting ? '转换中...' : '下载 MP3' }}
          </button>
        </div>
      </div>
    </section>

    <!-- ========================================
         使用说明
         ======================================== -->
    <section class="card card-help">
      <h2 class="card-title">
        <span class="icon">📖</span> 使用说明
      </h2>
      <ul class="help-list">
        <li><strong>MiMo-V2.5-TTS</strong>：使用内置音色，支持 <code>(唱歌)</code> 标签实现唱歌模式</li>
        <li><strong>VoiceDesign</strong>：通过文字描述自定义音色，无需音频样本。音色描述为必填项</li>
        <li><strong>VoiceClone</strong>：上传音频样本克隆音色，支持 mp3/wav 格式</li>
        <li>文本中可插入音频标签精细控制语音，如 <code>(叹气)唉...</code>、<code>(笑)哈哈哈</code></li>
        <li>在页面右上角填写自己的 API Key（优先使用），也可通过后端 <code>.env</code> 配置</li>
        <li>
          API 文档：<a href="https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5" target="_blank">MiMo TTS V2.5</a>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
/* ========================================
   顶部导航栏
   ======================================== */
.header {
  background: var(--accent-1);
  border-bottom: var(--border-width) solid var(--border);
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  box-shadow: 0px 4px 0px var(--shadow-color);
  margin-bottom: 12px;
}
[data-theme="soft-ui"] .header,
[data-theme="claymorphism"] .header {
  box-shadow: var(--shadow);
  border-bottom: none;
}
[data-theme="cyber-neon"] .header {
  background: rgba(10, 10, 12, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  box-shadow: 0 4px 20px rgba(0, 255, 204, 0.1);
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-right {
  display: flex;
  align-items: center;
}
.theme-switcher-wrapper {
  position: relative;
}
.api-key-wrapper {
  display: flex;
  align-items: center;
  gap: 0;
}
.api-key-input {
  padding: 6px 12px;
  font-size: 13px;
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius) 0 0 var(--radius);
  background: var(--card);
  color: var(--text);
  font-family: inherit;
  font-weight: 500;
  width: 160px;
  outline: none;
  transition: all 0.2s;
}
.api-key-toggle {
  padding: 6px 8px;
  font-size: 14px;
  border: var(--border-width) solid var(--border);
  border-left: none;
  border-radius: 0 var(--radius) var(--radius) 0;
  background: var(--card);
  cursor: pointer;
  transition: all 0.2s;
  line-height: 1;
}
[data-theme="soft-ui"] .api-key-input,
[data-theme="claymorphism"] .api-key-input,
[data-theme="soft-ui"] .api-key-toggle,
[data-theme="claymorphism"] .api-key-toggle {
  border: none;
  box-shadow: var(--shadow-active);
}
[data-theme="cyber-neon"] .api-key-input,
[data-theme="cyber-neon"] .api-key-toggle {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(136, 146, 176, 0.3);
  color: var(--primary);
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
}
[data-theme="cyber-neon"] .api-key-toggle {
  border-left: none;
}
.theme-switcher {
  padding: 6px 12px;
  font-size: 14px;
  border-radius: var(--radius);
  border: var(--border-width) solid var(--border);
  background: var(--card);
  color: var(--text);
  box-shadow: var(--shadow-hover);
  cursor: pointer;
  outline: none;
  appearance: none;
  font-family: inherit;
  font-weight: 700;
  transition: all 0.2s;
}
[data-theme="soft-ui"] .theme-switcher,
[data-theme="claymorphism"] .theme-switcher {
  box-shadow: var(--shadow);
  border: none;
  padding: 8px 16px;
}
[data-theme="claymorphism"] .theme-switcher:hover {
  box-shadow: var(--shadow-hover);
}
[data-theme="cyber-neon"] .theme-switcher {
  background: transparent;
  color: var(--primary);
  border: 1px solid var(--primary);
  box-shadow: 0 0 10px rgba(0, 255, 204, 0.2);
  text-shadow: 0 0 5px var(--primary);
}
[data-theme="cyber-neon"] .theme-switcher:hover {
  background: rgba(0, 255, 204, 0.1);
  box-shadow: 0 0 15px rgba(0, 255, 204, 0.4);
}
.header-title {
  font-size: 24px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: -0.5px;
}
[data-theme="claymorphism"] .header-title {
  text-transform: none;
  letter-spacing: 0;
  color: var(--primary);
}
[data-theme="cyber-neon"] .header-title {
  color: var(--text);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
  letter-spacing: 2px;
}
.header-badge {
  background: var(--accent-2);
  color: var(--text);
  font-size: 12px;
  padding: 4px 10px;
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius);
  font-weight: 700;
  box-shadow: 2px 2px 0px var(--shadow-color);
}
[data-theme="soft-ui"] .header-badge {
  border: none;
  box-shadow: var(--shadow);
}
[data-theme="claymorphism"] .header-badge {
  border: none;
  box-shadow: var(--shadow-active);
  background: var(--accent-3);
  color: #fff;
}
[data-theme="cyber-neon"] .header-badge {
  background: transparent;
  color: var(--accent-2);
  border: 1px solid var(--accent-2);
  box-shadow: 0 0 8px rgba(255, 0, 255, 0.5);
  text-shadow: 0 0 5px var(--accent-2);
}
.header-subtitle {
  color: var(--text);
  font-size: 14px;
  font-weight: 600;
}
[data-theme="cyber-neon"] .header-subtitle {
  color: var(--text-secondary);
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
}

/* ========================================
   主容器
   ======================================== */
.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ========================================
   卡片
   ======================================== */
.card {
  background: var(--card);
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
  transition: transform 0.2s, box-shadow 0.2s;
}
[data-theme="neo-brutalism"] .card:hover {
  transform: translate(-2px, -2px);
  box-shadow: 8px 8px 0px var(--shadow-color);
}
[data-theme="cyber-neon"] .card {
  background: rgba(10, 10, 12, 0.7);
  backdrop-filter: blur(5px);
  border: 1px solid var(--border);
  box-shadow: 0 0 15px rgba(0, 255, 204, 0.05);
}
[data-theme="cyber-neon"] .card:hover {
  border-color: rgba(0, 255, 204, 0.5);
  box-shadow: 0 0 20px rgba(0, 255, 204, 0.15);
}
.card-title {
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  text-transform: uppercase;
  border-bottom: 2px solid var(--border);
  padding-bottom: 8px;
}
[data-theme="soft-ui"] .card-title,
[data-theme="claymorphism"] .card-title {
  border-bottom: 2px solid rgba(0,0,0,0.05);
}
[data-theme="claymorphism"] .card-title {
  text-transform: none;
  color: var(--primary);
}
[data-theme="cyber-neon"] .card-title {
  border-bottom: 1px solid var(--border);
  color: var(--text);
  text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
  letter-spacing: 1px;
}
.card-center {
  text-align: center;
}
.card-help {
  font-size: 14px;
  font-weight: 500;
  background: var(--accent-3);
  color: var(--text);
}
[data-theme="claymorphism"] .card-help {
  background: var(--card);
  color: var(--text-secondary);
}
[data-theme="cyber-neon"] .card-help {
  background: rgba(255, 234, 0, 0.05);
  border: 1px dashed rgba(255, 234, 0, 0.3);
  color: var(--text-secondary);
}

/* ========================================
   模型选择网格
   ======================================== */
.model-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.model-option {
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  background: var(--card);
  box-shadow: var(--shadow-hover);
}
[data-theme="neo-brutalism"] .model-option:hover {
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow);
}
[data-theme="soft-ui"] .model-option,
[data-theme="claymorphism"] .model-option {
  box-shadow: var(--shadow);
}
[data-theme="soft-ui"] .model-option:hover,
[data-theme="claymorphism"] .model-option:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}
[data-theme="cyber-neon"] .model-option {
  background: rgba(26, 26, 31, 0.5);
  border: 1px solid rgba(136, 146, 176, 0.2);
  box-shadow: none;
}
[data-theme="cyber-neon"] .model-option:hover {
  border-color: var(--primary);
  box-shadow: inset 0 0 15px rgba(0, 255, 204, 0.1);
}
.model-option.active {
  background: var(--accent-1);
  transform: translate(2px, 2px);
  box-shadow: var(--shadow-active);
}
[data-theme="soft-ui"] .model-option.active,
[data-theme="claymorphism"] .model-option.active {
  transform: none;
  box-shadow: var(--shadow-active);
}
[data-theme="soft-ui"] .model-option.active {
  background: var(--bg);
}
[data-theme="cyber-neon"] .model-option.active {
  background: rgba(0, 255, 204, 0.05);
  border-color: var(--primary);
  box-shadow: var(--shadow);
  transform: none;
}
.model-name {
  font-size: 16px;
  font-weight: 800;
  margin-bottom: 6px;
  text-transform: uppercase;
}
[data-theme="claymorphism"] .model-name {
  text-transform: none;
  color: var(--primary);
}
[data-theme="cyber-neon"] .model-name {
  color: var(--text);
  letter-spacing: 1px;
}
[data-theme="cyber-neon"] .model-option.active .model-name {
  color: var(--primary);
  text-shadow: 0 0 8px var(--primary);
}
.model-id {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: monospace;
  font-weight: 700;
  margin-bottom: 10px;
  background: rgba(0,0,0,0.05);
  padding: 2px 6px;
  display: inline-block;
  border: var(--border-width) solid var(--border);
}
[data-theme="soft-ui"] .model-id,
[data-theme="claymorphism"] .model-id {
  border: none;
  border-radius: 6px;
}
[data-theme="claymorphism"] .model-id {
  background: var(--bg);
}
[data-theme="cyber-neon"] .model-id {
  background: rgba(136, 146, 176, 0.1);
  border: none;
  color: var(--primary);
}
.model-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  font-weight: 500;
}
[data-theme="cyber-neon"] .model-desc {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
}
.model-check {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 28px;
  height: 28px;
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius);
  background: var(--accent-2);
  color: var(--text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 800;
  box-shadow: 2px 2px 0px var(--shadow-color);
}
[data-theme="soft-ui"] .model-check,
[data-theme="claymorphism"] .model-check {
  border: none;
  border-radius: 50%;
  box-shadow: var(--shadow);
  top: -8px;
  right: -8px;
}
[data-theme="claymorphism"] .model-check {
  background: var(--primary);
  color: #fff;
}
[data-theme="cyber-neon"] .model-check {
  background: var(--bg);
  border: 1px solid var(--primary);
  color: var(--primary);
  box-shadow: 0 0 10px var(--primary);
  text-shadow: 0 0 5px var(--primary);
  top: -10px;
  right: -10px;
}

/* ========================================
   表单控件
   ======================================== */
label {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 8px;
  text-transform: uppercase;
}
[data-theme="claymorphism"] label {
  text-transform: none;
}
[data-theme="cyber-neon"] label {
  color: var(--primary);
  font-family: "JetBrains Mono", monospace;
  font-size: 12px;
  letter-spacing: 1px;
}
select,
textarea,
.file-input {
  width: 100%;
  padding: 12px 16px;
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius);
  font-size: 15px;
  font-weight: 500;
  font-family: inherit;
  background: var(--card);
  color: var(--text);
  transition: all 0.2s;
  box-shadow: var(--shadow-hover);
}
[data-theme="soft-ui"] select,
[data-theme="soft-ui"] textarea,
[data-theme="soft-ui"] .file-input,
[data-theme="claymorphism"] select,
[data-theme="claymorphism"] textarea,
[data-theme="claymorphism"] .file-input {
  box-shadow: var(--shadow-active);
  background: var(--bg);
  border: none;
}
[data-theme="cyber-neon"] select,
[data-theme="cyber-neon"] textarea,
[data-theme="cyber-neon"] .file-input {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(136, 146, 176, 0.3);
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.8);
  color: var(--primary);
  font-family: "JetBrains Mono", monospace;
}
[data-theme="neo-brutalism"] select:focus,
[data-theme="neo-brutalism"] textarea:focus,
[data-theme="neo-brutalism"] .file-input:focus {
  outline: none;
  background: #fff;
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow);
}
[data-theme="soft-ui"] select:focus,
[data-theme="soft-ui"] textarea:focus,
[data-theme="soft-ui"] .file-input:focus {
  outline: none;
  box-shadow: inset 8px 8px 12px 0 rgba(163, 177, 198, 0.8), inset -8px -8px 12px 0 rgba(255, 255, 255, 0.9);
}
[data-theme="claymorphism"] select:focus,
[data-theme="claymorphism"] textarea:focus,
[data-theme="claymorphism"] .file-input:focus {
  outline: none;
  box-shadow: var(--shadow);
  background: var(--card);
}
[data-theme="cyber-neon"] select:focus,
[data-theme="cyber-neon"] textarea:focus,
[data-theme="cyber-neon"] .file-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: inset 0 0 10px rgba(0, 255, 204, 0.1), 0 0 10px rgba(0, 255, 204, 0.2);
}
textarea {
  resize: vertical;
  min-height: 100px;
}
.file-input {
  padding: 10px;
  cursor: pointer;
  background: var(--accent-1);
}
[data-theme="cyber-neon"] .file-input {
  background: rgba(0, 0, 0, 0.5);
}
.required {
  color: var(--primary);
  font-weight: 900;
  font-size: 18px;
}
[data-theme="cyber-neon"] .required {
  color: var(--accent-2);
  text-shadow: 0 0 5px var(--accent-2);
}
.hint {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
  line-height: 1.5;
  font-weight: 500;
}
[data-theme="cyber-neon"] .hint {
  font-size: 11px;
  font-family: "JetBrains Mono", monospace;
}
.hint code {
  background: var(--accent-1);
  padding: 2px 6px;
  border: 1px solid var(--border);
  border-radius: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
}
[data-theme="soft-ui"] .hint code,
[data-theme="claymorphism"] .hint code {
  border: none;
  border-radius: 4px;
  box-shadow: var(--shadow-active);
  background: var(--bg);
}
[data-theme="cyber-neon"] .hint code {
  background: rgba(255, 0, 255, 0.1);
  border: 1px solid rgba(255, 0, 255, 0.3);
  color: var(--accent-2);
}
.form-group {
  margin-bottom: 20px;
}
.form-group:last-child {
  margin-bottom: 0;
}
.section-divider {
  margin-top: 24px;
  padding-top: 20px;
  border-top: var(--border-width) dashed var(--border);
}
[data-theme="soft-ui"] .section-divider,
[data-theme="claymorphism"] .section-divider {
  border-top: 2px solid rgba(0,0,0,0.05);
}
[data-theme="cyber-neon"] .section-divider {
  border-top: 1px solid rgba(0, 255, 204, 0.2);
}

/* ========================================
   按钮
   ======================================== */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 36px;
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius);
  font-size: 16px;
  font-weight: 800;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  box-shadow: var(--shadow);
}
[data-theme="soft-ui"] .btn,
[data-theme="claymorphism"] .btn {
  border: none;
}
[data-theme="claymorphism"] .btn {
  text-transform: none;
}
[data-theme="cyber-neon"] .btn {
  border: 1px solid var(--primary);
  background: transparent;
  color: var(--primary);
  box-shadow: 0 0 15px rgba(0, 255, 204, 0.2), inset 0 0 10px rgba(0, 255, 204, 0.1);
  text-shadow: 0 0 5px var(--primary);
  letter-spacing: 2px;
}
.btn-primary {
  background: var(--primary);
  color: #fff;
}
[data-theme="neo-brutalism"] .btn-primary {
  text-shadow: 1px 1px 0px #000;
}
[data-theme="neo-brutalism"] .btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translate(2px, 2px);
  box-shadow: var(--shadow-hover);
}
[data-theme="neo-brutalism"] .btn-primary:active:not(:disabled) {
  transform: translate(6px, 6px);
  box-shadow: var(--shadow-active);
}
[data-theme="soft-ui"] .btn-primary:hover:not(:disabled),
[data-theme="claymorphism"] .btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}
[data-theme="soft-ui"] .btn-primary:active:not(:disabled),
[data-theme="claymorphism"] .btn-primary:active:not(:disabled) {
  box-shadow: var(--shadow-active);
  transform: translateY(2px);
}
[data-theme="cyber-neon"] .btn-primary:hover:not(:disabled) {
  background: rgba(0, 255, 204, 0.2);
  box-shadow: 0 0 30px rgba(0, 255, 204, 0.6), inset 0 0 15px rgba(0, 255, 204, 0.4);
  text-shadow: 0 0 10px #fff;
}
[data-theme="cyber-neon"] .btn-primary:active:not(:disabled) {
  background: rgba(0, 255, 204, 0.4);
  box-shadow: 0 0 15px rgba(0, 255, 204, 0.4), inset 0 0 5px rgba(0, 255, 204, 0.2);
}
.btn-primary:disabled {
  background: #ccc;
  color: #666;
  text-shadow: none;
  cursor: not-allowed;
  box-shadow: none;
  transform: translate(6px, 6px);
}
[data-theme="soft-ui"] .btn-primary:disabled,
[data-theme="claymorphism"] .btn-primary:disabled {
  transform: none;
  background: var(--bg);
  box-shadow: var(--shadow-active);
}
[data-theme="cyber-neon"] .btn-primary:disabled {
  transform: none;
  border-color: #333;
  color: #555;
  box-shadow: none;
  text-shadow: none;
  background: transparent;
}

/* ========================================
   加载动画
   ======================================== */
.spinner {
  display: inline-block;
  width: 18px;
  height: 18px;
  border: 3px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
[data-theme="cyber-neon"] .spinner {
  border-color: var(--primary);
  border-top-color: transparent;
  box-shadow: 0 0 10px var(--primary);
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ========================================
   错误信息
   ======================================== */
.error-msg {
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  margin-top: 16px;
  padding: 12px 16px;
  background: var(--primary);
  border: var(--border-width) solid var(--border);
  box-shadow: 4px 4px 0px var(--border);
}
[data-theme="soft-ui"] .error-msg,
[data-theme="claymorphism"] .error-msg {
  border: none;
  box-shadow: var(--shadow);
  border-radius: var(--radius);
  color: var(--primary);
  background: var(--bg);
}
[data-theme="cyber-neon"] .error-msg {
  background: rgba(255, 0, 255, 0.1);
  border: 1px solid var(--accent-2);
  color: var(--accent-2);
  box-shadow: 0 0 15px rgba(255, 0, 255, 0.3);
  text-shadow: 0 0 5px var(--accent-2);
}

/* ========================================
   音频播放器
   ======================================== */
.audio-player {
  margin-top: 24px;
  padding: 20px;
  background: var(--accent-1);
  border: var(--border-width) solid var(--border);
  box-shadow: var(--shadow-hover);
}
[data-theme="soft-ui"] .audio-player,
[data-theme="claymorphism"] .audio-player {
  border: none;
  border-radius: var(--radius);
  box-shadow: var(--shadow-active);
}
[data-theme="claymorphism"] .audio-player {
  background: var(--bg);
}
[data-theme="cyber-neon"] .audio-player {
  background: rgba(0, 255, 204, 0.05);
  border: 1px solid rgba(0, 255, 204, 0.3);
  box-shadow: inset 0 0 20px rgba(0, 255, 204, 0.05);
}
.audio-label {
  font-size: 15px;
  font-weight: 800;
  color: var(--text);
  margin-bottom: 12px;
  text-transform: uppercase;
}
[data-theme="claymorphism"] .audio-label {
  text-transform: none;
}
[data-theme="cyber-neon"] .audio-label {
  color: var(--primary);
  text-shadow: 0 0 5px var(--primary);
}
.audio-player audio {
  width: 100%;
  border: var(--border-width) solid var(--border);
  border-radius: var(--radius);
  background: var(--card);
}
[data-theme="soft-ui"] .audio-player audio,
[data-theme="claymorphism"] .audio-player audio {
  border: none;
  box-shadow: var(--shadow);
}
[data-theme="cyber-neon"] .audio-player audio {
  border: 1px solid var(--primary);
  box-shadow: 0 0 10px rgba(0, 255, 204, 0.2);
  filter: sepia(100%) hue-rotate(130deg) saturate(300%);
}
.audio-player audio::-webkit-media-controls-panel {
  background: var(--card);
  border-radius: var(--radius);
}
.download-btns {
  display: flex;
  gap: 16px;
  margin-top: 16px;
  justify-content: center;
}
.btn-download {
  padding: 10px 24px;
  font-size: 14px;
  background: var(--card);
  color: var(--text);
  border: var(--border-width) solid var(--border);
  box-shadow: 3px 3px 0px var(--border);
  font-weight: 800;
  text-transform: uppercase;
}
[data-theme="soft-ui"] .btn-download,
[data-theme="claymorphism"] .btn-download {
  border: none;
  box-shadow: var(--shadow);
  border-radius: var(--radius);
}
[data-theme="claymorphism"] .btn-download {
  text-transform: none;
  background: var(--accent-1);
}
[data-theme="cyber-neon"] .btn-download {
  background: transparent;
  color: var(--accent-3);
  border: 1px solid var(--accent-3);
  box-shadow: 0 0 10px rgba(255, 234, 0, 0.2);
  text-shadow: 0 0 5px var(--accent-3);
}
[data-theme="neo-brutalism"] .btn-download:hover:not(:disabled) {
  background: var(--accent-2);
  transform: translate(2px, 2px);
  box-shadow: 1px 1px 0px var(--border);
}
[data-theme="neo-brutalism"] .btn-download:active:not(:disabled) {
  transform: translate(3px, 3px);
  box-shadow: 0px 0px 0px var(--border);
}
[data-theme="soft-ui"] .btn-download:hover:not(:disabled),
[data-theme="claymorphism"] .btn-download:hover:not(:disabled) {
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}
[data-theme="soft-ui"] .btn-download:active:not(:disabled),
[data-theme="claymorphism"] .btn-download:active:not(:disabled) {
  box-shadow: var(--shadow-active);
  transform: translateY(2px);
}
[data-theme="cyber-neon"] .btn-download:hover:not(:disabled) {
  background: rgba(255, 234, 0, 0.1);
  box-shadow: 0 0 20px rgba(255, 234, 0, 0.4);
}
.btn-download:disabled {
  background: #eee;
  color: #999;
  cursor: not-allowed;
  box-shadow: none;
  transform: translate(3px, 3px);
}
[data-theme="soft-ui"] .btn-download:disabled,
[data-theme="claymorphism"] .btn-download:disabled {
  transform: none;
  background: var(--bg);
  box-shadow: var(--shadow-active);
}
[data-theme="cyber-neon"] .btn-download:disabled {
  transform: none;
  border-color: #333;
  color: #555;
  box-shadow: none;
  text-shadow: none;
  background: transparent;
}

/* ========================================
   帮助列表
   ======================================== */
.help-list {
  padding-left: 24px;
}
.help-list li {
  margin-bottom: 8px;
}
.help-list code {
  background: var(--card);
  padding: 2px 6px;
  border: var(--border-width) solid var(--border);
  border-radius: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
}
[data-theme="soft-ui"] .help-list code,
[data-theme="claymorphism"] .help-list code {
  border: none;
  border-radius: 4px;
  box-shadow: var(--shadow-active);
  background: var(--bg);
}
[data-theme="cyber-neon"] .help-list code {
  background: rgba(0, 255, 204, 0.1);
  border: 1px solid rgba(0, 255, 204, 0.3);
  color: var(--primary);
  font-family: "JetBrains Mono", monospace;
}
.help-list a {
  color: var(--primary);
  font-weight: 800;
  text-decoration: none;
  border-bottom: 2px solid var(--primary);
}
.help-list a:hover {
  background: var(--primary);
  color: #fff;
}
[data-theme="soft-ui"] .help-list a,
[data-theme="claymorphism"] .help-list a {
  border-bottom: none;
}
[data-theme="soft-ui"] .help-list a:hover,
[data-theme="claymorphism"] .help-list a:hover {
  background: transparent;
  color: var(--primary-hover);
}
[data-theme="cyber-neon"] .help-list a {
  border-bottom: 1px dashed var(--primary);
  text-shadow: 0 0 5px var(--primary);
}
[data-theme="cyber-neon"] .help-list a:hover {
  background: rgba(0, 255, 204, 0.2);
  color: #fff;
  text-shadow: 0 0 8px #fff;
}

/* ========================================
   响应式
   ======================================== */
@media (max-width: 640px) {
  .model-grid {
    grid-template-columns: 1fr;
  }
  .header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
