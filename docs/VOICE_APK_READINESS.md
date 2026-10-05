# Sahaay multilingual voice and APK readiness

## Architecture

The voice path is deliberately separate from Sahaay's assistant and financial safety logic:

```text
User speaks
  -> VoiceService adapter
  -> server transcription endpoint
  -> recognized text shown to the user
  -> existing /api/ask pipeline
  -> existing validation, anomaly checks, and confirmation boundaries
  -> response text shown
  -> optional VoiceService TTS playback
```

The React application depends only on the `VoiceService` interface in `frontend/src/voice/voiceService.ts`:

- `startListening()`
- `stopListening()`
- `transcribe(audio, language)`
- `speak(text, language)`
- `stopSpeaking()`

The current `WebVoiceService` captures a short `MediaRecorder` clip and sends it to `POST /api/voice/transcribe`. The backend forwards the bytes to the managed Whisper-compatible transcription surface using the selected language as a prompt. Raw recordings are not persisted. Text-to-speech is an optional web adapter using `speechSynthesis`; a TTS failure leaves the response text visible.

## Supported languages

- English (`en-IN`)
- Hindi (`hi-IN`)
- Kannada (`kn-IN`)
- Telugu (`te-IN`)

The Profile preferred language is used for the voice request, STT prompt, and TTS locale. The explicit profile selection takes priority over provider language detection.

## Capacitor/Android path

When the React app is packaged with Capacitor, add a native implementation of the same `VoiceService` interface and select it at the adapter factory boundary. The Ask Sahaay components and backend APIs do not need to change. The native adapter can use a maintained Capacitor microphone/audio plugin and either send the resulting supported audio format to the same backend endpoint or use a native STT provider while preserving the `VoiceTranscript` contract.

### Future Android permissions

- `android.permission.RECORD_AUDIO` — required only while the user actively records a voice question.
- `android.permission.INTERNET` — normal network access for the existing API and managed transcription service.
- No `READ_SMS` permission.
- No SMS inbox access.
- No background microphone permission.
- No contacts, phone, storage, banking, UPI, or notification permissions are required for this feature.
- TTS itself does not require a sensitive permission.

The future native implementation must request microphone permission only at the point of the user's voice action and must show the same typed fallback if permission is denied.

## Safety boundary

Voice submits recognized text to the existing `/api/ask` endpoint. It cannot execute a payment. A voice payment request remains subject to the existing recipient validation, review screen, transaction anomaly check, stronger acknowledgment for flagged payments, and explicit simulated confirmation. No voice path reads SMS, stores credentials, or bypasses the backend.

## Limitations

- The current web adapter requires a browser/device that supports `MediaRecorder` and microphone capture.
- The managed transcription service and `MANUS_API_URL`/`MANUS_API_KEY` runtime configuration are required for server STT. If unavailable, the UI gives a typed fallback message.
- Browser TTS voice availability varies by operating system; playback is an enhancement and never a dependency.
- Android packaging is documented but not performed in this task.
