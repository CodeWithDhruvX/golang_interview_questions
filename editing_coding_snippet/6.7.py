import os
import subprocess
import json
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import logging
import ffmpeg
import re

logging.basicConfig(level=logging.INFO, format="🔹 %(message)s")

VIDEO_TITLE_MAP = []
try:
    with open("video_titles.json", "r", encoding="utf-8") as f:
        VIDEO_TITLE_MAP = json.load(f)
except FileNotFoundError:
    logging.warning("⚠️ 'video_titles.json' not found. Using default title.")

def format_time_for_ass(seconds):
    """Format time for ASS subtitle format (H:MM:SS.CC)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds * 100) % 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def parse_time_from_ass(time_str):
    """Parse time string back to seconds"""
    parts = time_str.split(':')
    if len(parts) == 3:
        h = int(parts[0])
        m = int(parts[1])
        s_parts = parts[2].split('.')
        s = int(s_parts[0])
        cs = int(s_parts[1]) if len(s_parts) > 1 else 0
        return h * 3600 + m * 60 + s + cs / 100
    return 0

def get_video_duration(file_path):
    """Get video duration using ffprobe"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'json', file_path
        ], capture_output=True, text=True, check=True)
        duration_json = json.loads(result.stdout)
        return float(duration_json["format"]["duration"])
    except Exception as e:
        logging.error(f"Failed to get video duration: {e}")
        raise

def find_matching_transcript(video_path):
    """Find matching transcript file for a video"""
    video_name = Path(video_path).stem
    video_dir = Path(video_path).parent
    
    # Common transcript filename patterns
    possible_names = [
        f"{video_name}_transcript.txt",
        f"{video_name}.txt",
        "transcript.txt"
    ]
    
    # Look for transcript file in the same directory as the video
    for name in possible_names:
        transcript_path = video_dir / name
        if transcript_path.exists():
            return str(transcript_path)
    
    # Look for any transcript file in the video directory
    for file in video_dir.glob("*transcript*.txt"):
        return str(file)
    
    return None

def load_transcript_with_timestamps(transcript_file, video_file):
    """Load transcript and add timestamps if needed"""
    lines = []
    
    if not os.path.exists(transcript_file):
        logging.error(f"Transcript file not found: {transcript_file}")
        return []
    
    with open(transcript_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if transcript already has timestamps
    if "-->" in content:
        logging.info("📝 Loading transcript with existing timestamps...")
        for line in content.strip().splitlines():
            if line.startswith("[") and "]" in line:
                try:
                    time_part, text = line.split("]", 1)
                    time_range = time_part[1:]  # Remove the opening bracket
                    if "-->" in time_range:
                        start, end = time_range.split("-->")
                        lines.append({
                            "start": start.strip(),
                            "end": end.strip(),
                            "text": text.strip()
                        })
                except ValueError:
                    continue
    else:
        # Generate timestamps using whisper_timestamped or fallback method
        logging.info("📝 Transcript has no timestamps, generating them...")
        
        # Try to use whisper_timestamped if available
        try:
            lines = generate_timestamps_with_whisper(transcript_file, video_file)
        except Exception as e:
            logging.warning(f"Whisper timestamped failed: {e}")
            logging.info("📝 Using fallback timestamp generation...")
            lines = generate_fallback_timestamps(content)

    return lines

def generate_timestamps_with_whisper(transcript_file, video_file):
    """Generate timestamps using whisper_timestamped"""
    lines = []
    audio_file = transcript_file.replace(".txt", "_temp.wav")
    
    try:
        # Extract audio from video
        logging.info(f"🔊 Extracting audio from video: {video_file}")
        ffmpeg.input(video_file).output(
            audio_file, 
            acodec='pcm_s16le', 
            ac=1, 
            ar='16000'
        ).run(overwrite_output=True, quiet=True)
        
        # Run whisper_timestamped
        logging.info("🧠 Running whisper_timestamped...")
        output_dir = os.path.dirname(transcript_file) or "."
        
        result = subprocess.run([
            "whisper_timestamped", audio_file,
            "--output_dir", output_dir,
            "--output_format", "json",
            "--model", "base",
            "--language", "en"
        ], capture_output=True, text=True, check=True)
        
        # Find the output JSON file
        base_name = Path(audio_file).stem
        json_output = os.path.join(output_dir, f"{base_name}.json")
        
        if os.path.exists(json_output):
            with open(json_output, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                for seg in data.get("segments", []):
                    lines.append({
                        "start": format_time_for_ass(seg["start"]),
                        "end": format_time_for_ass(seg["end"]),
                        "text": seg["text"].strip()
                    })
            # Clean up JSON file
            os.remove(json_output)
        else:
            raise Exception("Whisper output not found")
            
    except Exception as e:
        logging.error(f"Whisper timestamped failed: {e}")
        raise
    finally:
        # Clean up audio file
        if os.path.exists(audio_file):
            os.remove(audio_file)
    
    return lines

def generate_fallback_timestamps(content):
    """Generate simple timestamps based on text length"""
    lines = []
    text_lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    
    # Calculate duration per line based on text length
    for i, text in enumerate(text_lines):
        # Estimate 3 seconds per line + additional time for longer lines
        base_duration = 3.0
        char_bonus = len(text) * 0.05  # 0.05 seconds per character
        line_duration = base_duration + char_bonus
        
        start_time = i * base_duration
        end_time = start_time + line_duration
        
        lines.append({
            "start": format_time_for_ass(start_time),
            "end": format_time_for_ass(end_time),
            "text": text
        })
    
    return lines

def generate_ass_from_transcript(transcript_lines, ass_path):
    """Generate ASS subtitle file from transcript lines"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: Transcript Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,30,30,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        for line in transcript_lines:
            # Escape special characters for ASS format
            text = line['text'].replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
            f.write(f"Dialogue: 0,{line['start']},{line['end']},Default,,0,0,0,,{text}\n")

def get_title_for_video(input_video):
    """Get title for video from mapping file"""
    for entry in VIDEO_TITLE_MAP:
        if os.path.normpath(entry.get("slide_topic", "")) == os.path.normpath(input_video):
            return entry.get("title_text", "Go Routines Simplified")
    return "Go Routines Simplified"

def generate_hello_world_ass(ass_path, video_duration, title_text):
    """Generate ASS file for title overlay"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: Title Overlay
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitleStyle,Impact,24,&H000000FF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,0,8,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        title_escaped = title_text.upper().replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
        f.write(f"Dialogue: 0,{format_time_for_ass(0)},{format_time_for_ass(15)},TitleStyle,,0,0,0,,{title_escaped}\n")

def convert_to_ts(video_path, output_ts):
    """Convert video to MPEG-TS format for concatenation"""
    try:
        ffmpeg.input(video_path).output(
            output_ts, 
            format="mpegts", 
            vcodec="libx264", 
            acodec="aac", 
            strict="experimental"
        ).run(overwrite_output=True, quiet=True)
    except Exception as e:
        logging.error(f"Failed to convert to TS: {e}")
        raise

def merge_with_extra(main_video, extra_video, final_output):
    """Merge main video with extra video"""
    ts1 = "temp1.ts"
    ts2 = "temp2.ts"

    try:
        logging.info("🔄 Converting videos to TS format...")
        convert_to_ts(main_video, ts1)
        convert_to_ts(extra_video, ts2)

        logging.info("🔗 Concatenating videos...")
        ffmpeg.input(f"concat:{ts1}|{ts2}", format="mpegts").output(
            final_output, 
            vcodec="copy", 
            acodec="copy"
        ).run(overwrite_output=True, quiet=True)

    finally:
        # Clean up temporary files
        for temp_file in [ts1, ts2]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

def process_video(input_video, output_video, extra_video):
    """Process a single video with subtitles and title overlay"""
    base_name = Path(input_video).stem
    ass_path = f"subtitles_{base_name}.ass"
    hello_ass_path = f"hello_world_{base_name}.ass"
    final_with_subs = f"final_subs_{base_name}.mp4"

    try:
        # Find matching transcript file
        transcript_file = find_matching_transcript(input_video)
        if not transcript_file:
            logging.error(f"No transcript file found for video: {input_video}")
            logging.info("Expected transcript file patterns:")
            logging.info(f"  - {base_name}_transcript.txt")
            logging.info(f"  - {base_name}.txt")
            logging.info(f"  - transcript.txt")
            return

        logging.info(f"📝 Found transcript: {transcript_file}")
        transcript_lines = load_transcript_with_timestamps(transcript_file, input_video)
        
        if not transcript_lines:
            logging.error("No transcript lines found!")
            return

        generate_ass_from_transcript(transcript_lines, ass_path)
        logging.info(f"✅ Generated subtitle file: {ass_path}")

        duration = get_video_duration(input_video)
        title_text = get_title_for_video(input_video)
        generate_hello_world_ass(hello_ass_path, duration, title_text)
        logging.info(f"✅ Generated title overlay: {hello_ass_path}")

        logging.info("🎨 Burning subtitles and overlaying title...")
        
        # Escape paths for ffmpeg
        ass_path_escaped = ass_path.replace('\\', '/').replace(':', '\\:')
        hello_ass_path_escaped = hello_ass_path.replace('\\', '/').replace(':', '\\:')
        
        # Use ffmpeg command with proper subtitle burning
        cmd = [
            "ffmpeg", "-y", "-i", input_video,
            "-vf", f"ass={ass_path_escaped},ass={hello_ass_path_escaped}",
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-shortest", final_with_subs
        ]
        
        logging.info("Running FFmpeg command...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"FFmpeg error: {result.stderr}")
            # Try alternative approach with subtitles filter
            logging.info("Trying alternative subtitle approach...")
            cmd_alt = [
                "ffmpeg", "-y", "-i", input_video,
                "-filter_complex", f"[0:v]subtitles={ass_path_escaped}:force_style='Fontsize=20'[v1];[v1]subtitles={hello_ass_path_escaped}[v2]",
                "-map", "[v2]", "-map", "0:a",
                "-c:v", "libx264", "-crf", "23", "-preset", "fast",
                "-c:a", "aac", final_with_subs
            ]
            result = subprocess.run(cmd_alt, capture_output=True, text=True)
            
            if result.returncode != 0:
                logging.error(f"Alternative FFmpeg also failed: {result.stderr}")
                raise Exception(f"FFmpeg failed with return code {result.returncode}")

        if not os.path.exists(final_with_subs):
            raise Exception("Subtitle burning failed - output file not created")

        logging.info("🔗 Merging with extra video...")
        merge_with_extra(final_with_subs, extra_video, output_video)

        logging.info(f"✅ Done: {output_video}")

    except Exception as e:
        logging.error(f"❌ Failed processing {input_video}: {e}")
        raise
    finally:
        # Clean up temporary files
        for temp_file in [ass_path, hello_ass_path, final_with_subs]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

def main():
    """Main function to handle GUI and process videos"""
    root = tk.Tk()
    root.withdraw()

    input_videos = filedialog.askopenfilenames(
        title="Select Main Input Videos", 
        filetypes=[("Video Files", "*.mp4 *.mov *.mkv *.avi")]
    )
    if not input_videos:
        logging.warning("⚠️ No main videos selected.")
        return

    extra_video = filedialog.askopenfilename(
        title="Select Extra Video to Merge", 
        filetypes=[("Video Files", "*.mp4 *.mov *.mkv *.avi")]
    )
    if not extra_video:
        logging.warning("⚠️ No extra video selected.")
        return

    output_dir = filedialog.askdirectory(title="Select Output Folder")
    if not output_dir:
        logging.warning("⚠️ No output folder selected.")
        return

    success_count = 0
    total_count = len(input_videos)

    for input_video in input_videos:
        try:
            base = Path(input_video).stem
            output_path = os.path.join(output_dir, f"{base}_final.mp4")
            logging.info(f"🎬 Processing video ({success_count + 1}/{total_count}): {input_video}")
            process_video(input_video, output_path, extra_video)
            success_count += 1
        except Exception as e:
            logging.error(f"❌ Failed to process {input_video}: {e}")
            continue

    logging.info(f"🎉 Processing complete! Successfully processed {success_count}/{total_count} videos.")

if __name__ == "__main__":
    main())



remove the model generation subtitle instead using whisper_timestamped using transcription based plain text file in the above code