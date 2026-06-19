import os
import glob
import sys
import json
import subprocess

def probe_video(video_path):
    print(f"[REAL] Probing video file with ffprobe: {video_path}")
    
    # 1. Probe video stream details
    cmd_v = [
        "ffprobe", 
        "-v", "error", 
        "-select_streams", "v:0", 
        "-show_entries", "stream=codec_name,width,height,duration", 
        "-of", "json", 
        video_path
    ]
    res_v = subprocess.run(cmd_v, capture_output=True, text=True)
    if res_v.returncode != 0:
        raise Exception(f"ffprobe video stream check failed: {res_v.stderr}")
        
    v_data = json.loads(res_v.stdout)
    if not v_data.get("streams"):
        raise Exception("No video streams found in the file.")
    v_stream = v_data["streams"][0]
    
    # 2. Probe audio stream details
    cmd_a = [
        "ffprobe", 
        "-v", "error", 
        "-select_streams", "a:0", 
        "-show_entries", "stream=codec_name", 
        "-of", "json", 
        video_path
    ]
    res_a = subprocess.run(cmd_a, capture_output=True, text=True)
    a_codec = ""
    if res_a.returncode == 0:
        a_data = json.loads(res_a.stdout)
        if a_data.get("streams"):
            a_codec = a_data["streams"][0].get("codec_name", "")
            
    # 3. Get duration
    duration = v_stream.get("duration")
    if not duration or duration == "N/A":
        # Fallback to format duration
        cmd_f = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "json", 
            video_path
        ]
        res_f = subprocess.run(cmd_f, capture_output=True, text=True)
        if res_f.returncode == 0:
            f_data = json.loads(res_f.stdout)
            duration = f_data.get("format", {}).get("duration")
            
    if not duration or duration == "N/A":
        raise Exception("Could not determine video duration.")
        
    return {
        "width": int(v_stream.get("width", 0)),
        "height": int(v_stream.get("height", 0)),
        "duration": float(duration),
        "video_codec": v_stream.get("codec_name", ""),
        "audio_codec": a_codec
    }

def main():
    print("--- Running Video Detection and Validation ---")
    generation_mode = os.environ.get('GENERATION_MODE', 'mock').lower()
    
    # Scan for MP4 files recursively
    search_pattern = os.path.join("storage", "tasks", "**", "*.mp4")
    files = glob.glob(search_pattern, recursive=True)
    
    if not files:
        print("Error: No video files found in storage/tasks/")
        sys.exit(1)
        
    # Sort files by modification time, newest first
    files.sort(key=os.path.getmtime, reverse=True)
    latest_video = files[0]
    
    file_size_bytes = os.path.getsize(latest_video)
    file_size_kb = file_size_bytes / 1024
    print(f"Detected latest video: {latest_video}")
    print(f"File size: {file_size_kb:.2f} KB")
    
    # 1. Size Validation
    if file_size_kb < 100:
        print(f"Error: Video file size ({file_size_kb:.2f} KB) is under the 100 KB threshold.")
        sys.exit(1)
        
    video_info = {
        "video_path": latest_video,
        "size_bytes": file_size_bytes,
        "width": 1080,
        "height": 1920,
        "duration": 15.0,
        "video_codec": "h264",
        "audio_codec": "aac",
        "validation": "mocked"
    }

    if generation_mode == "real":
        try:
            probed = probe_video(latest_video)
            video_info.update(probed)
            video_info["validation"] = "passed"
            
            # Run checks
            # Duration <= 60 seconds
            if video_info["duration"] > 60.0:
                print(f"Error: Video duration {video_info['duration']}s exceeds maximum of 60 seconds.")
                sys.exit(1)
                
            # Vertical orientation (9:16)
            width = video_info["width"]
            height = video_info["height"]
            if height <= width:
                print(f"Error: Video is not vertical (width={width}, height={height}).")
                sys.exit(1)
            
            aspect_ratio = width / height
            if not (0.4 <= aspect_ratio <= 0.65):
                print(f"Error: Video aspect ratio {width}:{height} is not close to 9:16 (ratio={aspect_ratio:.2f}).")
                sys.exit(1)
                
            # Video codec H.264
            if video_info["video_codec"] != "h264":
                print(f"Error: Video codec is {video_info['video_codec']}, must be h264.")
                sys.exit(1)
                
            # Audio codec AAC (if audio exists)
            if not video_info["audio_codec"]:
                print("Error: No audio stream found, or format could not be verified.")
                sys.exit(1)
            elif video_info["audio_codec"] != "aac":
                print(f"Error: Audio codec is {video_info['audio_codec']}, must be aac.")
                sys.exit(1)
                
            print("Video metadata and codec validation passed successfully.")
            
        except Exception as e:
            print(f"Validation critical error: {e}")
            sys.exit(1)
    else:
        print("[MOCK] Bypassing ffprobe checks for mock video generation.")

    # Write video-info.json
    with open("video-info.json", "w", encoding="utf-8") as f:
        json.dump(video_info, f, indent=2)
    print(f"Wrote video-info.json:\n{json.dumps(video_info, indent=2)}")

    # Write the output path to GitHub step output
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"video_path={latest_video}\n")
        print(f"Wrote video_path to GitHub outputs.")

if __name__ == "__main__":
    main()
