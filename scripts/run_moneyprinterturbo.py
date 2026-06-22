import os
import sys
import subprocess
import shutil
import json

def main():
    topic = os.environ.get('TOPIC', 'Default Topic')
    title = os.environ.get('TITLE', 'Default Title')
    mock_mode = os.environ.get('MOCK_MODE', 'true').lower() == 'true'
    use_video_brief = os.environ.get('USE_VIDEO_BRIEF', 'false').lower() == 'true'

    print(f"--- Running MoneyPrinterTurbo Integration ---")
    print(f"Topic: {topic}")
    print(f"Title: {title}")
    print(f"Mock Mode: {mock_mode}")
    print(f"Use Video Brief: {use_video_brief}")

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
            
        # Verify required keys
        required_keys = ['profile_id', 'topic', 'hook', 'script_outline', 'scene_plan', 'voice_style', 'target_length_seconds']
        missing_keys = [k for k in required_keys if k not in brief]
        if missing_keys:
            print(f"Error: video-brief.json is missing required keys: {missing_keys}")
            sys.exit(1)
            
        print(f"Loaded video brief successfully. Profile ID: {brief['profile_id']}")
        
        # Check if retention storyboard exists and use it as primary prompt source
        storyboard_path = os.path.join("docs", "retention-storyboard.json")
        loaded_sb = False
        if os.path.exists(storyboard_path):
            try:
                with open(storyboard_path, "r", encoding="utf-8") as f:
                    sb = json.load(f)
                
                print("Loaded retention storyboard successfully for MoneyPrinterTurbo prompt.")
                loaded_sb = True
                
                topic_brief = "Create a 24-second vertical viral short.\n\n"
                topic_brief += "This must feel like a fast social media retention edit.\n\n"
                topic_brief += "Hard requirements:\n"
                topic_brief += "- 9:16 vertical\n"
                topic_brief += "- 20–30 seconds\n"
                topic_brief += "- 14–24 fast scenes\n"
                topic_brief += "- cuts every 0.5–1.5 seconds\n"
                topic_brief += "- constant motion\n"
                topic_brief += "- dramatic zooms\n"
                topic_brief += "- reaction shots\n"
                topic_brief += "- large center text overlays\n"
                topic_brief += "- 1–4 words per overlay\n"
                topic_brief += "- suspense music\n"
                topic_brief += "- whoosh/impact/riser transition sounds\n"
                topic_brief += "- no intro\n"
                topic_brief += "- no greeting\n"
                topic_brief += "- no logo\n"
                topic_brief += "- no static images\n"
                topic_brief += "- no copyrighted characters or logos\n\n"
                
                topic_brief += "Exact Storyboard:\n"
                for s in sb.get("scenes", []):
                    topic_brief += f"Scene {s.get('scene_id')}:\n"
                    topic_brief += f"- Time Range: {s.get('time_range')}\n"
                    topic_brief += f"- Visual Description (No Copyrighted Material): {s.get('visual')}\n"
                    topic_brief += f"- Narration: {s.get('audio')}\n"
                    topic_brief += f"- Motion/Zoom Cue: {s.get('movement')}\n"
                    topic_brief += f"- Sound Cue (SFX): {s.get('sfx')}\n"
                    topic_brief += f"- Role: {s.get('role')}\n\n"
                    
                target_len = sb.get("target_seconds", 24)
                min_words = int(target_len * 2.2)
                max_words = int(target_len * 2.7)
                topic_brief += f"=== SCRIPT LENGTH REQUIREMENT ===\n"
                topic_brief += f"The generated script MUST contain between {min_words} and {max_words} words to align with the target video duration of {target_len} seconds.\n"
                topic_brief += "Do not write a short script under 50 words! Expand the narration dynamically.\n"
                
            except Exception as e:
                print(f"Warning: Could not read retention storyboard: {e}. Falling back to brief prompt.")
                loaded_sb = False

        if not loaded_sb:
            # Override the topic parameter with a detailed prompt constructed from the brief
            topic_brief = f"Topic: {brief['topic']}\n"
            topic_brief += f"Hook: {brief['hook']}\n"
            topic_brief += "Script Outline:\n"
            for line in brief['script_outline']:
                topic_brief += f"- {line}\n"
            topic_brief += "Scene Plan:\n"
            for scene in brief['scene_plan']:
                time_range = scene.get('time_range', '')
                visual = scene.get('visual', '')
                audio = scene.get('audio', '')
                topic_brief += f"- [{time_range}] Visual: {visual} | Audio: {audio}\n"
            topic_brief += "Voice Style / Tone:\n"
            topic_brief += f"- Tone: {', '.join(brief['voice_style'].get('tone', []))}\n"
            topic_brief += f"- Style Rules: {', '.join(brief['voice_style'].get('style_rules', []))}\n"
            topic_brief += f"Target Length: {brief['target_length_seconds']} seconds\n"
            
            if brief.get("format_id") == "viral_curiosity_24s":
                topic_brief += "\n=== STRICT VIRAL SHORTS REQUIREMENTS ===\n"
                topic_brief += "Create a 20–30 second vertical Shorts video.\n"
                topic_brief += "Use this exact structure:\n"
                topic_brief += "0–3s: instant hook (no intro, no greetings)\n"
                topic_brief += "3–16s: suspense/evidence buildup (fast reveal, escalation)\n"
                topic_brief += "16–24s: reveal/payoff (twist/conclusion/prediction)\n"
                topic_brief += "Use 12–18 fast scenes. Each scene should last 1–2 seconds.\n"
                topic_brief += "Use constant movement and avoid static images.\n"
                topic_brief += "Use large center-screen text overlays with 1-4 words per overlay.\n"
                topic_brief += "Use short narration sentences (3-9 words each).\n"
                topic_brief += "Do not include intros, logos, greetings, or filler words.\n"
                topic_brief += "Avoid copyrighted characters or logos.\n"
                topic_brief += "CRITICAL: Do not make the final video shorter than 20 seconds. Do not make the final video longer than 30 seconds.\n"

            # Dynamic word count guard to prevent short video generation
            target_len = brief.get("target_length_seconds", 24)
            min_words = int(target_len * 2.2)
            max_words = int(target_len * 2.7)
            topic_brief += f"\n=== SCRIPT LENGTH REQUIREMENT ===\n"
            topic_brief += f"The generated script MUST contain between {min_words} and {max_words} words to align with the target video duration of {target_len} seconds.\n"
            topic_brief += f"Do not write a short script. If your draft is too short, please expand the content by adding helpful details or context to reach the required word count.\n"
            
        topic = topic_brief


    if mock_mode:
        print("[MOCK] Simulating MoneyPrinterTurbo generation...")
        # Create a mock video directory and file
        output_dir = "storage/tasks/mock-task"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "final-1.mp4")
        
        # Write dummy data to the file to make it look valid (>100KB)
        print(f"[MOCK] Writing dummy MP4 file of size ~150KB to {output_path}")
        with open(output_path, "wb") as f:
            f.write(b"0" * 150000)
        
        print("[MOCK] Mock video generation completed successfully.")
    else:
        print("[REAL] Setting up and running real MoneyPrinterTurbo...")
        
        repo_dir = "moneyprinter-repo"
        # 1. Clone repo if it doesn't exist
        if not os.path.exists(repo_dir):
            print(f"[REAL] Cloning harry0703/MoneyPrinterTurbo into {repo_dir}...")
            subprocess.run([
                "git", "clone", "https://github.com/harry0703/MoneyPrinterTurbo.git", repo_dir
            ], check=True)
        
        # 2. Write config.toml inside the cloned repo
        llm_provider = os.environ.get('MPT_PROVIDER', '').strip().lower() or os.environ.get('LLM_PROVIDER', '').strip().lower() or 'openai'
        video_source = os.environ.get('VIDEO_SOURCE', 'pexels')
        pexels_key = os.environ.get('PEXELS_API_KEY', '')
        
        openai_key = ''
        openai_base_url = ''
        openai_model = ''
        
        if llm_provider == "nvidia":
            nvidia_key = os.environ.get('NVIDIA_API_KEY', '').strip()
            nvidia_base = os.environ.get('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1').strip()
            nvidia_model = os.environ.get('NVIDIA_MODEL_NAME', '').strip()
            
            if not nvidia_key:
                print("Error: NVIDIA_API_KEY is required for LLM_PROVIDER=nvidia")
                sys.exit(1)
            if not nvidia_model:
                print("Error: NVIDIA_MODEL_NAME is required for LLM_PROVIDER=nvidia")
                sys.exit(1)
                
            llm_provider = "openai"
            openai_key = nvidia_key
            openai_base_url = nvidia_base
            openai_model = nvidia_model
        else:
            openai_key = os.environ.get('OPENAI_API_KEY', '')
            openai_base_url = os.environ.get('OPENAI_BASE_URL', '')
            openai_model = os.environ.get('OPENAI_MODEL_NAME', '').strip() or 'gpt-4o-mini'
            
        gemini_key = os.environ.get('GEMINI_API_KEY', '')
        gemini_model = os.environ.get('GEMINI_MODEL_NAME', '').strip() or 'gemini-2.5-flash'
        
        config_path = os.path.join(repo_dir, "config.toml")
        print(f"[REAL] Generating config.toml at {config_path}...")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(f"""[app]
video_source = "{video_source}"
pexels_api_keys = ["{pexels_key}"]
llm_provider = "{llm_provider}"
openai_api_key = "{openai_key}"
openai_base_url = "{openai_base_url}"
openai_model_name = "{openai_model}"
gemini_api_key = "{gemini_key}"
gemini_model_name = "{gemini_model}"
subtitle_provider = "edge"
""")
            
        # 3. Install dependencies in GHA
        print("[REAL] Installing MoneyPrinterTurbo dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", os.path.join(repo_dir, "requirements.txt")
        ], check=True)
        
        # Determine paragraph count dynamically
        paragraph_number = "1"
        if use_video_brief:
            target_len = brief.get("target_length_seconds", 48)
            format_id = brief.get("format_id", "")
            if format_id == "viral_curiosity_24s" or target_len < 30:
                paragraph_number = "3"
            elif target_len >= 45:
                paragraph_number = "4"
                
        # 4. Run CLI script
        print(f"[REAL] Executing MoneyPrinterTurbo CLI with paragraph_number={paragraph_number}...")
        cmd = [
            sys.executable,
            "cli.py",
            "--video-subject", topic,
            "--video-language", "en-US",
            "--voice-name", "en-US-AndrewNeural",
            "--paragraph-number", paragraph_number
        ]
        subprocess.run(cmd, cwd=repo_dir, check=True)
        
        # 5. Locate the generated output and copy it to our storage directory
        src_storage = os.path.join(repo_dir, "storage")
        dst_storage = "storage"
        if os.path.exists(src_storage):
            print(f"[REAL] Copying generated storage files from {src_storage} to {dst_storage}...")
            if os.path.exists(dst_storage):
                shutil.rmtree(dst_storage)
            shutil.copytree(src_storage, dst_storage)
            print("[REAL] Storage folder copied successfully.")
        else:
            print("Error: No storage directory generated inside MoneyPrinterTurbo repository.")
            sys.exit(1)

if __name__ == "__main__":
    main()
