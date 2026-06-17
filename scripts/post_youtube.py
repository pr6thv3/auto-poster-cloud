import os
import sys
import requests

def main():
    mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'
    title = os.environ.get('TITLE', 'Untitled Video')
    description = os.environ.get('DESCRIPTION', '')
    privacy = os.environ.get('PRIVACY', 'private')
    video_path = os.environ.get('VIDEO_PATH')
    
    print("--- Running YouTube Upload Script ---")
    print(f"Title: {title}")
    print(f"Privacy: {privacy}")
    print(f"Video Path: {video_path}")
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
        print("[REAL] Executing real YouTube upload...")
        client_id = os.environ.get('YOUTUBE_CLIENT_ID')
        client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
        refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')
        
        if not all([client_id, client_secret, refresh_token]):
            print("Error: Missing YouTube credentials (YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN)")
            sys.exit(1)
            
        if not video_path or not os.path.exists(video_path):
            print(f"Error: Video file not found at path: {video_path}")
            sys.exit(1)
            
        try:
            # 1. Refresh Access Token
            print("[REAL] Refreshing Google OAuth2 access token...")
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            token_res = requests.post(token_url, data=token_data)
            token_res.raise_for_status()
            access_token = token_res.json().get('access_token')
            
            # 2. Initiate Resumable Upload
            print("[REAL] Initiating resumable upload session...")
            init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-Upload-Content-Type": "video/mp4",
                "Content-Type": "application/json"
            }
            body = {
                "snippet": {
                    "title": title[:100],
                    "description": (description + "\n\n#Shorts")[:5000],
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": privacy if privacy in ["private", "unlisted", "public"] else "private",
                    "selfDeclaredMadeForKids": False
                }
            }
            init_res = requests.post(init_url, headers=headers, json=body)
            init_res.raise_for_status()
            
            upload_url = init_res.headers.get('Location')
            if not upload_url:
                raise Exception("Upload URL missing from YouTube API response Location header")
                
            # 3. Upload Video Binary
            print(f"[REAL] Uploading binary video file to resumable URL: {upload_url}")
            file_size = os.path.getsize(video_path)
            with open(video_path, "rb") as f:
                upload_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "video/mp4",
                    "Content-Length": str(file_size)
                }
                upload_res = requests.put(upload_url, headers=upload_headers, data=f)
                upload_res.raise_for_status()
                
            video_id = upload_res.json().get('id', '')
            status = "success"
            print(f"[REAL] YouTube Upload Successful. Video ID: {video_id}")
            
        except Exception as e:
            print(f"Error during YouTube upload: {str(e)}")
            error_msg = str(e)
            
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
