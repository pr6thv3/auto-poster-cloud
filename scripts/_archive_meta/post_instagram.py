import os
import sys
import requests
import time

def main():
    mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'
    description = os.environ.get('DESCRIPTION', '')
    public_video_url = os.environ.get('PUBLIC_VIDEO_URL')
    
    print("--- Running Instagram Reels Posting Script ---")
    print(f"Caption Length: {len(description)} chars")
    print(f"Video URL: {public_video_url}")
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
        print("[REAL] Executing real Instagram Reels posting...")
        access_token = os.environ.get('META_PAGE_ACCESS_TOKEN')
        ig_user_id = os.environ.get('IG_USER_ID')
        api_version = os.environ.get('GRAPH_API_VERSION', 'v25.0')
        
        if not all([access_token, ig_user_id]):
            print("Error: Missing Instagram credentials (META_PAGE_ACCESS_TOKEN, IG_USER_ID)")
            sys.exit(1)
            
        if not public_video_url:
            print("Error: PUBLIC_VIDEO_URL is missing")
            sys.exit(1)
            
        try:
            # 1. Create Media Container
            print("[REAL] Creating Instagram media container...")
            container_url = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media"
            container_data = {
                "media_type": "REELS",
                "video_url": public_video_url,
                "caption": description[:2200], # IG caption limit
                "share_to_feed": True,
                "access_token": access_token
            }
            container_res = requests.post(container_url, json=container_data)
            container_res.raise_for_status()
            container_id = container_res.json().get('id')
            
            if not container_id:
                raise Exception("Instagram API did not return container ID")
            print(f"[REAL] Container created. ID: {container_id}")
            
            # 2. Poll Container Status
            print("[REAL] Polling container processing status...")
            status_url = f"https://graph.facebook.com/{api_version}/{container_id}"
            status_params = {
                "fields": "status_code",
                "access_token": access_token
            }
            
            max_attempts = 15
            poll_interval = 15
            processing_finished = False
            
            for attempt in range(1, max_attempts + 1):
                print(f"[REAL] Check status attempt {attempt}/{max_attempts}...")
                status_res = requests.get(status_url, params=status_params)
                status_res.raise_for_status()
                
                status_code = status_res.json().get('status_code')
                print(f"[REAL] Current status_code: {status_code}")
                
                if status_code == 'FINISHED':
                    processing_finished = True
                    break
                elif status_code == 'ERROR':
                    raise Exception("Instagram container processing failed with status ERROR")
                
                time.sleep(poll_interval)
                
            if not processing_finished:
                raise Exception("Instagram container processing timed out")
                
            # 3. Publish Reel
            print("[REAL] Publishing Instagram Reel...")
            publish_url = f"https://graph.facebook.com/{api_version}/{ig_user_id}/media_publish"
            publish_data = {
                "creation_id": container_id,
                "access_token": access_token
            }
            publish_res = requests.post(publish_url, json=publish_data)
            publish_res.raise_for_status()
            
            media_id = publish_res.json().get('id', '')
            status = "success"
            print(f"[REAL] Instagram Reel published successfully! Media ID: {media_id}")
            
        except Exception as e:
            print(f"Error during Instagram posting: {str(e)}")
            error_msg = str(e)
            
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
