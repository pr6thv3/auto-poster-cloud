import os
import sys
import json
from datetime import datetime, timezone

def main():
    print("--- Running Content History Writeback ---")

    # 1. Parse USE_VIDEO_BRIEF
    use_video_brief = os.environ.get('USE_VIDEO_BRIEF', 'false').lower() == 'true'
    if not use_video_brief:
        print("USE_VIDEO_BRIEF is not enabled. Skipping history writeback.")
        sys.exit(0)

    # 2. Safety Mock check
    posting_mode = os.environ.get('POSTING_MODE', 'mock').lower()
    generation_mode = os.environ.get('GENERATION_MODE', 'mock').lower()
    allow_mock_history = os.environ.get('ALLOW_MOCK_HISTORY', 'false').lower() == 'true'

    is_mock = (posting_mode == "mock" or generation_mode == "mock")
    if is_mock and not allow_mock_history:
        print("Mock upload detected and ALLOW_MOCK_HISTORY is not true. Skipping history writeback.")
        sys.exit(0)

    # 3. Read input files
    brief_path = os.path.join("docs", "video-brief.json")
    quality_path = os.path.join("docs", "quality-report.json")
    yt_result_path = "youtube-result.json"

    if not os.path.exists(brief_path):
        print(f"Error: Video brief file missing at {brief_path}")
        sys.exit(1)
    if not os.path.exists(quality_path):
        print(f"Error: Quality report file missing at {quality_path}")
        sys.exit(1)
    if not os.path.exists(yt_result_path):
        print(f"Warning: youtube-result.json is missing. Upload status cannot be verified. Skipping.")
        sys.exit(0)

    try:
        with open(brief_path, "r", encoding="utf-8") as f:
            brief = json.load(f)
    except Exception as e:
        print(f"Error reading video brief: {e}")
        sys.exit(1)

    try:
        with open(quality_path, "r", encoding="utf-8") as f:
            quality = json.load(f)
    except Exception as e:
        print(f"Error reading quality report: {e}")
        sys.exit(1)

    try:
        with open(yt_result_path, "r", encoding="utf-8") as f:
            yt_res = json.load(f)
    except Exception as e:
        print(f"Error reading youtube-result.json: {e}")
        sys.exit(1)

    # 4. Check upload success
    yt_status = yt_res.get("youtube_status")
    yt_video_id = yt_res.get("youtube_video_id")

    if yt_status != "success":
        print(f"YouTube status is '{yt_status}' (not success). Skipping history writeback.")
        sys.exit(0)

    if not yt_video_id:
        print("Error: youtube_video_id is missing or empty in youtube-result.json despite success status.")
        sys.exit(1)

    # 5. Load history
    history_path = os.path.join("docs", "content-history.json")
    history = []
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            print(f"Error reading content history: {e}")
            sys.exit(1)

    # 6. Check duplicate by youtube_video_id
    for hist_item in history:
        if hist_item.get("youtube_video_id") == yt_video_id:
            print(f"Duplicate entry found for youtube_video_id '{yt_video_id}'. Skipping history writeback.")
            sys.exit(0)

    # 7. Resolve detailed idea parameters from scored-ideas.json
    idea_id = brief.get("idea_id")
    profile_id = brief.get("profile_id")
    topic = brief.get("topic")
    hook = brief.get("hook")
    freshness_score = brief.get("freshness_score", 100)

    angle = ""
    keywords = []
    format_type = ""

    scored_path = os.path.join("docs", "scored-ideas.json")
    if os.path.exists(scored_path):
        try:
            with open(scored_path, "r", encoding="utf-8") as f:
                scored_ideas = json.load(f)
                for idea in scored_ideas:
                    if idea.get("idea_id") == idea_id:
                        angle = idea.get("angle", "")
                        keywords = idea.get("keywords", [])
                        format_type = idea.get("format", "")
                        break
        except Exception as e:
            print(f"Warning: Failed to load scored-ideas.json: {e}")

    # Fallbacks from brief structure if not resolved from scored-ideas
    if not format_type:
        format_type = "list_top_3"  # default sensible fallback

    # Calculate quality score
    reasons = quality.get("reasons", [])
    quality_status = quality.get("status", "passed")
    quality_score = 100 if quality_status == "passed" else max(0, 100 - 10 * len(reasons))

    # 8. Construct new history entry
    new_entry = {
        "idea_id": idea_id,
        "profile_id": profile_id,
        "topic": topic,
        "angle": angle,
        "hook": hook,
        "keywords": keywords,
        "format": format_type,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "success",
        "youtube_video_id": yt_video_id,
        "freshness_score": freshness_score,
        "quality_score": quality_score,
        "source_run_id": os.environ.get('GITHUB_RUN_ID', 'local')
    }

    # 9. Append and Save
    history.append(new_entry)
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        print(f"Successfully appended new history entry for topic '{topic}' to {history_path}")
        print(f"YouTube Video ID: {yt_video_id}")
    except Exception as e:
        print(f"Error writing content history: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
