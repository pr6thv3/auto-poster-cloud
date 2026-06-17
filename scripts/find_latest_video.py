import os
import glob
import sys

def main():
    print("--- Running Video Detection Script ---")
    
    # We scan recursively for all .mp4 files inside the storage/tasks directory
    search_pattern = os.path.join("storage", "tasks", "**", "*.mp4")
    files = glob.glob(search_pattern, recursive=True)
    
    if not files:
        print("Error: No generated video files found in storage/tasks/")
        sys.exit(1)
        
    # Sort files by modification time, newest first
    files.sort(key=os.path.getmtime, reverse=True)
    latest_video = files[0]
    
    file_size_kb = os.path.getsize(latest_video) / 1024
    print(f"Detected latest video: {latest_video}")
    print(f"File size: {file_size_kb:.2f} KB")
    
    # Perform basic validation (>100KB check)
    if file_size_kb < 100:
        print(f"Error: Video file size ({file_size_kb:.2f} KB) is under the 100 KB threshold.")
        sys.exit(1)
        
    print("Video validation passed.")
    
    # Write the output path to GitHub step output
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"video_path={latest_video}\n")
        print(f"Wrote video_path to GitHub outputs: {latest_video}")
    else:
        print(f"Not running in GitHub Actions. Output path: {latest_video}")

if __name__ == "__main__":
    main()
