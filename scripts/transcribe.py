"""Word-level Vietnamese transcript with faster-whisper.

usage: python transcribe.py <video_or_audio> <out_words.json> [--model small|medium|large-v3]
Output: [{"w": "Video", "s": 0.00, "e": 0.32}, ...]  (flat list of words, seconds)
"""
import argparse
import json
import subprocess
import wave

import numpy as np
from faster_whisper import WhisperModel

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("out")
ap.add_argument("--model", default="small")
ap.add_argument("--lang", default="vi")  # "auto" = detect
a = ap.parse_args()

# Decode with ffmpeg ourselves: PyAV versions bundled with faster-whisper vary and break decode_audio.
wav = a.out + ".16k.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.src, "-ac", "1", "-ar", "16000", wav], check=True)
w = wave.open(wav)
audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

model = WhisperModel(a.model, device="cpu", compute_type="int8")
segs, _ = model.transcribe(audio, language=None if a.lang == "auto" else a.lang, word_timestamps=True, vad_filter=False)
words = []
for s in segs:
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}", flush=True)
    for x in s.words:
        words.append({"w": x.word.strip(), "s": round(x.start, 3), "e": round(x.end, 3)})
json.dump(words, open(a.out, "w"), ensure_ascii=False, indent=1)
print(f"{len(words)} words -> {a.out}")
