import os
import sys
import json
import glob
import subprocess

def main():
    print("--- Running Format Fidelity Validator ---")
    
    storyboard_path = os.path.join("docs", "retention-storyboard.json")
    if not os.path.exists(storyboard_path):
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
            
    print("Storyboard parameters validated successfully.")
    
    # 6. Video duration is between 18s and 32s
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
            
    print("Fidelity validation completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
