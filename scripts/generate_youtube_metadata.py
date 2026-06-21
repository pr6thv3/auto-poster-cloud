import os
import sys
import json
import requests
import time

def clean_json_response(text):
    """
    Cleans up any markdown formatting (like ```json ... ```) from the LLM output.
    """
    text = text.strip()
    if text.startswith("```"):
        # Remove first line if it contains the backticks
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def generate_mock_metadata(topic, niche, brief=None):
    print("[MOCK] Generating placeholder YouTube metadata...")
    if brief:
        title = f"Facts: {brief['topic'][:40]}! #Shorts"
        description = f"{brief['hook']}\n\nThis is about {brief['topic']}.\n\nSubscribe for more info!\n\n#Shorts"
        tags = [niche, "learning", "shorts"]
        hashtags = ["Shorts", niche]
        return {
            "title": title,
            "description": description,
            "tags": tags,
            "hashtags": hashtags,
            "categoryId": "28" if niche.lower() in ["ai", "science", "technology", "tech"] else "22"
        }
    return {
        "title": f"Amazing facts about {topic[:40]}! #Shorts",
        "description": f"Here is what you need to know about {topic}.\n\nSubscribe for more content on {niche}!\n\n#Shorts #learning #{niche}",
        "tags": [niche, "learning", "shorts", "interesting"],
        "hashtags": ["Shorts", "learning", niche],
        "categoryId": "28" if niche.lower() in ["ai", "science", "technology", "tech"] else "22"
    }

def call_gemini(topic, niche, script_text, system_prompt, user_prompt):
    gemini_key = os.environ.get('GEMINI_API_KEY')
    gemini_model = os.environ.get('GEMINI_MODEL_NAME', '').strip() or 'gemini-2.5-flash'
    if not gemini_key:
        raise Exception("Missing GEMINI_API_KEY")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": system_prompt + "\n\n" + user_prompt}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    # Retry once on transient errors (429, 5xx, timeout)
    for attempt in range(1, 3):
        try:
            print(f"[REAL] Generating metadata using Gemini ({gemini_model}) - Attempt {attempt}...")
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            
            # Check for transient status codes to retry
            if res.status_code in [429, 500, 502, 503, 504] and attempt == 1:
                print(f"Warning: Gemini API returned status {res.status_code}. Retrying in 2 seconds...")
                time.sleep(2)
                continue
                
            res.raise_for_status()
            res_json = res.json()
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            cleaned_text = clean_json_response(raw_text)
            return json.loads(cleaned_text)
        except requests.exceptions.RequestException as e:
            if attempt == 1:
                print(f"Warning: Gemini request failed: {e}. Retrying in 2 seconds...")
                time.sleep(2)
                continue
            raise e
        except Exception as e:
            raise e

def call_openai_compatible(provider_name, topic, niche, script_text, system_prompt, user_prompt, base_url, api_key, model_name):
    if not api_key:
        raise Exception(f"Missing API key for {provider_name}.")
    if not model_name:
        raise Exception(f"Missing model name for {provider_name}.")

    print(f"[REAL] Generating metadata using {provider_name} ({model_name})...")
    url = f"{base_url.rstrip('/')}/chat/completions" if base_url else "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"}
    }
    res = requests.post(url, headers=headers, json=payload, timeout=30)
    res.raise_for_status()
    res_json = res.json()
    raw_text = res_json["choices"][0]["message"]["content"]
    cleaned_text = clean_json_response(raw_text)
    return json.loads(cleaned_text)

def generate_real_metadata(topic, niche, script_text, system_prompt, user_prompt):
    llm_provider = os.environ.get('METADATA_PROVIDER', '').strip().lower() or os.environ.get('LLM_PROVIDER', '').strip().lower()
    
    # Defaults to gemini if not configured
    if not llm_provider:
        gemini_key = os.environ.get('GEMINI_API_KEY')
        nvidia_key = os.environ.get('NVIDIA_API_KEY')
        if gemini_key:
            llm_provider = "gemini"
        elif nvidia_key:
            llm_provider = "nvidia"
        else:
            raise Exception("No LLM provider keys configured in environment.")

    errors = []
    
    if llm_provider == "gemini":
        try:
            metadata = call_gemini(topic, niche, script_text, system_prompt, user_prompt)
            return metadata, "gemini", None
        except Exception as e:
            err_msg = f"Gemini failed: {str(e)}"
            print(err_msg)
            errors.append(err_msg)
            
            # Switch to NVIDIA if configured
            nvidia_key = os.environ.get('NVIDIA_API_KEY', '').strip()
            if nvidia_key:
                print("Transitioning to NVIDIA NIM fallback provider...")
                nvidia_base = os.environ.get('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1').strip()
                nvidia_model = os.environ.get('NVIDIA_MODEL_NAME', '').strip()
                try:
                    metadata = call_openai_compatible(
                        "nvidia", topic, niche, script_text, system_prompt, user_prompt,
                        nvidia_base, nvidia_key, nvidia_model
                    )
                    return metadata, "nvidia", "; ".join(errors)
                except Exception as n_err:
                    err_msg_nv = f"NVIDIA fallback failed: {str(n_err)}"
                    print(err_msg_nv)
                    errors.append(err_msg_nv)
            else:
                print("NVIDIA NIM is not configured (NVIDIA_API_KEY is missing). Fallback omitted.")
                
    elif llm_provider == "nvidia":
        nvidia_key = os.environ.get('NVIDIA_API_KEY', '').strip()
        nvidia_base = os.environ.get('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1').strip()
        nvidia_model = os.environ.get('NVIDIA_MODEL_NAME', '').strip()
        try:
            metadata = call_openai_compatible(
                "nvidia", topic, niche, script_text, system_prompt, user_prompt,
                nvidia_base, nvidia_key, nvidia_model
            )
            return metadata, "nvidia", None
        except Exception as e:
            err_msg = f"NVIDIA failed: {str(e)}"
            print(err_msg)
            errors.append(err_msg)
            
    elif llm_provider == "openai":
        openai_key = os.environ.get('OPENAI_API_KEY', '').strip()
        openai_base = os.environ.get('OPENAI_BASE_URL', '').strip()
        openai_model = os.environ.get('OPENAI_MODEL_NAME', '').strip() or 'gpt-4o-mini'
        try:
            metadata = call_openai_compatible(
                "openai", topic, niche, script_text, system_prompt, user_prompt,
                openai_base, openai_key, openai_model
            )
            return metadata, "openai", None
        except Exception as e:
            err_msg = f"OpenAI failed: {str(e)}"
            print(err_msg)
            errors.append(err_msg)
    else:
        raise Exception(f"Unsupported LLM provider: {llm_provider}")
        
    # If we reached here, all attempts failed
    raise Exception(f"All LLM attempts failed: {'; '.join(errors)}")

def main():
    print("--- Running YouTube Metadata Generator ---")
    topic = os.environ.get('TOPIC', 'Default Topic')
    niche = os.environ.get('NICHE', 'general')
    script_text = os.environ.get('SCRIPT_TEXT', '')
    
    metadata_mode = os.environ.get('METADATA_MODE', 'mock').lower()
    posting_mode = os.environ.get('POSTING_MODE', 'mock').lower()
    allow_mock_fallback = os.environ.get('ALLOW_MOCK_METADATA_FALLBACK', 'false').lower() == 'true'
    use_video_brief = os.environ.get('USE_VIDEO_BRIEF', 'false').lower() == 'true'
    
    # Record the requested provider
    requested_provider = os.environ.get('METADATA_PROVIDER', '').strip().lower() or os.environ.get('LLM_PROVIDER', '').strip().lower()
    if not requested_provider:
        if os.environ.get('GEMINI_API_KEY'):
            requested_provider = 'gemini'
        elif os.environ.get('NVIDIA_API_KEY'):
            requested_provider = 'nvidia'
        else:
            requested_provider = 'gemini'
            
    brief = None
    banned_words = []
    
    if use_video_brief:
        brief_path = os.path.join("docs", "video-brief.json")
        if not os.path.exists(brief_path):
            print(f"Error: video-brief.json is missing at {brief_path} (USE_VIDEO_BRIEF=true)")
            sys.exit(1)
        try:
            with open(brief_path, "r", encoding="utf-8") as f:
                brief = json.load(f)
        except Exception as e:
            print(f"Error: video-brief.json is invalid: {e} (USE_VIDEO_BRIEF=true)")
            sys.exit(1)
            
        required_keys = ['profile_id', 'topic', 'hook', 'title_guidance', 'hashtag_guidance', 'banned_words']
        missing_keys = [k for k in required_keys if k not in brief]
        if missing_keys:
            print(f"Error: video-brief.json is missing required keys: {missing_keys}")
            sys.exit(1)
            
        topic = brief["topic"]
        hook = brief["hook"]
        profile_id = brief["profile_id"]
        title_guidance = brief["title_guidance"]
        hashtag_guidance = brief["hashtag_guidance"]
        banned_words = brief["banned_words"]
        
        # Load profile yaml to find niche
        profile_path = os.path.join("profiles", f"{profile_id}.yml")
        niche = "general"
        if os.path.exists(profile_path):
            try:
                import yaml
                with open(profile_path, "r", encoding="utf-8") as pf:
                    profile_data = yaml.safe_load(pf)
                    niche = profile_data.get("niche", "general")
            except Exception as pe:
                print(f"Warning: Failed to load profile YAML {profile_path}: {pe}")
        else:
            print(f"Warning: Profile YAML {profile_path} not found. Defaulting niche to 'general'.")

    system_prompt = (
        "You are an expert YouTube Shorts metadata generator.\n"
        "Generate optimized metadata for a YouTube Short video. Return ONLY a raw JSON object containing the fields below. "
        "Do not include any explanation or markdown formatting (like ```json ... ```).\n\n"
        "JSON Fields:\n"
        '- "title": An engaging title of up to 100 characters. Avoid repetitive or click-bait phrases.\n'
        '- "description": A short description of up to 5000 characters summarizing the video. Ensure #Shorts is included.\n'
        '- "tags": An array of up to 10 strings for tags.\n'
        '- "hashtags": An array of up to 5 hashtags (without the # prefix).\n'
        '- "categoryId": A string representing the YouTube category (use "28" for science/technology, "27" for education, "22" for people/blogs).\n'
    )
    
    if use_video_brief and brief:
        system_prompt += (
            f"\nAdditional generation constraints from the Video Brief:\n"
            f"- Title Guidance: {title_guidance}\n"
            f"- Hashtag Guidance: {hashtag_guidance}\n"
            f"- CRITICAL: Do NOT use any of the following banned words/phrases in any output field: {', '.join(banned_words)}\n"
            f"- Ensure the niche is: {niche}\n"
            f"- Use hook: {hook}\n"
        )
    
    user_prompt = f"Topic: {topic}\nNiche: {niche}\n"
    if script_text:
        user_prompt += f"Video Script:\n{script_text}\n"
        
    metadata = {}
    metadata_status = "mock"
    metadata_provider_used = "mock"
    metadata_error = None
    
    # Decide if mock metadata fallback is allowed
    allow_fallback = (posting_mode == "mock" or allow_mock_fallback)
    
    if metadata_mode == 'real':
        try:
            metadata, provider_used, prior_errors = generate_real_metadata(topic, niche, script_text, system_prompt, user_prompt)
            metadata_status = "success"
            metadata_provider_used = provider_used
            metadata_error = prior_errors
        except Exception as e:
            full_error = str(e)
            print(f"Real metadata generation failed: {full_error}")
            
            if allow_fallback:
                print("Falling back to mock metadata generation because fallback is allowed.")
                metadata = generate_mock_metadata(topic, niche, brief)
                metadata_status = "fallback"
                metadata_provider_used = "mock"
                metadata_error = full_error
            else:
                print("Error: Metadata fallback is NOT allowed under the current safety rules.")
                metadata_final = {
                    "title": "",
                    "description": "",
                    "tags": [],
                    "hashtags": [],
                    "categoryId": "22",
                    "metadata_status": "failed",
                    "metadata_provider_used": "failed",
                    "metadata_error": full_error,
                    "requested_metadata_provider": requested_provider
                }
                with open("youtube-metadata.json", "w", encoding="utf-8") as f:
                    json.dump(metadata_final, f, indent=2)
                sys.exit(1)
    else:
        # metadata_mode == 'mock'
        metadata = generate_mock_metadata(topic, niche, brief)
        metadata_status = "mock"
        metadata_provider_used = "mock"
        metadata_error = None

    # Post-processing title/description limits
    title = metadata.get("title", f"Facts about {topic}")
    description = metadata.get("description", "")
    tags = metadata.get("tags", [])
    hashtags = metadata.get("hashtags", [])
    category_id = metadata.get("categoryId", "22")

    # Sanitization function for banned words (case-insensitive substring/word match)
    def sanitize_text(text, b_words):
        if not text or not b_words:
            return text
        import re
        for word in b_words:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            if pattern.search(text):
                print(f"Warning: Banned word '{word}' detected in generated text. Sanitizing it.")
                text = pattern.sub("", text)
        text = re.sub(r' +', ' ', text)
        return text.strip()

    def sanitize_list(lst, b_words):
        if not lst or not b_words:
            return lst
        cleaned = []
        for item in lst:
            cleaned_item = sanitize_text(item, b_words)
            if cleaned_item:
                cleaned.append(cleaned_item)
        return cleaned

    if use_video_brief and banned_words:
        title = sanitize_text(title, banned_words)
        description = sanitize_text(description, banned_words)
        tags = sanitize_list(tags, banned_words)
        hashtags = sanitize_list(hashtags, banned_words)

    if len(title) > 100:
        title = title[:97] + "..."
    if len(description) > 5000:
        description = description[:4990] + "..."

    has_shorts = "#shorts" in title.lower() or "#shorts" in description.lower()
    if not has_shorts:
        description += "\n\n#Shorts"

    metadata_final = {
        "title": title,
        "description": description,
        "tags": tags,
        "hashtags": hashtags,
        "categoryId": category_id,
        "metadata_status": metadata_status,
        "metadata_provider_used": metadata_provider_used,
        "metadata_error": metadata_error,
        "requested_metadata_provider": requested_provider
    }

    # Write to file
    with open("youtube-metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata_final, f, indent=2)
    print(f"Saved metadata to youtube-metadata.json:\n{json.dumps(metadata_final, indent=2)}")

    # Set GITHUB_OUTPUT
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"youtube_title={title}\n")
            f.write(f"youtube_category_id={category_id}\n")
        print("Wrote output variables to GITHUB_OUTPUT.")

if __name__ == "__main__":
    main()
