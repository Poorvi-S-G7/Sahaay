export type SupportedLanguage = 'English' | 'Hindi' | 'Kannada' | 'Telugu'

export type VoiceTranscript = {
  text: string
  language?: string
}

export interface VoiceService {
  startListening(): Promise<void>
  stopListening(): Promise<Blob | null>
  transcribe(audio: Blob, language: SupportedLanguage): Promise<VoiceTranscript>
  speak(text: string, language: SupportedLanguage): Promise<void>
  stopSpeaking(): void
}

const localeFor = (language: SupportedLanguage) => ({
  English: 'en-IN',
  Hindi: 'hi-IN',
  Kannada: 'kn-IN',
  Telugu: 'te-IN',
}[language])

export class WebVoiceService implements VoiceService {
  private recorder: MediaRecorder | null = null
  private stream: MediaStream | null = null
  private chunks: Blob[] = []
  private recordingResolve: ((audio: Blob | null) => void) | null = null

  async startListening(): Promise<void> {
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      throw new Error('Voice input is not available on this device.')
    }
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg'].find((type) => MediaRecorder.isTypeSupported(type))
    this.chunks = []
    this.recorder = new MediaRecorder(this.stream, mimeType ? { mimeType } : undefined)
    console.debug('[Sahaay voice] MediaRecorder MIME type:', this.recorder.mimeType || '<browser default>')
    this.recorder.ondataavailable = (event) => {
      if (event.data.size > 0) this.chunks.push(event.data)
    }
    this.recorder.start()
  }

  stopListening(): Promise<Blob | null> {
    if (!this.recorder || this.recorder.state === 'inactive') {
      this.releaseStream()
      return Promise.resolve(null)
    }
    const recorder = this.recorder
    return new Promise((resolve) => {
      this.recordingResolve = resolve
      recorder.onstop = () => {
        const type = recorder.mimeType || 'audio/webm'
        const audio = this.chunks.length ? new Blob(this.chunks, { type }) : null
        this.recordingResolve?.(audio)
        this.recordingResolve = null
        this.recorder = null
        this.chunks = []
        this.releaseStream()
      }
      recorder.stop()
    })
  }

  async transcribe(audio: Blob, language: SupportedLanguage): Promise<VoiceTranscript> {
    const form = new FormData()
    const baseMime = (audio.type || 'audio/webm').split(';', 1)[0]
    const extensionByMime: Record<string, string> = {
      'audio/webm': 'recording.webm',
      'audio/ogg': 'recording.ogg',
      'audio/wav': 'recording.wav',
      'audio/mpeg': 'recording.mp3',
      'audio/mp4': 'recording.mp4',
      'audio/x-m4a': 'recording.m4a',
    }
    const filename = extensionByMime[baseMime] || 'recording.webm'
    console.debug('[Sahaay voice] Upload MIME type:', audio.type || '<missing>', 'filename:', filename, 'size:', audio.size)
    form.append('file', audio, filename)
    form.append('language', language)
    const response = await fetch('/api/voice/transcribe', { method: 'POST', body: form })
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}))
      throw new Error(payload.detail || 'We could not understand that recording.')
    }
    return response.json()
  }

  speak(text: string, language: SupportedLanguage): Promise<void> {
    if (!('speechSynthesis' in window)) return Promise.resolve()
    window.speechSynthesis.cancel()
    return new Promise((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = localeFor(language)
      utterance.rate = 0.94
      utterance.pitch = 1
      utterance.onend = () => resolve()
      utterance.onerror = (event) => {
        if (event.error === 'canceled' || event.error === 'interrupted') resolve()
        else reject(new Error('Text-to-speech is unavailable.'))
      }
      window.speechSynthesis.speak(utterance)
    })
  }

  stopSpeaking(): void {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel()
  }

  private releaseStream(): void {
    this.stream?.getTracks().forEach((track) => track.stop())
    this.stream = null
  }
}

// Capacitor can provide a native implementation of the same interface later.
// React components intentionally depend only on VoiceService, not on browser or Android APIs.
export const voiceService: VoiceService = new WebVoiceService()
