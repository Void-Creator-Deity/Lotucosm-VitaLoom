#!/usr/bin/env python3
"""Generate the PVAEC sample project's short SR session audio cues."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path


def write_tone(path: Path, freqs: list[tuple[float, float]], duration: float = 0.35, volume: float = 0.35) -> None:
    sr = 22050
    n = int(sr * duration)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        frames = bytearray()
        for i in range(n):
            t = i / sr
            env = min(1.0, t / 0.02) * max(0.0, 1.0 - (t - duration * 0.6) / (duration * 0.4))
            sample = 0.0
            for freq, weight in freqs:
                sample += weight * math.sin(2 * math.pi * freq * t)
            val = int(32767 * volume * env * sample)
            val = max(-32767, min(32767, val))
            frames.extend(struct.pack("<h", val))
        w.writeframes(bytes(frames))


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    out = project_root / "assets" / "audio"
    write_tone(out / "victory.wav", [(523.25, 0.5), (659.25, 0.35), (783.99, 0.25)], duration=0.45)
    write_tone(out / "extinction.wav", [(220.0, 0.6), (185.0, 0.4)], duration=0.55, volume=0.28)
    print("Wrote", out / "victory.wav", out / "extinction.wav")


if __name__ == "__main__":
    main()
