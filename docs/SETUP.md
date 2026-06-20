# Setup Guide: auto-poster-cloud (YouTube Shorts Only)

This guide outlines the step-by-step process to configure the Cloud-Executed, Web/Cron-Triggered YouTube Shorts Auto-Posting Pipeline.

## 📋 Prerequisites
Before setting up the repository, ensure you have the following accounts and API credentials ready:
- A GitHub Account
- A Cloudflare Account (with Workers and optional R2 enabled)
- A Google Cloud Platform (GCP) project with the **YouTube Data API v3** enabled
- A LLM Provider API Key: **OpenAI API Key** or **Gemini API Key** (for metadata generation in real mode)

---

## 🔒 GitHub Secrets Configuration

Navigate to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**. Add the following keys:

### 1. YouTube OAuth2 Secrets
* `YOUTUBE_CLIENT_ID`: Your Google OAuth2 Client ID.
* `YOUTUBE_CLIENT_SECRET`: Your Google OAuth2 Client Secret.
* `YOUTUBE_REFRESH_TOKEN`: The offline refresh token obtained for your YouTube channel.

### 2. LLM Provider Secrets (For Metadata)
* `LLM_PROVIDER`: Set to either `openai`, `gemini`, or `nvidia` (Gemini remains default).
* `OPENAI_API_KEY`: Required if `LLM_PROVIDER` is `openai`.
* `OPENAI_MODEL_NAME`: Optional (defaults to `gpt-4o-mini`).
* `GEMINI_API_KEY`: Required if `LLM_PROVIDER` is `gemini`.
* `GEMINI_MODEL_NAME`: Optional (defaults to `gemini-2.5-flash`).
* `NVIDIA_API_KEY`: Required if `LLM_PROVIDER` is `nvidia` (e.g., `nvapi-...`).
* `NVIDIA_BASE_URL`: Optional if `LLM_PROVIDER` is `nvidia` (defaults to `https://integrate.api.nvidia.com/v1`).
* `NVIDIA_MODEL_NAME`: Required if `LLM_PROVIDER` is `nvidia` (e.g., `mistralai/mistral-medium-3.5-128b`).

### 3. Cloudflare R2 Secrets (Optional for Debug Archive)
* `R2_ACCOUNT_ID`: Your Cloudflare Account ID.
* `R2_ACCESS_KEY_ID`: S3 API Access Key ID for your bucket.
* `R2_SECRET_ACCESS_KEY`: S3 API Secret Access Key.
* `R2_BUCKET`: The name of your R2 bucket.
* `R2_PUBLIC_BASE_URL`: The custom domain or public endpoint mapped to your bucket.

### 4. Pipeline Trigger Secrets
* `GITHUB_DISPATCH_TOKEN`: Fine-grained GitHub PAT with `actions:write` and `contents:write` scopes to allow the worker to trigger runs and the workflow to update the queue.
* `WORKER_TRIGGER_SECRET`: A secure random string used as a shared secret between your Worker trigger calls and the Worker.

---

## ⚡ Cloudflare Worker Deployment & Setup

The trigger Worker is designed to be deployed using Wrangler.

### 1. Log In to Cloudflare
In your local command line, run:
```bash
npx wrangler login
```

### 2. Configure Worker Secrets
You must configure the required secrets in your Cloudflare environment. Run the following commands:

```bash
# GitHub repository owner (username or org name)
npx wrangler secret put GITHUB_OWNER

# GitHub repository name (e.g. auto-poster-cloud)
npx wrangler secret put GITHUB_REPO

# Target workflow file name (generate-youtube-short.yml)
npx wrangler secret put GITHUB_WORKFLOW_FILE

# Fine-grained GitHub PAT with actions:write and contents:write scope to trigger dispatch and update queue
npx wrangler secret put GITHUB_DISPATCH_TOKEN

# Shared trigger secret
npx wrangler secret put WORKER_TRIGGER_SECRET
```

### 3. Deploy the Worker
Run the deploy command from the `cloud-pipeline/worker/` directory:
```bash
npx wrangler deploy
```

---

## 📅 Scheduled Postings (Cron & Content Queue)

The pipeline is set up to run three times daily via Cloudflare Cron Triggers:
- **9:00 AM IST** (03:30 UTC): cron expression `30 3 * * *`
- **2:00 PM IST** (08:30 UTC): cron expression `30 8 * * *`
- **7:00 PM IST** (13:30 UTC): cron expression `30 13 * * *`

When a cron trigger fires:
1. The Cloudflare Worker fetches **[`docs/content-queue.json`](file:///docs/content-queue.json)** directly from the GitHub API.
2. It parses the queue, identifies the first item where `"posted"` is `false` and `"status"` is `"pending"`.
3. It triggers GHA workflow `generate-youtube-short.yml` via `workflow_dispatch` with the item's parameters (and `queue_item_id`).
4. Upon successful posting, the GHA run updates `"posted": true`, `"status": "success"`, and `"youtube_video_id"` in `docs/content-queue.json` and commits it back.
