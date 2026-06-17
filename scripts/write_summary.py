import os
import sys

def main():
    print("--- Writing GitHub Actions Job Summary ---")
    
    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if not summary_file:
        print("Error: GITHUB_STEP_SUMMARY environment variable not set. Printing to stdout instead.")
        f_out = sys.stdout
    else:
        f_out = open(summary_file, "w", encoding="utf-8")
        
    topic = os.environ.get('TOPIC', 'N/A')
    title = os.environ.get('TITLE', 'Untitled Video')
    niche = os.environ.get('NICHE', 'general')
    platforms = os.environ.get('PLATFORMS', '')
    privacy = os.environ.get('PRIVACY', 'private')
    mock_mode = os.environ.get('MOCK_MODE', 'true')
    
    video_path = os.environ.get('VIDEO_PATH', 'Not Found')
    public_video_url = os.environ.get('PUBLIC_VIDEO_URL', 'Not Uploaded')
    
    yt_status = os.environ.get('YT_STATUS', 'skipped')
    yt_video_id = os.environ.get('YT_VIDEO_ID', '')
    yt_error = os.environ.get('YT_ERROR', '')
    
    ig_status = os.environ.get('IG_STATUS', 'skipped')
    ig_media_id = os.environ.get('IG_MEDIA_ID', '')
    ig_error = os.environ.get('IG_ERROR', '')
    
    fb_status = os.environ.get('FB_STATUS', 'skipped')
    fb_video_id = os.environ.get('FB_VIDEO_ID', '')
    fb_error = os.environ.get('FB_ERROR', '')

    # Helper function for status emoji
    def get_status_emoji(status):
        if status == 'success':
            return '✅ SUCCESS'
        elif status == 'failed':
            return '❌ FAILED'
        elif status == 'skipped':
            return '⚪ SKIPPED'
        else:
            return '🟡 PENDING'

    markdown = f"""# 🎬 Video Posting Pipeline Run Summary

### 📊 Parameters
* **Topic/Subject**: `{topic}`
* **Post Title**: `{title}`
* **Niche**: `{niche}`
* **Target Platforms**: `{platforms}`
* **Privacy Level**: `{privacy}`
* **Mock Mode**: `{mock_mode}`

---

### 📦 Video Details & Storage
* **Local Path**: `{video_path}`
* **Cloudflare R2 Public URL**: {f"[Open Video]({public_video_url})" if public_video_url != "Not Uploaded" and public_video_url != "Not Found" else "`Not Uploaded`"}
  * *R2 Key*: `{os.path.basename(public_video_url) if public_video_url != "Not Uploaded" else "N/A"}`

---

### 🚀 Posting Statuses

| Platform | Status | ID / URL | Details |
|---|---|---|---|
| **YouTube Shorts** | {get_status_emoji(yt_status)} | `{yt_video_id or "N/A"}` | {f"Error: {yt_error}" if yt_error else "Posted successfully" if yt_status == "success" else "N/A"} |
| **Instagram Reels** | {get_status_emoji(ig_status)} | `{ig_media_id or "N/A"}` | {f"Error: {ig_error}" if ig_error else "Published successfully" if ig_status == "success" else "N/A"} |
| **Facebook Reels** | {get_status_emoji(fb_status)} | `{fb_video_id or "N/A"}` | {f"Error: {fb_error}" if fb_error else "Published successfully" if fb_status == "success" else "N/A"} |

---

### ⏱️ Run Information
* **Timestamp**: `{os.environ.get('GITHUB_RUN_ID', 'Local Run')}`
* **GitHub Actions Run Link**: [View Run](https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'local')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')})
"""
    f_out.write(markdown)
    if summary_file:
        f_out.close()
        print("Summary written successfully to GITHUB_STEP_SUMMARY.")

    # 1. Write platform-results.json
    import json
    import datetime
    
    platform_results = {
        "youtube": {
            "status": yt_status,
            "video_id": yt_video_id,
            "error": yt_error
        },
        "instagram": {
            "status": ig_status,
            "media_id": ig_media_id,
            "error": ig_error
        },
        "facebook": {
            "status": fb_status,
            "video_id": fb_video_id,
            "error": fb_error
        }
    }
    try:
        with open("platform-results.json", "w", encoding="utf-8") as f:
            json.dump(platform_results, f, indent=2)
        print("Wrote platform-results.json successfully.")
    except Exception as e:
        print(f"Error writing platform-results.json: {str(e)}")

    # 2. Write run-log.json
    run_log = {
        "job_id": os.environ.get('GITHUB_RUN_ID', 'local'),
        "topic": topic,
        "title": title,
        "niche": niche,
        "privacy": privacy,
        "mock_mode": mock_mode,
        "video_path": video_path,
        "public_video_url": public_video_url,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "results": platform_results
    }
    try:
        with open("run-log.json", "w", encoding="utf-8") as f:
            json.dump(run_log, f, indent=2)
        print("Wrote run-log.json successfully.")
    except Exception as e:
        print(f"Error writing run-log.json: {str(e)}")

if __name__ == "__main__":
    main()
