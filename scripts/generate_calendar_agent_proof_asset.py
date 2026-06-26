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

def main():
    print("--- Generating Calendar Agent Proof Asset ---")
    
    # 1. Setup Directories
    frames_dir = os.path.join("scratch", "calendar_frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    output_dir = os.path.join("assets", "proof_capture", "calendar_agent")
    os.makedirs(output_dir, exist_ok=True)
    
    output_video_path = os.path.join(output_dir, "calendar_agent_demo_001.mp4")
    
    # Video details
    width, height = 1080, 1920
    fps = 15
    duration_seconds = 7.0
    total_frames = int(fps * duration_seconds) # 105 frames
    
    # Define colors
    bg_color = (18, 18, 24)
    header_bg = (30, 30, 40)
    grid_line_color = (50, 50, 60)
    text_white = (255, 255, 255)
    text_grey = (150, 150, 160)
    
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
    
    # Layout dimensions
    margin_left = 90
    col_width = 180
    grid_top = 380
    grid_bottom = 1500
    grid_height = grid_bottom - grid_top
    
    for f_idx in range(total_frames):
        t = f_idx / fps
        
        # Create base image
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # 1. Draw Header
        draw.rectangle([(0, 0), (width, 240)], fill=header_bg)
        draw.text((width // 2, 70), "AI SCHEDULING AGENT", fill=text_white, font=title_font, anchor="mm")
        draw.text((width // 2, 160), "OPTIMIZING WEEKLY WORKFLOW", fill=(52, 152, 219), font=subtitle_font, anchor="mm")
        
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
            
        # 3. Draw animated schedule blocks
        
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

        # Wed: Conflict Warning (appears at 3.0s, stays until 4.5s)
        if 3.0 <= t < 4.5:
            x0 = margin_left + 2 * col_width + 5
            x1 = x0 + col_width - 10
            y0 = grid_top + 200
            y1 = y0 + 180
            
            # Conflict warnings: Red block
            if t < 4.0:
                draw.rectangle([(x0, y0), (x1, y1)], fill=red_block, outline=text_white, width=2)
                draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "CONFLICT", fill=text_white, font=block_font, anchor="mm")
            else:
                # Flashing yellow/resolving state
                flash = int(f_idx % 4 >= 2)
                bg = yellow_block if flash else red_block
                draw.rectangle([(x0, y0), (x1, y1)], fill=bg, outline=text_white, width=2)
                draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "SOLVING...", fill=text_white if not flash else (0, 0, 0), font=block_font, anchor="mm")
                
        # Wed: Rescheduled study block (appears after 4.5s)
        if t >= 4.5:
            x0 = margin_left + 2 * col_width + 5
            x1 = x0 + col_width - 10
            # Shifted down to a free slot (3 PM)
            y0 = grid_top + 600
            y1 = y0 + 180
            draw.rectangle([(x0, y0), (x1, y1)], fill=green_block, outline=text_white, width=1)
            draw.text(((x0 + x1) // 2, (y0 + y1) // 2), "Study\n(Fixed)", fill=text_white, font=block_font, anchor="mm", align="center")

        # 4. Final Payoff Banner (5.0s to 7.0s)
        if t >= 5.0:
            # Slides up / fades in
            banner_y = max(900, 1100 - int((t - 5.0) * 400))
            
            # Draw semi-transparent background overlay
            overlay_color = (46, 204, 113) # bright green
            draw.rectangle([(100, banner_y - 120), (width - 100, banner_y + 120)], fill=overlay_color, outline=text_white, width=3)
            draw.text((width // 2, banner_y), "WEEK PLANNED", fill=text_white, font=banner_font, anchor="mm")
            
        # Save frame
        frame_name = f"frame_{f_idx:03d}.png"
        frame_path = os.path.join(frames_dir, frame_name)
        img.save(frame_path)
        
    print(f"Successfully generated {total_frames} frames under {frames_dir}")
    
    # 4. Compile into MP4 using ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-r", str(fps),
        "-i", os.path.join(frames_dir, "frame_%03d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_video_path
    ]
    print(f"Compiling video: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"Successfully generated proof video at {output_video_path}")
    else:
        print(f"Error compiling video with ffmpeg: {res.stderr}")
        sys.exit(1)
        
    # 5. Clean up frames
    try:
        shutil.rmtree(frames_dir)
        print("Cleaned up temporary frames folder.")
    except Exception as e:
        print(f"Warning: Failed to delete frames folder: {e}")
        
    sys.exit(0)

if __name__ == "__main__":
    main()
