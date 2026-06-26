import os
import sys
import json
import subprocess

def main():
    print("--- Running Mock Proof Asset Generator (v2.1b) ---")
    
    # Paths
    proof_dir = os.path.join("assets", "proof_capture", "calendar_agent")
    os.makedirs(proof_dir, exist_ok=True)
    
    video_path = os.path.join(proof_dir, "mock_calendar_agent_demo.mp4")
    registry_path = os.path.join("assets", "proof_capture", "proof_assets.json")
    
    # 1. Generate video using ffmpeg testsrc2 (a dynamic colored vertical pattern)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "testsrc2=size=1080x1920:rate=30",
        "-t", "6.0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        video_path
    ]
    
    print(f"Running ffmpeg command to generate mock proof asset: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Successfully generated mock proof video at {video_path}")
        else:
            print(f"Warning: ffmpeg exited with non-zero code {res.returncode}. Writing dummy file instead.")
            print(f"ffmpeg stderr: {res.stderr}")
            with open(video_path, "wb") as f:
                f.write(b"mock video data placeholder")
    except FileNotFoundError:
        print("Warning: ffmpeg not found in PATH. Writing dummy file placeholder instead.")
        with open(video_path, "wb") as f:
            f.write(b"mock video data placeholder")
            
    # 2. Update proof_assets.json registry
    registry = {"assets": []}
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load registry: {e}")
            
    assets = registry.get("assets", [])
    
    mock_entry = {
        "asset_id": "calendar_agent_demo_mock_001",
        "file_path": video_path.replace("\\", "/"),
        "project": "calendar_agent",
        "descriptor": "Mock AI scheduling assistant automatically fills a weekly calendar",
        "keywords": ["calendar", "schedule", "meeting", "week", "automation", "productivity"],
        "supported_scene_roles": ["proof", "payoff"],
        "supported_topics": ["ai_tools", "productivity", "calendar automation"],
        "duration_seconds": 6.0,
        "orientation": "vertical_or_crop_safe",
        "source_type": "synthetic_mock_asset",
        "approved_for_private_validation": True,
        "approved_for_public_use": False,
        "contains_private_data": False,
        "notes": "For private/mock validation only. Not final public creative."
    }
    
    # Check if already exists in registry
    exists = False
    for idx, asset in enumerate(assets):
        if asset.get("asset_id") == mock_entry["asset_id"]:
            assets[idx] = mock_entry
            exists = True
            break
            
    if not exists:
        assets.append(mock_entry)
        
    registry["assets"] = assets
    
    try:
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
        print(f"Successfully registered mock proof asset in {registry_path}")
    except Exception as e:
        print(f"Error updating registry: {e}")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
