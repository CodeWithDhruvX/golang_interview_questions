import os
import subprocess
import json
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import logging
import ffmpeg

logging.basicConfig(level=logging.INFO, format="🔹 %(message)s")

VIDEO_TITLE_MAP = []
try:
    with open("video_titles.json", "r", encoding="utf-8") as f:
        VIDEO_TITLE_MAP = json.load(f)
except FileNotFoundError:
    logging.warning("⚠️ 'video_titles.json' not found. Using default title.")

def format_time_for_ass(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds * 100) % 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def get_video_duration(file_path):
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

def load_transcript_with_timestamps(transcript_file, input_video):
    lines = []
    try:
        with open(transcript_file, "r", encoding="utf-8") as f:
            text = f.read().replace("\n", " ").strip()
    except Exception as e:
        logging.error(f"Failed to read transcript: {e}")
        return []

    if not text:
        logging.warning("Transcript is empty.")
        return []

    words = text.split()
    if not words:
        logging.warning("No words found in transcript.")
        return []

    # Group words in chunks of 4
    chunks = [' '.join(words[i:i+4]) for i in range(0, len(words), 4)]

    try:
        video_duration = get_video_duration(input_video)
        duration_per_chunk = video_duration / len(chunks)
    except Exception as e:
        logging.warning(f"Failed to get duration; using default timing. Error: {e}")
        duration_per_chunk = 3.0
        video_duration = duration_per_chunk * len(chunks)

    for i, chunk in enumerate(chunks):
        start_time = i * duration_per_chunk
        end_time = min((i + 1) * duration_per_chunk, video_duration)
        lines.append({
            "start": format_time_for_ass(start_time),
            "end": format_time_for_ass(end_time),
            "text": chunk
        })

    return lines

def generate_ass_from_transcript(transcript_lines, ass_path):
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: One Word at a Time Subs
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,18,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text

""")
        for line in transcript_lines:
            text = line['text'].replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
            f.write(f"Dialogue: 0,{line['start']},{line['end']},Default,,0,0,0,,{text}\n")

def get_title_for_video(input_video):
    for entry in VIDEO_TITLE_MAP:
        if os.path.normpath(entry.get("slide_topic", "")) == os.path.normpath(input_video):
            return entry.get("title_text", "Go Routines Simplified")
    return "Go Routines Simplified"

def generate_hello_world_ass(ass_path, video_duration, title_text):
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

def process_video(input_video, output_video, transcript_folder):
    base_name = Path(input_video).stem
    transcript_file = os.path.join(transcript_folder, f"{base_name}_transcript.txt")
    ass_path = f"subtitles_{base_name}.ass"
    hello_ass_path = f"hello_world_{base_name}.ass"
    final_with_subs = f"final_subs_{base_name}.mp4"

    try:
        if not os.path.exists(transcript_file):
            logging.error(f"Transcript file not found: {transcript_file}")
            return

        logging.info(f"📜 Processing transcript: {transcript_file}")
        transcript_lines = load_transcript_with_timestamps(transcript_file, input_video)
        if not transcript_lines:
            logging.error("No transcript lines found!")
            return

        generate_ass_from_transcript(transcript_lines, ass_path)
        duration = get_video_duration(input_video)
        title_text = get_title_for_video(input_video)
        generate_hello_world_ass(hello_ass_path, duration, title_text)

        ass_path_escaped = ass_path.replace('\\', '/').replace(':', '\\:')
        hello_ass_path_escaped = hello_ass_path.replace('\\', '/').replace(':', '\\:')

        cmd = [
            "ffmpeg", "-y", "-i", input_video,
            "-vf", f"ass={ass_path_escaped},ass={hello_ass_path_escaped}",
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-shortest", final_with_subs
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"FFmpeg error: {result.stderr}")
            return

        os.rename(final_with_subs, output_video)
        logging.info(f"✅ Done: {output_video}")

    finally:
        for temp_file in [ass_path, hello_ass_path, final_with_subs]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

def main():
    root = tk.Tk()
    root.withdraw()

    input_videos = filedialog.askopenfilenames(
        title="Select Videos to Process",
        filetypes=[("Video Files", "*.mp4 *.mov *.mkv")]
    )
    if not input_videos:
        logging.warning("⚠️ No videos selected.")
        return

    transcript_folder = filedialog.askdirectory(title="Select Transcript Folder")
    if not transcript_folder:
        logging.warning("⚠️ No transcript folder selected.")
        return

    output_dir = filedialog.askdirectory(title="Select Output Folder")
    if not output_dir:
        logging.warning("⚠️ No output folder selected.")
        return

    for input_video in input_videos:
        base = Path(input_video).stem
        output_path = os.path.join(output_dir, f"{base}_final.mp4")
        process_video(input_video, output_path, transcript_folder)

    logging.info("🎉 All videos processed!")

if __name__ == "__main__":
    main()
