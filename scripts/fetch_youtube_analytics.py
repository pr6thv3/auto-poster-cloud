import os
import sys
import json
import requests
from datetime import datetime

def main():
    print("--- Running YouTube Analytics Fetch Loop ---")
    
    history_path = os.path.join("docs", "content-history.json")
    if not os.path.exists(history_path):
        print(f"Error: Content history file not found at {history_path}")
        sys.exit(1)
        
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception as e:
        print(f"Error reading content history: {e}")
        sys.exit(1)
        
    # Ensure all entries have an analytics block
    for entry in history:
        if "analytics" not in entry or not isinstance(entry["analytics"], dict):
            entry["analytics"] = {
                "views": None,
                "likes": None,
                "comments": None,
                "checked_at": None,
                "privacy": None,
                "source": "not_checked"
            }
        elif "source" not in entry["analytics"]:
            entry["analytics"]["source"] = "not_checked"
            
    # Gather video IDs to fetch
    video_entries = []
    for entry in history:
        vid_id = entry.get("youtube_video_id", "").strip()
        if vid_id and not vid_id.startswith("mock_"):
            video_entries.append((vid_id, entry))
            
    if not video_entries:
        print("No real YouTube video IDs found in content history. Ensuring schema is initialized.")
        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            print("Successfully initialized analytics schema for all history entries.")
        except Exception as e:
            print(f"Error writing content history: {e}")
            sys.exit(1)
        return

    # Check for credentials
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')
    api_key = os.environ.get('YOUTUBE_API_KEY')
    
    # Check if we should run in mock mode
    mock_mode = os.environ.get('MOCK_MODE', 'false').lower() == 'true'
    is_mock = mock_mode or not (all([client_id, client_secret, refresh_token]) or api_key)
    
    video_stats = {}
    
    if is_mock:
        print("[MOCK] Running in mock mode. Simulating analytics responses...")
        # Simulate stats for real-looking video IDs
        for vid_id, _ in video_entries:
            video_stats[vid_id] = {
                "views": 420,
                "likes": 69,
                "comments": 7,
                "privacy": "private"
            }
    else:
        print("[REAL] Fetching stats from YouTube API...")
        try:
            access_token = None
            headers = {}
            
            if all([client_id, client_secret, refresh_token]):
                print("[REAL] Refreshing OAuth2 token...")
                token_url = "https://oauth2.googleapis.com/token"
                token_data = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
                # Mask credentials in any print (though requests won't print by default)
                token_res = requests.post(token_url, data=token_data, timeout=15)
                token_res.raise_for_status()
                access_token = token_res.json().get('access_token')
                headers = {"Authorization": f"Bearer {access_token}"}
                
            # Process in batches of 50
            video_ids = [vid_id for vid_id, _ in video_entries]
            batch_size = 50
            for i in range(0, len(video_ids), batch_size):
                batch_ids = video_ids[i:i+batch_size]
                ids_str = ",".join(batch_ids)
                
                url = "https://www.googleapis.com/youtube/v3/videos?part=statistics,status"
                if access_token:
                    url += f"&id={ids_str}"
                elif api_key:
                    url += f"&id={ids_str}&key={api_key}"
                    
                res = requests.get(url, headers=headers, timeout=20)
                res.raise_for_status()
                
                items = res.json().get("items", [])
                for item in items:
                    vid_id = item.get("id")
                    stats = item.get("statistics", {})
                    status = item.get("status", {})
                    
                    video_stats[vid_id] = {
                        "views": int(stats.get("viewCount")) if "viewCount" in stats else None,
                        "likes": int(stats.get("likeCount")) if "likeCount" in stats else None,
                        "comments": int(stats.get("commentCount")) if "commentCount" in stats else None,
                        "privacy": status.get("privacyStatus")
                    }
                    
        except Exception as e:
            # We don't fail the entire script if API request fails, but log the warning
            print(f"Warning: Failed to fetch live analytics from YouTube API: {e}")
            print("Falling back to leaving existing analytics intact.")
            
    # Update content history with fetched stats
    current_time = datetime.utcnow().isoformat() + "Z"
    for vid_id, entry in video_entries:
        if vid_id in video_stats:
            stats = video_stats[vid_id]
            entry["analytics"]["views"] = stats["views"]
            entry["analytics"]["likes"] = stats["likes"]
            entry["analytics"]["comments"] = stats["comments"]
            entry["analytics"]["privacy"] = stats["privacy"]
            entry["analytics"]["checked_at"] = current_time
            entry["analytics"]["source"] = "mock" if is_mock else "youtube_api"
        else:
            print(f"Skipping stats update for video {vid_id} (not returned by API / private / deleted).")
            # Ensure checked_at is updated if we attempted the check
            entry["analytics"]["checked_at"] = current_time
            entry["analytics"]["source"] = "not_checked"

    # Write back to history file
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        print(f"Successfully updated content history at {history_path}")
    except Exception as e:
        print(f"Error writing content history: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
