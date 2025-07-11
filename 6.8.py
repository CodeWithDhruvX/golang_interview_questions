import os
import subprocess
import json
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import logging
from faster_whisper import WhisperModel
import ffmpeg

logging.basicConfig(level=logging.INFO, format="🔹 %(message)s")

with open("video_titles.json", "r", encoding="utf-8") as f:
    VIDEO_TITLE_MAP = json.load(f)

class Word:
    def __init__(self, word, start, end):
        self.word = word
        self.start = float(start)
        self.end = float(end)

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds * 100) % 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"

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

def transcribe_audio(audio_path):
    logging.info(f"🧠 Transcribing: {audio_path}")
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, beam_size=5, word_timestamps=True, language="en")
    # hindi to english version
    # segments, _ = model.transcribe(audio_path,task="translate", beam_size=5, word_timestamps=True, language=hi")
    words = []
    for segment in segments:
        for w in segment.words:
            if w.word.strip():
                words.append({"word": w.word.strip(), "start": w.start, "end": w.end})
    return words

def generate_ass(words, ass_path):
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: One Word at a Time Subs
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,24,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text

""")
        for w in words:
            word = w["word"].strip().upper()
            start = w["start"]
            end = w["end"]
            if not word:
                continue
            text = f"{{\\fad(100,100)\\c&HFFFFFF&}}{word}"
            f.write(f"Dialogue: 0,{format_time(start)},{format_time(end)},Default,,0,0,0,,{text}\n")

def get_title_for_video(input_video):
    for entry in VIDEO_TITLE_MAP:
        if os.path.normpath(entry["slide_topic"]) == os.path.normpath(input_video):
            return entry["title_text"]
    return "Go Routines Simplified"

def generate_hello_world_ass(ass_path, video_duration, title_text):
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: Hello World Overlay
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: HelloStyle,Impact,18,&H000000FF,&H00FFFF00,-1,0,0,0,100,100,0,0,1,3,0,8,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        f.write(f"Dialogue: 0,{format_time(0)},{format_time(15)},HelloStyle,,0,0,0,,{title_text.upper()}\n")

def convert_to_ts(video_path, output_ts):
    ffmpeg.input(video_path).output(output_ts, format="mpegts", vcodec="libx264", acodec="aac", strict="experimental").run(overwrite_output=True)

def merge_with_extra(main_video, extra_video, final_output):
    ts1 = "temp1.ts"
    ts2 = "temp2.ts"

    convert_to_ts(main_video, ts1)
    convert_to_ts(extra_video, ts2)

    ffmpeg.input(f"concat:{ts1}|{ts2}", format="mpegts").output(final_output, vcodec="copy", acodec="copy").run(overwrite_output=True)

    os.remove(ts1)
    os.remove(ts2)

def process_video(input_video, output_video, extra_video):
    base_name = Path(input_video).stem
    auto_edited = f"auto_{base_name}.mp4"
    audio_path = f"temp_{base_name}.wav"
    ass_path = f"subtitles_{base_name}.ass"
    hello_ass_path = f"hello_world_{base_name}.ass"
    final_with_subs = f"final_subs_{base_name}.mp4"

    try:
        logging.info(f"⚙️ Auto-editing: {input_video}")
        subprocess.run([
            "auto-editor", input_video, "-o", auto_edited,
            "--no-open", "--frame-rate", "30", "--silent-speed", "99999"
        ], check=True)

        logging.info(f"🔊 Extracting audio from: {auto_edited}")
        subprocess.run([
            "ffmpeg", "-y", "-i", auto_edited, "-vn",
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path
        ], check=True)

        words = transcribe_audio(audio_path)
        generate_ass(words, ass_path)

        duration = get_video_duration(auto_edited)
        title_text = get_title_for_video(input_video)
        generate_hello_world_ass(hello_ass_path, duration, title_text)

        logging.info("🎬 Burning subtitles and overlaying title...")
        subprocess.run([
            "ffmpeg", "-y", "-i", auto_edited,
            "-filter_complex", f"ass={ass_path},ass={hello_ass_path}",
            "-map", "0:a", "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-shortest", final_with_subs
        ], check=True)

        # Merge with extra video
        merge_with_extra(final_with_subs, extra_video, output_video)

        logging.info(f"✅ Done: {output_video}")

    except Exception as e:
        logging.error(f"❌ Failed processing {input_video}: {e}")
    finally:
        for temp_file in [audio_path, ass_path, hello_ass_path, auto_edited, final_with_subs]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

def main():
    root = tk.Tk()
    root.withdraw()

    input_videos = filedialog.askopenfilenames(title="Select Main Input Videos", filetypes=[("Video Files", "*.mp4 *.mov *.mkv")])
    if not input_videos:
        logging.warning("⚠️ No main videos selected.")
        return

    extra_video = filedialog.askopenfilename(title="Select Extra Video to Merge", filetypes=[("Video Files", "*.mp4 *.mov *.mkv")])
    if not extra_video:
        logging.warning("⚠️ No extra video selected.")
        return

    output_dir = filedialog.askdirectory(title="Select Output Folder")
    if not output_dir:
        logging.warning("⚠️ No output folder selected.")
        return

    for input_video in input_videos:
        base = Path(input_video).stem
        output_path = os.path.join(output_dir, f"{base}_final.mp4")
        process_video(input_video, output_path, extra_video)

    logging.info("🎉 All videos processed and merged!")

if __name__ == "__main__":
    main()
