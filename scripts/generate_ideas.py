import os
import sys
import json
import argparse
import yaml

# Candidate ideas catalog by niche
IDEAS_CATALOG = {
    "ai": [
        {
            "topic": "This hidden AI tool restores old blurry photos in seconds",
            "angle": "photo restoration technology",
            "hook": "This hidden AI tool restores old blurry photos.",
            "curiosity_gap": "It uses a deep neural network to predict and reconstruct high-resolution face details that are completely missing.",
            "visual_promise": "Watch a pixelated black-and-white face instantly sharpen into high-definition color.",
            "payoff": "Your family's old memories look like they were shot yesterday.",
            "final_question_or_twist": "Would you pay a professional restorer when this exists?",
            "keywords": ["photo restoration", "face enhancement", "old photos"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 30,
            "risk_flags": []
        },
        {
            "topic": "One messy recording becomes studio clean",
            "angle": "audio restoration technology",
            "hook": "See how one messy recording becomes studio clean.",
            "curiosity_gap": "A secret neural network isolates the speaker's voice by predicting and reconstructing missing vocal frequencies.",
            "visual_promise": "Watch the background noise waveform instantly flatten to a straight line.",
            "payoff": "The low-quality street audio transforms into crisp studio sound.",
            "final_question_or_twist": "Could this technology make expensive microphones completely obsolete?",
            "keywords": ["audio restoration", "voice cleaning", "neural network sound"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 14,
            "risk_flags": []
        },
        {
            "topic": "This boring file turns into something wild",
            "angle": "interactive data visualization",
            "hook": "Watch this boring file turn into something wild.",
            "curiosity_gap": "A hidden python script parses a simple CSV list and generates a stunning interactive 3D solar system visualization.",
            "visual_promise": "Witness rows of numbers instantly render into orbits, stars, and rotating planets.",
            "payoff": "We built a complete, interactive galaxy map without writing a single line of WebGL.",
            "final_question_or_twist": "Why aren't schools using this to teach astronomy?",
            "keywords": ["data visualization", "python script", "interactive 3d"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 14,
            "risk_flags": []
        },
        {
            "topic": "Nobody expects this AI trick to work",
            "angle": "document translation layout preserve",
            "hook": "Nobody expects this AI trick to work.",
            "curiosity_gap": "A new layout-preserving translator replaces text in complex diagrams without losing the original fonts or borders.",
            "visual_promise": "A technical blueprint transitions seamlessly between languages while keeping every design element intact.",
            "payoff": "It translates a full multi-layer PDF document in under three seconds.",
            "final_question_or_twist": "Is this the end of traditional translation services?",
            "keywords": ["document translation", "layout preservation", "pdf tools"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 14,
            "risk_flags": []
        },
        {
            "topic": "Create beautiful presentation slides instantly using artificial intelligence",
            "angle": "presentation slide design automation",
            "hook": "Stop spending hours designing presentation slides today.",
            "curiosity_gap": "This new AI website builds entire slide decks from a single prompt.",
            "visual_promise": "Type in your topic and watch the presentation populate.",
            "payoff": "Export clean PowerPoint slides in seconds.",
            "final_question_or_twist": "Is PowerPoint finally dead?",
            "keywords": ["presentation slide", "ai presentation", "design deck"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 14,
            "risk_flags": []
        },
        {
            "topic": "This AI tool turns a website idea into a landing page",
            "angle": "landing page layout recreation",
            "hook": "Stop coding landing page mockups from scratch today.",
            "curiosity_gap": "This AI website builder generates a website draft from a prompt.",
            "visual_promise": "Watch it recreate a landing page layout instantly.",
            "payoff": "Create a landing page mockup and export clean HTML.",
            "final_question_or_twist": "Will this make web developers obsolete?",
            "keywords": ["website builder", "ai design", "landing page mockup"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 14,
            "risk_flags": []
        },
        {
            "topic": "3 AI tools to start a side hustle",
            "angle": "side hustle automation",
            "hook": "These 3 AI tools will build a side hustle for you in minutes.",
            "curiosity_gap": "But most people are using them completely wrong.",
            "visual_promise": "We show the exact screen, the generated output, and the earnings dashboard.",
            "payoff": "Use them today before they become saturated.",
            "final_question_or_twist": "Which of these side hustles will you try first?",
            "keywords": ["side hustle", "ai tools", "make money online"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 14,
            "risk_flags": []
        },
        {
            "topic": "This AI website writes all your emails",
            "angle": "email productivity",
            "hook": "Stop wasting hours writing emails.",
            "curiosity_gap": "This free AI website writes them exactly in your voice.",
            "visual_promise": "Showing a blank email draft auto-filling in one click.",
            "payoff": "It saves hours and sounds completely human.",
            "final_question_or_twist": "Would you trust an AI to email your boss?",
            "keywords": ["write emails", "ai website", "productivity hacks"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 7,
            "risk_flags": []
        },
        {
            "topic": "How to create an AI voiceover using your own voice",
            "angle": "voice cloning tutorial",
            "hook": "Create an AI voiceover using your own voice with consent in seconds.",
            "curiosity_gap": "But you need to verify your permission first to prevent scams.",
            "visual_promise": "Record a 10 second audio clip and see it clone instantly.",
            "payoff": "Safe, consent-based voiceovers are now instant.",
            "final_question_or_twist": "Would you clone your own voice for content?",
            "keywords": ["personal voiceover", "ai voice", "voice cloning"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 30,
            "risk_flags": ["voice_cloning"]
        },
        {
            "topic": "3 AI extensions for Google Chrome you need today",
            "angle": "browser extension recommendations",
            "hook": "Stop using Google Chrome normally.",
            "curiosity_gap": "These 3 AI Chrome extensions make it twenty times smarter.",
            "visual_promise": "Quick cuts showing each extension sidebar activating in Chrome.",
            "payoff": "They are free to install and change how you browse.",
            "final_question_or_twist": "Which Chrome extension is your favorite?",
            "keywords": ["chrome extensions", "google chrome", "ai plugins"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 14,
            "risk_flags": []
        },
        {
            "topic": "This AI tool generates fully animated videos from text",
            "angle": "text to video animation",
            "hook": "This AI tool turns text into a full video.",
            "curiosity_gap": "But the result looks almost unreal.",
            "visual_promise": "You type one sentence. It builds scenes, captions, and motion.",
            "payoff": "This could change how creators make Shorts.",
            "final_question_or_twist": "Will AI completely replace animators?",
            "keywords": ["text to video", "animated videos", "ai video generator"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 10,
            "risk_flags": []
        },
        {
            "topic": "This AI tool generates 3D models from simple text prompts",
            "angle": "text to 3D generation",
            "hook": "You can generate fully textured 3D models in seconds just by typing.",
            "curiosity_gap": "This new AI software builds 3D assets that are ready to import into games.",
            "visual_promise": "Watch a 3D character render on screen from a single word prompt.",
            "payoff": "Download the file and use it in your game engine immediately.",
            "final_question_or_twist": "Is this the future of game design?",
            "keywords": ["3d models", "text to 3d", "game assets"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 14,
            "risk_flags": []
        },
        {
            "topic": "This free AI website removes background noise from any audio file",
            "angle": "audio cleanup tool",
            "hook": "Stop recording video with background fan noise or traffic sounds.",
            "curiosity_gap": "This free AI audio cleanup site makes a cheap microphone sound as clear as a studio microphone.",
            "visual_promise": "Showing an audio waveform graph with noise disappearing in real time.",
            "payoff": "Upload your audio and get a studio quality podcast sound instantly.",
            "final_question_or_twist": "Will you use this to clean up your audio?",
            "keywords": ["audio cleanup", "remove noise", "free ai tool"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 14,
            "risk_flags": []
        }
    ],
    "fifa": [
        {
            "topic": "The 3 most overpowered cheap beasts in FIFA",
            "angle": "cheap squad builders",
            "hook": "Stop spending millions on meta FIFA players.",
            "curiosity_gap": "These 3 cheap players outperform cards worth millions.",
            "visual_promise": "Compare card stats and show in-game clip of a crazy goal.",
            "payoff": "Buy them now before their price skyrockets.",
            "keywords": ["cheap beasts", "fifa squad", "overpowered players"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 7,
            "risk_flags": []
        },
        {
            "topic": "How to score every time using this skill move",
            "angle": "skill move tutorial",
            "hook": "This simple skill move is completely broken.",
            "curiosity_gap": "Almost nobody knows the correct trigger timing.",
            "visual_promise": "Slow motion controller overlay pointing at the analog stick.",
            "payoff": "Learn this sequence to win every FUT game.",
            "keywords": ["fifa tutorial", "skill move", "score goals"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 14,
            "risk_flags": []
        },
        {
            "topic": "Rate this 500k meta starter squad",
            "angle": "meta squad review",
            "hook": "This is the best 500k starter squad you can build right now.",
            "curiosity_gap": "But it has one secret flaw in the midfield.",
            "visual_promise": "Hovering over squad lineup and highlighting player link lines.",
            "payoff": "Fix this link, and you have a champion team.",
            "keywords": ["starter squad", "meta players", "squad builder"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 7,
            "risk_flags": []
        },
        {
            "topic": "Is this new player item worth doing?",
            "angle": "sbc player review",
            "hook": "EA just dropped a new player SBC.",
            "curiosity_gap": "Is it actually worth your fodder, or is it a scam?",
            "visual_promise": "Review player stats and gameplay traits.",
            "payoff": "Avoid this unless you need the specific team links.",
            "keywords": ["sbc review", "player rating", "meta review"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 5,
            "risk_flags": []
        },
        {
            "topic": "Unbelievable pack luck in the weekend league rewards",
            "angle": "rewards pack opening",
            "hook": "We just opened the weekend league rewards.",
            "curiosity_gap": "You won't believe who we packed on the very last card.",
            "visual_promise": "Opening pack animation, board reveal, and walkout.",
            "payoff": "A million coins player from a free pack.",
            "keywords": ["pack opening", "rewards luck", "meta packing"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 3,
            "risk_flags": []
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
            "hook": "Apple just announced the new iPhone 18.",
            "curiosity_gap": "And it features a major design change that shocks fans.",
            "visual_promise": "Show mockups of the new screen layout and cameras.",
            "payoff": "This could redefine standard phone design.",
            "keywords": ["iphone 18", "apple launch", "new iphone"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 7,
            "risk_flags": []
        },
        {
            "topic": "Google drops its new open source AI model",
            "angle": "tech breakthroughs",
            "hook": "Google just released a brand new AI model.",
            "curiosity_gap": "It runs completely locally on your phone without internet.",
            "visual_promise": "Demo showing instant text responses offline.",
            "payoff": "A massive win for secure personal assistants.",
            "keywords": ["google ai", "local model", "tech breakthrough"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 10,
            "risk_flags": []
        },
        {
            "topic": "Change these 3 settings to protect your data now",
            "angle": "user privacy alerts",
            "hook": "Your phone is spying on you.",
            "curiosity_gap": "Change these 3 privacy settings immediately.",
            "visual_promise": "Scrolling through iOS or Android privacy menus.",
            "payoff": "Keep your private data secure from third-party trackers.",
            "keywords": ["data privacy", "phone settings", "security alerts"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 30,
            "risk_flags": []
        },
        {
            "topic": "The AI startup CEO drama explained",
            "angle": "industry news and drama",
            "hook": "There is a massive boardroom fight happening at a top AI company.",
            "curiosity_gap": "Here is what happened behind closed doors.",
            "visual_promise": "Timeline showing fired executives and employee letters.",
            "payoff": "The future of the company remains highly unstable.",
            "keywords": ["tech drama", "ceo fired", "industry news"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 7,
            "risk_flags": []
        },
        {
            "topic": "How quantum computing will change encryption",
            "angle": "tech breakthroughs",
            "hook": "Quantum computers are coming.",
            "curiosity_gap": "Will they break all of our passwords in seconds?",
            "visual_promise": "Animations explaining qubits and encryption keys.",
            "payoff": "We need post-quantum security protocols ready today.",
            "keywords": ["quantum computing", "encryption", "future tech"],
            "format": "viral_curiosity_24s",
            "freshness_window_days": 60,
            "risk_flags": []
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
    # Build all ideas based on catalog
    for i, catalog_idea in enumerate(catalog_ideas):
        idea = {
            "idea_id": f"idea_{profile_id}_{i+1}",
            "profile_id": profile_id,
            "topic": catalog_idea["topic"],
            "angle": catalog_idea["angle"],
            "hook": catalog_idea["hook"],
            "keywords": catalog_idea["keywords"],
            "format": catalog_idea["format"],
            "freshness_window_days": catalog_idea["freshness_window_days"],
            "curiosity_gap": catalog_idea.get("curiosity_gap", ""),
            "visual_promise": catalog_idea.get("visual_promise", ""),
            "payoff": catalog_idea.get("payoff", ""),
            "final_question_or_twist": catalog_idea.get("final_question_or_twist", ""),
            "risk_flags": catalog_idea.get("risk_flags", [])
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
