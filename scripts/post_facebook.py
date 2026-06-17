import os
import sys

def main():
    mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'
    title = os.environ.get('TITLE', 'Untitled Video')
    description = os.environ.get('DESCRIPTION', '')
    
    print("--- Running Facebook Reels Posting Script ---")
    print(f"Title: {title}")
    print(f"Caption Length: {len(description)} chars")
    print(f"Mock Mode: {mock_mode}")
    
    video_id = ""
    status = "failed"
    error_msg = ""
    
    if mock_mode:
        print("[MOCK] Simulating Facebook Reels upload session and publishing...")
        video_id = "mock_fb_reel_789"
        status = "success"
        print(f"[MOCK] Simulated FB Reel published. Video ID: {video_id}")
    else:
        print("[REAL] Real Facebook posting is not enabled in Phase 1.")
        error_msg = "Real API posting not configured in Phase 1"
        
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"fb_video_id={video_id}\n")
            f.write(f"facebook_status={status}\n")
            if error_msg:
                f.write(f"facebook_error={error_msg}\n")
        print(f"Wrote outputs to GITHUB_OUTPUT: status={status}")

if __name__ == "__main__":
    main()
