import os
import sys
import json
from datetime import datetime, timezone

def calculate_word_overlap(str1, str2):
    # Normalize strings: lowercase and split into words
    words1 = set(str1.lower().replace("!", "").replace("?", "").replace(".", "").split())
    words2 = set(str2.lower().replace("!", "").replace("?", "").replace(".", "").split())
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    return len(intersection) / max(len(words1), len(words2))

def is_money_related(text):
    text_lower = text.lower()
    money_triggers = ["money", "side hustle", "earn", "wealth", "salary", "cash", "hustle"]
    return any(trigger in text_lower for trigger in money_triggers)

def parse_date(date_str):
    # Parse ISO 8601 date string, replacing Z with UTC offset
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

def main():
    ideas_path = os.path.join("docs", "generated-ideas.json")
    history_path = os.path.join("docs", "content-history.json")
    
    if not os.path.exists(ideas_path):
        print(f"Error: Generated ideas file not found at {ideas_path}")
        sys.exit(1)
        
    if not os.path.exists(history_path):
        # If no history exists, create an empty history list
        history = []
    else:
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            print(f"Error reading history file: {e}")
            sys.exit(1)
            
    try:
        with open(ideas_path, "r", encoding="utf-8") as f:
            ideas = json.load(f)
    except Exception as e:
        print(f"Error reading generated ideas: {e}")
        sys.exit(1)
        
    # Get current time for recency calculations
    now = datetime.now(timezone.utc)
    
    # Filter history for the current profile
    profile_id = ideas[0].get("profile_id") if ideas else "unknown"
    profile_history = [item for item in history if item.get("profile_id") == profile_id]
    
    # Sort profile history by created_at descending (most recent first)
    profile_history.sort(key=lambda x: parse_date(x.get("created_at")), reverse=True)
    
    # Extract last 30 days history items
    last_30_days_history = []
    for item in profile_history:
        item_date = parse_date(item.get("created_at"))
        days_diff = (now - item_date).days
        if days_diff <= 30:
            last_30_days_history.append(item)
            
    scored_ideas = []
    
    for idea in ideas:
        score = 100
        penalties = []
        penalty_reasons = []
        recent_history_matches = []
        
        # 1. Exact topic match: -60 or similar topic match: -40
        exact_match = False
        matched_hist_item = None
        for hist_item in profile_history:
            if idea.get("topic", "").strip().lower() == hist_item.get("topic", "").strip().lower():
                exact_match = True
                matched_hist_item = hist_item
                break
                
        if exact_match:
            score -= 60
            penalties.append(f"Exact topic overlap with '{matched_hist_item.get('topic')}' (-60)")
            penalty_reasons.append("exact_topic_overlap")
            recent_history_matches.append({
                "type": "exact_topic",
                "history_topic": matched_hist_item.get("topic"),
                "video_id": matched_hist_item.get("youtube_video_id"),
                "date": matched_hist_item.get("created_at")
            })
        else:
            for hist_item in profile_history[:10]: # Check last 10 items for similarity
                overlap = calculate_word_overlap(idea.get("topic", ""), hist_item.get("topic", ""))
                if overlap > 0.4:
                    score -= 40
                    penalties.append(f"Similar topic overlap ({int(overlap*100)}%) with '{hist_item.get('topic')}' (-40)")
                    penalty_reasons.append("similar_topic_overlap")
                    recent_history_matches.append({
                        "type": "similar_topic",
                        "history_topic": hist_item.get("topic"),
                        "video_id": hist_item.get("youtube_video_id"),
                        "date": hist_item.get("created_at"),
                        "overlap": overlap
                    })
                    break
                    
        # 2. Hook pattern match: -25
        for hist_item in profile_history[:5]:
            idea_hook_words = idea.get("hook", "").lower().split()[:3]
            hist_hook_words = hist_item.get("hook", "").lower().split()[:3]
            if len(idea_hook_words) >= 3 and len(hist_hook_words) >= 3 and idea_hook_words == hist_hook_words:
                score -= 25
                penalties.append(f"Hook pattern start '{' '.join(idea_hook_words)}' matches recent video (-25)")
                penalty_reasons.append("hook_pattern_overlap")
                recent_history_matches.append({
                    "type": "hook_pattern",
                    "history_topic": hist_item.get("topic"),
                    "video_id": hist_item.get("youtube_video_id"),
                    "date": hist_item.get("created_at"),
                    "hook": hist_item.get("hook")
                })
                break
                
        # 3. Angle recency: -25
        for hist_item in last_30_days_history:
            if idea.get("angle", "").strip().lower() == hist_item.get("angle", "").strip().lower():
                score -= 25
                penalties.append(f"Angle recency conflict: Angle '{idea.get('angle')}' used recently (-25)")
                penalty_reasons.append("angle_recency_conflict")
                recent_history_matches.append({
                    "type": "angle_recency",
                    "history_topic": hist_item.get("topic"),
                    "video_id": hist_item.get("youtube_video_id"),
                    "date": hist_item.get("created_at"),
                    "angle": hist_item.get("angle")
                })
                break

        # 4. Keyword fatigue: 2+ same keywords from last 30 days is -20
        used_keywords_30d = set()
        for hist_item in last_30_days_history:
            for kw in hist_item.get("keywords", []):
                used_keywords_30d.add(kw.lower().strip())
                
        matching_kws = [kw for kw in idea.get("keywords", []) if kw.lower().strip() in used_keywords_30d]
        if len(matching_kws) >= 2:
            score -= 20
            penalties.append(f"Reused 2+ keywords ({', '.join(matching_kws)}) from last 30 days (-20)")
            penalty_reasons.append("keyword_fatigue")
            for hist_item in last_30_days_history:
                overlapping_kws = [kw for kw in idea.get("keywords", []) if kw.lower().strip() in [hk.lower().strip() for hk in hist_item.get("keywords", [])]]
                if overlapping_kws:
                    recent_history_matches.append({
                        "type": "keyword_overlap",
                        "history_topic": hist_item.get("topic"),
                        "video_id": hist_item.get("youtube_video_id"),
                        "date": hist_item.get("created_at"),
                        "keywords": overlapping_kws
                    })
            
        # 5. Format fatigue: Matches format of either of the last 2 history entries -> -15
        format_fatigue = False
        matched_format_hist = None
        if len(profile_history) >= 1 and idea.get("format") == profile_history[0].get("format"):
            format_fatigue = True
            matched_format_hist = profile_history[0]
        elif len(profile_history) >= 2 and idea.get("format") == profile_history[1].get("format"):
            format_fatigue = True
            matched_format_hist = profile_history[1]
            
        if format_fatigue:
            score -= 15
            penalties.append(f"Format fatigue: Matches recent video format '{idea.get('format')}' (-15)")
            penalty_reasons.append("format_fatigue")
            recent_history_matches.append({
                "type": "format_fatigue",
                "history_topic": matched_format_hist.get("topic"),
                "video_id": matched_format_hist.get("youtube_video_id"),
                "date": matched_format_hist.get("created_at"),
                "format": idea.get("format")
            })
            
        # 6. Money repetition: -20
        if is_money_related(idea.get("topic", "")):
            recent_money_match = None
            for hist_item in last_30_days_history:
                if is_money_related(hist_item.get("topic", "")):
                    recent_money_match = hist_item
                    break
            if recent_money_match:
                score -= 20
                penalties.append(f"Money/side-hustle topic repeated recently: Matches '{recent_money_match.get('topic')}' (-20)")
                penalty_reasons.append("money_repetition")
                recent_history_matches.append({
                    "type": "money_repetition",
                    "history_topic": recent_money_match.get("topic"),
                    "video_id": recent_money_match.get("youtube_video_id"),
                    "date": recent_money_match.get("created_at")
                })
                
        # Clamp score between 0 and 100
        score = max(0, min(100, score))
        
        idea_copy = idea.copy()
        idea_copy["freshness_score"] = score
        idea_copy["penalties"] = penalties
        idea_copy["penalty_reasons"] = penalty_reasons
        idea_copy["recent_history_matches"] = recent_history_matches
        idea_copy["selected"] = False
        idea_copy["selected_reason"] = None
        scored_ideas.append(idea_copy)
        
    # Mark the best idea as selected
    if scored_ideas:
        generation_mode = os.environ.get('GENERATION_MODE', 'mock').lower()
        input_topic = os.environ.get('TOPIC', '').strip()
        
        pinned_idea = None
        
        # If a specific TOPIC was provided, try to pin a matching idea
        if input_topic:
            # 1. Try exact match first
            for idea in scored_ideas:
                if idea.get("topic", "").strip().lower() == input_topic.lower():
                    pinned_idea = idea
                    break
            
            # 2. Try high word-overlap match (>= 60%)
            if not pinned_idea:
                best_overlap = 0.0
                best_match = None
                for idea in scored_ideas:
                    overlap = calculate_word_overlap(input_topic, idea.get("topic", ""))
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_match = idea
                if best_overlap >= 0.6 and best_match:
                    pinned_idea = best_match
                    print(f"Topic pin: No exact match for '{input_topic}', using closest match '{best_match['topic']}' ({int(best_overlap*100)}% overlap).")
            
            if pinned_idea:
                pinned_idea["selected"] = True
                pinned_idea["selected_reason"] = f"Pinned by input TOPIC='{input_topic}' (Score: {pinned_idea['freshness_score']})."
                print(f"Topic pin: Selected idea '{pinned_idea['topic']}' (Score: {pinned_idea['freshness_score']}) matching input topic.")
            else:
                print(f"Warning: Input TOPIC='{input_topic}' did not match any idea in the catalog. Falling back to highest-scoring idea.")
        
        # Fallback: select the highest-scoring idea if no pin matched
        if not pinned_idea:
            scored_ideas.sort(key=lambda x: x["freshness_score"], reverse=True)
            scored_ideas[0]["selected"] = True
            scored_ideas[0]["selected_reason"] = f"Selected as the highest scoring fresh idea (Score: {scored_ideas[0]['freshness_score']})."
        
        # Check freshness policy in real mode
        selected = next((i for i in scored_ideas if i["selected"]), None)
        if selected and generation_mode == 'real' and selected["freshness_score"] < 70:
            print(f"Error: Selected idea '{selected['topic']}' has freshness score {selected['freshness_score']}, which is below the minimum required threshold (70) in real mode.")
            sys.exit(1)
            
        # Re-sort by idea_id to preserve output order
        scored_ideas.sort(key=lambda x: x["idea_id"])
        
    output_path = os.path.join("docs", "scored-ideas.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(scored_ideas, f, indent=2)
        selected_idea = next((i for i in scored_ideas if i["selected"]), None)
        print(f"Scored {len(scored_ideas)} ideas. Saved to {output_path}.")
        if selected_idea:
            print(f"Selected Idea: '{selected_idea['topic']}' (Score: {selected_idea['freshness_score']})")
    except Exception as e:
        print(f"Error writing scored ideas: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
