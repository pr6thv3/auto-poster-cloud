# Runbook: auto-poster-cloud

This document serves as the operations guide for triggering, monitoring, and troubleshooting the cloud video posting pipeline.

## 🚀 Triggering the Pipeline

### Option 1: Manual Trigger via GitHub Mobile / Web UI
1. Go to your GitHub Repository -> **Actions** tab.
2. Select the **Generate and Post Video** workflow.
3. Click **Run workflow** and fill in the inputs:
   - **topic**: "e.g., 3 productivity tips for developers"
   - **title**: "Social post title"
   - **description**: "Post caption/hashtags"
   - **platforms**: "youtube,instagram,facebook" (or a subset)
   - **privacy**: "private" (use for testing) or "public"
   - **mock_mode**: "true" (to verify GHA runs without posting) or "false" (live)
4. Click **Run workflow**.

---

## 📅 Scheduled Trigger (Content Queue)

To support automated postings on a schedule without hardcoding topics in the cron worker, a queue file is placed in this repository: `docs/content-queue.json`.

### Queue Structure (`docs/content-queue.json`):
```json
[
  {
    "topic": "3 AI websites you did not know existed",
    "title": "Unbelievable AI Websites!",
    "description": "These 3 websites will save you hours of work. #ai #productivity",
    "niche": "ai",
    "posted": false
  },
  {
    "topic": "The history of the first computer bug",
    "title": "The First Computer Bug 🐛",
    "description": "How a literal moth in a relay caused the term 'bug' to be coined. #techhistory",
    "niche": "history",
    "posted": false
  }
]
```

### Scheduled Execution Logic:
1. The Cloudflare Cron trigger fires at the scheduled time.
2. The Worker requests the `docs/content-queue.json` from the repository main branch.
3. The Worker finds the first item where `"posted": false`.
4. It calls `workflow_dispatch` passing the item's parameters.
5. Once the run completes, the user commits `"posted": true` (or the pipeline handles it automatically in a future phase).

---

## 📊 Monitoring Runs

1. **GitHub Job Summary**: Every workflow run generates a Markdown summary visible at the bottom of the Action Run details page. It details exactly what files were generated, the Cloudflare R2 staging URL, and individual status for YouTube, Instagram, and Facebook.
2. **GitHub Mobile app**: Enable push notifications for workflow status to get instant notifications when a job completes or fails.

---

## 🛠️ Recovery Procedures

### 1. Job Fails During Generation
* **Symptom**: MoneyPrinterTurbo crashes or errors out.
* **Resolution**: Check the Actions run logs. If it's a network timeout, click **Re-run failed jobs**. If it's an API error (e.g. LLM rate limit), verify your LLM API keys in Secrets.

### 2. Failure on a Single Platform (e.g., Instagram fails, YouTube succeeds)
* **Symptom**: Part of the posting fails while other platforms succeed.
* **Resolution**: 
  1. Open the GHA run details and look at the job summary. Copy the **Cloudflare R2 Public URL** (which is already uploaded and valid).
  2. Go to Actions -> Select **Post Existing Video** workflow.
  3. Click **Run workflow** and paste the R2 URL as `video_url`, select only the failed platform (e.g., `instagram`), and set `mock_mode` to `false`.
  4. This posts the already-generated video without wasting Actions minutes or LLM API calls on regeneration!
