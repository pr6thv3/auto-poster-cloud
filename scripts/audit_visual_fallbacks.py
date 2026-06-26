import os
import sys
import json
import re

def main():
    print("--- Running Visual Fallback Auditor (v2.1a) ---")
    
    storyboard_path = os.path.join("docs", "retention-storyboard.json")
    brief_path = os.path.join("docs", "video-brief.json")
    
    if not os.path.exists(storyboard_path) or not os.path.exists(brief_path):
        print("Required documents missing. Skipping fallback audit.")
        sys.exit(0)
        
    try:
        with open(storyboard_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
        with open(brief_path, "r", encoding="utf-8") as f:
            brief = json.load(f)
    except Exception as e:
        print(f"Error loading storyboard/brief: {e}")
        sys.exit(1)
        
    generation_mode = os.environ.get('GENERATION_MODE', 'mock').lower()
    
    topic = brief.get("topic", "")
    topic_lower = topic.lower()
    
    # Determine domain category exactly like build_retention_storyboard.py
    category = "fallback"
    if any(k in topic_lower for k in ["voice", "audio", "noise", "mic", "sound", "podcast", "speech"]):
        category = "audio_cleanup"
    elif any(k in topic_lower for k in ["slide", "presentation", "powerpoint", "ppt", "doc", "pdf"]):
        category = "slides"
    elif any(k in topic_lower for k in ["3d", "render", "model", "graphics", "blender", "cad"]):
        category = "3d"
        
    scenes = sb.get("scenes", [])
    
    # Irrelevant terms detection
    banned_terms = {"food", "recipe", "jar", "honey", "cooking", "construction", "blueprint"}
    # Filter terms: only search for them if they are not in the topic
    active_banned_terms = {term for term in banned_terms if term not in topic_lower}
    
    # Audit each scene
    scene_audits = []
    generic_fallback_count = 0
    proof_scene_failed = False
    payoff_scene_failed = False
    final_20_percent_failed = False
    irrelevant_terms_detected = set()
    has_proof_payoff_visual = False
    
    final_20_start_idx = int(len(scenes) * 0.8) # e.g. 24 * 0.8 = 19
    
    # We will also parse downloaded assets if logged in moneyprinter-log.txt
    downloaded_assets = {}
    log_path = "moneyprinter-log.txt"
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as lf:
                log_content = lf.read()
            # Try finding downloaded videos
            downloads = re.findall(r"video saved:\s+\S+/vid-(\w+)\.mp4", log_content)
            for idx, d in enumerate(downloads):
                downloaded_assets[idx] = f"vid-{d}.mp4"
        except Exception:
            pass

    for idx, s in enumerate(scenes):
        scene_id = s.get("scene_id", idx + 1)
        role = s.get("reaction_or_reveal_type", "") # e.g. hook, context, proof, payoff
        query = s.get("stock_search_query", "")
        visual = s.get("visual_prompt", "")
        narr_query = s.get("narration_derived_query", "")
        preset_query = s.get("preset_fallback_query", "")
        
        # Determine if fallback was used
        fallback_used = not bool(narr_query)
        
        # Generic fallback is when fallback was used and category is 'fallback'
        generic_fallback = fallback_used and (category == "fallback")
        
        if generic_fallback:
            generic_fallback_count += 1
            
        # Check irrelevant terms in stock query or visual prompt
        found_banned = []
        for term in active_banned_terms:
            if re.search(rf"\b{term}\b", query.lower()) or re.search(rf"\b{term}\b", visual.lower()):
                found_banned.append(term)
                irrelevant_terms_detected.add(term)
                
        # Validate payoff/proof scenes
        if role in ["proof", "payoff"]:
            if generic_fallback:
                if role == "proof":
                    proof_scene_failed = True
                if role == "payoff":
                    payoff_scene_failed = True
            else:
                has_proof_payoff_visual = True
                
        # Validate final 20%
        if idx >= final_20_start_idx and generic_fallback:
            final_20_percent_failed = True
            
        asset_name = downloaded_assets.get(idx, None)
        
        scene_audits.append({
            "scene_index": scene_id,
            "expected_visual_concept": visual,
            "stock_query": query,
            "narration_derived_query": narr_query,
            "preset_fallback_query": preset_query,
            "selected_asset_name": asset_name,
            "fallback_used": fallback_used,
            "generic_fallback": generic_fallback,
            "banned_irrelevant_terms": found_banned,
            "scene_role": role
        })
        
    # Check final scene specifically
    final_scene_generic_fallback = False
    final_scene_not_payoff = False
    if scenes:
        last_scene = scenes[-1]
        last_role = last_scene.get("reaction_or_reveal_type", "")
        last_narr = last_scene.get("narration_derived_query", "")
        last_generic = (not bool(last_narr)) and (category == "fallback")
        if last_generic:
            final_scene_generic_fallback = True
        if last_role != "payoff":
            final_scene_not_payoff = True

    # Check overall status
    reasons = []
    
    if generic_fallback_count > 2:
        print(f"Warning: Generic fallback count ({generic_fallback_count}) exceeds limit of 2, but context/supporting scenes are allowed to use stock footage.")
        
    if final_scene_generic_fallback:
        reasons.append("Final scene uses generic stock fallback instead of custom/relevant visuals.")
    if final_scene_not_payoff:
        reasons.append(f"Final scene role '{scenes[-1].get('reaction_or_reveal_type', '') if scenes else ''}' is not 'payoff'.")
    if proof_scene_failed:
        reasons.append("Proof scene uses generic stock fallback instead of custom/relevant visuals.")
    if payoff_scene_failed:
        reasons.append("Payoff scene uses generic stock fallback instead of custom/relevant visuals.")
    if not has_proof_payoff_visual:
        reasons.append("No proof/payoff visual exists in storyboard (all proof/payoff scenes use generic fallback).")
    if irrelevant_terms_detected:
        reasons.append(f"Irrelevant search/visual terms detected: {list(irrelevant_terms_detected)}")
        
    status = "failed" if reasons else "passed"
    
    report = {
        "status": status,
        "generic_fallback_count": generic_fallback_count,
        "proof_scene_status": "failed" if (proof_scene_failed or not has_proof_payoff_visual) else "passed",
        "payoff_scene_status": "failed" if (payoff_scene_failed or not has_proof_payoff_visual) else "passed",
        "final_scene_role": scenes[-1].get("reaction_or_reveal_type", "unknown") if scenes else "unknown",
        "irrelevant_terms_detected": list(irrelevant_terms_detected),
        "reasons": reasons,
        "scene_audits": scene_audits
    }
    
    report_path = os.path.join("docs", "visual-fallback-report.json")
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Visual Fallback Report saved to {report_path}. Status: {status.upper()}")
    except Exception as e:
        print(f"Error writing fallback report: {e}")
        sys.exit(1)
        
    if status == "failed":
        if generation_mode == "real":
            # If real proof footage is unavailable, fail real mode with manual_proof_asset_required
            if proof_scene_failed or payoff_scene_failed or not has_proof_payoff_visual or final_scene_generic_fallback:
                print("Error: manual_proof_asset_required - Real proof/payoff scenes cannot use generic stock.")
            for r in reasons:
                print(f"Error: {r}")
            sys.exit(1)
        else:
            print("Warning: Visual fallback failures ignored in mock mode.")
            for r in reasons:
                print(f" - Warning: {r}")
                
    sys.exit(0)

if __name__ == "__main__":
    main()
