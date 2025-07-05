import os
import subprocess
import json
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import logging
from faster_whisper import WhisperModel

# Setup logging
logging.basicConfig(level=logging.INFO, format="🔹 %(message)s")


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
    segments, _ = model.transcribe(audio_path, beam_size=5, word_timestamps=True)
    words = []
    for segment in segments:
        for w in segment.words:
            if w.word.strip():
                words.append({"word": w.word.strip(), "start": w.start, "end": w.end})
    return words


def generate_ass(words, ass_path):
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: Animated Subs
ScriptType: v4.00+
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,18,&H00FFFFFF,&H64000000,-1,0,0,0,100,100,0,0,1,2,1,2,20,20,65,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text

""")
        line = []
        max_words_per_line = 3
        max_duration_per_line = 5.0

        def flush():
            nonlocal line
            if not line:
                return
            start = line[0].start
            end = line[-1].end
            text = ""
            for i, w in enumerate(line):
                k_dur = int((w.end - w.start) * 100)
                color = "\\c&HFFFFFF&" if i == 0 else "\\c&H00FFFF&"
                text += f"{{\\fad(200,200)\\k{k_dur}{color}}}{w.word.upper()} "
            f.write(f"Dialogue: 0,{format_time(start)},{format_time(end)},Default,,0,0,0,,{text.strip()}\n")
            line = []

        for w in words:
            if len(line) < max_words_per_line and (not line or w["end"] - line[0].start <= max_duration_per_line):
                line.append(Word(w["word"], w["start"], w["end"]))
            else:
                flush()
                line.append(Word(w["word"], w["start"], w["end"]))
        flush()


def generate_hello_world_ass(ass_path, video_duration):
    start = 0  # Display from start
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
        f.write(f"Dialogue: 0,{format_time(start)},"
                f"{format_time(video_duration)},HelloStyle,,0,0,0,,Go Routines Simplified\n")

def generate_hello_world_ass(ass_path, video_duration):
    start = 0  # Display from start
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: Hello World Overlay
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: HelloStyle,Impact,18,&H00FFFFFF,&H000000FF,-1,0,0,0,100,100,0,0,3,1,0,8,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        f.write(f"Dialogue: 0,{format_time(start)},{format_time(video_duration)},HelloStyle,,0,0,0,,🧪 Go Routines Simplified\n")



def process_video(input_video, output_video):
    base_name = Path(input_video).stem
    audio_path = f"temp_{base_name}.wav"
    ass_path = f"subtitles_{base_name}.ass"
    hello_ass_path = f"hello_world_{base_name}.ass"

    try:
        logging.info(f"🔊 Extracting audio from: {input_video}")
        subprocess.run([
            "ffmpeg", "-y", "-i", input_video, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path
        ], check=True)

        words = transcribe_audio(audio_path)
        generate_ass(words, ass_path)

        duration = get_video_duration(input_video)
        generate_hello_world_ass(hello_ass_path, duration)

        logging.info("🎬 Burning subtitles and overlaying 'Hello World'...")

        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-filter_complex", f"ass={ass_path},ass={hello_ass_path}",
            "-map", "0:a",
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "aac", "-shortest",
            output_video
        ]

        subprocess.run(cmd, check=True)
        logging.info(f"✅ Done: {output_video}")
    except Exception as e:
        logging.error(f"❌ Failed processing {input_video}: {e}")
    finally:
        for temp_file in [audio_path, ass_path, hello_ass_path]:
            if os.path.exists(temp_file):
                os.remove(temp_file)


def main():
    root = tk.Tk()
    root.withdraw()

    input_videos = filedialog.askopenfilenames(
        title="Select Input Videos",
        filetypes=[("Video Files", "*.mp4 *.mov *.mkv")]
    )
    if not input_videos:
        logging.warning("⚠️ No input videos selected.")
        return

    output_dir = filedialog.askdirectory(title="Select Output Folder")
    if not output_dir:
        logging.warning("⚠️ No output folder selected.")
        return

    for input_video in input_videos:
        base = Path(input_video).stem
        output_path = os.path.join(output_dir, f"{base}_subtitled.mp4")
        process_video(input_video, output_path)

    logging.info("🎉 All videos processed!")


if __name__ == "__main__":
    main()
