import os
import sys
import requests

def main():
    mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'
    title = os.environ.get('TITLE', 'Untitled Video')
    description = os.environ.get('DESCRIPTION', '')
    public_video_url = os.environ.get('PUBLIC_VIDEO_URL')
    
    print("--- Running Facebook Reels Posting Script ---")
    print(f"Title: {title}")
    print(f"Caption Length: {len(description)} chars")
    print(f"Video URL: {public_video_url}")
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
        print("[REAL] Executing real Facebook Reels posting...")
        access_token = os.environ.get('META_PAGE_ACCESS_TOKEN')
        page_id = os.environ.get('FACEBOOK_PAGE_ID')
        api_version = os.environ.get('GRAPH_API_VERSION', 'v25.0')
        
        if not all([access_token, page_id]):
            print("Error: Missing Facebook Page credentials (META_PAGE_ACCESS_TOKEN, FACEBOOK_PAGE_ID)")
            sys.exit(1)
            
        if not public_video_url:
            print("Error: PUBLIC_VIDEO_URL is missing")
            sys.exit(1)
            
        try:
            # 1. Start Upload Session
            print("[REAL] Starting Facebook Reels upload session...")
            start_url = f"https://graph.facebook.com/{api_version}/{page_id}/video_reels"
            start_data = {
                "upload_phase": "start",
                "access_token": access_token
            }
            start_res = requests.post(start_url, json=start_data)
            start_res.raise_for_status()
            
            session_data = start_res.json()
            video_id = session_data.get('video_id')
            upload_url = session_data.get('upload_url')
            
            if not video_id or not upload_url:
                raise Exception("Facebook API did not return video_id or upload_url")
            print(f"[REAL] Upload session started. Video ID: {video_id}")
            
            # 2. Upload Video via Public URL
            print(f"[REAL] Requesting Facebook to pull video from: {public_video_url}...")
            upload_headers = {
                "Authorization": f"OAuth {access_token}"
            }
            upload_data = {
                "file_url": public_video_url
            }
            # Note: This upload endpoint expects form-urlencoded POST
            upload_res = requests.post(upload_url, headers=upload_headers, data=upload_data)
            upload_res.raise_for_status()
            print("[REAL] Video upload requested successfully.")
            
            # 3. Publish Reel
            print("[REAL] Finishing and publishing Facebook Reel...")
            publish_url = f"https://graph.facebook.com/{api_version}/{page_id}/video_reels"
            publish_data = {
                "upload_phase": "finish",
                "video_id": video_id,
                "video_state": "PUBLISHED",
                "title": title[:255],
                "description": description[:5000],
                "access_token": access_token
            }
            publish_res = requests.post(publish_url, json=publish_data)
            publish_res.raise_for_status()
            
            success = publish_res.json().get('success') or publish_res.json().get('video_id')
            if success:
                status = "success"
                print(f"[REAL] Facebook Reel published successfully! Video ID: {video_id}")
            else:
                raise Exception(f"Facebook API publish returned failure: {publish_res.text}")
                
        except Exception as e:
            print(f"Error during Facebook posting: {str(e)}")
            error_msg = str(e)
            
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
