import os
import sys
import json
import yaml

def get_script_and_scenes_for_format(format_type, topic, hook):
    if format_type == "list_top_3":
        outline = [
            "0:00 - 0:05: Hook: " + hook,
            "0:05 - 0:15: Introduction and first tool highlight",
            "0:15 - 0:30: Second tool highlight with major utility",
            "0:30 - 0:45: Third tool highlight (the best one)",
            "0:45 - 0:50: Outro and Call-To-Action (CTA)"
        ]
        scenes = [
            {"time_range": "0:00 - 0:05", "visual": "Fast cuts of the 3 tools, zoom on text overlay with topic name.", "audio": "Hook narration with high energy."},
            {"time_range": "0:05 - 0:15", "visual": "Screen recording of Tool 1 interface showing a quick demo.", "audio": "Explain what Tool 1 is and why it helps."},
            {"time_range": "0:15 - 0:30", "visual": "Screen recording of Tool 2 showing automated processing.", "audio": "Explain the major benefit of Tool 2."},
            {"time_range": "0:30 - 0:45", "visual": "Screen recording of Tool 3 executing a complex task in 1-click.", "audio": "Show the mind-blowing feature of Tool 3."},
            {"time_range": "0:45 - 0:50", "visual": "CTA overlay text (e.g. Subscribe/Link in bio) with animated button.", "audio": "Encourage user to follow/subscribe for more tech hacks."}
        ]
    elif format_type == "tutorial":
        outline = [
            "0:00 - 0:05: Hook: " + hook,
            "0:05 - 0:15: Step 1: Preparation / Setup",
            "0:15 - 0:35: Step 2: Implementation core steps",
            "0:35 - 0:45: Step 3: Final result / Output check",
            "0:45 - 0:50: Outro / Try it yourself CTA"
        ]
        scenes = [
            {"time_range": "0:00 - 0:05", "visual": "Before/After split screen showing the final tutorial result.", "audio": "Hook narration with engaging tone."},
            {"time_range": "0:05 - 0:15", "visual": "Navigate to the site and show where to click first.", "audio": "Step 1 details: Go to the website and import your file."},
            {"time_range": "0:15 - 0:35", "visual": "Clicking buttons and adjusting sliders in real time.", "audio": "Step 2 details: Adjust settings and hit generate to process it."},
            {"time_range": "0:35 - 0:45", "visual": "Show the final downloaded asset/output in high quality.", "audio": "Step 3 details: Look at this perfect output. It took just seconds."},
            {"time_range": "0:45 - 0:50", "visual": "CTA social buttons and text overlays.", "audio": "Outro: Try it out and follow for more tutorials!"}
        ]
    else: # one_tool_highlight or generic
        outline = [
            "0:00 - 0:05: Hook: " + hook,
            "0:05 - 0:20: The major problem faced by users",
            "0:20 - 0:45: The tool demo showing how it solves the problem",
            "0:45 - 0:50: CTA and outro"
        ]
        scenes = [
            {"time_range": "0:00 - 0:05", "visual": "Headline overlay text with tool logo.", "audio": "Hook narration."},
            {"time_range": "0:05 - 0:20", "visual": "Frustrated user clip or slow paid software loading screen.", "audio": "Explain the pain point of paying too much or wasting hours."},
            {"time_range": "0:20 - 0:45", "visual": "Screen recording of the tool executing the solution automatically.", "audio": "Showcase the features of this specific tool."},
            {"time_range": "0:45 - 0:50", "visual": "Subscribe CTA overlay.", "audio": "Follow for daily tool breakdowns."}
        ]
    return outline, scenes

def main():
    scored_path = os.path.join("docs", "scored-ideas.json")
    
    if not os.path.exists(scored_path):
        print(f"Error: Scored ideas file not found at {scored_path}")
        sys.exit(1)
        
    try:
        with open(scored_path, "r", encoding="utf-8") as f:
            scored_ideas = json.load(f)
    except Exception as e:
        print(f"Error reading scored ideas: {e}")
        sys.exit(1)
        
    # Find selected idea
    selected_idea = next((i for i in scored_ideas if i.get("selected")), None)
    if not selected_idea:
        print("Error: No selected idea found in scored-ideas.json.")
        sys.exit(1)
        
    profile_id = selected_idea.get("profile_id")
    profile_path = os.path.join("profiles", f"{profile_id}.yml")
    
    if not os.path.exists(profile_path):
        print(f"Error: Profile configuration not found at {profile_path}")
        sys.exit(1)
        
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading profile configuration: {e}")
        sys.exit(1)
        
    format_type = selected_idea.get("format", "")
    topic = selected_idea.get("topic", "")
    hook = selected_idea.get("hook", "")
    
    outline, scenes = get_script_and_scenes_for_format(format_type, topic, hook)
    
    # Compile brief
    brief = {
        "profile_id": profile_id,
        "idea_id": selected_idea.get("idea_id"),
        "topic": topic,
        "hook": hook,
        "freshness_score": selected_idea.get("freshness_score", 100),
        "script_outline": outline,
        "scene_plan": scenes,
        "voice_style": {
            "tone": profile.get("tone", ["professional"]),
            "style_rules": profile.get("style", {}).get("audio", ["voiceover first"])
        },
        "subtitle_style": {
            "style_rules": profile.get("style", {}).get("visuals", ["clean subtitle text"])
        },
        "title_guidance": "Create an engaging title under 50 characters summarizing: " + topic,
        "hashtag_guidance": "Include #Shorts, the niche #" + profile.get("niche", "tech") + ", and keywords: " + ", ".join(selected_idea.get("keywords", [])),
        "banned_words": profile.get("banned_words", []),
        "target_length_seconds": profile.get("preferred_duration_seconds", 48),
        "preferred_duration_seconds": profile.get("preferred_duration_seconds", 48),
        "hard_max_duration_seconds": profile.get("hard_max_duration_seconds", 58)
    }
    
    output_path = os.path.join("docs", "video-brief.json")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(brief, f, indent=2)
        print(f"Successfully generated video brief for topic '{topic}' to {output_path}")
    except Exception as e:
        print(f"Error writing video brief: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
