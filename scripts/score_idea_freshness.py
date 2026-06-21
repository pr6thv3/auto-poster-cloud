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
        
        # 1. Same topic match: Word overlap penalty of 40 points if overlap is > 40%
        for hist_item in profile_history[:10]: # Check last 10 items
            overlap = calculate_word_overlap(idea.get("topic", ""), hist_item.get("topic", ""))
            if overlap > 0.4:
                score -= 40
                penalties.append(f"Similar topic overlap ({int(overlap*100)}%) with '{hist_item.get('topic')}' (-40)")
                break # Only penalize once for topic
                
        # 2. Keyword reuse: Penalize 10 points for each keyword used in last 30 days
        used_keywords_30d = set()
        for hist_item in last_30_days_history:
            for kw in hist_item.get("keywords", []):
                used_keywords_30d.add(kw.lower())
                
        keyword_penalty_count = 0
        for kw in idea.get("keywords", []):
            if kw.lower() in used_keywords_30d:
                score -= 10
                keyword_penalty_count += 1
        if keyword_penalty_count > 0:
            penalties.append(f"Reused {keyword_penalty_count} keywords from last 30 days (-{keyword_penalty_count * 10})")
            
        # 3. Hook pattern match: Penalize 20 points if hook matches recently used patterns
        # We check if hook starts with similar words (first 3 words) or matches typical patterns
        for hist_item in profile_history[:5]:
            idea_hook_words = idea.get("hook", "").lower().split()[:3]
            hist_hook_words = hist_item.get("hook", "").lower().split()[:3]
            if len(idea_hook_words) >= 3 and len(hist_hook_words) >= 3 and idea_hook_words == hist_hook_words:
                score -= 20
                penalties.append(f"Hook pattern start '{' '.join(idea_hook_words)}' matches recent video (-20)")
                break
                
        # 4. Format fatigue: Penalize 15 points if the format matches any of the last 2 history entries
        if len(profile_history) >= 1 and idea.get("format") == profile_history[0].get("format"):
            score -= 15
            penalties.append(f"Format fatigue: Matches most recent video format '{idea.get('format')}' (-15)")
        elif len(profile_history) >= 2 and idea.get("format") == profile_history[1].get("format"):
            score -= 15
            penalties.append(f"Format fatigue: Matches 2nd most recent video format '{idea.get('format')}' (-15)")
            
        # 5. Angle recency: Penalize 30 points if the same angle was used in the last 30 days
        for hist_item in last_30_days_history:
            if idea.get("angle", "").lower() == hist_item.get("angle", "").lower():
                score -= 30
                penalties.append(f"Angle recency conflict: Angle '{idea.get('angle')}' used recently (-30)")
                break
                
        # Clamp score between 0 and 100
        score = max(0, min(100, score))
        
        idea_copy = idea.copy()
        idea_copy["freshness_score"] = score
        idea_copy["penalties"] = penalties
        idea_copy["selected"] = False
        scored_ideas.append(idea_copy)
        
    # Mark the best idea as selected
    if scored_ideas:
        # Sort by freshness_score descending to find the highest scorer
        scored_ideas.sort(key=lambda x: x["freshness_score"], reverse=True)
        scored_ideas[0]["selected"] = True
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
