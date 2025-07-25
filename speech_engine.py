import queue
import re
import threading
import comtypes
import pyttsx3


class SpeechEngine:
    def __init__(self, pause_recording=None, resume_recording=None):
        self.voice_lock = threading.Lock()
        self.speech_queue = queue.Queue()
        self.running = True
        self.last_speak_end = 0.0
         # 錄音控制回調（從 MainAssistant 注入）
        self.pause_recording = pause_recording  # 暫停錄音的函數
        self.resume_recording = resume_recording  # 恢復錄音的函數
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()

    def speak(self, text):
        if text and isinstance(text, str):
            # 放入隊列前暫停錄音（若回調存在）
            if self.pause_recording:
                self.pause_recording()
            self.speech_queue.put(text)
            
    def _detect_language(self, text):
        if re.search(r'[A-Za-z]', text):
            return "english"
        else:
            return "other"
    
    def _speech_worker(self):
        comtypes.CoInitialize()
        try:
            engine = pyttsx3.init("sapi5")
            voices = engine.getProperty('voices')

            # 篩選中英文語音包
            english_voice = None
            chinese_voice = None
            for voice in voices:
                if "chinese" in voice.id.lower() or "zh" in voice.id.lower():
                    chinese_voice = voice.id
                elif "english" in voice.id.lower() or "en" in voice.id.lower():
                    english_voice = voice.id
            
            # 設置默認語音（優先中文）
            default_voice = chinese_voice if chinese_voice else voices[0].id
            if not english_voice:
                english_voice = default_voice
            
            engine.setProperty('volume', 1.0)  # 音量範圍：0.0-1.0
            
            while self.running:
                text = self.speech_queue.get()
                if text is None:
                    break
                lang = self._detect_language(text)
                with self.voice_lock:
                    if lang == "english":
                        engine.setProperty('voice', english_voice)
                        engine.setProperty('rate', 170)
                    else:
                        engine.setProperty('voice', default_voice)
                        engine.setProperty('rate', 140)
                    engine.say(text)
                    engine.runAndWait()
                 # 播報結束後恢復錄音（若回調存在）
                if self.resume_recording:
                    self.resume_recording()
                self.speech_queue.task_done()
        finally:
            comtypes.CoUninitialize()

    def stop(self):
        self.running = False
        self.speech_queue.put(None)
        self.speech_thread.join()