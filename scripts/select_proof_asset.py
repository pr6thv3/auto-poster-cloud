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
    print("--- Running Proof Asset Selector (v2.2) ---")
    
    storyboard_path = os.path.join("docs", "retention-storyboard.json")
    brief_path = os.path.join("docs", "video-brief.json")
    registry_path = os.path.join("assets", "proof_capture", "proof_assets.json")
    
    generation_mode = os.environ.get('GENERATION_MODE', 'mock').lower()
    posting_mode = os.environ.get('POSTING_MODE', 'mock').lower()
    privacy = os.environ.get('PRIVACY', 'private').lower()
    
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
    
    # Initialize reuse counts
    reuse_counts = {asset["asset_id"]: 0 for asset in assets}
    
    # 1. Identify scenes requiring proof assets
    required_scenes = []
    for idx, s in enumerate(scenes):
        role = s.get("reaction_or_reveal_type", "")
        is_proof_required = s.get("proof_asset_required", False) or role in ["proof", "payoff"]
        if is_proof_required:
            required_scenes.append((idx, s))
            required_scene_count += 1

    final_scene_role = scenes[-1].get("reaction_or_reveal_type", "unknown") if scenes else "unknown"
    final_payoff_asset_status = "missing"
    final_payoff_asset_id = None
    final_payoff_asset_variant = None
    final_payoff_strength = None
    
    has_strong_final_payoff = False
    reasons = []
    
    # Process final payoff scene first if it exists
    final_payoff_idx_in_required = None
    if required_scenes and required_scenes[-1][0] == len(scenes) - 1 and final_scene_role == "payoff":
        final_payoff_idx_in_required = len(required_scenes) - 1
        idx, s = required_scenes[-1]
        role = s.get("reaction_or_reveal_type", "")
        
        desc = s.get("proof_descriptor", "")
        vis = s.get("expected_result_visual", "") or s.get("visual_prompt", "")
        narr = s.get("narration_line", "")
        
        scene_text = f"{desc} {vis} {narr}"
        scene_stems = get_stems(scene_text).union(topic_stems)
        
        # Get candidates
        candidates = []
        for asset in assets:
            if not asset.get("approved_for_private_validation", False):
                continue
            if asset.get("contains_private_data", True):
                continue
            if role not in asset.get("supported_scene_roles", []):
                continue
            candidates.append(asset)
            
        # Score candidates with final payoff preference
        scored_candidates = []
        for asset in candidates:
            asset_keywords = asset.get("keywords", []) + asset.get("supported_topics", [])
            asset_text = " ".join(asset_keywords) + " " + asset.get("descriptor", "")
            asset_stems = get_stems(asset_text)
            
            overlap = scene_stems.intersection(asset_stems)
            keyword_score = len(overlap)
            
            if keyword_score <= 0:
                continue
                
            # Add payoff preference score
            pref_score = 0
            if asset.get("asset_variant") == "final_result_visual":
                pref_score += 1000
            if asset.get("payoff_strength") == "strong":
                pref_score += 500
            best_positions = asset.get("best_for_scene_position", [])
            if "final_payoff" in best_positions or "last_3_seconds" in best_positions:
                pref_score += 250
                
            total_score = keyword_score + pref_score
            scored_candidates.append((total_score, asset))
            
        # Sort and pick best
        if scored_candidates:
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            best_asset = scored_candidates[0][1]
            
            # Check if it meets the strong payoff requirement
            is_strong = (
                best_asset.get("asset_variant") == "final_result_visual" and
                best_asset.get("payoff_strength") == "strong" and
                any(pos in best_asset.get("best_for_scene_position", []) for pos in ["final_payoff", "last_3_seconds"])
            )
            
            if is_strong:
                has_strong_final_payoff = True
                
            matched_scene_count += 1
            final_payoff_asset_status = "matched"
            final_payoff_asset_id = best_asset["asset_id"]
            final_payoff_asset_variant = best_asset.get("asset_variant")
            final_payoff_strength = best_asset.get("payoff_strength")
            
            selected_assets[str(s["scene_id"])] = {
                "asset_id": best_asset["asset_id"],
                "file_path": best_asset["file_path"],
                "descriptor": best_asset["descriptor"]
            }
            s["selected_proof_asset"] = {
                "asset_id": best_asset["asset_id"],
                "file_path": best_asset["file_path"]
            }
            reuse_counts[best_asset["asset_id"]] += 1
        else:
            missing_scene_count += 1
            missing_requirements.append({
                "scene_id": s["scene_id"],
                "role": role,
                "proof_descriptor": desc or vis
            })
            
    # Process remaining required scenes in order
    for req_i, (idx, s) in enumerate(required_scenes):
        if req_i == final_payoff_idx_in_required:
            continue
            
        role = s.get("reaction_or_reveal_type", "")
        desc = s.get("proof_descriptor", "")
        vis = s.get("expected_result_visual", "") or s.get("visual_prompt", "")
        narr = s.get("narration_line", "")
        
        scene_text = f"{desc} {vis} {narr}"
        scene_stems = get_stems(scene_text).union(topic_stems)
        
        candidates = []
        for asset in assets:
            if not asset.get("approved_for_private_validation", False):
                continue
            if asset.get("contains_private_data", True):
                continue
            if role not in asset.get("supported_scene_roles", []):
                continue
            candidates.append(asset)
            
        scored_candidates = []
        for asset in candidates:
            asset_keywords = asset.get("keywords", []) + asset.get("supported_topics", [])
            asset_text = " ".join(asset_keywords) + " " + asset.get("descriptor", "")
            asset_stems = get_stems(asset_text)
            
            overlap = scene_stems.intersection(asset_stems)
            keyword_score = len(overlap)
            
            if keyword_score <= 0:
                continue
                
            scored_candidates.append((keyword_score, asset))
            
        if scored_candidates:
            # Sort by keyword_score descending, then reuse count ascending to distribute
            scored_candidates.sort(key=lambda x: (x[0], -reuse_counts[x[1]["asset_id"]]), reverse=True)
            best_asset = scored_candidates[0][1]
            
            matched_scene_count += 1
            selected_assets[str(s["scene_id"])] = {
                "asset_id": best_asset["asset_id"],
                "file_path": best_asset["file_path"],
                "descriptor": best_asset["descriptor"]
            }
            s["selected_proof_asset"] = {
                "asset_id": best_asset["asset_id"],
                "file_path": best_asset["file_path"]
            }
            reuse_counts[best_asset["asset_id"]] += 1
        else:
            missing_scene_count += 1
            missing_requirements.append({
                "scene_id": s["scene_id"],
                "role": role,
                "proof_descriptor": desc or vis
            })
            
    # Calculate diversity metrics
    actual_used_assets = {selected_assets[sid]["asset_id"] for sid in selected_assets}
    unique_proof_assets_used = len(actual_used_assets)
    max_asset_reuse_count = max(reuse_counts.values()) if reuse_counts else 0
    repeated_asset_ids = [aid for aid, count in reuse_counts.items() if count > 1]
    
    single_asset_fallback_used = False
    allow_single_asset_private_validation = False
    
    if matched_scene_count > 0 and unique_proof_assets_used == 1:
        single_asset_fallback_used = True
        single_asset_id = list(actual_used_assets)[0]
        # Find in registry to check validation fallback approval
        for asset in assets:
            if asset["asset_id"] == single_asset_id:
                allow_single_asset_private_validation = bool(asset.get("allow_single_asset_private_validation", False))
                break
                
    status = "passed"
    
    # 1. Missing required assets check
    if missing_scene_count > 0:
        if generation_mode == "real":
            status = "failed"
            reasons.append("manual_proof_asset_required")
            
    # 2. Final Payoff strong asset requirement
    if final_scene_role == "payoff":
        if final_payoff_asset_status == "missing":
            if generation_mode == "real":
                status = "failed"
                reasons.append("final_payoff_asset_required")
        elif not has_strong_final_payoff:
            if generation_mode == "real":
                status = "failed"
                reasons.append("final_payoff_asset_required")
            else:
                print("Warning: final_payoff_asset_required (No strong final payoff asset matched in mock mode).")
                
    # 3. Asset repetition limit check
    if max_asset_reuse_count > 4:
        if generation_mode == "real":
            status = "failed"
            reasons.append(f"Hard reuse limit exceeded: An asset was reused {max_asset_reuse_count} times (> 4).")
        else:
            print(f"Warning: An asset was reused {max_asset_reuse_count} times (> 4) in mock mode.")
            
    # 4. Single-asset fallback checks
    if single_asset_fallback_used:
        is_public = (posting_mode == "real" and privacy == "public")
        is_private_real = (generation_mode == "real" and privacy == "private")
        
        if is_public:
            status = "failed"
            reasons.append("Single asset reuse across all scenes is forbidden in public mode.")
        elif is_private_real:
            if not allow_single_asset_private_validation:
                status = "failed"
                reasons.append("Single asset fallback is not allowed for this asset in private real mode.")
        else:
            print("Warning: Only one proof asset is used across all scenes. Make sure more variants are provided for public use.")

    proof_asset_diversity_status = "passed"
    if status == "failed":
        proof_asset_diversity_status = "failed"
    elif max_asset_reuse_count > 3 or single_asset_fallback_used:
        proof_asset_diversity_status = "warning"
        
    report = {
        "status": status,
        "required_scene_count": required_scene_count,
        "matched_scene_count": matched_scene_count,
        "missing_scene_count": missing_scene_count,
        "final_scene_role": final_scene_role,
        "final_payoff_asset_status": final_payoff_asset_status,
        "selected_assets": selected_assets,
        "missing_requirements": missing_requirements,
        "asset_reuse_counts": reuse_counts,
        "max_asset_reuse_count": max_asset_reuse_count,
        "repeated_asset_ids": repeated_asset_ids,
        "proof_asset_diversity_status": proof_asset_diversity_status,
        "single_asset_fallback_used": single_asset_fallback_used,
        "allow_single_asset_private_validation": allow_single_asset_private_validation,
        "reasons": reasons
    }
    
    # Save selection report
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
        
    # Task 6: Write docs/proof-diversity-report.json
    diversity_report = {
        "proof_assets_required": required_scene_count,
        "proof_assets_matched": matched_scene_count,
        "unique_proof_assets_used": unique_proof_assets_used,
        "asset_reuse_counts": reuse_counts,
        "max_asset_reuse_count": max_asset_reuse_count,
        "repeated_asset_ids": repeated_asset_ids,
        "final_payoff_asset_id": final_payoff_asset_id,
        "final_payoff_asset_variant": final_payoff_asset_variant,
        "final_payoff_strength": final_payoff_strength,
        "proof_asset_diversity_status": proof_asset_diversity_status,
        "status": status
    }
    diversity_report_path = os.path.join("docs", "proof-diversity-report.json")
    try:
        with open(diversity_report_path, "w", encoding="utf-8") as f:
            json.dump(diversity_report, f, indent=2)
        print(f"Proof Diversity Report saved to {diversity_report_path}. Diversity Status: {proof_asset_diversity_status.upper()}")
    except Exception as e:
        print(f"Error writing diversity report: {e}")
        sys.exit(1)
        
    if status == "failed":
        print("Error: Proof asset diversity/selection rules failed in real mode:")
        for r in reasons:
            print(f" - {r}")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
