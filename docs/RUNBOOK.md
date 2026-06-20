# Runbook: auto-poster-cloud (YouTube Shorts Only)

This document serves as the operations guide for triggering, monitoring, and troubleshooting the YouTube Shorts posting pipeline.

## 🚀 Manual Execution via GitHub Actions

### Option 1: Generate & Post Workflow
1. Go to your GitHub Repository -> **Actions** tab.
2. Select the **Generate and Post YouTube Short** workflow.
3. Click **Run workflow** and specify:
   - **topic**: "e.g., 3 productivity tips for developers"
   - **niche**: "ai" (or your niche folder name)
   - **generation_mode**: `mock` (creates dummy MP4) or `real` (runs MoneyPrinterTurbo)
   - **metadata_mode**: `mock` (static title/desc) or `real` (queries OpenAI/Gemini/NVIDIA LLM)
   - **llm_provider**: `nvidia` (optional override to test NVIDIA NIM; otherwise falls back to repository default `LLM_PROVIDER` secret, which defaults to `gemini`)
   - **posting_mode**: `mock` (skips upload) or `real` (posts to YouTube)
   - **privacy**: `private` (recommended for testing), `unlisted`, or `public`

### Option 2: Post Existing Video Workflow
1. Go to Actions -> **Post Existing Video to YouTube**.
2. Click **Run workflow** and specify:
   - **video_url_or_path**: Public HTTPS URL or local file path of the MP4 video.
   - **topic**: Video topic name.
   - **niche**: Niche category.
   - **metadata_mode**: `mock` or `real`.
   - **posting_mode**: `mock` or `real`.
   - **privacy**: `private`, `unlisted`, or `public`.

---

## 📅 Scheduled Trigger (Content Queue)

Automated posting reads from `docs/content-queue.json`.

### Queue Schema:
```json
[
  {
    "id": "1",
    "enabled": true,
    "posted": false,
    "status": "pending",
    "topic": "3 AI websites you did not know existed",
    "niche": "ai",
    "privacy": "private",
    "generation_mode": "mock",
    "metadata_mode": "mock",
    "posting_mode": "mock",
    "slot": "1",
    "attempts": 0,
    "last_error": "",
    "youtube_video_id": ""
  }
]
```

### Scheduled Handler Logic:
1. Cloudflare trigger fires at 9 AM, 2 PM, or 7 PM IST.
2. Worker fetches queue file from the main branch.
3. Worker picks the first item where `"posted": false` and `"status": "pending"`.
4. Worker dispatches GHA with item inputs.
5. GHA uploads and updates the item fields (setting `"posted": true`, `"status": "success"`, `"youtube_video_id"`).

---

## 🧪 Testing Matrix

To verify reliability before live posting, run through this progressive testing matrix:

1. **Mock End-to-End**:
   - `generation_mode=mock`, `metadata_mode=mock`, `posting_mode=mock`
   - Bypasses all APIs, tests workflow pipeline orchestration, and updates queue in under 30 seconds.
2. **Real Generation Only**:
   - `generation_mode=real`, `metadata_mode=mock`, `posting_mode=mock`
   - Validates MoneyPrinterTurbo cloning, config.toml generation, script generation, and local file storage.
3. **Real Generation & Metadata**:
   - `generation_mode=real`, `metadata_mode=real`, `posting_mode=mock`
   - Validates LLM metadata completion (title length, description format, #Shorts presence) and writes to `youtube-metadata.json`.
4. **NVIDIA NIM LLM Provider Test**:
   - `generation_mode=mock`, `metadata_mode=real`, `posting_mode=mock`, `llm_provider=nvidia` (or setting `LLM_PROVIDER` secret to `nvidia`)
   - Bypasses video generation (mock), but calls NVIDIA NIM completions to generate real metadata (title, description, tags, hashtags) and writes to `youtube-metadata.json`. Useful for validation without rendering/generating a real video.
5. **Post Existing Video (Manual)**:
   - Run **Post Existing Video to YouTube** with a known vertical MP4 link, `posting_mode=real`, and `privacy=private`.
   - Verifies OAuth2 refreshing and resumable YouTube uploads.
6. **Full Private Post**:
   - `generation_mode=real`, `metadata_mode=real`, `posting_mode=real`, `privacy=private`
   - Verifies the full pipeline end-to-end without publishing publicly.
7. **Unlisted / Public**:
   - Transition to `unlisted` or `public` once private tests pass successfully.

---

## 🛡️ Reliability & Safety Safeguards
- **Format Validation**: Any real MP4 upload is checked via `ffprobe` to confirm it is vertical 9:16, <= 60 seconds duration, and encoded with H.264 video / AAC audio.
- **Quota Exceeded Check**: If the YouTube API responds with `dailyLimitExceeded` or `quotaExceeded` (403/429), the script terminates cleanly with status `quota_exceeded`, avoiding blind retries.
- **Duplicate Protection**: If the queue item already contains a `youtube_video_id` or the workflow input includes it, the upload step skips automatically.
- **n8n Fallback**: Telegram, Hermes, and complex n8n workflows are removed. n8n remains available strictly as a fallback tool for local testing.
