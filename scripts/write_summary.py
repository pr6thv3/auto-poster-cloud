import os
import sys
import json
import datetime
import glob

def main():
    print("--- Running GitHub Actions Job Summary ---")
    
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

    # MPT Providers
    requested_mpt_provider = os.environ.get('MPT_PROVIDER', '').strip().lower() or os.environ.get('LLM_PROVIDER', '').strip().lower() or 'gemini'
    if generation_mode == 'real':
        actual_mpt_provider_used = requested_mpt_provider
    else:
        actual_mpt_provider_used = 'mock'

    # Read audit fields from youtube-metadata.json
    meta_status = 'unknown'
    meta_provider = 'unknown'
    meta_error = None
    meta_requested = ''
    
    if os.path.exists("youtube-metadata.json"):
        try:
            with open("youtube-metadata.json", "r", encoding="utf-8") as f:
                meta = json.load(f)
                meta_status = meta.get("metadata_status", "unknown")
                meta_provider = meta.get("metadata_provider_used", "unknown")
                meta_error = meta.get("metadata_error", None)
                meta_requested = meta.get("requested_metadata_provider", "")
        except Exception as e:
            print(f"Warning: Failed to read youtube-metadata.json: {e}")

    # Fallbacks for metadata providers
    if not meta_requested:
        meta_requested = os.environ.get('METADATA_PROVIDER', '').strip().lower() or os.environ.get('LLM_PROVIDER', '').strip().lower() or 'gemini'
    if not meta_provider or meta_provider == 'unknown':
        if metadata_mode == 'real':
            meta_provider = meta_requested
        else:
            meta_provider = 'mock'

    requested_metadata_provider = meta_requested
    actual_metadata_provider_used = meta_provider

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

    def get_meta_status_emoji(status):
        if status == 'success':
            return '✅ SUCCESS'
        elif status == 'mock':
            return '⚪ MOCK'
        elif status == 'fallback':
            return '⚠️ FALLBACK'
        elif status == 'failed':
            return '❌ FAILED'
        else:
            return '❓ UNKNOWN'

    fallback_occurred = (meta_status == 'fallback')

    # Content Engine Audit variables
    use_video_brief = os.environ.get('USE_VIDEO_BRIEF', 'false').lower() == 'true'
    profile_id = "N/A"
    selected_idea = "N/A"
    freshness_score = "N/A"
    quality_status = "N/A"
    
    if use_video_brief:
        brief_path = "docs/video-brief.json"
        if os.path.exists(brief_path):
            try:
                with open(brief_path, "r", encoding="utf-8") as f:
                    brief_data = json.load(f)
                    profile_id = brief_data.get("profile_id", "N/A")
                    selected_idea = brief_data.get("topic", "N/A")
                    freshness_score = brief_data.get("freshness_score", "N/A")
            except Exception as e:
                print(f"Warning: Failed to load {brief_path} for summary: {e}")
                
        quality_path = "docs/quality-report.json"
        if os.path.exists(quality_path):
            try:
                with open(quality_path, "r", encoding="utf-8") as f:
                    q_data = json.load(f)
                    quality_status = q_data.get("status", "N/A")
            except Exception as e:
                print(f"Warning: Failed to load {quality_path} for summary: {e}")

    # Read viral audit details
    format_id = "N/A"
    target_duration_seconds = "N/A"
    actual_duration_seconds = "N/A"
    duration_status = "N/A"
    duration_warning = None
    scene_count = "N/A"
    hook_status = "passed"
    text_overlay_status = "passed"
    sound_design_status = "passed"
    viral_format_status = "passed"

    if os.path.exists("video-info.json"):
        try:
            with open("video-info.json", "r", encoding="utf-8") as f:
                v_info = json.load(f)
                actual_duration_seconds = v_info.get("actual_duration_seconds", "N/A")
                target_duration_seconds = v_info.get("target_duration_seconds", "N/A")
                duration_status = v_info.get("duration_status", "N/A")
                duration_warning = v_info.get("duration_warning", None)
        except Exception as e:
            print(f"Warning: Failed to read video-info.json: {e}")

    if os.path.exists("docs/video-brief.json"):
        try:
            with open("docs/video-brief.json", "r", encoding="utf-8") as f:
                v_brief = json.load(f)
                format_id = v_brief.get("format_id", "N/A")
                scene_count = len(v_brief.get("scene_plan", []))
        except Exception as e:
            print(f"Warning: Failed to read docs/video-brief.json: {e}")

    if os.path.exists("docs/quality-report.json"):
        try:
            with open("docs/quality-report.json", "r", encoding="utf-8") as f:
                q_rep = json.load(f)
                q_reasons = q_rep.get("reasons", [])
                q_warnings = q_rep.get("warnings", [])
                
                if any("hook" in str(r).lower() or "hook" in str(w).lower() for r in q_reasons for w in q_warnings):
                    hook_status = "failed" if any("hook" in str(r).lower() for r in q_reasons) else "warning"
                if any("caption" in str(r).lower() or "overlay" in str(r).lower() or "caption" in str(w).lower() or "overlay" in str(w).lower() for r in q_reasons for w in q_warnings):
                    text_overlay_status = "failed" if any("caption" in str(r).lower() or "overlay" in str(r).lower() for r in q_reasons) else "warning"
                if any("sound" in str(r).lower() or "music" in str(r).lower() or "sound" in str(w).lower() or "music" in str(w).lower() for r in q_reasons for w in q_warnings):
                    sound_design_status = "failed" if any("sound" in str(r).lower() or "music" in str(r).lower() for r in q_reasons) else "warning"

                if q_rep.get("status") == "failed":
                    viral_format_status = "failed"
                elif q_rep.get("status") == "warning":
                    viral_format_status = "warning"
        except Exception as e:
            print(f"Warning: Failed to read docs/quality-report.json: {e}")

    # Retention Format Audit variables
    retention_storyboard_exists = os.path.exists("docs/retention-storyboard.json")
    retention_scene_count = "N/A"
    retention_overlay_count = "N/A"
    retention_motion_status = "passed"
    retention_sound_status = "passed"
    retention_copyright_status = "passed"
    retention_format_status = "skipped"

    retention_postprocess_status = "skipped"
    final_video_source = "raw_mpt"
    subtitle_mode_disabled = False
    avg_overlay_duration = "N/A"
    contact_sheet_path = "N/A"
    format_fidelity_status = "skipped"
    manual_review_required = True

    if retention_storyboard_exists:
        retention_format_status = "passed"
        try:
            with open("docs/retention-storyboard.json", "r", encoding="utf-8") as f:
                sb_data = json.load(f)
                retention_scene_count = len(sb_data.get("scenes", []))
                retention_overlay_count = len(sb_data.get("text_overlays", []))
        except Exception as e:
            print(f"Warning: Failed to load docs/retention-storyboard.json: {e}")

        # Determine average overlay duration
        if retention_overlay_count != "N/A" and int(retention_overlay_count) > 0:
            avg_overlay_duration = f"{24.0 / int(retention_overlay_count):.2f}s"
        else:
            avg_overlay_duration = "N/A"

        # Determine if subtitle mode is disabled in logs
        log_path = "moneyprinter-log.txt"
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    log_content = f.read()
                if "--no-subtitle-enabled" in log_content:
                    subtitle_mode_disabled = True
            except Exception:
                pass

        # Determine final video source
        if "final-retention.mp4" in video_path:
            final_video_source = "final_retention"

        # Determine postprocess status
        if os.path.exists(video_path) and video_path.endswith("final-retention.mp4"):
            retention_postprocess_status = "success"

        # Contact sheet path
        if os.path.exists("docs/retention-contact-sheet.jpg"):
            contact_sheet_path = "docs/retention-contact-sheet.jpg"

        # Format fidelity status
        if retention_postprocess_status == "success":
            task_dir = os.path.dirname(video_path)
            srt_files = glob.glob(os.path.join(task_dir, "*.srt")) if task_dir else []
            if not srt_files:
                format_fidelity_status = "passed"
            else:
                format_fidelity_status = "failed"
        else:
            format_fidelity_status = "failed"

        if os.path.exists("docs/quality-report.json"):
            try:
                with open("docs/quality-report.json", "r", encoding="utf-8") as f:
                    q_rep = json.load(f)
                    q_reasons = q_rep.get("reasons", [])
                    q_warnings = q_rep.get("warnings", [])
                    q_status = q_rep.get("status", "passed")
                    
                    if q_status == "failed":
                        retention_format_status = "failed"
                    elif q_status == "warning":
                        retention_format_status = "warning"
                        
                    if any("motion" in str(r).lower() or "camera" in str(r).lower() for r in q_reasons):
                        retention_motion_status = "failed"
                    elif any("motion" in str(w).lower() or "camera" in str(w).lower() for w in q_warnings):
                        retention_motion_status = "warning"
                        
                    if any("sound" in str(r).lower() or "sfx" in str(r).lower() or "cue" in str(r).lower() for r in q_reasons):
                        retention_sound_status = "failed"
                    elif any("sound" in str(w).lower() or "sfx" in str(w).lower() or "cue" in str(w).lower() for w in q_warnings):
                        retention_sound_status = "warning"
                        
                    copyright_kws = ["copyright", "disney", "simpsons", "fox", "mickey", "marvel", "star wars", "pixar"]
                    if any(any(kw in str(r).lower() for kw in copyright_kws) for r in q_reasons):
                        retention_copyright_status = "failed"
                    elif any(any(kw in str(w).lower() for kw in copyright_kws) for w in q_warnings):
                        retention_copyright_status = "warning"
            except Exception as e:
                print(f"Warning: Failed to load docs/quality-report.json: {e}")

    content_engine_md = ""
    if use_video_brief:
        content_engine_md = f"""
### 🧠 Content Engine Audit
* **Use Video Brief**: `{use_video_brief}`
* **Profile ID**: `{profile_id}`
* **Selected Idea**: `{selected_idea}`
* **Freshness Score**: `{freshness_score}`
* **Quality Gate Status**: `{quality_status.upper()}`

---
"""

    viral_format_audit_md = ""
    if format_id == "viral_curiosity_24s":
        viral_format_audit_md = f"""
### 🎬 Viral Format Audit
* **Format Preset**: `{format_id}`
* **Target Duration**: `{target_duration_seconds}s`
* **Actual Duration**: `{actual_duration_seconds}s`
* **Duration Status**: `{duration_status.upper()}`
{f"* **Duration Warning**: `{duration_warning}`" if duration_warning else ""}
* **Scene Count**: `{scene_count}`
* **Hook Status**: `{hook_status}`
* **Text Overlay Status**: `{text_overlay_status}`
* **Sound Design Status**: `{sound_design_status}`

---
"""

    retention_fidelity_audit_md = ""
    if retention_storyboard_exists:
        retention_fidelity_audit_md = f"""
### ⚡ Retention Fidelity Audit
* **Retention Post-process Status**: `{retention_postprocess_status.upper()}`
* **Final Video Source**: `{final_video_source}`
* **Subtitle Mode Disabled**: `{str(subtitle_mode_disabled).lower()}`
* **Overlay Count**: `{retention_overlay_count}`
* **Scene Count**: `{retention_scene_count}`
* **Average Overlay Duration**: `{avg_overlay_duration}`
* **Contact Sheet Path**: `{contact_sheet_path}`
* **Format Fidelity Status**: `{format_fidelity_status.upper()}`
* **Manual Review Required**: `true`

---
"""

    markdown = f"""# 🎬 YouTube Shorts Auto-Posting Run Summary

### 📊 Configuration Parameters
* **Topic/Subject**: `{topic}`
* **Niche**: `{niche}`
* **Privacy Level**: `{privacy}`
* **Generation Mode**: `{generation_mode}`
* **Metadata Mode**: `{metadata_mode}`
* **Posting Mode**: `{posting_mode}`

---
{content_engine_md}
{viral_format_audit_md}
{retention_fidelity_audit_md}
### 🔍 LLM Provider Audit

#### 🎥 Video Generation (MoneyPrinterTurbo)
* **Requested MPT Provider**: `{requested_mpt_provider}`
* **Actual MPT Provider Used**: `{actual_mpt_provider_used}`

#### 📝 Metadata Generation
* **Requested Metadata Provider**: `{requested_metadata_provider}`
* **Actual Metadata Provider Used**: `{actual_metadata_provider_used}`
* **Status**: {get_meta_status_emoji(meta_status)}
* **Fallback Occurred**: `{fallback_occurred}`
{f"* **Error**: `{meta_error}`" if meta_error else ""}

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
        "requested_mpt_provider": requested_mpt_provider,
        "actual_mpt_provider_used": actual_mpt_provider_used,
        "requested_metadata_provider": requested_metadata_provider,
        "actual_metadata_provider_used": actual_metadata_provider_used,
        "metadata_fallback_occurred": fallback_occurred,
        "metadata_status": meta_status,
        "metadata_error": meta_error,
        "video_path": video_path,
        "public_video_url": public_video_url,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "use_video_brief": use_video_brief,
        "profile_id": profile_id,
        "selected_idea": selected_idea,
        "freshness_score": freshness_score,
        "quality_status": quality_status,
        "format_id": format_id,
        "target_duration_seconds": target_duration_seconds,
        "actual_duration_seconds": actual_duration_seconds,
        "duration_status": duration_status,
        "viral_format_status": viral_format_status,
        "retention_format_status": retention_format_status,
        "retention_scene_count": retention_scene_count,
        "retention_overlay_count": retention_overlay_count,
        "retention_motion_status": retention_motion_status,
        "retention_sound_status": retention_sound_status,
        "retention_copyright_status": retention_copyright_status,
        "retention_postprocess_status": retention_postprocess_status,
        "final_video_source": final_video_source,
        "subtitle_mode_disabled": subtitle_mode_disabled,
        "avg_overlay_duration": float(avg_overlay_duration.replace("s", "")) if avg_overlay_duration != "N/A" else 0.5,
        "contact_sheet_path": contact_sheet_path,
        "format_fidelity_status": format_fidelity_status,
        "manual_review_required": True,
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
