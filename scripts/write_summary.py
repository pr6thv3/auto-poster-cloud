import os
import sys
import json
import datetime

def main():
    print("--- Writing GitHub Actions Job Summary ---")
    
    summary_file = os.environ.get('GITHUB_STEP_SUMMARY')
    if not summary_file:
        print("Error: GITHUB_STEP_SUMMARY environment variable not set. Printing to stdout instead.")
        f_out = sys.stdout
    else:
        f_out = open(summary_file, "w", encoding="utf-8")
        
    topic = os.environ.get('TOPIC', 'N/A')
    niche = os.environ.get('NICHE', 'general')
    privacy = os.environ.get('PRIVACY', 'private')
    
    generation_mode = os.environ.get('GENERATION_MODE', 'mock')
    metadata_mode = os.environ.get('METADATA_MODE', 'mock')
    posting_mode = os.environ.get('POSTING_MODE', 'mock')
    
    video_path = os.environ.get('VIDEO_PATH', 'Not Found')
    public_video_url = os.environ.get('PUBLIC_VIDEO_URL', 'Not Uploaded')
    
    # Try reading from youtube-result.json
    yt_status = 'skipped'
    yt_video_id = ''
    yt_error = ''
    
    if os.path.exists("youtube-result.json"):
        try:
            with open("youtube-result.json", "r", encoding="utf-8") as f:
                res = json.load(f)
                yt_status = res.get("youtube_status", "failed")
                yt_video_id = res.get("youtube_video_id", "")
                yt_error = res.get("youtube_error", "")
        except Exception as e:
            print(f"Warning: Failed to read youtube-result.json: {e}")

    # Helper function for status emoji
    def get_status_emoji(status):
        if status == 'success':
            return '✅ SUCCESS'
        elif status == 'failed':
            return '❌ FAILED'
        elif status == 'quota_exceeded':
            return '⚠️ QUOTA EXCEEDED'
        elif status == 'skipped':
            return '⚪ SKIPPED'
        else:
            return '🟡 PENDING'

    markdown = f"""# 🎬 YouTube Shorts Auto-Posting Run Summary

### 📊 Configuration Parameters
* **Topic/Subject**: `{topic}`
* **Niche**: `{niche}`
* **Privacy Level**: `{privacy}`
* **Generation Mode**: `{generation_mode}`
* **Metadata Mode**: `{metadata_mode}`
* **Posting Mode**: `{posting_mode}`

---

### 📦 Video Details & Storage
* **Local Video Path**: `{video_path}`
* **Cloudflare R2 Public URL**: {f"[Open Video]({public_video_url})" if public_video_url != "Not Uploaded" and public_video_url != "Not Found" else "`Not Uploaded`"}
  * *R2 Key*: `{os.path.basename(public_video_url) if public_video_url != "Not Uploaded" else "N/A"}`

---

### 🚀 YouTube Status

| Platform | Status | Video ID / URL | Details |
|---|---|---|---|
| **YouTube Shorts** | {get_status_emoji(yt_status)} | {f"`{yt_video_id}`" if yt_video_id else "`N/A`"} | {f"Error: {yt_error}" if yt_error else "Posted successfully" if yt_status == "success" else "N/A"} |

---

### ⏱️ Run Information
* **Workflow Run ID**: `{os.environ.get('GITHUB_RUN_ID', 'Local Run')}`
* **GitHub Actions Run Link**: [View Run](https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'local')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')})
"""
    f_out.write(markdown)
    if summary_file:
        f_out.close()
        print("Summary written successfully to GITHUB_STEP_SUMMARY.")

    # 1. Write platform-results.json
    platform_results = {
        "youtube": {
            "status": yt_status,
            "video_id": yt_video_id,
            "error": yt_error
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
        "niche": niche,
        "privacy": privacy,
        "generation_mode": generation_mode,
        "metadata_mode": metadata_mode,
        "posting_mode": posting_mode,
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
