# LocalFlow AI

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=flat&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![faster-whisper](https://img.shields.io/badge/STT-faster--whisper-blue?style=flat)](https://github.com/SYSTRAN/faster-whisper)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-black?style=flat&logo=ollama&logoColor=white)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> A lightweight, 100% offline push-to-talk voice dictation assistant that captures speech globally, performs on-device transcription, and cleans raw transcripts into polished text using a local Large Language Model.

Traditional operating system dictation tools transcribe every verbal misstep literally—capturing speech disfluencies ("um", "ah"), awkward grammar, and false starts. Cloud alternatives introduce API latency, recurring costs, and privacy concerns for sensitive notes.

LocalFlow AI solves this through a local dual-model inference pipeline:
1. Captures global push-to-talk audio without taking window focus.
2. Performs sub-second speech-to-text via INT8-quantized CTranslate2.
3. Automatically refines transcripts through an on-device LLM (llama3.2:1b) to strip fillers and resolve mid-sentence self-corrections into production-ready prose.

**System Architecture**
[ Global Push-to-Talk (F8) ] -> [ Audio Ingest (sounddevice @ 16kHz) ] -> [ faster-whisper Engine (CTranslate2 INT8) ] -> Raw Transcribed Text -> [ Local LLM Cleanup (Ollama / Llama 3.2 1B) ] -> Cleaned, Punctuation-Corrected Text -> [ Thread-Safe Qt Bridge (PyQt6 HUD) ] -> [ Clipboard Injection ]

**Key Technical Features**
- Zero Cloud Footprint: 100% private and offline; voice buffers and processed text never leave the local machine.
- Asynchronous Execution: Background thread isolation via WorkerSignals prevents UI freezing during inference bursts.
- Dynamic Context Normalization: Removes hesitations, formats capitalization/punctuation, and resolves verbal corrections ("Meeting at three, no wait, four" $\rightarrow$ "Meeting at 4:00").
- Universal Hardware Compatibility: Standardized on INT8 CPU quantization to execute cleanly on any standard multi-core machine without requiring proprietary CUDA/cuDNN driver toolchains.
- Seamless Desktop Integration: Includes a floating, draggable HUD bar and top-level modal with one-click clipboard copying.

**Installation & Setup**

Prerequisites
1. Python 3.10 - 3.12 installed on your system.
2. Ollama installed and running locally (ollama.com).
3. Pull the target language model: ollama pull llama3.2:1b

**Quickstart**
1. Clone the repository: git clone [https://github.com/Rishi6180](https://github.com/Rishi6180)/localflow-ai.git cd localflow-ai
2. Install dependencies: pip install -r requirements.txt

**Usage Guide**
1. Ensure Ollama is running in the background (ollama serve).
2. Run python app.py. A floating status pill will appear on your desktop.
3. Hold F8 to record your voice. The pill changes to 🔴 Listening....
4. Release F8 when finished. The app executes transcription and LLM cleanup.
5. The output modal presents the cleaned text; click Copy & Close to place the text directly onto your clipboard.

**License**

Distributed under the MIT License.
