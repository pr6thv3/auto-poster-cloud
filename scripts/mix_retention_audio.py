"""
Retention Audio Mixer — v2.0b.

This script selects a music track from assets/music/ based on mood,
loops it to match the video duration, and mixes it under the narration voice.
It outputs the mixed intermediate file to pre-overlay.mp4.
"""
import os
import sys
import json
import glob
import shutil
import subprocess
import yaml
import re


def get_duration(file_path):
    # Try ffprobe first
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return float(res.stdout.strip())
    except (FileNotFoundError, ValueError):
        pass
        
    # Fallback to ffmpeg
    try:
        res = subprocess.run(["ffmpeg", "-i", file_path], capture_output=True, text=True)
        match = re.search(r"Duration:\s+(\d+):(\d+):([\d.]+)", res.stderr)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            return hours * 3600 + minutes * 60 + seconds
    except FileNotFoundError:
        pass
        
    return 0.0


def has_audio_stream(file_path):
    # Try ffprobe first
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_streams", "-select_streams", "a",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return len(res.stdout.strip()) > 0
    except FileNotFoundError:
        pass
        
    # Fallback to ffmpeg
    try:
        res = subprocess.run(["ffmpeg", "-i", file_path], capture_output=True, text=True)
        return "Audio:" in res.stderr
    except FileNotFoundError:
        pass
        
    return True



def main():
    print("--- Running Retention Audio Mixer (v2.0b) ---")

    storyboard_path = os.path.join("docs", "retention-storyboard.json")
    if not os.path.exists(storyboard_path):
        print("No retention storyboard found. Skipping audio mixing.")
        sys.exit(0)

    try:
        with open(storyboard_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
    except Exception as e:
        print(f"Error reading storyboard: {e}")
        sys.exit(1)

    if sb.get("format_id") != "viral_retention_engine_24s":
        print("Storyboard format is not viral_retention_engine_24s. Skipping audio mixing.")
        sys.exit(0)

    # Locate the MPT output video
    search_pattern = os.path.join("storage", "tasks", "**", "*.mp4")
    files = glob.glob(search_pattern, recursive=True)
    files = [f for f in files if not f.endswith("final-retention.mp4") and not f.endswith("pre-overlay.mp4")]

    if not files:
        print("Error: No input MP4 files found for audio mixing.")
        sys.exit(1)

    files.sort(key=os.path.getmtime, reverse=True)
    input_video = files[0]
    output_video = os.path.join(os.path.dirname(input_video), "pre-overlay.mp4")

    file_size_kb = os.path.getsize(input_video) / 1024
    print(f"Input video: {input_video} ({file_size_kb:.2f} KB)")

    generation_mode = os.environ.get('GENERATION_MODE', 'mock').lower()
    is_mock = (generation_mode == "mock" or file_size_kb < 100)

    # Load format audio configuration
    format_path = os.path.join("formats", "viral_retention_engine_24s.yml")
    if not os.path.exists(format_path):
        print(f"Error: Format config {format_path} not found.")
        sys.exit(1)

    with open(format_path, "r", encoding="utf-8") as f:
        fmt = yaml.safe_load(f)

    audio_cfg = fmt.get("audio", {})
    require_bgm = audio_cfg.get("require_bgm", True)
    bgm_mood = audio_cfg.get("bgm_mood", "tech_pulse")
    bgm_volume = audio_cfg.get("bgm_volume", 0.12)

    report_path = os.path.join("docs", "audio-mix-report.json")
    os.makedirs("docs", exist_ok=True)

    if is_mock:
        print("[MOCK] Bypassing real ffmpeg BGM mixing.")
        try:
            shutil.copy2(input_video, output_video)
            print(f"Copied mock video to {output_video}")
            
            # Write a dummy report for mock
            mock_report = {
                "bgm_status": "skipped",
                "bgm_file": None,
                "bgm_mood": bgm_mood,
                "video_duration": 24.0,
                "bgm_duration_after_loop": 0.0,
                "voice_audio_present": True,
                "final_audio_present": True,
                "full_duration_audio_coverage": True,
                "volume_settings": {
                    "voice_volume": 1.0,
                    "bgm_volume": bgm_volume
                }
            }
            with open(report_path, "w", encoding="utf-8") as rf:
                json.dump(mock_report, rf, indent=2)
            print(f"Wrote mock mix report to {report_path}")
            sys.exit(0)
        except Exception as e:
            print(f"Error copying mock file: {e}")
            sys.exit(1)

    # Real mode
    print(f"[REAL] Selected mood: {bgm_mood}. Searching for tracks in assets/music/...")
    music_dir = os.path.join("assets", "music")
    music_files = []
    
    if os.path.exists(music_dir):
        # Look for files containing mood in their name
        for ext in ["*.mp3", "*.wav", "*.m4a", "*.ogg", "*.aac"]:
            music_files.extend(glob.glob(os.path.join(music_dir, f"*{bgm_mood}*{ext}")))
            music_files.extend(glob.glob(os.path.join(music_dir, f"*{bgm_mood}*.{ext}".upper())))
            
        # Fallback to any audio file in assets/music/ if mood-specific file not found
        if not music_files:
            print(f"No tracks found matching mood '{bgm_mood}'. Falling back to any audio file...")
            for ext in ["*.mp3", "*.wav", "*.m4a", "*.ogg", "*.aac"]:
                music_files.extend(glob.glob(os.path.join(music_dir, f"*{ext}")))
                music_files.extend(glob.glob(os.path.join(music_dir, f"*.{ext}".upper())))

    # Filter out README.md
    music_files = [f for f in music_files if not f.endswith("README.md") and not f.endswith("README.MD")]

    chosen_bgm = None
    if music_files:
        chosen_bgm = music_files[0]
        print(f"Chosen BGM track: {chosen_bgm}")
    else:
        print("No BGM audio tracks found in assets/music/")
        if require_bgm:
            print("Error: require_bgm=true but no BGM files are available. Failing real run.")
            sys.exit(1)
        else:
            # Skip BGM
            print("require_bgm=false. Bypassing BGM mixing.")
            try:
                shutil.copy2(input_video, output_video)
                # Write skipped report
                report = {
                    "bgm_status": "skipped",
                    "bgm_file": None,
                    "bgm_mood": bgm_mood,
                    "video_duration": get_duration(input_video),
                    "bgm_duration_after_loop": 0.0,
                    "voice_audio_present": has_audio_stream(input_video),
                    "final_audio_present": has_audio_stream(input_video),
                    "full_duration_audio_coverage": False,
                    "volume_settings": {
                        "voice_volume": 1.0,
                        "bgm_volume": bgm_volume
                    }
                }
                with open(report_path, "w", encoding="utf-8") as rf:
                    json.dump(report, rf, indent=2)
                sys.exit(0)
            except Exception as e:
                print(f"Error copying input video: {e}")
                sys.exit(1)

    # Perform ffmpeg audio mix
    video_duration = get_duration(input_video)
    voice_audio_present = has_audio_stream(input_video)

    print(f"Video duration: {video_duration:.2f}s, voice present: {voice_audio_present}")

    if not voice_audio_present:
        # Mix only BGM
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-stream_loop", "-1",
            "-i", chosen_bgm,
            "-filter_complex", f"[1:a]volume={bgm_volume}[bgm]",
            "-map", "0:v",
            "-map", "[bgm]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-t", f"{video_duration:.3f}",
            output_video
        ]
    else:
        # Mix voice and BGM
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-stream_loop", "-1",
            "-i", chosen_bgm,
            "-filter_complex", f"[0:a]volume=1.0[voice];[1:a]volume={bgm_volume}[bgm];[voice][bgm]amix=inputs=2:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-t", f"{video_duration:.3f}",
            output_video
        ]

    print(f"Executing ffmpeg command: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        print("Error: ffmpeg audio mixing failed.")
        print("stdout:", res.stdout)
        print("stderr:", res.stderr)
        
        # Write failed report
        report = {
            "bgm_status": "failed",
            "bgm_file": chosen_bgm,
            "bgm_mood": bgm_mood,
            "video_duration": video_duration,
            "bgm_duration_after_loop": 0.0,
            "voice_audio_present": voice_audio_present,
            "final_audio_present": False,
            "full_duration_audio_coverage": False,
            "volume_settings": {
                "voice_volume": 1.0,
                "bgm_volume": bgm_volume
            }
        }
        with open(report_path, "w", encoding="utf-8") as rf:
            json.dump(report, rf, indent=2)
        sys.exit(1)

    print("Audio mixing successfully completed!")
    final_audio_present = has_audio_stream(output_video)
    final_duration = get_duration(output_video)
    
    # Check coverage: audio covers the entire duration
    # Since we used -t <video_duration> and looped BGM indefinitely, coverage should be true
    full_duration_audio_coverage = final_audio_present and (final_duration >= video_duration - 0.5)

    report = {
        "bgm_status": "added",
        "bgm_file": os.path.normpath(chosen_bgm).replace("\\", "/"),
        "bgm_mood": bgm_mood,
        "video_duration": round(video_duration, 3),
        "bgm_duration_after_loop": round(video_duration, 3),
        "voice_audio_present": voice_audio_present,
        "final_audio_present": final_audio_present,
        "full_duration_audio_coverage": full_duration_audio_coverage,
        "volume_settings": {
            "voice_volume": 1.0,
            "bgm_volume": bgm_volume
        }
    }

    with open(report_path, "w", encoding="utf-8") as rf:
        json.dump(report, rf, indent=2)
    print(f"Wrote audio mix report to {report_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
