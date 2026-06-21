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
        llm_provider = os.environ.get('LLM_PROVIDER', 'openai').strip().lower()
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
        
        # 4. Run CLI script
        print("[REAL] Executing MoneyPrinterTurbo CLI...")
        cmd = [
            sys.executable,
            "cli.py",
            "--video-subject", topic,
            "--video-language", "en-US",
            "--voice-name", "en-US-AndrewNeural",
            "--paragraph-number", "1"
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
