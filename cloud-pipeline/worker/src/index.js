// Cloudflare Worker: auto-poster-trigger-worker

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Check path
    if (url.pathname !== '/' && url.pathname !== '/run') {
      return new Response('Not Found', { status: 404 });
    }

    // Auth validation helper
    const isAuthorized = (req) => {
      const secret = env.WORKER_TRIGGER_SECRET;
      if (!secret) return false;

      // 1. Check Query Token
      const queryToken = url.searchParams.get('token');
      if (queryToken === secret) return true;

      // 2. Check Auth Header
      const authHeader = req.headers.get('Authorization');
      if (authHeader) {
        const parts = authHeader.split(' ');
        if (parts.length === 2 && parts[0].toLowerCase() === 'bearer' && parts[1] === secret) {
          return true;
        }
      }

      return false;
    };

    if (!isAuthorized(request)) {
      return new Response('Unauthorized: Invalid or missing token', { 
        status: 401,
        headers: { 'WWW-Authenticate': 'Bearer' }
      });
    }

    // Handle GET: Serve HTML Trigger UI
    if (request.method === 'GET') {
      return serveHTML(url.searchParams.get('token'));
    }

    // Handle POST: Trigger GHA Workflow
    if (request.method === 'POST') {
      try {
        let body = {};
        const contentType = request.headers.get('Content-Type') || '';
        
        if (contentType.includes('application/json')) {
          body = await request.json();
        } else if (contentType.includes('application/x-www-form-urlencoded') || contentType.includes('multipart/form-data')) {
          const formData = await request.formData();
          for (const [key, value] of formData.entries()) {
            body[key] = value;
          }
        }

        // Validate Inputs
        const topic = body.topic?.trim();
        const niche = body.niche?.trim() || 'ai';
        const privacy = body.privacy || 'private';
        const generationMode = body.generation_mode || 'mock';
        const metadataMode = body.metadata_mode || 'mock';
        const postingMode = body.posting_mode || 'mock';
        const llmProvider = body.llm_provider || '';
        const jobId = body.job_id || 'job_' + Math.random().toString(36).substring(2, 10);

        if (!topic) {
          return new Response(JSON.stringify({ 
            status: 'error', 
            message: 'Missing required field: topic' 
          }), { 
            status: 400, 
            headers: { 'Content-Type': 'application/json' } 
          });
        }

        // GitHub Dispatch API payload
        const githubPayload = {
          ref: 'main',
          inputs: {
            topic: topic,
            niche: niche,
            privacy: privacy,
            generation_mode: generationMode,
            metadata_mode: metadataMode,
            posting_mode: postingMode,
            llm_provider: llmProvider,
            queue_item_id: '',
            job_id: jobId
          }
        };

        // Trigger GitHub Actions
        const triggerResult = await triggerWorkflow(env, githubPayload);

        if (triggerResult.status !== 'success') {
          return new Response(JSON.stringify({ 
            status: 'error', 
            message: triggerResult.message
          }), { 
            status: 502, 
            headers: { 'Content-Type': 'application/json' } 
          });
        }

        const workflowUrl = `https://github.com/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions`;

        return new Response(JSON.stringify({
          status: 'success',
          message: 'Pipeline triggered successfully!',
          job_id: jobId,
          workflow_url: workflowUrl
        }), { 
          status: 200, 
          headers: { 'Content-Type': 'application/json' } 
        });

      } catch (err) {
        return new Response(JSON.stringify({ 
          status: 'error', 
          message: `Internal server error: ${err.message}` 
        }), { 
          status: 500, 
          headers: { 'Content-Type': 'application/json' } 
        });
      }
    }

    return new Response('Method Not Allowed', { status: 405 });
  },
  async scheduled(event, env, ctx) {
    if (env.ENABLE_CRON !== 'true') {
      console.log('Cron is disabled (ENABLE_CRON is not true). Returning early.');
      return;
    }
    ctx.waitUntil(handleScheduled(env));
  }
};

// HTML Template function
function serveHTML(token) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>YouTube Shorts Trigger UI</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #09090b;
      --glass-bg: rgba(24, 24, 27, 0.6);
      --glass-border: rgba(63, 63, 70, 0.4);
      --text: #f4f4f5;
      --text-muted: #a1a1aa;
      --accent: #ff0000;
      --accent-hover: #cc0000;
      --accent-glow: rgba(255, 0, 0, 0.2);
      --success: #10b981;
      --error: #ef4444;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: var(--bg);
      color: var(--text);
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 20px;
      overflow-x: hidden;
      position: relative;
    }

    /* Red/Orange glow blobs for YouTube theme */
    body::before, body::after {
      content: '';
      position: absolute;
      width: 300px;
      height: 300px;
      border-radius: 50%;
      filter: blur(100px);
      z-index: -1;
      opacity: 0.35;
    }

    body::before {
      background: rgba(255, 0, 0, 0.3);
      top: 10%;
      left: 10%;
    }

    body::after {
      background: rgba(249, 115, 22, 0.2);
      bottom: 15%;
      right: 10%;
    }

    .container {
      width: 100%;
      max-width: 540px;
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      padding: 30px;
      backdrop-filter: blur(12px);
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
      animation: fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    h1 {
      font-size: 24px;
      font-weight: 700;
      margin-bottom: 8px;
      text-align: center;
      background: linear-gradient(135deg, #fff 0%, var(--text-muted) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .subtitle {
      font-size: 14px;
      color: var(--text-muted);
      text-align: center;
      margin-bottom: 28px;
    }

    .form-group {
      margin-bottom: 20px;
    }

    label {
      display: block;
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    input[type="text"],
    select {
      width: 100%;
      padding: 12px 16px;
      background: rgba(9, 9, 11, 0.8);
      border: 1px solid var(--glass-border);
      border-radius: 10px;
      color: var(--text);
      font-family: inherit;
      font-size: 15px;
      transition: border-color 0.2s, box-shadow 0.2s;
    }

    input[type="text"]:focus,
    select:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }

    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .btn-submit {
      width: 100%;
      padding: 14px;
      background: var(--accent);
      border: none;
      border-radius: 10px;
      color: #fff;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s, transform 0.1s;
      margin-top: 10px;
      box-shadow: 0 4px 12px var(--accent-glow);
    }

    .btn-submit:hover {
      background: var(--accent-hover);
    }

    .btn-submit:active {
      transform: scale(0.98);
    }

    /* Result Card styling */
    .result-card {
      margin-top: 24px;
      padding: 16px;
      border-radius: 10px;
      font-size: 14px;
      display: none;
      animation: slideDown 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }

    @keyframes slideDown {
      from { opacity: 0; transform: translateY(-10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .result-card.success {
      display: block;
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.4);
      color: #34d399;
    }

    .result-card.error {
      display: block;
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #fca5a5;
    }

    .result-link {
      display: inline-block;
      margin-top: 8px;
      color: #fff;
      font-weight: 600;
      text-decoration: underline;
    }

    .loader {
      display: none;
      width: 20px;
      height: 20px;
      border: 2px solid #fff;
      border-bottom-color: transparent;
      border-radius: 50%;
      margin: 0 auto;
      animation: rotation 1s linear infinite;
    }

    @keyframes rotation {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>YouTube Shorts Pipeline</h1>
    <div class="subtitle">Trigger GHA Auto-Posting Workflow</div>

    <form id="triggerForm">
      <input type="hidden" name="token" value="${token}">
      <input type="hidden" id="jobId" name="job_id" value="">

      <div class="form-group">
        <label for="topic">Video Subject / Topic</label>
        <input type="text" id="topic" name="topic" placeholder="e.g. 3 AI websites that feel illegal to know" required>
      </div>

      <div class="row">
        <div class="form-group">
          <label for="niche">Niche</label>
          <input type="text" id="niche" name="niche" value="ai" required>
        </div>
        <div class="form-group">
          <label for="privacy">Privacy Status</label>
          <select id="privacy" name="privacy">
            <option value="private" selected>Private</option>
            <option value="unlisted">Unlisted</option>
            <option value="public">Public</option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label for="generationMode">Video Generation</label>
        <select id="generationMode" name="generation_mode">
          <option value="mock" selected>Mock Generation (Bypass MPT)</option>
          <option value="real">Real Generation (MoneyPrinterTurbo)</option>
        </select>
      </div>

      <div class="form-group">
        <label for="metadataMode">Metadata Generation</label>
        <select id="metadataMode" name="metadata_mode">
          <option value="mock" selected>Mock Metadata (Static Stub)</option>
          <option value="real">Real Metadata (Gemini/OpenAI LLM)</option>
        </select>
      </div>

      <div class="form-group">
        <label for="llmProvider">LLM Provider (Metadata)</label>
        <select id="llmProvider" name="llm_provider">
          <option value="" selected>Default (Secret/Gemini)</option>
          <option value="gemini">Gemini (gemini-2.5-flash)</option>
          <option value="nvidia">NVIDIA NIM (mistral-medium)</option>
          <option value="openai">OpenAI (gpt-4o-mini)</option>
        </select>
      </div>

      <div class="form-group">
        <label for="postingMode">YouTube Posting</label>
        <select id="postingMode" name="posting_mode">
          <option value="mock" selected>Mock Post (Bypass Upload)</option>
          <option value="real">Real Post (Live YouTube Upload)</option>
        </select>
      </div>

      <button type="submit" class="btn-submit" id="submitBtn">
        <span id="btnText">Trigger Workflow</span>
        <div class="loader" id="btnLoader"></div>
      </button>
    </form>

    <div class="result-card" id="resultCard"></div>
  </div>

  <script>
    // Generate unique Job ID on load
    document.getElementById('jobId').value = 'job_' + Math.random().toString(36).substring(2, 10);

    const form = document.getElementById('triggerForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const btnLoader = document.getElementById('btnLoader');
    const resultCard = document.getElementById('resultCard');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      // UI feedback loading state
      submitBtn.disabled = true;
      btnText.style.display = 'none';
      btnLoader.style.display = 'block';
      resultCard.className = 'result-card';
      resultCard.style.display = 'none';

      const formData = new FormData(form);

      try {
        const response = await fetch('/run', {
          method: 'POST',
          headers: {
            'Authorization': 'Bearer ' + formData.get('token')
          },
          body: formData
        });

        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
          resultCard.className = 'result-card success';
          resultCard.innerHTML = \`
            <strong>Success!</strong> \${result.message}<br>
            Job ID: <code>\${result.job_id}</code><br>
            <a href="\${result.workflow_url}" target="_blank" class="result-link">View GitHub Actions Runs</a>
          \`;
        } else {
          resultCard.className = 'result-card error';
          resultCard.innerHTML = \`<strong>Error:</strong> \${result.message || 'Trigger failed'}\`;
        }
      } catch (err) {
        resultCard.className = 'result-card error';
        resultCard.innerHTML = \`<strong>Network Error:</strong> \${err.message}\`;
      } finally {
        submitBtn.disabled = false;
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
      }
    });
  </script>
</body>
</html>`;
  return new Response(html, {
    headers: { 'Content-Type': 'text/html;charset=UTF-8' }
  });
}

// Helper: Trigger GitHub Actions workflow_dispatch
async function triggerWorkflow(env, payload) {
  // Gracefully fallback to generate-youtube-short.yml if the old config name is used
  const workflowFile = env.GITHUB_WORKFLOW_FILE || 'generate-youtube-short.yml';
  const targetWorkflow = (workflowFile === 'generate-and-post.yml' || workflowFile === 'generate-and-post') 
    ? 'generate-youtube-short.yml' 
    : workflowFile;

  const githubUrl = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/${targetWorkflow}/dispatches`;
  
  const res = await fetch(githubUrl, {
    method: 'POST',
    headers: {
      'Accept': 'application/vnd.github+json',
      'Authorization': `Bearer ${env.GITHUB_DISPATCH_TOKEN}`,
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'Cloudflare-Worker'
    },
    body: JSON.stringify(payload)
  });

  if (res.status === 204) {
    return { status: 'success' };
  } else {
    const errorText = await res.text();
    return { status: 'error', message: `GitHub API status ${res.status}. Details: ${errorText}` };
  }
}

// Helper: Fetch docs/content-queue.json and trigger next pending unposted video
async function handleScheduled(env) {
  console.log('Cron triggered! Fetching content queue...');
  
  if (!env.GITHUB_OWNER || !env.GITHUB_REPO || !env.GITHUB_DISPATCH_TOKEN) {
    console.error('Error: Missing GitHub configuration secrets (GITHUB_OWNER, GITHUB_REPO, GITHUB_DISPATCH_TOKEN)');
    return;
  }

  const contentsUrl = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/contents/docs/content-queue.json`;
  
  try {
    const res = await fetch(contentsUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/vnd.github+json',
        'Authorization': `Bearer ${env.GITHUB_DISPATCH_TOKEN}`,
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'Cloudflare-Worker'
      }
    });

    if (!res.ok) {
      const errText = await res.text();
      console.error(`Failed to fetch content queue from GitHub. Status: ${res.status}. Details: ${errText}`);
      return;
    }

    const data = await res.json();
    if (!data.content) {
      console.error('Error: Content field is missing from GitHub contents API response.');
      return;
    }

    // Decode base64 content
    const decodedContent = atob(data.content.replace(/\s/g, ''));
    const queue = JSON.parse(decodedContent);

    if (!Array.isArray(queue)) {
      console.error('Error: Content queue is not a valid JSON array.');
      return;
    }

    // Find first item where posted is false AND status is pending
    const item = queue.find(i => i.posted === false && i.status === 'pending');
    if (!item) {
      console.log('No pending, unposted queue items found. Nothing to do.');
      return;
    }

    console.log(`Found pending unposted item ID ${item.id}: "${item.topic}". Triggering pipeline...`);

    const jobId = 'cron_' + Math.random().toString(36).substring(2, 10);

    // Safety guardrails for scheduled trigger
    let generationMode = item.generation_mode || 'mock';
    let metadataMode = item.metadata_mode || 'mock';
    
    let postingMode = item.posting_mode || 'mock';
    if (postingMode === 'real' && env.ALLOW_LIVE_CRON !== 'true') {
      console.warn(`[SAFETY] Cron posting_mode is 'real' but ALLOW_LIVE_CRON is not 'true'. Overriding to 'mock'.`);
      postingMode = 'mock';
    }

    let privacy = item.privacy || 'private';
    if (privacy === 'public' && env.ALLOW_PUBLIC_CRON !== 'true') {
      console.warn(`[SAFETY] Cron privacy is 'public' but ALLOW_PUBLIC_CRON is not 'true'. Overriding to 'private'.`);
      privacy = 'private';
    }

    const payload = {
      ref: 'main',
      inputs: {
        topic: item.topic,
        niche: item.niche || 'ai',
        privacy: privacy,
        generation_mode: generationMode,
        metadata_mode: metadataMode,
        posting_mode: postingMode,
        queue_item_id: String(item.id),
        job_id: jobId
      }
    };


    const triggerRes = await triggerWorkflow(env, payload);
    if (triggerRes.status === 'success') {
      console.log(`Successfully triggered pipeline for "${item.topic}". Job ID: ${jobId}`);
    } else {
      console.error(`Failed to trigger pipeline for "${item.topic}": ${triggerRes.message}`);
    }

  } catch (err) {
    console.error(`Error in scheduled handler: ${err.message}`);
  }
}
