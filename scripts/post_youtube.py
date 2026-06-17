import os
import sys

def main():
    mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'
    title = os.environ.get('TITLE', 'Untitled Video')
    privacy = os.environ.get('PRIVACY', 'private')
    
    print("--- Running YouTube Upload Script ---")
    print(f"Title: {title}")
    print(f"Privacy: {privacy}")
    print(f"Mock Mode: {mock_mode}")
    
    video_id = ""
    status = "failed"
    error_msg = ""
    
    if mock_mode:
        print("[MOCK] Simulating YouTube upload...")
        video_id = "mock_yt_shorts_123"
        status = "success"
        print(f"[MOCK] Simulated upload successful. Video ID: {video_id}")
    else:
        print("[REAL] Real YouTube posting is not enabled in Phase 1.")
        error_msg = "Real API posting not configured in Phase 1"
        
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"youtube_video_id={video_id}\n")
            f.write(f"youtube_status={status}\n")
            if error_msg:
                f.write(f"youtube_error={error_msg}\n")
        print(f"Wrote outputs to GITHUB_OUTPUT: status={status}")

if __name__ == "__main__":
    main()
