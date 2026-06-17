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
        const title = body.title?.trim();
        const description = body.description?.trim();
        const niche = body.niche?.trim() || 'general';
        const platforms = body.platforms || 'youtube'; // Can be string or array
        const privacy = body.privacy || 'private';
        const mockMode = body.mock_mode === undefined ? 'true' : String(body.mock_mode);
        const jobId = body.job_id || 'job_' + Math.random().toString(36).substring(2, 10);

        if (!topic || !title || !description) {
          return new Response(JSON.stringify({ 
            status: 'error', 
            message: 'Missing required fields: topic, title, description' 
          }), { 
            status: 400, 
            headers: { 'Content-Type': 'application/json' } 
          });
        }

        // Format platforms as comma-separated string if passed as list
        const formattedPlatforms = Array.isArray(platforms) 
          ? platforms.join(',') 
          : String(platforms);

        // GitHub Dispatch API payload
        const githubPayload = {
          ref: 'main',
          inputs: {
            topic: topic,
            title: title,
            description: description,
            niche: niche,
            platforms: formattedPlatforms,
            privacy: privacy,
            mock_mode: mockMode,
            job_id: jobId
          }
        };

        // Trigger GitHub Actions
        const githubUrl = `https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/${env.GITHUB_WORKFLOW_FILE}/dispatches`;
        
        const ghResponse = await fetch(githubUrl, {
          method: 'POST',
          headers: {
            'Accept': 'application/vnd.github+json',
            'Authorization': `Bearer ${env.GITHUB_DISPATCH_TOKEN}`,
            'X-GitHub-Api-Version': '2022-11-28',
            'User-Agent': 'Cloudflare-Worker'
          },
          body: JSON.stringify(githubPayload)
        });

        if (ghResponse.status !== 204) {
          const errorText = await ghResponse.text();
          return new Response(JSON.stringify({ 
            status: 'error', 
            message: `GitHub API error: Status ${ghResponse.status}. Details: ${errorText}`
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
  }
};

// HTML Template function
function serveHTML(token) {
  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Auto Poster Cloud Trigger</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #09090b;
      --glass-bg: rgba(24, 24, 27, 0.6);
      --glass-border: rgba(63, 63, 70, 0.4);
      --text: #f4f4f5;
      --text-muted: #a1a1aa;
      --accent: #6366f1;
      --accent-hover: #4f46e5;
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

    /* Gradient Background blobs */
    body::before, body::after {
      content: '';
      position: absolute;
      width: 300px;
      height: 300px;
      border-radius: 50%;
      filter: blur(100px);
      z-index: -1;
      opacity: 0.5;
    }

    body::before {
      background: rgba(99, 102, 241, 0.4);
      top: 10%;
      left: 10%;
    }

    body::after {
      background: rgba(168, 85, 247, 0.3);
      bottom: 15%;
      right: 10%;
    }

    .container {
      width: 100%;
      max-width: 520px;
      background: var(--glass-bg);
      border: 1px solid var(--glass-border);
      border-radius: 20px;
      padding: 30px;
      backdrop-filter: blur(12px);
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
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
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    input[type="text"],
    textarea,
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
    textarea:focus,
    select:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    }

    textarea {
      resize: vertical;
      min-height: 80px;
    }

    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .checkbox-group {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 4px;
    }

    .checkbox-card {
      flex: 1 1 100px;
      position: relative;
    }

    .checkbox-card input[type="checkbox"] {
      position: absolute;
      opacity: 0;
      cursor: pointer;
      height: 0;
      width: 0;
    }

    .checkbox-label {
      display: block;
      padding: 12px 10px;
      background: rgba(9, 9, 11, 0.6);
      border: 1px solid var(--glass-border);
      border-radius: 10px;
      font-size: 14px;
      font-weight: 500;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s;
      user-select: none;
    }

    .checkbox-card input:checked + .checkbox-label {
      border-color: var(--accent);
      background: rgba(99, 102, 241, 0.15);
      color: var(--text);
      box-shadow: 0 0 0 1px var(--accent);
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
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
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
    <h1>Auto Poster Cloud</h1>
    <div class="subtitle">Trigger GHA Video Posting Pipeline</div>

    <form id="triggerForm">
      <input type="hidden" name="token" value="${token}">
      <input type="hidden" id="jobId" name="job_id" value="">

      <div class="form-group">
        <label for="topic">Video Subject / Topic</label>
        <input type="text" id="topic" name="topic" placeholder="e.g. 3 AI websites you should use" required>
      </div>

      <div class="form-group">
        <label for="title">Post Title</label>
        <input type="text" id="title" name="title" placeholder="e.g. Unbelievable AI Websites!" required>
      </div>

      <div class="form-group">
        <label for="description">Caption / Description</label>
        <textarea id="description" name="description" placeholder="e.g. These websites will save you hours of work..." required></textarea>
      </div>

      <div class="row">
        <div class="form-group">
          <label for="niche">Niche</label>
          <input type="text" id="niche" name="niche" value="ai" required>
        </div>
        <div class="form-group">
          <label for="privacy">Privacy</label>
          <select id="privacy" name="privacy">
            <option value="private" selected>Private</option>
            <option value="unlisted">Unlisted</option>
            <option value="public">Public</option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label>Target Platforms</label>
        <div class="checkbox-group">
          <div class="checkbox-card">
            <input type="checkbox" id="plat_yt" name="platforms" value="youtube" checked>
            <label for="plat_yt" class="checkbox-label">YouTube</label>
          </div>
          <div class="checkbox-card">
            <input type="checkbox" id="plat_ig" name="platforms" value="instagram" checked>
            <label for="plat_ig" class="checkbox-label">Instagram</label>
          </div>
          <div class="checkbox-card">
            <input type="checkbox" id="plat_fb" name="platforms" value="facebook" checked>
            <label for="plat_fb" class="checkbox-label">Facebook</label>
          </div>
        </div>
      </div>

      <div class="form-group">
        <label for="mockMode">Execution Mode</label>
        <select id="mockMode" name="mock_mode">
          <option value="true" selected>Mock Run (Safe)</option>
          <option value="false">Live Posting (Real API)</option>
        </select>
      </div>

      <button type="submit" class="btn-submit" id="submitBtn">
        <span id="btnText">Generate & Post</span>
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

      // Parse platforms checkboxes
      const selectedPlatforms = [];
      document.querySelectorAll('input[name="platforms"]:checked').forEach(cb => {
        selectedPlatforms.push(cb.value);
      });

      const formData = new FormData(form);
      // Replace platforms with formatted string
      formData.delete('platforms');
      formData.append('platforms', selectedPlatforms.join(','));

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
            <a href="\${result.workflow_url}" target="_blank" class="result-link">View GitHub Actions Run</a>
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
