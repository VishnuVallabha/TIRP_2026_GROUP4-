"""
SACA — Text-to-Speech engine.

Works on Windows WITHOUT pyttsx3 by using PowerShell's built-in
SpeechSynthesizer. If pyttsx3 IS installed it is used instead (better quality).

speak(text)  — non-blocking, safe from any thread or Tkinter callback.
_init_tts()  — no-op, kept for compatibility.
"""
import sys
import threading
import queue
import subprocess

_IS_WIN = (sys.platform == "win32")

_tts_queue  = queue.Queue()
_tts_ready  = threading.Event()
_tts_engine = None          # pyttsx3 engine if available
_USE_PYTTSX = False         # set True if pyttsx3 loads successfully


# ── PowerShell SAPI fallback (Windows, no extra packages) ─────────
_PS_SCRIPT = (
    "Add-Type -AssemblyName System.Speech; "
    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
    "$s.Rate = 1; "                     # -10 (slow) to 10 (fast); 1 = slightly fast, clear
    "$s.Volume = 100; "
    "$s.Speak([Console]::In.ReadToEnd())"
)


def _speak_powershell(text: str):
    """Speak using Windows PowerShell SpeechSynthesizer — no pip required."""
    try:
        proc = subprocess.Popen(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-Command", _PS_SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if _IS_WIN else 0,
        )
        proc.communicate(input=text.encode("utf-8"), timeout=30)
    except Exception as e:
        print(f"[TTS] PowerShell speak error: {e}")


def _worker():
    global _tts_engine, _USE_PYTTSX

    # ── Try pyttsx3 first (better quality) ────────────────────────
    if _IS_WIN:
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass

    try:
        import pyttsx3
        eng = pyttsx3.init()
        eng.setProperty("rate", 150)
        eng.setProperty("volume", 1.0)
        voices = eng.getProperty("voices")
        for v in voices:
            n = v.name.lower()
            if any(k in n for k in ("zira", "hazel", "karen", "female",
                                     "en-au", "en_au")):
                eng.setProperty("voice", v.id)
                break
        _tts_engine = eng
        _USE_PYTTSX = True
        print("[TTS] pyttsx3 engine ready")
    except Exception:
        _tts_engine = None
        _USE_PYTTSX = False
        if _IS_WIN:
            print("[TTS] pyttsx3 not available — using PowerShell SAPI (built-in)")
        else:
            print("[TTS] pyttsx3 not available — speech disabled on this platform")

    _tts_ready.set()

    # ── Main speak loop ────────────────────────────────────────────
    while True:
        try:
            text = _tts_queue.get(timeout=1.0)
        except queue.Empty:
            continue

        if text is None:          # shutdown sentinel
            break

        # Drain duplicates so rapid taps don't stack up
        while not _tts_queue.empty():
            try:
                _tts_queue.get_nowait()
                _tts_queue.task_done()
            except queue.Empty:
                break

        # Speak
        if _USE_PYTTSX and _tts_engine:
            try:
                _tts_engine.say(text)
                _tts_engine.runAndWait()
            except Exception as e:
                print(f"[TTS] pyttsx3 error: {e}")
                try: _tts_engine.stop()
                except Exception: pass
        elif _IS_WIN:
            _speak_powershell(text)
        # else: silently skip on non-Windows without pyttsx3

        _tts_queue.task_done()

    # Cleanup
    if _IS_WIN:
        try:
            import pythoncom
            pythoncom.CoUninitialize()
        except Exception:
            pass


# Start the worker thread at import time
_worker_thread = threading.Thread(
    target=_worker, daemon=True, name="SACA-TTS-Worker")
_worker_thread.start()


def _init_tts():
    """No-op — kept for backward compatibility."""
    pass


def speak(text: str):
    """
    Queue *text* for speech. Non-blocking. Safe from any thread.
    Uses pyttsx3 if installed, otherwise Windows PowerShell SAPI.
    """
    if not text or not text.strip():
        return
    # Wait up to 3s for engine initialisation on first call
    _tts_ready.wait(timeout=3.0)
    try:
        _tts_queue.put_nowait(text)
    except Exception:
        pass
