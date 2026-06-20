import os
import sys
import json
import requests

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

def generate_mock_metadata(topic, niche):
    print("[MOCK] Generating placeholder YouTube metadata...")
    return {
        "title": f"Amazing facts about {topic[:40]}! #Shorts",
        "description": f"Here is what you need to know about {topic}.\n\nSubscribe for more content on {niche}!\n\n#Shorts #learning #{niche}",
        "tags": [niche, "learning", "shorts", "interesting"],
        "hashtags": ["Shorts", "learning", niche],
        "categoryId": "28" if niche.lower() in ["ai", "science", "technology", "tech"] else "22"
    }

def generate_real_metadata(topic, niche, script_text):
    llm_provider = os.environ.get('LLM_PROVIDER', '').lower()
    openai_key = os.environ.get('OPENAI_API_KEY')
    openai_model = os.environ.get('OPENAI_MODEL_NAME', '').strip() or 'gpt-4o-mini'
    gemini_key = os.environ.get('GEMINI_API_KEY')
    gemini_model = os.environ.get('GEMINI_MODEL_NAME', '').strip() or 'gemini-2.5-flash'

    # Autodetect provider if not explicitly configured
    if not llm_provider:
        if gemini_key:
            llm_provider = "gemini"
        elif openai_key:
            llm_provider = "openai"
        else:
            print("Error: No API keys configured for LLM. Set OPENAI_API_KEY or GEMINI_API_KEY.")
            sys.exit(1)

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
    
    user_prompt = f"Topic: {topic}\nNiche: {niche}\n"
    if script_text:
        user_prompt += f"Video Script:\n{script_text}\n"

    try:
        if llm_provider == "openai":
            if not openai_key:
                raise Exception("Missing OPENAI_API_KEY")
            print(f"[REAL] Generating metadata using OpenAI ({openai_model})...")
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_key}"
            }
            payload = {
                "model": openai_model,
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
            
        elif llm_provider == "gemini":
            if not gemini_key:
                raise Exception("Missing GEMINI_API_KEY")
            print(f"[REAL] Generating metadata using Gemini ({gemini_model})...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": system_prompt + "\n\n" + user_prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            res_json = res.json()
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            
        else:
            raise Exception(f"Unsupported LLM provider: {llm_provider}")

        cleaned_text = clean_json_response(raw_text)
        metadata = json.loads(cleaned_text)
        return metadata

    except Exception as e:
        print(f"LLM Metadata Generation failed: {e}. Falling back to mock metadata.")
        return generate_mock_metadata(topic, niche)

def main():
    print("--- Running YouTube Metadata Generator ---")
    topic = os.environ.get('TOPIC', 'Default Topic')
    niche = os.environ.get('NICHE', 'general')
    script_text = os.environ.get('SCRIPT_TEXT', '')
    
    # Check modes
    metadata_mode = os.environ.get('METADATA_MODE', 'mock').lower()
    
    if metadata_mode == 'real':
        metadata = generate_real_metadata(topic, niche, script_text)
    else:
        metadata = generate_mock_metadata(topic, niche)

    # Validation and post-processing
    title = metadata.get("title", f"Facts about {topic}")
    description = metadata.get("description", "")
    tags = metadata.get("tags", [])
    hashtags = metadata.get("hashtags", [])
    category_id = metadata.get("categoryId", "22")

    # Limit title length
    if len(title) > 100:
        title = title[:97] + "..."
        
    # Limit description length
    if len(description) > 5000:
        description = description[:4990] + "..."

    # Ensure #Shorts appears in title or description
    has_shorts = "#shorts" in title.lower() or "#shorts" in description.lower()
    if not has_shorts:
        description += "\n\n#Shorts"

    metadata_final = {
        "title": title,
        "description": description,
        "tags": tags,
        "hashtags": hashtags,
        "categoryId": category_id
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
