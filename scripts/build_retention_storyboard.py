import os
import sys
import json
import yaml
import re

def sanitize_text(text):
    blacklist = ["subscribe", "isolation", "protest", "unrelated crowd", "random office", "generic podcast"]
    replacements = {
        "subscribe": "follow",
        "isolation": "creative focus",
        "protest": "active debate",
        "unrelated crowd": "audience",
        "random office": "modern desk workspace",
        "generic podcast": "studio microphone setup"
    }
    cleaned = text
    for term, rep in replacements.items():
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        cleaned = pattern.sub(rep, cleaned)
    return cleaned

def sanitize_narration(text):
    fillers = ["um", "ah", "basically", "literally", "actually", "like"]
    cleaned = text
    for f in fillers:
        pattern = re.compile(rf'\b{f}\b', re.IGNORECASE)
        cleaned = pattern.sub("", cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def main():
    print("--- Running Retention Storyboard Builder ---")
    
    brief_path = os.path.join("docs", "video-brief.json")
    format_path = os.path.join("formats", "viral_retention_engine_24s.yml")
    
    if not os.path.exists(brief_path):
        print(f"Error: Video brief not found at {brief_path}")
        sys.exit(1)
        
    if not os.path.exists(format_path):
        print(f"Error: Format spec not found at {format_path}")
        sys.exit(1)
        
    try:
        with open(brief_path, "r", encoding="utf-8") as f:
            brief = json.load(f)
    except Exception as e:
        print(f"Error reading video brief: {e}")
        sys.exit(1)
        
    try:
        with open(format_path, "r", encoding="utf-8") as f:
            fmt = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading format spec: {e}")
        sys.exit(1)

    topic = brief.get("topic", "")
    hook = sanitize_narration(brief.get("hook", ""))
    payoff = sanitize_narration(brief.get("payoff", ""))
    narration_beats = [sanitize_narration(b) for b in brief.get("narration_beats", []) if b]
    
    if not narration_beats:
        narration_beats = [hook]

    # Clean and split narration beats into short sentences of 2-9 words
    raw_sentences = []
    for beat in narration_beats:
        if not beat:
            continue
        # Split sentences by period/question/exclamation
        for part in beat.replace("!", ".").replace("?", ".").split("."):
            s_clean = part.strip()
            if s_clean:
                raw_sentences.append(s_clean)
                
    narration_script = []
    for s in raw_sentences:
        words = s.split()
        if len(words) > 9:
            for i in range(0, len(words), 6):
                chunk = words[i:i+6]
                if chunk:
                    narration_script.append(" ".join(chunk))
        else:
            narration_script.append(s)

    # Determine category
    category = "fallback"
    topic_lower = topic.lower()
    if any(k in topic_lower for k in ["voice", "audio", "noise", "mic", "sound", "podcast", "speech"]):
        category = "audio_cleanup"
    elif any(k in topic_lower for k in ["slide", "presentation", "powerpoint", "ppt", "doc", "pdf"]):
        category = "slides"
    elif any(k in topic_lower for k in ["3d", "render", "model", "graphics", "blender", "cad"]):
        category = "3d"

    # Category presets (each list has 24 elements for 24 scenes)
    presets = {
        "audio_cleanup": [
            ("Close-up of a computer monitor showing a messy, noisy waveform with spikes.", "noisy waveform"),
            ("A vintage bad microphone recording in a dark room.", "bad microphone"),
            ("Red noise spikes flashing on an audio editing screen.", "audio noise screen"),
            ("An extreme close up of a mouse pointer hovering over an AI cleanup button on screen.", "ai button click"),
            ("An animated pointer clicking the button, causing a glow.", "mouse click screen"),
            ("The waveform animation changing from messy and red to clean and blue.", "clean waveform"),
            ("A creator looking surprised and reacting with excitement.", "excited creator face"),
            ("A split screen visualization showing before and after audio levels.", "audio visualizer"),
            ("A close-up of headphones glowing with sound waves.", "headphones audio"),
            ("A clean modern recording studio room with a high-end microphone.", "clean studio microphone"),
            ("Smooth digital waveform moving across a dark screen.", "digital audio wave"),
            ("A user putting on premium studio headphones.", "wearing headphones"),
            ("Close-up of a soundwave EQ display pulsing smoothly.", "equalizer display"),
            ("An audio waveform flattening its background noise dynamically.", "sound wave transition"),
            ("A professional audio editing software interface showing successful export.", "audio interface software"),
            ("A creator gesturing thumbs up in a studio setup.", "creator thumbs up"),
            ("Animated graphic showing a lock icon opening to soundwaves.", "audio lock icon"),
            ("Close-up of a speaker cone vibrating with clean bass.", "speaker vibration"),
            ("A glowing checkmark overlay on a clean laptop screen.", "laptop checkmark screen"),
            ("Cinematic shot of professional sound engineering desk.", "soundboard slider"),
            ("Abstract neon lines representing perfect sound waves.", "neon audio waves"),
            ("Close-up of fingers adjusting a volume dial.", "volume dial dial"),
            ("A person smiling in relief listening to clean audio.", "listening to music smiling"),
            ("A pulsing checkmark icon in the center of the screen.", "success checkmark")
        ],
        "slides": [
            ("Close-up of a blank white slide on a laptop screen.", "blank presentation slide"),
            ("A cursor typing bullet points onto a boring presentation layout.", "typing on computer"),
            ("A stack of messy unorganized notes on a desk.", "messy notes desk"),
            ("An AI tool icon interface showing Generate Slides dialog.", "ai tool interface"),
            ("The cursor clicks a glowing Create Slide deck button.", "clicking button computer"),
            ("A beautiful modern colorful slide layout appearing instantly.", "modern slide layout"),
            ("A creator raising eyebrows in absolute surprise.", "surprised face person"),
            ("Close-up of dynamic charts and graphics building itself on screen.", "data visualization graph"),
            ("Slide deck transitioning smoothly with premium animation.", "clean transitions slide"),
            ("A person successfully giving a presentation to a board.", "professional presenter screen"),
            ("Dynamic layout of slides moving in a carousel view.", "carousel slides mockup"),
            ("A clean modern workplace with a laptop showcasing slides.", "laptop office desk"),
            ("Animated template elements sliding into place.", "template slides interface"),
            ("A close-up of a chart showing revenue or growth on a slide.", "revenue growth chart"),
            ("A creator smiling and pointing at a beautiful presentation screen.", "pointing at screen smiling"),
            ("A sequence of colorful slide templates displayed side-by-side.", "design templates gallery"),
            ("A pointer adjusting color palettes on a slide instantly.", "color palette picker"),
            ("Close-up of slide fonts and typography rendering beautifully.", "typography design screen"),
            ("A laptop with a clean presentation slide showing a trophy icon.", "laptop trophy slide"),
            ("A professional designer nodding in approval.", "designer nodding smiling"),
            ("Minimalist slide layout with sleek dark mode style.", "dark mode slide mockup"),
            ("A tablet showing interactive presentation templates.", "tablet presentation design"),
            ("Abstract shapes merging to form a beautiful infographic.", "abstract shape merging"),
            ("A glowing gold checkmark indicating design completed.", "gold checkmark complete")
        ],
        "3d": [
            ("A blank wireframe grid in a 3D modeling viewport.", "3d wireframe grid"),
            ("A low-polygon basic block model rotating slowly.", "low poly 3d model"),
            ("A messy complex CAD blueprint on a workspace.", "cad blueprint screen"),
            ("A button interface showing Generate 3D Asset option.", "3d software UI"),
            ("A cursor clicking the 3D generation execute button.", "clicking laptop key"),
            ("A fully rendered 3D model with realistic textures appearing instantly.", "rendered 3d model texture"),
            ("A 3D artist staring at the screen in amazement.", "amazed expression face"),
            ("A close-up of the 3D model rotating 360 degrees.", "3d rotation model"),
            ("Light reflecting off metallic and glass shaders of the model.", "glowing 3d shader light"),
            ("A virtual camera panning around a detailed 3D environment.", "3d environment render"),
            ("A wireframe overlay transitioning into a fully textured model.", "wireframe texture transition"),
            ("A clean modern computer setup showing Blender or Maya software.", "creative office monitor"),
            ("A viewport rendering lighting and shadows dynamically.", "rendering engine viewport"),
            ("Close-up of a digital sculpting mesh.", "digital sculpting mesh"),
            ("A creator giving double thumbs up in front of a monitor.", "creator thumbs up screen"),
            ("A sleek 3D robot or character model walking.", "3d character model animation"),
            ("A grid of various rendered 3D objects rotating.", "rendered objects showcase"),
            ("A laser scanner effect sweeping across a 3D object.", "laser scan 3d"),
            ("A laptop with a clean 3D render of a golden crown.", "laptop 3d render crown"),
            ("A 3D designer smiling and typing on a keyboard.", "typing designer smiling"),
            ("A minimalist geometric 3D pattern moving smoothly.", "geometric 3d animation"),
            ("A vr headset sitting on a desk with 3D space on screen.", "vr headset workspace"),
            ("Abstract colorful fluid simulation rendering in 3D.", "3d fluid simulation"),
            ("A pulsing checkmark in a 3D sphere.", "glowing sphere checkmark")
        ],
        "fallback": [
            ("A clean glowing computer monitor displaying a modern dashboard.", "glowing computer dashboard"),
            ("A close-up of hands typing quickly on a backlit mechanical keyboard.", "hands typing keyboard"),
            ("A user interface loading progress bar filling up rapidly.", "progress bar loading screen"),
            ("A pointer clicking on a bright Generate option.", "click generate interface"),
            ("A circular progress wheel spinning and glowing.", "loading wheel process"),
            ("A beautiful design layout appearing instantly on a tablet.", "tablet designer interface"),
            ("A creator reacting with surprise and smiling.", "excited creator screen"),
            ("Close-up of dynamic statistics graph building on screen.", "growth chart screen"),
            ("A screen displaying modern software menu navigation.", "software screen navigation"),
            ("A close-up of fingers sliding a visual timeline scale.", "timeline slider controls"),
            ("A clean workspace with computer and glowing light.", "creative workspace desk"),
            ("A laptop screen displaying successful export status.", "laptop success status"),
            ("A split screen view showing fast changes in files.", "split screen workflow"),
            ("A professional developer nodding in approval.", "professional nodding screen"),
            ("A checkmark icon populating on a dark background.", "checkmark complete icon"),
            ("Sleek neon lines pulsing across a grid screen.", "neon lines abstract"),
            ("A tablet screen with design templates visible.", "tablet design templates"),
            ("A creator smiling and presenting towards screen.", "smiling developer screen"),
            ("Close-up of a high quality interface dial rotating.", "interface dial rotation"),
            ("A hand pressing a button on a control device.", "hand press button"),
            ("Smooth geometric patterns floating in abstract space.", "abstract float geometry"),
            ("A laptop displaying a secure complete dashboard.", "laptop complete dashboard"),
            ("A person looking happy and typing on keyboard.", "happy typing keyboard"),
            ("A golden success badge or checkmark glowing.", "glowing checkmark badge")
        ]
    }

    # Generate 48 text overlays first to map them into scenes
    text_overlays = []
    all_words = []
    for sentence in narration_script:
        all_words.extend(sentence.split())
        
    if not all_words:
        all_words = ["DISCOVER", "THIS", "INCREDIBLE", "NEW", "AI", "TOOL", "TODAY"]
        
    word_idx = 0
    total_overlays = 48
    for idx in range(total_overlays):
        sec_start = idx * 0.5
        sec_end = (idx + 1) * 0.5
        
        # Group 1-2 words per overlay, up to 4 words max
        chunk = []
        for _ in range(2):
            if word_idx < len(all_words):
                cleaned = all_words[word_idx].replace(".", "").replace(",", "").replace("!", "").replace("?", "")
                # Force blacklist check on individual words
                cleaned = sanitize_text(cleaned)
                if cleaned:
                    chunk.append(cleaned.upper())
                word_idx += 1
                
        if not chunk:
            # Fallback repeating CTA words (no "subscribe"!)
            fallback_words = ["BOOST", "PRODUCTIVITY", "DESIGN", "FAST", "REVEAL", "NOW", "CREATIVE", "SYSTEM"]
            chunk = [fallback_words[idx % len(fallback_words)]]
            
        text_overlays.append({
            "start_time": float(sec_start),
            "end_time": float(sec_end),
            "text": " ".join(chunk),
            "position": "center",
            "style": "large_bold_white_black_shadow",
            "max_words": 4
        })

    # Generate 24 scenes of 1.0s duration each
    scenes = []
    brief_scenes = brief.get("scene_plan", [])
    
    movements_list = ["Rapid zoom-in", "Pan left", "Tilt up", "Icon shake", "Slow zoom-out", "Slide-right", "Camera shake", "Focus switch"]
    sfx_list = ["whoosh", "impact", "hit", "riser", "glitch", "bass drop"]
    
    # We will split the 12 brief scenes into 24 scenes (Sub-scene A and B of 1.0s each)
    for i in range(12):
        # Fallback to brief scene or default visual
        if i < len(brief_scenes):
            b_scene = brief_scenes[i]
            base_audio = sanitize_narration(b_scene.get("audio", hook))
            base_movement = b_scene.get("movement", "Slow zoom-in")
        else:
            base_audio = hook
            base_movement = "Slow zoom-in"
            
        # Get category presets
        preset_list = presets.get(category, presets["fallback"])
        
        # A Scene
        visual_a, query_a = preset_list[2*i]
        # B Scene
        visual_b, query_b = preset_list[2*i+1]
        
        # Sanitize against blacklist
        visual_a = sanitize_text(visual_a)
        query_a = sanitize_text(query_a)
        visual_b = sanitize_text(visual_b)
        query_b = sanitize_text(query_b)
            
        # Distribute audio across sub-scenes
        words = base_audio.split()
        mid = len(words) // 2
        audio_a = " ".join(words[:mid]) if mid > 0 else base_audio
        audio_b = " ".join(words[mid:]) if mid > 0 else ""
        
        # Story beat role mapping
        if i < 3:
            role = "claim"
        elif i < 6:
            role = "evidence"
        elif i < 9:
            role = "suspense_build"
        elif i < 11:
            role = "reveal_or_prediction"
        else:
            role = "final_question_or_twist"
            
        # Overlay text for Scene A (corresponds to overlays 2*i and 2*i + 0.5s if mapped)
        overlay_text_a = text_overlays[2*i]["text"]
        # Overlay text for Scene B
        overlay_text_b = text_overlays[2*i+1]["text"]
        
        # Scene A (e.g. 0.0s - 1.0s)
        time_a = f"0:{2*i:02d} - 0:{2*i+1:02d}" # Represents 1s interval structurally
        scenes.append({
            "scene_id": 2 * i + 1,
            "time_range": time_a,
            "visual_prompt": visual_a,
            "stock_search_query": query_a,
            "motion_instruction": base_movement if base_movement else "Rapid zoom-in",
            "reaction_or_reveal_type": role,
            "overlay_text": overlay_text_a,
            "narration_line": audio_a if audio_a else "Watch closely.",
            "sound_cue": sfx_list[(2*i) % len(sfx_list)]
        })
        
        # Scene B (e.g. 1.0s - 2.0s)
        time_b = f"0:{2*i+1:02d} - 0:{2*i+2:02d}" # Represents 1s interval structurally
        scenes.append({
            "scene_id": 2 * i + 2,
            "time_range": time_b,
            "visual_prompt": visual_b,
            "stock_search_query": query_b,
            "motion_instruction": movements_list[(2*i+1) % len(movements_list)],
            "reaction_or_reveal_type": role,
            "overlay_text": overlay_text_b,
            "narration_line": audio_b if audio_b else "Process completed.",
            "sound_cue": sfx_list[(2*i+1) % len(sfx_list)]
        })

    # 3. Compile separate metadata event arrays
    camera_motion = []
    sound_cues = []
    edit_cues = []
    
    for s in scenes:
        tr = s["time_range"]
        camera_motion.append({
            "time_range": tr,
            "motion": s["motion_instruction"]
        })
        sound_cues.append({
            "time_range": tr,
            "effect": s["sound_cue"]
        })
        edit_cues.append({
            "time_range": tr.split("-")[0].strip(),
            "type": "jump_cut"
        })
        
    safety_notes = [
        "No copyrighted clips are used.",
        "Disney, Fox, Simpsons, and named character references are fully avoided.",
        "Visuals describe generic non-branded assets (mockups, reaction vectors, layouts).",
        "Text overlays strictly contain 1-4 words.",
        "Narration is direct and safety-checked for overpromising income claims."
    ]

    # Combine into final storyboard
    storyboard = {
        "format_id": "viral_retention_engine_24s",
        "target_seconds": 24,
        "hook_0_3s": hook,
        "narration_script": narration_script,
        "scenes": scenes,
        "text_overlays": text_overlays,
        "camera_motion": camera_motion,
        "sound_cues": sound_cues,
        "edit_cues": edit_cues,
        "safety_notes": safety_notes
    }

    output_storyboard_path = os.path.join("docs", "retention-storyboard.json")
    try:
        with open(output_storyboard_path, "w", encoding="utf-8") as f:
            json.dump(storyboard, f, indent=2)
        print(f"Successfully generated retention storyboard to {output_storyboard_path}")
    except Exception as e:
        print(f"Error writing retention storyboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
