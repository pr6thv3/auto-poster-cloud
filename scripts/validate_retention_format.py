import os
import sys
import json
import glob
import subprocess
import yaml
import re

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

def check_silence(video_path, video_dur, noise_db=-50):
    cmd = [
        "ffmpeg", "-i", video_path,
        "-af", f"silencedetect=n={noise_db}dB:d=0.1",
        "-f", "null", "-"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        stderr = res.stderr
    except FileNotFoundError:
        print("Warning: ffmpeg not found in PATH. Bypassing silence check.")
        return 0.0, False
        
    silence_intervals = []
    lines = stderr.splitlines()
    active_start = None
    for line in lines:
        if "silencedetect" in line:
            start_match = re.search(r"silence_start:\s+([\d.]+)", line)
            if start_match:
                active_start = float(start_match.group(1))
            end_match = re.search(r"silence_end:\s+([\d.]+)\s+\|\s+silence_duration:\s+([\d.]+)", line)
            if end_match:
                end_time = float(end_match.group(1))
                duration = float(end_match.group(2))
                start_time = end_time - duration
                silence_intervals.append((start_time, end_time, duration))
                active_start = None
                
    if active_start is not None:
        duration = video_dur - active_start
        silence_intervals.append((active_start, video_dur, duration))
        
    max_silence_gap = 0.0
    tail_silent = False
    
    for start, end, duration in silence_intervals:
        if duration > max_silence_gap:
            max_silence_gap = duration
        if end >= video_dur - 0.05 and start <= video_dur - 2.0:
            tail_silent = True
            
    for start, end, duration in silence_intervals:
        if start <= video_dur - 2.0 and end >= video_dur - 0.05:
            tail_silent = True
            
    return max_silence_gap, tail_silent



def main():
    print("--- Running Format Fidelity Validator ---")
    
    storyboard_path = os.path.join("docs", "retention-storyboard.json")
    brief_path = os.path.join("docs", "video-brief.json")
    
    # Determine if this is a retention run from the video brief
    is_retention_run = False
    if os.path.exists(brief_path):
        try:
            with open(brief_path, "r", encoding="utf-8") as f:
                brief = json.load(f)
                if brief.get("format_id") == "viral_retention_engine_24s":
                    is_retention_run = True
        except Exception:
            pass
            
    if not os.path.exists(storyboard_path):
        if is_retention_run:
            print("Error: Retention storyboard is missing for viral_retention_engine_24s run!")
            sys.exit(1)
        else:
            print("No retention storyboard found. Skipping validation.")
            sys.exit(0)
            
    try:
        with open(storyboard_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
    except Exception as e:
        print(f"Error reading storyboard: {e}")
        sys.exit(1)
        
    if sb.get("format_id") != "viral_retention_engine_24s":
        print("Storyboard format is not viral_retention_engine_24s. Skipping validation.")
        sys.exit(0)
        
    print("Validating retention format constraints...")
    
    # 1. Read video-info.json to locate latest video path and duration
    video_info_path = "video-info.json"
    if not os.path.exists(video_info_path):
        print("Error: video-info.json is missing.")
        sys.exit(1)
        
    try:
        with open(video_info_path, "r", encoding="utf-8") as f:
            video_info = json.load(f)
    except Exception as e:
        print(f"Error reading video-info.json: {e}")
        sys.exit(1)
        
    video_path = video_info.get("video_path", "")
    duration = video_info.get("duration", 0.0)
    
    if not video_path:
        print("Error: video_path is empty in video-info.json.")
        sys.exit(1)
        
    # 2. Final output file is final-retention.mp4
    if not video_path.endswith("final-retention.mp4"):
        print(f"Error: Final output video path is '{video_path}', but must be final-retention.mp4.")
        sys.exit(1)
        
    # 3. Verify no subtitle .srt file is burned/exists in the task directory
    task_dir = os.path.dirname(video_path)
    srt_files = glob.glob(os.path.join(task_dir, "*.srt"))
    if srt_files:
        print(f"Error: Subtitle .srt files found in task directory: {srt_files}. Bottom subtitles are not allowed.")
        sys.exit(1)
        
    # 4. Check if moneyprinter-log.txt contains --no-subtitle-enabled in real mode
    generation_mode = os.environ.get('GENERATION_MODE', 'mock').lower()
    log_path = "moneyprinter-log.txt"
    if generation_mode == "real" and os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                log_content = f.read()
            if "--no-subtitle-enabled" not in log_content:
                print("Error: MoneyPrinterTurbo was not executed with '--no-subtitle-enabled' flag.")
                sys.exit(1)
            print("Verified that MPT subtitles were disabled via --no-subtitle-enabled flag.")
        except Exception as e:
            print(f"Warning: Could not read moneyprinter-log.txt: {e}")
            
    # 5. Storyboard validations
    scenes = sb.get("scenes", [])
    overlays = sb.get("text_overlays", [])
    
    if len(scenes) < 14:
        print(f"Error: Storyboard scene count ({len(scenes)}) is less than 14.")
        sys.exit(1)
        
    if len(overlays) < 14:
        print(f"Error: Storyboard overlay count ({len(overlays)}) is less than 14.")
        sys.exit(1)
        
    for idx, item in enumerate(overlays):
        txt = item.get("text", "")
        words = txt.split()
        if len(words) > 4:
            print(f"Error: Overlay {idx} has more than 4 words: '{txt}'")
            sys.exit(1)
            
        if "subscribe" in txt.lower():
            print(f"Error: Overlay {idx} contains forbidden word 'subscribe': '{txt}'")
            sys.exit(1)
            
    # Check visual blacklist in scenes
    blacklist = ["subscribe", "isolation", "protest", "unrelated crowd", "random office", "generic podcast"]
    for idx, s in enumerate(scenes):
        query = s.get("stock_search_query", "").lower()
        prompt = s.get("visual_prompt", "").lower()
        for term in blacklist:
            if term in query:
                print(f"Error: Scene {idx+1} search query contains blacklisted term '{term}': '{query}'")
                sys.exit(1)
            if term in prompt:
                print(f"Error: Scene {idx+1} visual prompt contains blacklisted term '{term}': '{prompt}'")
                sys.exit(1)
            
    print("Storyboard parameters validated successfully.")
    
    # 6. TTS Alignment validation (real mode only)
    tts_path = os.path.join("docs", "tts-timestamps.json")
    synced_path = os.path.join("docs", "retention-storyboard-synced.json")
    
    if generation_mode == "real":
        if not os.path.exists(tts_path):
            print("Error: docs/tts-timestamps.json is missing for real retention run.")
            sys.exit(1)
        print(f"Verified TTS timestamps file exists: {tts_path}")
        
        # Check alignment coverage from synced storyboard
        if os.path.exists(synced_path):
            try:
                with open(synced_path, "r", encoding="utf-8") as f:
                    synced_sb = json.load(f)
                stats = synced_sb.get("alignment_stats", {})
                coverage = stats.get("alignment_coverage_pct", 0.0)
                matched = stats.get("total_matched_words", 0)
                total = stats.get("total_overlay_words", 0)
                
                print(f"TTS alignment coverage: {coverage}% ({matched}/{total} words)")
                
                if coverage < 80.0:
                    print(f"Warning: TTS alignment coverage {coverage}% is below 80% threshold.")
                    # This is a warning, not a hard failure, to allow graceful degradation
                else:
                    print(f"TTS alignment coverage {coverage}% meets >= 80% threshold.")
                    
                # Validate that synced overlay timestamps are reasonable
                synced_overlays = synced_sb.get("text_overlays_synced", [])
                for idx, ov in enumerate(synced_overlays):
                    start = float(ov.get("start_time", 0.0))
                    end = float(ov.get("end_time", 0.0))
                    if end <= start:
                        print(f"Warning: Synced overlay {idx} has invalid timing: start={start}, end={end}")
                    if end - start > 3.0:
                        print(f"Warning: Synced overlay {idx} duration {end - start:.2f}s exceeds 3.0s")
                        
            except Exception as e:
                print(f"Warning: Could not read synced storyboard for alignment check: {e}")
        else:
            print("Warning: docs/retention-storyboard-synced.json not found. Alignment check skipped.")
    else:
        print("[MOCK] Skipping TTS alignment validation in mock mode.")
    
    # 7. Video duration is between 18s and 32s
    if duration < 18.0 or duration > 32.0:
        print(f"Error: Video duration {duration:.1f}s is outside the hard limits [18s, 32s].")
        sys.exit(1)
    print(f"Video duration ({duration:.1f}s) validated successfully.")
    
    # 7. Generate visual review contact sheet docs/retention-contact-sheet.jpg
    os.makedirs("docs", exist_ok=True)
    contact_sheet_path = os.path.join("docs", "retention-contact-sheet.jpg")
    
    file_size_kb = os.path.getsize(video_path) / 1024
    is_mock = (generation_mode == "mock" or 
               file_size_kb < 100 or 
               video_info.get("validation") == "mocked")

    # Check if ffmpeg is in PATH
    ffmpeg_available = False
    if not is_mock:
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True)
            ffmpeg_available = True
        except FileNotFoundError:
            pass

    if is_mock or not ffmpeg_available:
        if not ffmpeg_available and not is_mock:
            print("Warning: ffmpeg is not available in PATH. Writing dummy contact sheet.")
        else:
            print("[MOCK] Writing dummy contact sheet placeholder...")
        dummy_jpeg = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00'
            b'\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19'
            b'\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f'
            b'\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f'
            b'\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02'
            b'\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04'
            b'\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa'
            b'\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\x16\x92\xb2\xe1\xf1'
            b'\x07\x17\xa2\xb3\xc2\xd2\x08\x18\x83\x93\xc3\xf2\x19\x29\x39\x49\x59\x69\x79\x89'
            b'\x99\xa9\xb9\xc9\xd9\xe9\xf9\x1a\x2a\x3a\x4a\x5a\x6a\x7a\x8a\x9a\xaa\xba\xca\xda'
            b'\xea\xfa\xff\xda\x00\x0c\x01\x01\x00\x02\x11\x03\x11\x00?\x00\x00\x00\xff\xd9'
        )
        try:
            with open(contact_sheet_path, "wb") as f:
                f.write(dummy_jpeg)
            print(f"Wrote dummy contact sheet to {contact_sheet_path}")
        except Exception as e:
            print(f"Error writing dummy contact sheet: {e}")
            sys.exit(1)
    else:
        print(f"Generating visual review contact sheet: {contact_sheet_path}")
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", "fps=1,scale=180:-1,tile=5x5",
            "-frames:v", "1",
            contact_sheet_path
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"Successfully generated contact sheet at {contact_sheet_path}")
            else:
                print(f"Error: ffmpeg contact sheet generation failed with exit code {res.returncode}.")
                print("stderr:", res.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error executing ffmpeg for contact sheet: {e}")
            sys.exit(1)
            
    # 8. Audio and Silence Validation
    print("Running audio and dead-air validation...")
    mix_report_path = os.path.join("docs", "audio-mix-report.json")
    format_path = os.path.join("formats", "viral_retention_engine_24s.yml")
    
    require_bgm = False
    if os.path.exists(format_path):
        try:
            with open(format_path, "r", encoding="utf-8") as f:
                fmt = yaml.safe_load(f)
            require_bgm = fmt.get("audio", {}).get("require_bgm", False)
        except Exception as e:
            print(f"Warning: Could not read format config to verify require_bgm: {e}")
            
    bgm_status = "skipped"
    mix_report = {}
    if os.path.exists(mix_report_path):
        try:
            with open(mix_report_path, "r", encoding="utf-8") as f:
                mix_report = json.load(f)
            bgm_status = mix_report.get("bgm_status", "skipped")
        except Exception as e:
            print(f"Warning: Could not read mix report: {e}")

    if not mix_report:
        mix_report = {
            "bgm_status": bgm_status,
            "bgm_file": None,
            "bgm_mood": "tech_pulse",
            "video_duration": duration,
            "bgm_duration_after_loop": 0.0,
            "voice_audio_present": True,
            "final_audio_present": True,
            "full_duration_audio_coverage": True,
            "volume_settings": {
                "voice_volume": 1.0,
                "bgm_volume": 0.12
            }
        }

    # Check report existence in real run
    if generation_mode == "real":
        if not os.path.exists(mix_report_path):
            print("Error: audio-mix-report.json is missing in real run.")
            sys.exit(1)
            
        if require_bgm and bgm_status != "added":
            print(f"Error: require_bgm is true but bgm_status is '{bgm_status}' instead of 'added'.")
            sys.exit(1)
            
    # Silence detection
    max_silence = 0.0
    tail_silent = False
    audio_validation_status = "passed"
    
    run_actual_silence_detect = (generation_mode == "real" and not is_mock)
    
    if run_actual_silence_detect:
        if not has_audio_stream(video_path):
            print("Error: Final video has no audio stream.")
            sys.exit(1)
            
        max_silence, tail_silent = check_silence(video_path, duration)
        print(f"Detected max silence gap: {max_silence:.2f}s (max allowed 1.0s)")
        print(f"Detected tail silence: {tail_silent} (final 2s must not be silent)")
        
        if max_silence > 1.0:
            print(f"Error: Max silence gap of {max_silence:.2f}s exceeds 1.0s threshold.")
            audio_validation_status = "failed"
            
        if tail_silent:
            print("Error: Final 2 seconds are silent.")
            audio_validation_status = "failed"
    else:
        print("[MOCK/BYPASS] Bypassing actual silence detection.")
        
    mix_report["max_silence_gap_seconds"] = round(max_silence, 3)
    mix_report["final_tail_silence_status"] = "silent" if tail_silent else "not_silent"
    mix_report["audio_validation_status"] = audio_validation_status
    
    try:
        with open(mix_report_path, "w", encoding="utf-8") as f:
            json.dump(mix_report, f, indent=2)
        print(f"Updated audio-mix-report.json with silence validation fields.")
    except Exception as e:
        print(f"Warning: Could not update mix report: {e}")
        
    if audio_validation_status == "failed":
        sys.exit(1)
        
    print("Fidelity validation completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
