import os
import sys
import json
import re

def stem_word(w):
    w = w.lower()
    for _ in range(2):
        for suffix in ['ingly', 'fully', 'ally', 'ly', 'ing', 'ed', 'es', 'er', 'est', 's', 'y']:
            if w.endswith(suffix) and len(w) - len(suffix) >= 3:
                w = w[:-len(suffix)]
                break
    return w

def get_stems(text):
    if not text:
        return set()
    stop_words = {"this", "that", "these", "those", "is", "are", "was", "were", "the", "a", "an", "and", "or", "but", "if", "you", "your", "my", "to", "for", "in", "on", "at", "with", "it", "its", "will", "let", "would", "should"}
    words = re.findall(r'[a-zA-Z]{3,}', text.lower())
    return {stem_word(w) for w in words if w not in stop_words}

def main():
    print("--- Running Proof Asset Selector (v2.1b) ---")
    
    storyboard_path = os.path.join("docs", "retention-storyboard.json")
    brief_path = os.path.join("docs", "video-brief.json")
    registry_path = os.path.join("assets", "proof_capture", "proof_assets.json")
    
    generation_mode = os.environ.get('GENERATION_MODE', 'mock').lower()
    
    if not os.path.exists(storyboard_path) or not os.path.exists(brief_path):
        print("Required documents missing. Skipping proof asset selection.")
        sys.exit(0)
        
    try:
        with open(storyboard_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
        with open(brief_path, "r", encoding="utf-8") as f:
            brief = json.load(f)
    except Exception as e:
        print(f"Error loading storyboard/brief: {e}")
        sys.exit(1)
        
    registry = {"assets": []}
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load registry: {e}")
            
    assets = registry.get("assets", [])
    scenes = sb.get("scenes", [])
    
    brief_topic = brief.get("topic", "")
    topic_stems = get_stems(brief_topic)
    
    selected_assets = {}
    missing_requirements = []
    required_scene_count = 0
    matched_scene_count = 0
    missing_scene_count = 0
    
    final_scene_role = scenes[-1].get("reaction_or_reveal_type", "unknown") if scenes else "unknown"
    final_payoff_asset_status = "missing"
    
    # Process each scene
    for idx, s in enumerate(scenes):
        role = s.get("reaction_or_reveal_type", "")
        # Under v2.1b, proof or payoff scenes require proof assets
        is_proof_required = s.get("proof_asset_required", False) or role in ["proof", "payoff"]
        
        if is_proof_required:
            required_scene_count += 1
            
            # Extract scene stems
            desc = s.get("proof_descriptor", "")
            vis = s.get("expected_result_visual", "") or s.get("visual_prompt", "")
            narr = s.get("narration_line", "")
            
            scene_text = f"{desc} {vis} {narr}"
            scene_stems = get_stems(scene_text).union(topic_stems)
            
            # Find candidate matches
            candidates = []
            for asset in assets:
                # Private validation check
                if not asset.get("approved_for_private_validation", False):
                    continue
                # Contains private data check
                if asset.get("contains_private_data", True):
                    continue
                # Scene role support check
                if role not in asset.get("supported_scene_roles", []):
                    continue
                    
                candidates.append(asset)
                
            best_asset = None
            best_score = -1
            
            for asset in candidates:
                asset_keywords = asset.get("keywords", []) + asset.get("supported_topics", [])
                asset_text = " ".join(asset_keywords) + " " + asset.get("descriptor", "")
                asset_stems = get_stems(asset_text)
                
                # Check overlap
                overlap = scene_stems.intersection(asset_stems)
                score = len(overlap)
                
                if score > best_score:
                    best_score = score
                    best_asset = asset
            
            # If no keyword overlap exists, score is 0, which is not a match
            if best_score <= 0:
                best_asset = None
                
            if best_asset:
                matched_scene_count += 1
                selected_assets[str(s["scene_id"])] = {
                    "asset_id": best_asset["asset_id"],
                    "file_path": best_asset["file_path"],
                    "descriptor": best_asset["descriptor"]
                }
                # Inject selected asset directly into the storyboard scene dict
                s["selected_proof_asset"] = {
                    "asset_id": best_asset["asset_id"],
                    "file_path": best_asset["file_path"]
                }
                if idx == len(scenes) - 1 and role == "payoff":
                    final_payoff_asset_status = "matched"
            else:
                missing_scene_count += 1
                missing_requirements.append({
                    "scene_id": s["scene_id"],
                    "role": role,
                    "proof_descriptor": desc or vis
                })
                
    # Determine selection status
    # In real mode: missing any proof asset causes failure.
    # In mock mode: warnings are logged, but the status is passed.
    status = "passed"
    if missing_scene_count > 0:
        if generation_mode == "real":
            status = "failed"
        else:
            status = "passed"
            
    # Final Payoff scene requirement
    if final_scene_role == "payoff" and final_payoff_asset_status == "missing":
        if generation_mode == "real":
            status = "failed"
            
    report = {
        "status": status,
        "required_scene_count": required_scene_count,
        "matched_scene_count": matched_scene_count,
        "missing_scene_count": missing_scene_count,
        "final_scene_role": final_scene_role,
        "final_payoff_asset_status": final_payoff_asset_status,
        "selected_assets": selected_assets,
        "missing_requirements": missing_requirements
    }
    
    # Save report
    report_path = os.path.join("docs", "proof-asset-selection-report.json")
    try:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Proof Asset Selection Report saved to {report_path}. Status: {status.upper()}")
    except Exception as e:
        print(f"Error writing selection report: {e}")
        sys.exit(1)
        
    # Write back the updated storyboard with selected assets
    try:
        with open(storyboard_path, "w", encoding="utf-8") as f:
            json.dump(sb, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to update storyboard with proof assets: {e}")
        
    if status == "failed":
        print("Error: manual_proof_asset_required - Required proof assets are missing in real mode.")
        for req in missing_requirements:
            print(f" - Missing Asset for Scene {req['scene_id']} [{req['role']}]: {req['proof_descriptor']}")
        if final_scene_role == "payoff" and final_payoff_asset_status == "missing":
            print(" - Missing Asset for Final Payoff Scene.")
        sys.exit(1)
    elif missing_scene_count > 0:
        print("Warning: Missing proof assets in mock mode. Bypassing failures.")
        for req in missing_requirements:
            print(f" - Warning: Missing Asset for Scene {req['scene_id']} [{req['role']}]: {req['proof_descriptor']}")
            
    sys.exit(0)

if __name__ == "__main__":
    main()
