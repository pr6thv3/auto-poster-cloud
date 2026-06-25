import os
import sys
import json
import subprocess
import glob
import shutil

def get_system_font():
    # Candidates for Linux, Windows, and macOS
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "C\\:/Windows/Fonts/arialbd.ttf",
        "C\\:/Windows/Fonts/arial.ttf",
        "C\\:/Windows/Fonts/tahoma.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    for c in candidates:
        unescaped = c.replace("C\\:", "C:").replace("\\", "/")
        if os.path.exists(unescaped):
            return c
    return None

def main():
    print("--- Running Retention Post-Processing Layer ---")
    
    storyboard_path = os.path.join("docs", "retention-storyboard.json")
    if not os.path.exists(storyboard_path):
        print("No retention storyboard found. Skipping post-processing.")
        sys.exit(0)
        
    try:
        with open(storyboard_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
    except Exception as e:
        print(f"Error reading storyboard: {e}")
        sys.exit(1)
        
    if sb.get("format_id") != "viral_retention_engine_24s":
        print("Storyboard format is not viral_retention_engine_24s. Skipping post-processing.")
        sys.exit(0)
        
    # Scan for MP4 files in storage/tasks/ recursively
    search_pattern = os.path.join("storage", "tasks", "**", "*.mp4")
    files = glob.glob(search_pattern, recursive=True)
    
    # Filter out already post-processed videos
    files = [f for f in files if not f.endswith("final-retention.mp4")]
    
    if not files:
        print("Error: No input MP4 files found for post-processing.")
        sys.exit(1)
        
    # Get newest MP4 file
    files.sort(key=os.path.getmtime, reverse=True)
    input_video = files[0]
    file_size_kb = os.path.getsize(input_video) / 1024
    print(f"Input video detected: {input_video} ({file_size_kb:.2f} KB)")
    
    output_video = os.path.join(os.path.dirname(input_video), "final-retention.mp4")
    
    generation_mode = os.environ.get('GENERATION_MODE', 'mock').lower()
    is_mock = generation_mode == "mock" or file_size_kb < 100
    
    # If in mock mode or input file is too small, bypass post-processing to avoid ffmpeg errors
    if is_mock:
        print("[MOCK] Mock mode or dummy file detected. Bypassing ffmpeg post-processing.")
        try:
            shutil.copy2(input_video, output_video)
            print(f"[MOCK] Copied mock video to {output_video}")
            sys.exit(0)
        except Exception as e:
            print(f"Failed to copy mock file: {e}")
            sys.exit(1)
            
    overlays = sb.get("text_overlays", [])
    if not overlays:
        print("Error: No text overlays defined in storyboard.")
        sys.exit(1)
        
    font_path = get_system_font()
    if not font_path:
        print("Warning: No system fonts found. Text overlays might fail if fontfile parameter is omitted.")
        
    # Build filter graph using start_time and end_time
    filters = []
    font_clause = f"fontfile='{font_path}':" if font_path else ""
    
    for item in overlays:
        text = item.get("text", "").replace("'", "\\'").replace(":", "\\:")
        start = float(item.get("start_time", 0.0))
        end = float(item.get("end_time", 0.0))
        
        # Center-screen overlay drawtext filter with large bold styling, black shadow, and black border stroke
        f_str = (
            f"drawtext={font_clause}"
            f"text='{text}':"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"fontsize=72:fontcolor=white:"
            f"borderw=4:bordercolor=black:"
            f"shadowcolor=black:shadowx=4:shadowy=4:"
            f"enable='between(t\\,{start:.2f}\\,{end:.2f})'"
        )
        filters.append(f_str)
        
    filter_graph = ",".join(filters)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", filter_graph,
        "-codec:a", "copy",
        output_video
    ]
    
    print(f"Executing ffmpeg post-processing to generate retention styled video: {output_video}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Successfully completed post-processing overlay rendering! Output: {output_video}")
            sys.exit(0)
        else:
            print(f"Error: ffmpeg post-processing failed with exit code {res.returncode}.")
            print("stderr:", res.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to execute post-processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
