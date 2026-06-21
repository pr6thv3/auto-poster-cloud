import os
import sys
import json
import argparse
import yaml

# Candidate ideas catalog by niche
IDEAS_CATALOG = {
    "ai": [
        {
            "topic": "3 AI tools to start a side hustle",
            "angle": "side hustle automation",
            "hook": "Want to start a side hustle? These 3 AI tools will do all the work for you.",
            "keywords": ["side hustle", "ai tools", "make money online"],
            "format": "list_top_3",
            "freshness_window_days": 14
        },
        {
            "topic": "This AI website writes all your emails",
            "angle": "email productivity",
            "hook": "Stop wasting hours writing emails. Let this free AI website do it in seconds.",
            "keywords": ["write emails", "ai website", "productivity hacks"],
            "format": "one_tool_highlight",
            "freshness_window_days": 7
        },
        {
            "topic": "How to create an AI voiceover using your own voice",
            "angle": "voice cloning tutorial",
            "hook": "Create an AI voiceover using your own voice with consent in seconds. Here is how.",
            "keywords": ["personal voiceover", "ai voice", "voice cloning"],
            "format": "tutorial",
            "freshness_window_days": 30
        },
        {
            "topic": "3 AI extensions for Google Chrome you need today",
            "angle": "browser extension recommendations",
            "hook": "If you aren't using these 3 Google Chrome extensions, you're working too hard.",
            "keywords": ["chrome extensions", "google chrome", "ai plugins"],
            "format": "list_top_3",
            "freshness_window_days": 14
        },
        {
            "topic": "This AI tool generates fully animated videos from text",
            "angle": "text to video animation",
            "hook": "You can generate fully animated videos just by typing text. Here is how.",
            "keywords": ["text to video", "animated videos", "ai video generator"],
            "format": "one_tool_highlight",
            "freshness_window_days": 10
        }
    ],
    "fifa": [
        {
            "topic": "The 3 most overpowered cheap beasts in FIFA",
            "angle": "cheap squad builders",
            "hook": "Stop spending millions! These 3 cheap players are absolute cheats in game.",
            "keywords": ["cheap beasts", "fifa squad", "overpowered players"],
            "format": "list_top_3",
            "freshness_window_days": 7
        },
        {
            "topic": "How to score every time using this skill move",
            "angle": "skill move tutorial",
            "hook": "This simple skill move is completely broken. Here is how to perform it.",
            "keywords": ["fifa tutorial", "skill move", "score goals"],
            "format": "skill_tutorials",
            "freshness_window_days": 14
        },
        {
            "topic": "Rate this 500k meta starter squad",
            "angle": "meta squad review",
            "hook": "This is the best 500k starter squad you can build right now. Let's rate it.",
            "keywords": ["starter squad", "meta players", "squad builder"],
            "format": "squad_builders",
            "freshness_window_days": 7
        },
        {
            "topic": "Is this new player item worth doing?",
            "angle": "sbc player review",
            "hook": "EA just dropped a new player SBC. Is it actually worth your fodder?",
            "keywords": ["sbc review", "player rating", "meta review"],
            "format": "player_reviews",
            "freshness_window_days": 5
        },
        {
            "topic": "Unbelievable pack luck in the weekend league rewards",
            "angle": "rewards pack opening",
            "hook": "We just opened the weekend league rewards and you won't believe who we packed.",
            "keywords": ["pack opening", "rewards luck", "meta packing"],
            "format": "pack_openings",
            "freshness_window_days": 3
        }
    ],
    "cricket": [
        {
            "topic": "Virat Kohli vs Babar Azam: The stats breakdown",
            "angle": "player comparison statistics",
            "hook": "Who is actually the king of modern cricket? The numbers don't lie.",
            "keywords": ["kohli vs babar", "cricket stats", "batting average"],
            "format": "stats_comparison",
            "freshness_window_days": 30
        },
        {
            "topic": "3 cricket records that will never be broken",
            "angle": "historical trivia",
            "hook": "These 3 cricket world records are practically impossible to break. Here is why.",
            "keywords": ["world records", "cricket history", "impossible stats"],
            "format": "trivia",
            "freshness_window_days": 60
        },
        {
            "topic": "Why this player is the greatest test match bowler",
            "angle": "legend tribute",
            "hook": "This bowler dominated test cricket like no other in history. Let's look back.",
            "keywords": ["test bowler", "cricket legend", "best wickets"],
            "format": "legend_tributes",
            "freshness_window_days": 90
        },
        {
            "topic": "India vs Pakistan: 3 key match matchups",
            "angle": "match predictions",
            "hook": "The biggest rivalry is back. These 3 matchups will decide who wins.",
            "keywords": ["ind vs pak", "match predictions", "key matchups"],
            "format": "match_predictions",
            "freshness_window_days": 7
        },
        {
            "topic": "The fastest century in ODI history",
            "angle": "historical match trivia",
            "hook": "This batsman scored a century in just 31 balls. Here is how it happened.",
            "keywords": ["fastest century", "odi record", "ab de villiers"],
            "format": "trivia",
            "freshness_window_days": 45
        }
    ],
    "finance": [
        {
            "topic": "How to save your first 10k in a year",
            "angle": "budgeting methods",
            "hook": "Saving 10k in a single year is easier than you think if you follow these rules.",
            "keywords": ["saving money", "budgeting", "financial freedom"],
            "format": "saving_tips",
            "freshness_window_days": 30
        },
        {
            "topic": "3 side hustles you can start from your couch",
            "angle": "passive income side hustles",
            "hook": "Want to earn extra cash without leaving your house? Try these 3 side hustles.",
            "keywords": ["side hustle", "earn money online", "passive income"],
            "format": "side_hustle_guides",
            "freshness_window_days": 14
        },
        {
            "topic": "The 50-30-20 budget rule explained simply",
            "angle": "basic personal finance rules",
            "hook": "If you don't know how to manage your salary, use the simple 50-30-20 rule.",
            "keywords": ["budget rule", "salary manager", "saving tips"],
            "format": "budgeting_methods",
            "freshness_window_days": 45
        },
        {
            "topic": "How standard tax deductions work",
            "angle": "tax deduction guide",
            "hook": "Don't leave money on the table. Here is how standard tax deductions work.",
            "keywords": ["tax hacks", "write offs", "deductions"],
            "format": "tax_hacks",
            "freshness_window_days": 90
        },
        {
            "topic": "Why compound interest is a cheat code for wealth",
            "angle": "investment fundamentals",
            "hook": "Albert Einstein called compound interest the eighth wonder of the world. Here's why.",
            "keywords": ["compound interest", "investing basics", "grow wealth"],
            "format": "saving_tips",
            "freshness_window_days": 60
        }
    ],
    "tech_news": [
        {
            "topic": "Apple announces the brand new iPhone 18",
            "angle": "product launch coverage",
            "hook": "Apple just announced the new iPhone 18, and it features a major design change.",
            "keywords": ["iphone 18", "apple launch", "new iphone"],
            "format": "product_launches",
            "freshness_window_days": 7
        },
        {
            "topic": "Google drops its new open source AI model",
            "angle": "tech breakthroughs",
            "hook": "Google just released a brand new AI model that runs locally on your phone.",
            "keywords": ["google ai", "local model", "tech breakthrough"],
            "format": "tech_breakthroughs",
            "freshness_window_days": 10
        },
        {
            "topic": "Change these 3 settings to protect your data now",
            "angle": "user privacy alerts",
            "hook": "Your phone is spying on you. Change these 3 privacy settings immediately.",
            "keywords": ["data privacy", "phone settings", "security alerts"],
            "format": "privacy_alerts",
            "freshness_window_days": 30
        },
        {
            "topic": "The AI startup CEO drama explained",
            "angle": "industry news and drama",
            "hook": "There is a massive boardroom fight happening at a top AI company. Here is what happened.",
            "keywords": ["tech drama", "ceo fired", "industry news"],
            "format": "industry_news",
            "freshness_window_days": 7
        },
        {
            "topic": "How quantum computing will change encryption",
            "angle": "tech breakthroughs",
            "hook": "Quantum computers are coming. Will they break all of our passwords?",
            "keywords": ["quantum computing", "encryption", "future tech"],
            "format": "tech_breakthroughs",
            "freshness_window_days": 60
        }
    ]
}

def main():
    parser = argparse.ArgumentParser(description="Generate candidate ideas based on a profile configuration.")
    parser.add_argument("--profile", required=True, help="Path to the profile YAML configuration file.")
    args = parser.parse_args()
    
    if not os.path.exists(args.profile):
        print(f"Error: Profile file not found at {args.profile}")
        sys.exit(1)
        
    try:
        with open(args.profile, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading profile config: {e}")
        sys.exit(1)
        
    profile_id = profile.get("profile_id")
    niche = profile.get("niche")
    
    if not profile_id or not niche:
        print("Error: Profile config must contain profile_id and niche.")
        sys.exit(1)
        
    catalog_ideas = IDEAS_CATALOG.get(niche, [])
    if not catalog_ideas:
        print(f"Error: No pre-defined ideas found for niche '{niche}'.")
        sys.exit(1)
        
    generated_ideas = []
    # Build 5 ideas based on catalog
    for i, catalog_idea in enumerate(catalog_ideas[:5]):
        idea = {
            "idea_id": f"idea_{profile_id}_{i+1}",
            "profile_id": profile_id,
            "topic": catalog_idea["topic"],
            "angle": catalog_idea["angle"],
            "hook": catalog_idea["hook"],
            "keywords": catalog_idea["keywords"],
            "format": catalog_idea["format"],
            "freshness_window_days": catalog_idea["freshness_window_days"]
        }
        generated_ideas.append(idea)
        
    output_dir = "docs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "generated-ideas.json")
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(generated_ideas, f, indent=2)
        print(f"Successfully generated {len(generated_ideas)} ideas for profile '{profile_id}' to {output_path}")
    except Exception as e:
        print(f"Error writing generated ideas: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
