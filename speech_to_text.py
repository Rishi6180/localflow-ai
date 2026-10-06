import os
import sys
import threading
import wave
import numpy as np
import sounddevice as sd
import requests
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from pynput import keyboard
from faster_whisper import WhisperModel

# ---------------------------------------------------------
# 1. CONFIGURATION & MODEL LOADING
# ---------------------------------------------------------
HOTKEY = keyboard.Key.f8  # Hold down F8 to speak
SAMPLE_RATE = 16000
TEMP_AUDIO_FILE = "temp_recording.wav"

print("Loading LocalFlow AI transcription engine...")
whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
print("LocalFlow AI engine ready!")

# Threading signal bridge for UI safety
class WorkerSignals(QObject):
    transcription_done = pyqtSignal(str)
    status_update = pyqtSignal(str)

signals = WorkerSignals()

# ---------------------------------------------------------
# 2. POPUP RESULT WINDOW
# ---------------------------------------------------------
class ResultPopupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LocalFlow AI - Output")
        self.setGeometry(300, 300, 450, 250)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()
        self.label = QLabel("Cleaned Output:")
        self.text_area = QTextEdit()

        self.copy_btn = QPushButton("Copy & Close")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)

        layout.addWidget(self.label)
        layout.addWidget(self.text_area)
        layout.addWidget(self.copy_btn)
        self.setLayout(layout)

    def show_result(self, text):
        self.text_area.setText(text)
        self.show()
        self.raise_()
        self.activateWindow()

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.text_area.toPlainText())
        self.close()

# ---------------------------------------------------------
# 3. MAIN FLOATING BAR
# ---------------------------------------------------------
class FloatingControlBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LocalFlow AI Bar")
        self.setFixedSize(260, 50)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)

        layout = QVBoxLayout()
        self.status_label = QLabel("LocalFlow AI | Hold [F8] to Speak")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        self.drag_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)

# ---------------------------------------------------------
# 4. AUDIO RECORDING & AI CONTROLLER
# ---------------------------------------------------------
class LocalFlowController:
    def __init__(self, main_bar, popup_window):
        self.main_bar = main_bar
        self.popup_window = popup_window
        self.is_recording = False
        self.audio_frames = []
        self.stream = None

        signals.status_update.connect(self.main_bar.status_label.setText)
        signals.transcription_done.connect(self.popup_window.show_result)

        # Global Hotkey Listener
        self.listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.listener.start()

    def on_key_press(self, key):
        if key == HOTKEY and not self.is_recording:
            self.is_recording = True
            self.audio_frames = []
            signals.status_update.emit("🔴 Listening...")

            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                callback=self._audio_callback
            )
            self.stream.start()

    def on_key_release(self, key):
        if key == HOTKEY and self.is_recording:
            self.is_recording = False
            signals.status_update.emit("⚡ LocalFlow AI Processing...")

            if self.stream:
                self.stream.stop()
                self.stream.close()

            threading.Thread(target=self._process_pipeline, daemon=True).start()

    def _audio_callback(self, indata, frames, time, status):
        if self.is_recording:
            self.audio_frames.append(indata.copy())

    def _process_pipeline(self):
        if not self.audio_frames:
            signals.status_update.emit("LocalFlow AI | Hold [F8] to Speak")
            return

        # Export audio buffer to wav
        audio_data = np.concatenate(self.audio_frames, axis=0)
        audio_int16 = (audio_data * 32767).astype(np.int16)

        with wave.open(TEMP_AUDIO_FILE, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_int16.tobytes())

        # Step 1: Speech-to-Text via local Whisper (CPU)
        segments, _ = whisper_model.transcribe(TEMP_AUDIO_FILE, beam_size=1)
        raw_text = " ".join([seg.text for seg in segments]).strip()

        if not raw_text:
            signals.status_update.emit("LocalFlow AI | Hold [F8] to Speak")
            return

        # Step 2: Cleanup via local Ollama LLM
        prompt = (
            "You are a voice dictation assistant. Clean up this raw voice transcript: "
            "Remove filler words (um, ah, like), fix grammar, and fix self-corrections. "
            f"Output ONLY the cleaned text:\n\n\"{raw_text}\""
        )

        try:
            res = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:1b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10
            )
            cleaned_text = res.json().get("response", raw_text).strip()
        except Exception:
            cleaned_text = raw_text

        if os.path.exists(TEMP_AUDIO_FILE):
            os.remove(TEMP_AUDIO_FILE)

        signals.status_update.emit("LocalFlow AI | Hold [F8] to Speak")
        signals.transcription_done.emit(cleaned_text)

# ---------------------------------------------------------
# 5. APPLICATION ENTRY
# ---------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("LocalFlow AI")
    app.setQuitOnLastWindowClosed(False)

    main_bar = FloatingControlBar()
    main_bar.show()

    popup_window = ResultPopupWindow()
    controller = LocalFlowController(main_bar, popup_window)

    sys.exit(app.exec())