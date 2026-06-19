import os
import sys
import json
import requests

def write_outputs(video_id, status, error_msg):
    # Write to youtube-result.json
    result = {
        "youtube_video_id": video_id,
        "youtube_status": status,
        "youtube_error": error_msg
    }
    try:
        with open("youtube-result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print("Wrote youtube-result.json successfully.")
    except Exception as e:
        print(f"Error writing youtube-result.json: {e}")

    # Write to GITHUB_OUTPUT
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        try:
            with open(github_output, "a", encoding="utf-8") as f:
                f.write(f"youtube_video_id={video_id}\n")
                f.write(f"youtube_status={status}\n")
                if error_msg:
                    f.write(f"youtube_error={error_msg}\n")
            print("Wrote outputs to GITHUB_OUTPUT.")
        except Exception as e:
            print(f"Error writing to GITHUB_OUTPUT: {e}")

def main():
    print("--- Running YouTube Upload Script ---")
    
    # 1. Check for duplicate upload
    existing_video_id = os.environ.get('YOUTUBE_VIDEO_ID', '').strip()
    if existing_video_id:
        print(f"YouTube upload skipped: Video already uploaded with ID: {existing_video_id}")
        write_outputs(existing_video_id, "success", "")
        return

    # Check docs/content-queue.json for already posted video ID matching the queue item ID
    queue_item_id = os.environ.get('QUEUE_ITEM_ID', '').strip()
    if queue_item_id and os.path.exists("docs/content-queue.json"):
        try:
            with open("docs/content-queue.json", "r", encoding="utf-8") as f:
                queue = json.load(f)
                for item in queue:
                    if str(item.get("id")) == str(queue_item_id):
                        q_video_id = item.get("youtube_video_id")
                        if q_video_id:
                            print(f"YouTube upload skipped: Video already uploaded for queue item {queue_item_id} with ID: {q_video_id}")
                            write_outputs(q_video_id, "success", "")
                            return
        except Exception as e:
            print(f"Warning: Failed to check content queue for duplicates: {e}")


    # Check posting mode (default to mock for safety)
    posting_mode = os.environ.get('POSTING_MODE', 'mock').lower()
    mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'
    is_mock = (posting_mode == "mock") or mock_mode

    # Read privacy (force default to private)
    privacy = os.environ.get('PRIVACY', 'private').lower()
    if privacy not in ["private", "unlisted", "public"]:
        privacy = "private"

    video_path = os.environ.get('VIDEO_PATH')
    
    # Read metadata from file if available, fallback to env vars
    title = os.environ.get('TITLE', 'Untitled Video')
    description = os.environ.get('DESCRIPTION', '')
    tags = []
    category_id = "22" # default

    if os.path.exists("youtube-metadata.json"):
        try:
            with open("youtube-metadata.json", "r", encoding="utf-8") as f:
                meta = json.load(f)
                title = meta.get("title", title)
                description = meta.get("description", description)
                tags = meta.get("tags", tags)
                category_id = meta.get("categoryId", category_id)
            print("Successfully loaded metadata from youtube-metadata.json")
        except Exception as e:
            print(f"Warning: Failed to load youtube-metadata.json: {e}. Using fallback values.")

    # Ensure #Shorts appears in description or title
    if "#shorts" not in title.lower() and "#shorts" not in description.lower():
        description += "\n\n#Shorts"

    print(f"Final Title: {title}")
    print(f"Privacy Status: {privacy}")
    print(f"Video Path: {video_path}")
    print(f"Mock Mode: {is_mock}")

    video_id = ""
    status = "failed"
    error_msg = ""

    if is_mock:
        print("[MOCK] Simulating YouTube upload...")
        video_id = "mock_yt_shorts_123"
        status = "success"
        print(f"[MOCK] Simulated upload successful. Video ID: {video_id}")
        write_outputs(video_id, status, error_msg)
        return

    # Real YouTube posting
    print("[REAL] Executing real YouTube upload...")
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')

    if not all([client_id, client_secret, refresh_token]):
        error_msg = "Missing YouTube credentials (YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN)"
        print(f"Error: {error_msg}")
        write_outputs(video_id, "failed", error_msg)
        sys.exit(1)

    if not video_path or not os.path.exists(video_path):
        error_msg = f"Video file not found at path: {video_path}"
        print(f"Error: {error_msg}")
        write_outputs(video_id, "failed", error_msg)
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
        token_res = requests.post(token_url, data=token_data, timeout=15)
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
                "description": description[:5000],
                "categoryId": category_id,
                "tags": tags[:15]
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False
            }
        }
        
        init_res = requests.post(init_url, headers=headers, json=body, timeout=20)
        
        # Check for Quota Errors
        if init_res.status_code in [403, 429]:
            try:
                err_json = init_res.json()
                for err in err_json.get("error", {}).get("errors", []):
                    reason = err.get("reason", "")
                    if reason in ["dailyLimitExceeded", "quotaExceeded", "rateLimitExceeded"]:
                        print(f"CRITICAL ERROR: YouTube API Quota Exceeded ({reason}). Stopping immediately.")
                        write_outputs(video_id, "quota_exceeded", f"Quota exceeded: {reason}")
                        sys.exit(1)
            except Exception as e:
                print(f"Could not parse error response: {e}")
                
        init_res.raise_for_status()
        
        upload_url = init_res.headers.get('Location')
        if not upload_url:
            raise Exception("Upload URL missing from Location header.")

        # 3. Upload Video Binary
        print(f"[REAL] Uploading video binary size={os.path.getsize(video_path)} bytes...")
        file_size = os.path.getsize(video_path)
        with open(video_path, "rb") as f:
            upload_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "video/mp4",
                "Content-Length": str(file_size)
            }
            # Put the binary with a larger timeout to avoid failure on slow network
            upload_res = requests.put(upload_url, headers=upload_headers, data=f, timeout=120)
            upload_res.raise_for_status()

        video_id = upload_res.json().get('id', '')
        status = "success"
        print(f"[REAL] YouTube Upload Successful! Video ID: {video_id}")

    except Exception as e:
        print(f"Error during YouTube upload: {str(e)}")
        status = "failed"
        error_msg = str(e)

    write_outputs(video_id, status, error_msg)
    if status != "success":
        sys.exit(1)

if __name__ == "__main__":
    main()
