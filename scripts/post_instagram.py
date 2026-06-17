import os
import sys

def main():
    mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'
    description = os.environ.get('DESCRIPTION', '')
    
    print("--- Running Instagram Reels Posting Script ---")
    print(f"Caption Length: {len(description)} chars")
    print(f"Mock Mode: {mock_mode}")
    
    media_id = ""
    status = "failed"
    error_msg = ""
    
    if mock_mode:
        print("[MOCK] Simulating Instagram Reels container creation, polling, and publishing...")
        media_id = "mock_ig_reel_456"
        status = "success"
        print(f"[MOCK] Simulated IG Reel published. Media ID: {media_id}")
    else:
        print("[REAL] Real Instagram posting is not enabled in Phase 1.")
        error_msg = "Real API posting not configured in Phase 1"
        
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"ig_media_id={media_id}\n")
            f.write(f"instagram_status={status}\n")
            if error_msg:
                f.write(f"instagram_error={error_msg}\n")
        print(f"Wrote outputs to GITHUB_OUTPUT: status={status}")

if __name__ == "__main__":
    main()
