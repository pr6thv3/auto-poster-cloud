import os
import sys
import json
import subprocess
import glob

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
        # Check if file exists (unescaped path for os.path.exists check)
        unescaped = c.replace("C\\:", "C:").replace("\\", "/")
        if os.path.exists(unescaped):
            return c
    return None

def parse_range_to_seconds(tr_str):
    parts = tr_str.split("-")
    if len(parts) != 2:
        return 0.0, 0.0
    
    def to_sec(t_str):
        t_str = t_str.strip()
        parts_colon = t_str.split(":")
        if len(parts_colon) == 2:
            return float(parts_colon[0]) * 60 + float(parts_colon[1])
        elif len(parts_colon) == 3:
            return float(parts_colon[0]) * 3600 + float(parts_colon[1]) * 60 + float(parts_colon[2])
        return float(t_str)
        
    try:
        return to_sec(parts[0]), to_sec(parts[1])
    except Exception:
        return 0.0, 0.0

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
        sys.exit(0)
        
    if sb.get("format_id") != "viral_retention_engine_24s":
        print("Storyboard format is not viral_retention_engine_24s. Skipping post-processing.")
        sys.exit(0)
        
    # Scan for MP4 files in storage/tasks/ recursively
    search_pattern = os.path.join("storage", "tasks", "**", "*.mp4")
    files = glob.glob(search_pattern, recursive=True)
    
    # Filter out already post-processed videos if any
    files = [f for f in files if not f.endswith("final-retention.mp4")]
    
    if not files:
        print("No input MP4 files found for post-processing.")
        sys.exit(0)
        
    # Get newest MP4 file
    files.sort(key=os.path.getmtime, reverse=True)
    input_video = files[0]
    file_size_kb = os.path.getsize(input_video) / 1024
    print(f"Input video detected: {input_video} ({file_size_kb:.2f} KB)")
    
    # If the input file is too small (e.g. a mock dummy file), bypass post-processing to avoid ffmpeg errors
    if file_size_kb < 100:
        print("[MOCK] Input is a mock dummy file. Bypassing ffmpeg post-processing.")
        # Just copy input to final-retention.mp4 for mock validation
        output_video = input_video.replace(".mp4", "-retention.mp4")
        try:
            with open(input_video, "rb") as f_in, open(output_video, "wb") as f_out:
                f_out.write(f_in.read())
            print(f"[MOCK] Copied mock video to {output_video}")
            sys.exit(0)
        except Exception as e:
            print(f"Failed to copy mock file: {e}")
            sys.exit(0)
            
    overlays = sb.get("text_overlays", [])
    if not overlays:
        print("No text overlays defined in storyboard. Skipping.")
        sys.exit(0)
        
    font_path = get_system_font()
    if not font_path:
        print("Warning: No system fonts found. Text overlays might fail if fontfile parameter is omitted.")
        
    # Build filter graph
    filters = []
    font_clause = f"fontfile='{font_path}':" if font_path else ""
    
    for item in overlays:
        text = item.get("text", "").replace("'", "\\'").replace(":", "\\:")
        tr = item.get("time_range", "")
        start, end = parse_range_to_seconds(tr)
        
        # Center-screen overlay drawtext filter
        f_str = (
            f"drawtext={font_clause}"
            f"text='{text}':"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"fontsize=68:fontcolor=white:"
            f"shadowcolor=black:shadowx=4:shadowy=4:"
            f"enable='between(t,{start:.2f},{end:.2f})'"
        )
        filters.append(f_str)
        
    filter_graph = ",".join(filters)
    output_video = input_video.replace(".mp4", "-retention.mp4")
    
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
            print("Successfully completed post-processing overlay rendering!")
            # Replace original MP4 with post-processed version to ensure subsequent GHA upload maps correctly
            os.remove(input_video)
            os.rename(output_video, input_video)
            print(f"Replaced {input_video} with post-processed video.")
        else:
            print(f"Warning: ffmpeg post-processing failed with exit code {res.returncode}.")
            print("stderr:", res.stderr)
            print("Preserving the original MP4 video intact.")
    except Exception as e:
        print(f"Warning: Failed to execute post-processing: {e}")
        print("Preserving the original MP4 video intact.")

if __name__ == "__main__":
    main()
