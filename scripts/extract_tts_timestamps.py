import os
import sys
import json
import subprocess
import glob


def main():
    print("--- Running TTS Timestamp Extractor ---")

    storyboard_path = os.path.join("docs", "retention-storyboard.json")
    if not os.path.exists(storyboard_path):
        print("No retention storyboard found. Skipping TTS timestamp extraction.")
        sys.exit(0)

    try:
        with open(storyboard_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
    except Exception as e:
        print(f"Error reading storyboard: {e}")
        sys.exit(1)

    if sb.get("format_id") != "viral_retention_engine_24s":
        print("Storyboard format is not viral_retention_engine_24s. Skipping TTS extraction.")
        sys.exit(0)

    generation_mode = os.environ.get('GENERATION_MODE', 'mock').lower()
    output_path = os.path.join("docs", "tts-timestamps.json")
    os.makedirs("docs", exist_ok=True)

    # --- MOCK MODE ---
    if generation_mode == "mock":
        print("[MOCK] Generating synthetic TTS timestamps from storyboard overlays...")
        overlays = sb.get("text_overlays", [])
        words = []
        cursor = 0.0
        for overlay in overlays:
            text = overlay.get("text", "")
            start = float(overlay.get("start_time", cursor))
            end = float(overlay.get("end_time", start + 0.5))
            overlay_words = text.split()
            if not overlay_words:
                continue
            word_duration = (end - start) / len(overlay_words)
            for w in overlay_words:
                cleaned = w.strip().lower().replace(".", "").replace(",", "").replace("!", "").replace("?", "")
                if cleaned:
                    words.append({
                        "word": cleaned,
                        "start": round(cursor, 3),
                        "end": round(cursor + word_duration, 3)
                    })
                    cursor = round(cursor + word_duration, 3)

        result = {
            "mode": "mock",
            "words": words,
            "total_duration": round(cursor, 3),
            "word_count": len(words)
        }
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"[MOCK] Wrote {len(words)} synthetic word timestamps to {output_path}")
            sys.exit(0)
        except Exception as e:
            print(f"Error writing mock timestamps: {e}")
            sys.exit(1)

    # --- REAL MODE ---
    print("[REAL] Extracting TTS word-level timestamps from video audio...")

    # 1. Locate the MPT output video (before retention post-processing)
    search_pattern = os.path.join("storage", "tasks", "**", "*.mp4")
    files = glob.glob(search_pattern, recursive=True)
    # Filter out already post-processed videos
    files = [f for f in files if not f.endswith("final-retention.mp4") and not f.endswith("pre-overlay.mp4")]

    if not files:
        print("Error: No input MP4 files found for TTS extraction.")
        sys.exit(1)

    files.sort(key=os.path.getmtime, reverse=True)
    input_video = files[0]
    print(f"Input video for TTS extraction: {input_video}")

    # 2. Extract audio track to WAV (16kHz mono for Whisper)
    audio_wav = os.path.join(os.path.dirname(input_video), "tts_audio_extract.wav")
    extract_cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        audio_wav
    ]
    print(f"Extracting audio: {' '.join(extract_cmd)}")
    try:
        res = subprocess.run(extract_cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error: ffmpeg audio extraction failed: {res.stderr}")
            sys.exit(1)
        print(f"Audio extracted to {audio_wav}")
    except Exception as e:
        print(f"Error extracting audio: {e}")
        sys.exit(1)

    # 3. Run faster-whisper for word-level timestamps
    # Using 'base' model — TTS audio is single-voice, clean, no background noise.
    # A larger model solves a harder problem than we have.
    whisper_model_size = os.environ.get("WHISPER_MODEL_SIZE", "base")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("Error: faster-whisper is not installed. Run: pip install faster-whisper")
        sys.exit(1)

    print(f"[REAL] Loading faster-whisper '{whisper_model_size}' model for word-level transcription...")
    try:
        model = WhisperModel(whisper_model_size, device="cpu", compute_type="int8")
        segments, info = model.transcribe(
            audio_wav,
            word_timestamps=True,
            language="en"
        )
        # faster-whisper returns a generator, materialize it
        segments_list = list(segments)
    except Exception as e:
        print(f"Error running faster-whisper transcription: {e}")
        sys.exit(1)

    print(f"[REAL] Detected language: {info.language} (probability {info.language_probability:.2f})")
    print(f"[REAL] Audio duration: {info.duration:.2f}s")

    # 4. Extract word-level timestamps from faster-whisper result
    words = []
    full_transcript = ""
    for segment in segments_list:
        full_transcript += segment.text
        if segment.words:
            for w in segment.words:
                word_text = w.word.strip().lower()
                word_text = word_text.replace(".", "").replace(",", "").replace("!", "").replace("?", "")
                if word_text:
                    words.append({
                        "word": word_text,
                        "start": round(w.start, 3),
                        "end": round(w.end, 3)
                    })

    if not words:
        print("Warning: faster-whisper returned no word-level timestamps. Falling back to segment-level.")
        for segment in segments_list:
            seg_text = segment.text.strip()
            if seg_text:
                seg_words = seg_text.split()
                seg_start = segment.start
                seg_end = segment.end
                seg_duration = seg_end - seg_start
                word_dur = seg_duration / max(len(seg_words), 1)
                for i, sw in enumerate(seg_words):
                    cleaned = sw.strip().lower().replace(".", "").replace(",", "").replace("!", "").replace("?", "")
                    if cleaned:
                        words.append({
                            "word": cleaned,
                            "start": round(seg_start + i * word_dur, 3),
                            "end": round(seg_start + (i + 1) * word_dur, 3)
                        })

    # Calculate total audio duration
    total_duration = info.duration if info.duration else 0.0
    if not total_duration and words:
        total_duration = words[-1]["end"]

    timestamp_data = {
        "mode": "real",
        "words": words,
        "total_duration": round(total_duration, 3),
        "word_count": len(words),
        "whisper_model": whisper_model_size,
        "whisper_backend": "faster-whisper",
        "full_transcript": full_transcript.strip()
    }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(timestamp_data, f, indent=2)
        print(f"[REAL] Extracted {len(words)} word-level timestamps to {output_path}")
        print(f"[REAL] Total audio duration: {total_duration:.2f}s")
        print(f"[REAL] Transcript: {full_transcript.strip()[:200]}")
    except Exception as e:
        print(f"Error writing timestamps: {e}")
        sys.exit(1)

    # 5. Clean up temp audio file
    try:
        os.remove(audio_wav)
        print(f"Cleaned up temp audio: {audio_wav}")
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
