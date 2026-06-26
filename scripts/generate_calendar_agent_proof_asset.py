import os
import sys
import json
import subprocess
import shutil
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    font_paths = [
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

def draw_base_calendar(draw, width, height, title, subtitle, header_bg, title_font, subtitle_font, day_font, margin_left, col_width, grid_top, grid_bottom, grid_height, grid_line_color, text_white, text_grey):
    bg_color = (18, 18, 24)
    # 1. Draw Header
    draw.rectangle([(0, 0), (width, 240)], fill=header_bg)
    draw.text((width // 2, 70), title, fill=text_white, font=title_font, anchor="mm")
    draw.text((width // 2, 160), subtitle, fill=(52, 152, 219), font=subtitle_font, anchor="mm")
    
    # 2. Draw Calendar Grid structure
    days = ["MON", "TUE", "WED", "THU", "FRI"]
    for i, day in enumerate(days):
        col_x = margin_left + i * col_width
        # Column headers
        draw.text((col_x + col_width // 2, grid_top - 40), day, fill=text_grey, font=day_font, anchor="mm")
        # Vertical column lines
        draw.line([(col_x, grid_top), (col_x, grid_bottom)], fill=grid_line_color, width=2)
        
    # Draw final vertical line closing the grid
    draw.line([(margin_left + 5 * col_width, grid_top), (margin_left + 5 * col_width, grid_bottom)], fill=grid_line_color, width=2)
    
    # Draw horizontal hour lines
    hours = ["9 AM", "12 PM", "3 PM", "6 PM"]
    for i, hour in enumerate(hours):
        row_y = grid_top + i * (grid_height // 4)
        draw.line([(margin_left, row_y), (margin_left + 5 * col_width, row_y)], fill=grid_line_color, width=2)
        draw.text((margin_left - 15, row_y), hour, fill=text_grey, font=day_font, anchor="rm")

def main():
    print("--- Generating Calendar Agent Proof Assets (v2.2) ---")
    
    # 1. Setup Directories
    frames_dir = os.path.join("scratch", "calendar_frames")
    output_dir = os.path.join("assets", "proof_capture", "calendar_agent")
    os.makedirs(output_dir, exist_ok=True)
    
    # Common layout parameters
    width, height = 1080, 1920
    fps = 15
    bg_color = (18, 18, 24)
    header_bg = (30, 30, 40)
    grid_line_color = (50, 50, 60)
    text_white = (255, 255, 255)
    text_grey = (150, 150, 160)
    
    # Colors for schedule blocks
    blue_block = (41, 128, 185)
    green_block = (39, 174, 96)
    purple_block = (142, 68, 173)
    orange_block = (211, 84, 0)
    red_block = (192, 57, 43)
    yellow_block = (241, 196, 15)
    
    # Load fonts
    title_font = get_font(55)
    subtitle_font = get_font(35)
    day_font = get_font(30)
    block_font = get_font(28)
    banner_font = get_font(75)
    
    margin_left = 90
    col_width = 180
    grid_top = 380
    grid_bottom = 1500
    grid_height = grid_bottom - grid_top
    
    # Asset Specs
    assets_specs = [
        {
            "filename": "calendar_agent_demo_001.mp4",
            "duration": 7.0,
            "title": "AI SCHEDULING AGENT",
            "subtitle": "OPTIMIZING WEEKLY WORKFLOW",
            "type": "demo"
        },
        {
            "filename": "calendar_agent_hook_001.mp4",
            "duration": 6.0,
            "title": "CALENDAR OVERLOAD",
            "subtitle": "MANAGING 12+ CONFLICTS",
            "type": "hook"
        },
        {
            "filename": "calendar_agent_process_001.mp4",
            "duration": 6.0,
            "title": "AUTO-SCHEDULING...",
            "subtitle": "AI AGENT PLACING EVENTS",
            "type": "process"
        },
        {
            "filename": "calendar_agent_conflict_fix_001.mp4",
            "duration": 6.0,
            "title": "RESOLVING CONFLICTS",
            "subtitle": "FINDING OPTIMAL SLOTS",
            "type": "conflict_fix"
        },
        {
            "filename": "calendar_agent_final_payoff_001.mp4",
            "duration": 7.0,
            "title": "WEEKLY SCHEDULE",
            "subtitle": "FULLY AUTOMATED & TIDY",
            "type": "final_payoff"
        }
    ]
    
    for spec in assets_specs:
        filename = spec["filename"]
        duration = spec["duration"]
        title = spec["title"]
        subtitle = spec["subtitle"]
        a_type = spec["type"]
        
        output_video_path = os.path.join(output_dir, filename)
        os.makedirs(frames_dir, exist_ok=True)
        
        total_frames = int(fps * duration)
        print(f"Generating frames for {filename} ({total_frames} frames)...")
        
        for f_idx in range(total_frames):
            t = f_idx / fps
            img = Image.new("RGB", (width, height), bg_color)
            draw = ImageDraw.Draw(img)
            
            draw_base_calendar(
                draw, width, height, title, subtitle, header_bg, title_font, subtitle_font,
                day_font, margin_left, col_width, grid_top, grid_bottom, grid_height,
                grid_line_color, text_white, text_grey
            )
            
            if a_type == "demo":
                # Original demo animation
                # Mon: Team Sync (1.0s to 1.5s fade-in)
                if t >= 1.0:
                    alpha = min(1.0, (t - 1.0) / 0.5)
                    block_color = tuple(int(c * alpha) for c in blue_block)
                    x0 = margin_left + 0 * col_width + 5
                    x1 = x0 + col_width - 10
                    y0 = grid_top + 100
                    y1 = y0 + 180
                    draw.rectangle([(x0, y0), (x1, y1)], fill=block_color, outline=text_white, width=1)
                    draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "Team\nSync", fill=text_white, font=block_font, anchor="mm", align="center")
                # Tue: Focus Block (1.5s to 2.0s fade-in)
                if t >= 1.5:
                    alpha = min(1.0, (t - 1.5) / 0.5)
                    block_color = tuple(int(c * alpha) for c in green_block)
                    x0 = margin_left + 1 * col_width + 5
                    x1 = x0 + col_width - 10
                    y0 = grid_top + 400
                    y1 = y0 + 200
                    draw.rectangle([(x0, y0), (x1, y1)], fill=block_color, outline=text_white, width=1)
                    draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "Focus\nBlock", fill=text_white, font=block_font, anchor="mm", align="center")
                # Thu: Deep Work (2.0s to 2.5s fade-in)
                if t >= 2.0:
                    alpha = min(1.0, (t - 2.0) / 0.5)
                    block_color = tuple(int(c * alpha) for c in purple_block)
                    x0 = margin_left + 3 * col_width + 5
                    x1 = x0 + col_width - 10
                    y0 = grid_top + 250
                    y1 = y0 + 220
                    draw.rectangle([(x0, y0), (x1, y1)], fill=block_color, outline=text_white, width=1)
                    draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "Deep\nWork", fill=text_white, font=block_font, anchor="mm", align="center")
                # Fri: Workout (2.5s to 3.0s fade-in)
                if t >= 2.5:
                    alpha = min(1.0, (t - 2.5) / 0.5)
                    block_color = tuple(int(c * alpha) for c in orange_block)
                    x0 = margin_left + 4 * col_width + 5
                    x1 = x0 + col_width - 10
                    y0 = grid_top + 30
                    y1 = y0 + 130
                    draw.rectangle([(x0, y0), (x1, y1)], fill=block_color, outline=text_white, width=1)
                    draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "Workout", fill=text_white, font=block_font, anchor="mm", align="center")
                # Wed: Conflict/Solved
                if 3.0 <= t < 4.5:
                    x0 = margin_left + 2 * col_width + 5
                    x1 = x0 + col_width - 10
                    y0 = grid_top + 200
                    y1 = y0 + 180
                    if t < 4.0:
                        draw.rectangle([(x0, y0), (x1, y1)], fill=red_block, outline=text_white, width=2)
                        draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "CONFLICT", fill=text_white, font=block_font, anchor="mm")
                    else:
                        flash = int(f_idx % 4 >= 2)
                        bg = yellow_block if flash else red_block
                        draw.rectangle([(x0, y0), (x1, y1)], fill=bg, outline=text_white, width=2)
                        draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "SOLVING...", fill=text_white if not flash else (0, 0, 0), font=block_font, anchor="mm")
                if t >= 4.5:
                    x0 = margin_left + 2 * col_width + 5
                    x1 = x0 + col_width - 10
                    y0 = grid_top + 600
                    y1 = y0 + 180
                    draw.rectangle([(x0, y0), (x1, y1)], fill=green_block, outline=text_white, width=1)
                    draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "Study\n(Fixed)", fill=text_white, font=block_font, anchor="mm", align="center")
                if t >= 5.0:
                    banner_y = max(900, 1100 - int((t - 5.0) * 400))
                    draw.rectangle([(100, banner_y - 120), (width - 100, banner_y + 120)], fill=(46, 204, 113), outline=text_white, width=3)
                    draw.text((width // 2, banner_y), "WEEK PLANNED", fill=text_white, font=banner_font, anchor="mm")
                    
            elif a_type == "hook":
                # Messy overloaded calendar with multiple conflicts
                # Draw several overlapping red blocks
                # Mon: Team Sync vs Deep Work (9 AM)
                x0 = margin_left + 0 * col_width + 5
                x1 = x0 + col_width - 10
                draw.rectangle([(x0, grid_top + 50), (x1, grid_top + 180)], fill=red_block, outline=text_white, width=1)
                draw.rectangle([(x0 + 10, grid_top + 100), (x1 + 10, grid_top + 230)], fill=red_block, outline=text_white, width=1)
                draw.text((x0 + col_width // 2, grid_top + 140), "CONFLICT", fill=text_white, font=block_font, anchor="mm")
                
                # Wed: Focus Block vs Workout vs Study
                x0 = margin_left + 2 * col_width + 5
                x1 = x0 + col_width - 10
                draw.rectangle([(x0, grid_top + 200), (x1, grid_top + 350)], fill=red_block, outline=text_white, width=1)
                draw.rectangle([(x0 + 5, grid_top + 300), (x1 + 5, grid_top + 450)], fill=orange_block, outline=text_white, width=1)
                draw.text((x0 + col_width // 2, grid_top + 330), "OVERLAP", fill=text_white, font=block_font, anchor="mm")
                
                # Fri: Empty slot warnings or general mess
                x0 = margin_left + 4 * col_width + 5
                x1 = x0 + col_width - 10
                draw.rectangle([(x0, grid_top + 400), (x1, grid_top + 600)], fill=red_block, outline=text_white, width=1)
                draw.text((x0 + col_width // 2, grid_top + 500), "CONFLICT", fill=text_white, font=block_font, anchor="mm")
                
                # Big flashing alert at bottom
                flash = int(f_idx % 6 >= 3)
                alert_bg = red_block if flash else (30, 30, 40)
                draw.rectangle([(100, 1300), (width - 100, 1450)], fill=alert_bg, outline=text_white, width=2)
                draw.text((width // 2, 1375), "MESSY SCHEDULE", fill=text_white, font=subtitle_font, anchor="mm")
                
            elif a_type == "process":
                # Meeting blocks appear automatically
                # Mon Team Sync at 0.5s
                if t >= 0.5:
                    x0 = margin_left + 0 * col_width + 5
                    x1 = x0 + col_width - 10
                    draw.rectangle([(x0, grid_top + 50), (x1, grid_top + 200)], fill=blue_block, outline=text_white, width=1)
                    draw.text((x0 + col_width // 2, grid_top + 125), "Team\nSync", fill=text_white, font=block_font, anchor="mm", align="center")
                # Tue Focus Block at 1.5s
                if t >= 1.5:
                    x0 = margin_left + 1 * col_width + 5
                    x1 = x0 + col_width - 10
                    draw.rectangle([(x0, grid_top + 400), (x1, grid_top + 580)], fill=green_block, outline=text_white, width=1)
                    draw.text((x0 + col_width // 2, grid_top + 490), "Focus\nBlock", fill=text_white, font=block_font, anchor="mm", align="center")
                # Wed Study at 2.5s
                if t >= 2.5:
                    x0 = margin_left + 2 * col_width + 5
                    x1 = x0 + col_width - 10
                    draw.rectangle([(x0, grid_top + 150), (x1, grid_top + 330)], fill=purple_block, outline=text_white, width=1)
                    draw.text((x0 + col_width // 2, grid_top + 240), "Study", fill=text_white, font=block_font, anchor="mm", align="center")
                # Thu Deep Work at 3.5s
                if t >= 3.5:
                    x0 = margin_left + 3 * col_width + 5
                    x1 = x0 + col_width - 10
                    draw.rectangle([(x0, grid_top + 250), (x1, grid_top + 470)], fill=purple_block, outline=text_white, width=1)
                    draw.text((x0 + col_width // 2, grid_top + 360), "Deep\nWork", fill=text_white, font=block_font, anchor="mm", align="center")
                # Fri Workout at 4.5s
                if t >= 4.5:
                    x0 = margin_left + 4 * col_width + 5
                    x1 = x0 + col_width - 10
                    draw.rectangle([(x0, grid_top + 50), (x1, grid_top + 180)], fill=orange_block, outline=text_white, width=1)
                    draw.text((x0 + col_width // 2, grid_top + 115), "Workout", fill=text_white, font=block_font, anchor="mm")
                    
            elif a_type == "conflict_fix":
                # Conflict warning disappears and best slot is selected
                # Wed: Workout vs Study conflict (9 AM)
                x0 = margin_left + 2 * col_width + 5
                x1 = x0 + col_width - 10
                
                if t < 2.0:
                    # Drawing red block
                    draw.rectangle([(x0, grid_top + 50), (x1, grid_top + 200)], fill=red_block, outline=text_white, width=2)
                    draw.text((x0 + col_width // 2, grid_top + 125), "CONFLICT", fill=text_white, font=block_font, anchor="mm")
                elif t < 4.0:
                    # Flashing resolving state
                    flash = int(f_idx % 4 >= 2)
                    bg = yellow_block if flash else red_block
                    draw.rectangle([(x0, grid_top + 50), (x1, grid_top + 200)], fill=bg, outline=text_white, width=2)
                    draw.text((x0 + col_width // 2, grid_top + 125), "RESOLVING...", fill=text_white if not flash else (0,0,0), font=block_font, anchor="mm")
                else:
                    # Conflict resolved! Study is placed at 9 AM (green), Workout is rescheduled to 3 PM (green)
                    draw.rectangle([(x0, grid_top + 50), (x1, grid_top + 200)], fill=green_block, outline=text_white, width=1)
                    draw.text((x0 + col_width // 2, grid_top + 125), "Study\n(Ok)", fill=text_white, font=block_font, anchor="mm", align="center")
                    
                    x0_resched = margin_left + 2 * col_width + 5
                    x1_resched = x0_resched + col_width - 10
                    draw.rectangle([(x0_resched, grid_top + 600), (x1_resched, grid_top + 750)], fill=green_block, outline=text_white, width=1)
                    draw.text((x0_resched + col_width // 2, grid_top + 675), "Workout\n(Moved)", fill=text_white, font=block_font, anchor="mm", align="center")
                    
            elif a_type == "final_payoff":
                # Completed weekly calendar with nice tidy blocks
                # Mon: Team Sync
                x0 = margin_left + 0 * col_width + 5
                x1 = x0 + col_width - 10
                draw.rectangle([(x0, grid_top + 50), (x1, grid_top + 200)], fill=blue_block, outline=text_white, width=1)
                draw.text((x0 + col_width // 2, grid_top + 125), "Team\nSync", fill=text_white, font=block_font, anchor="mm", align="center")
                
                # Tue: Focus Block
                x0 = margin_left + 1 * col_width + 5
                x1 = x0 + col_width - 10
                draw.rectangle([(x0, grid_top + 400), (x1, grid_top + 580)], fill=green_block, outline=text_white, width=1)
                draw.text((x0 + col_width // 2, grid_top + 490), "Focus\nBlock", fill=text_white, font=block_font, anchor="mm", align="center")
                
                # Wed: Study
                x0 = margin_left + 2 * col_width + 5
                x1 = x0 + col_width - 10
                draw.rectangle([(x0, grid_top + 150), (x1, grid_top + 330)], fill=purple_block, outline=text_white, width=1)
                draw.text((x0 + col_width // 2, grid_top + 240), "Study", fill=text_white, font=block_font, anchor="mm")
                
                # Thu: Deep Work
                x0 = margin_left + 3 * col_width + 5
                x1 = x0 + col_width - 10
                draw.rectangle([(x0, grid_top + 250), (x1, grid_top + 470)], fill=purple_block, outline=text_white, width=1)
                draw.text((x0 + col_width // 2, grid_top + 360), "Deep\nWork", fill=text_white, font=block_font, anchor="mm", align="center")
                
                # Fri: Workout
                x0 = margin_left + 4 * col_width + 5
                x1 = x0 + col_width - 10
                draw.rectangle([(x0, grid_top + 50), (x1, grid_top + 180)], fill=orange_block, outline=text_white, width=1)
                draw.text((x0 + col_width // 2, grid_top + 115), "Workout", fill=text_white, font=block_font, anchor="mm")
                
                # Banner at bottom / middle: WEEK PLANNED (appears at 2.0s, fully stable at 3s)
                if t >= 2.0:
                    banner_y = max(900, 1100 - int((t - 2.0) * 400))
                    draw.rectangle([(100, banner_y - 120), (width - 100, banner_y + 120)], fill=(46, 204, 113), outline=text_white, width=3)
                    draw.text((width // 2, banner_y), "WEEK PLANNED", fill=text_white, font=banner_font, anchor="mm")
                    
            # Save frame
            frame_name = f"frame_{f_idx:03d}.png"
            frame_path = os.path.join(frames_dir, frame_name)
            img.save(frame_path)
            
        # Compile to MP4
        cmd = [
            "ffmpeg", "-y",
            "-r", str(fps),
            "-i", os.path.join(frames_dir, "frame_%03d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_video_path
        ]
        print(f"Compiling {filename}: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Successfully generated proof video at {output_video_path}")
        else:
            print(f"Error compiling video with ffmpeg: {res.stderr}")
            sys.exit(1)
            
        # Clean frames
        try:
            shutil.rmtree(frames_dir)
        except Exception:
            pass

    # 6. Write JSON sidecars and update registry
    print("\nWriting JSON sidecars and registry...")
    assets_metadata = [
        {
            "asset_id": "calendar_agent_demo_001",
            "file_path": "assets/proof_capture/calendar_agent/calendar_agent_demo_001.mp4",
            "project": "calendar_agent",
            "descriptor": "AI scheduling assistant automatically fills a weekly calendar and books meetings",
            "keywords": ["calendar", "schedule", "meeting", "week", "automation", "agent", "planned", "booked", "planner", "auto-fills", "scheduling"],
            "supported_scene_roles": ["proof", "payoff"],
            "supported_topics": ["ai_tools", "productivity", "calendar automation", "AI agent schedules your entire week", "AI bot auto-fills your calendar", "smart scheduling", "meeting planner"],
            "duration_seconds": 7.0,
            "orientation": "vertical_or_crop_safe",
            "source_type": "synthetic_private_validation_asset",
            "approved_for_private_validation": True,
            "approved_for_public_use": False,
            "contains_private_data": False,
            "notes": "Synthetic demo asset for private proof-asset validation only.",
            "asset_variant": "proof_visual",
            "visual_strength_score": 4,
            "best_for_scene_position": ["proof", "payoff"],
            "allowed_reuse_count": 2,
            "allow_single_asset_private_validation": True,
            "payoff_strength": "medium",
            "visual_notes": "AI scheduling assistant automatically fills a weekly calendar and books meetings."
        },
        {
            "asset_id": "calendar_agent_hook_001",
            "file_path": "assets/proof_capture/calendar_agent/calendar_agent_hook_001.mp4",
            "project": "calendar_agent",
            "descriptor": "Messy weekly calendar with calendar conflicts and warning labels",
            "keywords": ["calendar", "conflict", "schedule", "messy", "empty", "overlap"],
            "supported_scene_roles": ["proof"],
            "supported_topics": ["ai_tools", "productivity", "calendar automation", "AI agent schedules your entire week"],
            "duration_seconds": 6.0,
            "orientation": "vertical_or_crop_safe",
            "source_type": "synthetic_private_validation_asset",
            "approved_for_private_validation": True,
            "approved_for_public_use": False,
            "contains_private_data": False,
            "notes": "Synthetic hook asset. Not approved for public posting until manually reviewed.",
            "asset_variant": "hook_visual",
            "visual_strength_score": 4,
            "best_for_scene_position": ["hook", "first_3_seconds"],
            "allowed_reuse_count": 2,
            "allow_single_asset_private_validation": False,
            "payoff_strength": "weak",
            "visual_notes": "Shows messy calendar with red conflict warning highlights."
        },
        {
            "asset_id": "calendar_agent_process_001",
            "file_path": "assets/proof_capture/calendar_agent/calendar_agent_process_001.mp4",
            "project": "calendar_agent",
            "descriptor": "Meeting blocks automatically appearing on a calendar grid",
            "keywords": ["calendar", "schedule", "automation", "process", "planning", "auto-fills"],
            "supported_scene_roles": ["proof"],
            "supported_topics": ["ai_tools", "productivity", "calendar automation", "AI agent schedules your entire week"],
            "duration_seconds": 6.0,
            "orientation": "vertical_or_crop_safe",
            "source_type": "synthetic_private_validation_asset",
            "approved_for_private_validation": True,
            "approved_for_public_use": False,
            "contains_private_data": False,
            "notes": "Synthetic process asset. Not approved for public posting until manually reviewed.",
            "asset_variant": "process_visual",
            "visual_strength_score": 4,
            "best_for_scene_position": ["process"],
            "allowed_reuse_count": 2,
            "allow_single_asset_private_validation": False,
            "payoff_strength": "medium",
            "visual_notes": "Shows meetings appearing sequentially on calendar grid."
        },
        {
            "asset_id": "calendar_agent_conflict_fix_001",
            "file_path": "assets/proof_capture/calendar_agent/calendar_agent_conflict_fix_001.mp4",
            "project": "calendar_agent",
            "descriptor": "Conflict warnings disappearing and a rescheduled block being placed in the best slot",
            "keywords": ["calendar", "conflict", "fix", "reschedule", "slots", "resolved"],
            "supported_scene_roles": ["proof", "payoff"],
            "supported_topics": ["ai_tools", "productivity", "calendar automation", "AI agent schedules your entire week"],
            "duration_seconds": 6.0,
            "orientation": "vertical_or_crop_safe",
            "source_type": "synthetic_private_validation_asset",
            "approved_for_private_validation": True,
            "approved_for_public_use": False,
            "contains_private_data": False,
            "notes": "Synthetic conflict fix asset. Not approved for public posting until manually reviewed.",
            "asset_variant": "proof_visual",
            "visual_strength_score": 5,
            "best_for_scene_position": ["proof", "payoff"],
            "allowed_reuse_count": 2,
            "allow_single_asset_private_validation": False,
            "payoff_strength": "medium",
            "visual_notes": "Shows conflict banner resolving and study block moving."
        },
        {
            "asset_id": "calendar_agent_final_payoff_001",
            "file_path": "assets/proof_capture/calendar_agent/calendar_agent_final_payoff_001.mp4",
            "project": "calendar_agent",
            "descriptor": "Completed weekly schedule with a large readable WEEK PLANNED banner",
            "keywords": ["calendar", "schedule", "week", "planned", "payoff", "booked"],
            "supported_scene_roles": ["payoff"],
            "supported_topics": ["ai_tools", "productivity", "calendar automation", "AI agent schedules your entire week"],
            "duration_seconds": 7.0,
            "orientation": "vertical_or_crop_safe",
            "source_type": "synthetic_private_validation_asset",
            "approved_for_private_validation": True,
            "approved_for_public_use": False,
            "contains_private_data": False,
            "notes": "Synthetic final payoff asset. Approved for private validation fallback if requested.",
            "asset_variant": "final_result_visual",
            "visual_strength_score": 5,
            "best_for_scene_position": ["final_payoff", "last_3_seconds"],
            "allowed_reuse_count": 2,
            "allow_single_asset_private_validation": True,
            "payoff_strength": "strong",
            "visual_notes": "Shows fully planned week with WEEK PLANNED overlay."
        }
    ]
    
    # Save individual sidecars
    for meta in assets_metadata:
        sidecar_path = os.path.join(output_dir, f"{meta['asset_id']}.json")
        with open(sidecar_path, "w", encoding="utf-8") as sf:
            json.dump(meta, sf, indent=2)
        print(f"Wrote sidecar file: {sidecar_path}")
        
    # Write to registry assets/proof_capture/proof_assets.json
    registry_path = os.path.join("assets", "proof_capture", "proof_assets.json")
    registry = {"assets": assets_metadata}
    with open(registry_path, "w", encoding="utf-8") as rf:
        json.dump(registry, rf, indent=2)
    print(f"Updated registry file: {registry_path}")
    
    print("--- Finished proof asset generation ---")
    sys.exit(0)

if __name__ == "__main__":
    main()
