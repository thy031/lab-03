#!/usr/bin/env python3
"""Narrated presentation: footage from media/video.mp4, scripts from this file."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from gtts import gTTS
from imageio_ffmpeg import get_ffmpeg_exe
from moviepy import AudioFileClip, VideoFileClip

FFMPEG = get_ffmpeg_exe()

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "media" / "video.mp4"
OUT = ROOT / "media" / "greedy_pair_merge_presentation.mp4"
WORK = ROOT / "slides" / "video_frames"

slide_data = [
    {
        "t": 0.08,
        "script": "Greedy pair merge is the simplest coarsening engine that still feels like CAD. We repeatedly merge the most attractive legal pair.",
    },
    {
        "t": 0.32,
        "script": "Agglomerative clustering begins with five singletons. Edge A-B has the highest weight of 5 and merges first into a supernode.",
    },
    {
        "t": 0.58,
        "script": "After contraction, C connects to AB with combined weight 5, tying D-E. Lexicographical tie-breaking merges C next to form A-B-C.",
    },
    {
        "t": 0.82,
        "script": "Finally, D and E merge at weight 5. We reach our target of two clusters with a final cutsize of 3.",
    },
]


def ff(*args: str) -> None:
    r = subprocess.run([FFMPEG, "-y", *args], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])


def create_presentation_video(output_filename: str = str(OUT)) -> None:
    if not SOURCE.exists():
        raise SystemExit(f"missing source video: {SOURCE}")
    WORK.mkdir(parents=True, exist_ok=True)
    src = VideoFileClip(str(SOURCE))
    total = float(src.duration or 1)
    src.close()

    parts: list[Path] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for idx, slide in enumerate(slide_data):
            mp3 = tmp_path / f"n{idx}.mp3"
            gTTS(text=slide["script"], lang="en", slow=False).save(str(mp3))
            dur = AudioFileClip(str(mp3)).duration + 0.5
            t0 = min(max(slide["t"] * total, 0.0), max(total - dur, 0.0))
            clip_path = tmp_path / f"c{idx}.mp4"
            ff(
                "-ss", f"{t0:.3f}",
                "-i", str(SOURCE),
                "-i", str(mp3),
                "-t", f"{dur:.3f}",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-shortest",
                str(clip_path),
            )
            still = WORK / f"slide{idx + 1}.png"
            ff("-ss", f"{t0:.3f}", "-i", str(SOURCE), "-frames:v", "1", str(still))
            parts.append(clip_path)
            print(f"clip {idx + 1}: source {t0:.1f}s + {dur:.1f}s narration")

        listing = tmp_path / "list.txt"
        listing.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
        Path(output_filename).parent.mkdir(parents=True, exist_ok=True)
        ff(
            "-f", "concat",
            "-safe", "0",
            "-i", str(listing),
            "-c", "copy",
            output_filename,
        )

    print(f"\nVideo successfully exported to: {output_filename}")


if __name__ == "__main__":
    create_presentation_video()
