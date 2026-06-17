# Setup Guide: auto-poster-cloud

This guide outlines the step-by-step process to configure the Cloud-Executed, Phone-Triggered Video Posting Pipeline.

## 📋 Prerequisites
Before setting up the repository, ensure you have the following accounts and permissions ready:
- A GitHub Account
- A Cloudflare Account (with Workers and R2 enabled)
- A Google Cloud Platform (GCP) project with the **YouTube Data API v3** enabled
- A Meta Developer App with **Instagram Graph API** and **Facebook Login** configured
- A Facebook Page connected to a professional Instagram (Business or Creator) account

---

## 🔒 GitHub Secrets Configuration

Navigate to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**. Add the following keys:

### 1. Cloudflare R2 Secrets
* `R2_ACCOUNT_ID`: Your Cloudflare Account ID (found on your Cloudflare dashboard Home page or R2 page).
* `R2_ACCESS_KEY_ID`: S3 API Access Key ID for your bucket.
* `R2_SECRET_ACCESS_KEY`: S3 API Secret Access Key.
* `R2_BUCKET`: `shorts-staging` (the name of your R2 bucket).
* `R2_PUBLIC_BASE_URL`: The custom domain or public endpoint mapped to your bucket (e.g., `https://media.yourdomain.com`).

### 2. YouTube OAuth2 Secrets
* `YOUTUBE_CLIENT_ID`: Your Google OAuth2 Client ID.
* `YOUTUBE_CLIENT_SECRET`: Your Google OAuth2 Client Secret.
* `YOUTUBE_REFRESH_TOKEN`: The offline refresh token obtained for your YouTube channel.

### 3. Meta Graph API Secrets
* `META_PAGE_ACCESS_TOKEN`: Long-lived Page Access Token (or permanent System User token).
* `IG_USER_ID`: Your Instagram Business Account ID.
* `FACEBOOK_PAGE_ID`: Your Facebook Page ID.
* `GRAPH_API_VERSION`: `v25.0` (or your pinned API version).

### 4. Pipeline Trigger Secrets
* `CLOUDFLARE_TRIGGER_SECRET`: A secure random string used as a shared secret between your phone (the Cloudflare Worker) and GitHub Actions.

---

## 🪣 Cloudflare R2 Bucket Configuration

1. Create a bucket named `shorts-staging` in **R2** -> **Create Bucket**.
2. Set up **Public Access** in the bucket settings:
   - Either enable the default `r2.dev` subdomain (good for testing, but not recommended for production due to rate limiting).
   - **Recommended:** Connect a custom domain (e.g., `media.yourdomain.com`) in the bucket Settings -> **Domain Names**.
3. Add a **Lifecycle Rule** (Object TTL) to automatically delete staging files after 7 days to keep storage usage within the free tier:
   - Go to R2 bucket Settings -> **Lifecycle Rules** -> **Add Rule**.
   - Action: **Delete objects**.
   - Age: **7 days** (or 24 hours).

---

## 🔑 API Credential Exchanges (Human Tasks)

### 1. YouTube Resumable Upload
* In Google Cloud Console, configure the OAuth Consent Screen as **External** and add your own Google email as a **Test User**.
* If your Google Cloud app remains in "Testing" mode, the OAuth tokens will expire every 7 days unless refreshed, and uploads will default to **private**.
* Apply for API Audit/Verification if you need videos to be uploaded directly as **public**.

### 2. Meta Graph Token Exchange
* Get a short-lived user token from the **Graph API Explorer** with permissions: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`.
* Exchange it for a 60-day user token via:
  ```
  GET https://graph.facebook.com/{version}/oauth/access_token?grant_type=fb_exchange_token&client_id={app_id}&client_secret={app_secret}&fb_exchange_token={short_lived_token}
  ```
* Retrieve the permanent Page Access token using the 60-day token:
  ```
  GET https://graph.facebook.com/{version}/me/accounts?fields=id,name,access_token,instagram_business_account&access_token={60_day_token}
  ```
* Store the returned `access_token` as `META_PAGE_ACCESS_TOKEN`.

---

## ⚡ Cloudflare Worker Deployment & Setup

The trigger Worker is designed to be deployed using Wrangler.

### 1. Log In to Cloudflare
In your local command line, run:
```bash
npx wrangler login
```

### 2. Configure Worker Secrets
You must configure the required secrets in your Cloudflare environment. These secrets are encrypted and kept hidden on Cloudflare servers. Run the following commands:

```bash
# GitHub repository owner (username or org name)
npx wrangler secret put GITHUB_OWNER

# GitHub repository name (e.g. auto-poster-cloud)
npx wrangler secret put GITHUB_REPO

# Target workflow file name (e.g. generate-and-post.yml)
npx wrangler secret put GITHUB_WORKFLOW_FILE

# Fine-grained GitHub PAT with actions:write scope to trigger dispatch
npx wrangler secret put GITHUB_DISPATCH_TOKEN

# Shared trigger secret (matches CLOUDFLARE_TRIGGER_SECRET in GHA)
npx wrangler secret put WORKER_TRIGGER_SECRET
```

### 3. Deploy the Worker
Run the deploy command from the `cloud-pipeline/worker/` directory:
```bash
npx wrangler deploy
```

Once deployed, Cloudflare will output the Worker URL (e.g., `https://auto-poster-trigger-worker.<your-subdomain>.workers.dev`). Use this URL on your phone or in API calls!

