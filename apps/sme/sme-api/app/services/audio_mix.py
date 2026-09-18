"""Mixes voiceover + background music into one track and muxes it onto an
already-generated (silent) video, via the `ffmpeg` binary.

This is a real external system dependency, not a pip package — install it
separately (e.g. `winget install ffmpeg` on Windows, `brew install ffmpeg` on
macOS, `apt install ffmpeg` on Linux) and make sure it's on PATH. Same "gated,
not broken, if unconfigured" pattern as every other optional integration in this
codebase: `is_available()` lets the caller check up front and record a clear
audio_gen_error instead of the whole variant failing — a video without audio is
still a usable variant, so this is treated as a soft failure, never fatal.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path


def is_available() -> bool:
    return shutil.which("ffmpeg") is not None


def mix_and_mux(video_bytes: bytes, voiceover_bytes: bytes | None, music_bytes: bytes | None) -> bytes:
    """Muxes whichever audio is given onto `video_bytes` — voiceover only, music
    only, or both (ducked to 25% under the voiceover via `amix`, so a bed never
    competes with spoken narration). Raises ValueError if both are None (nothing
    to mux — the caller shouldn't reach this function in that case, but this
    keeps the failure explicit rather than silently no-op-ing). The output is
    trimmed to the video's own duration (`-shortest`) rather than looping/
    extending audio to match — a voiceover script longer than the video just
    gets cut off, which is why the LLM-written scripts are budgeted to the
    video's known duration up front (see llm.write_audio_script). Raises
    RuntimeError with ffmpeg's own stderr on failure; raises FileNotFoundError
    if ffmpeg isn't on PATH (check `is_available()` first to avoid a confusing
    raw subprocess error)."""
    if voiceover_bytes is None and music_bytes is None:
        raise ValueError("mix_and_mux needs at least one of voiceover_bytes or music_bytes")
    if not is_available():
        raise FileNotFoundError(
            "ffmpeg is not installed / not on PATH — required to mix and mux audio onto video."
        )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        video_path = tmp_path / "video.mp4"
        output_path = tmp_path / "output.mp4"
        video_path.write_bytes(video_bytes)

        if voiceover_bytes and music_bytes:
            voice_path = tmp_path / "voiceover.mp3"
            music_path = tmp_path / "music.mp3"
            voice_path.write_bytes(voiceover_bytes)
            music_path.write_bytes(music_bytes)
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(voice_path),
                "-i", str(music_path),
                "-filter_complex",
                "[2:a]volume=0.25[music];[1:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "copy", "-c:a", "aac", "-shortest",
                str(output_path),
            ]
        else:
            # Exactly one of the two is present — mux it straight through, no amix/ducking needed.
            audio_bytes = voiceover_bytes or music_bytes
            assert audio_bytes is not None  # narrowed by the ValueError check above
            audio_path = tmp_path / "audio.mp3"
            audio_path.write_bytes(audio_bytes)
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-shortest",
                str(output_path),
            ]

        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed (exit {result.returncode}): {result.stderr.decode(errors='replace')}")

        return output_path.read_bytes()
