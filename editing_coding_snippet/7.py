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

def create_speech_segments(words, video_duration, merge_gap=0.8, fade_buffer=0.4):
    """
    Create optimized speech segments for ducking with proper merging.
    
    Args:
        words: List of word dictionaries with 'start' and 'end' timestamps
        video_duration: Total duration of the video
        merge_gap: Maximum gap between words to merge into one segment (seconds)
        fade_buffer: Extra time to add before/after each segment
    
    Returns:
        List of (start, end) tuples for speech segments
    """
    if not words:
        return []
    
    # Sort words by start time
    sorted_words = sorted(words, key=lambda x: x["start"])
    
    # First pass: merge close words
    merged_segments = []
    current_start = sorted_words[0]["start"]
    current_end = sorted_words[0]["end"]
    
    for word in sorted_words[1:]:
        if word["start"] - current_end <= merge_gap:
            current_end = max(current_end, word["end"])
        else:
            merged_segments.append((current_start, current_end))
            current_start = word["start"]
            current_end = word["end"]
    
    merged_segments.append((current_start, current_end))
    
    # Second pass: add buffers and ensure no overlaps
    final_segments = []
    for start, end in merged_segments:
        buffered_start = max(0, start - fade_buffer)
        buffered_end = min(video_duration, end + fade_buffer)
        
        # Merge with previous segment if they overlap after buffering
        if final_segments and buffered_start <= final_segments[-1][1]:
            final_segments[-1] = (final_segments[-1][0], max(final_segments[-1][1], buffered_end))
        else:
            final_segments.append((buffered_start, buffered_end))
    
    return final_segments

def add_background_music_with_ducking(video_path, music_path, output_path, words, music_volume=0.15, ducked_volume=0.04):
    """
    Add background music with proper auto-ducking that actually works.
    
    Args:
        video_path: Path to input video
        music_path: Path to background music file
        output_path: Path for output video
        words: List of word dictionaries with timestamps
        music_volume: Normal background music volume (keep low)
        ducked_volume: Reduced music volume during speech (very low)
    """
    try:
        logging.info("🎵 Adding background music with auto-ducking...")
        
        video_duration = get_video_duration(video_path)
        speech_segments = create_speech_segments(words, video_duration)
        
        if not speech_segments:
            logging.info("No speech detected, adding music at low volume")
            subprocess.run([
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", music_path,
                "-filter_complex", 
                f"[1:a]aloop=loop=-1:size=2e+09,volume={ducked_volume}[bg_music];"
                f"[0:a][bg_music]amix=inputs=2:duration=first:dropout_transition=2,volume=1.0[audio_out]",
                "-map", "0:v",
                "-map", "[audio_out]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                "-shortest",
                output_path
            ], check=True)
            return
        
        logging.info(f"🎯 Speech segments detected: {len(speech_segments)}")
        for i, (start, end) in enumerate(speech_segments):
            logging.info(f"  📍 Segment {i+1}: {start:.2f}s - {end:.2f}s")
        
        # Use a step-by-step approach with multiple volume filters
        filter_parts = []
        
        # Start with the background music at normal (low) volume
        filter_parts.append(f"[1:a]aloop=loop=-1:size=2e+09,volume={music_volume}[bg_normal]")
        
        current_label = "bg_normal"
        
        # Apply ducking for each speech segment
        for i, (start, end) in enumerate(speech_segments):
            next_label = f"bg_step_{i}"
            # This will reduce volume ONLY during this specific time range
            filter_parts.append(
                f"[{current_label}]volume=enable='between(t,{start:.3f},{end:.3f})':volume={ducked_volume/music_volume:.3f}[{next_label}]"
            )
            current_label = next_label
        
        # Mix the processed background with original audio, ensuring original audio dominates
        filter_parts.append(f"[0:a][{current_label}]amix=inputs=2:duration=first:weights='1.0 0.8'[audio_out]")
        
        filter_complex = ";".join(filter_parts)
        
        logging.info("🎛️ Applying step-by-step volume ducking...")
        
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[audio_out]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            output_path
        ], check=True)
        
        logging.info(f"✅ Background music with ducking applied successfully!")
        
    except Exception as e:
        logging.error(f"❌ Ducking failed: {e}")
        # Fallback: add very quiet background music
        logging.info("🔄 Using fallback: very quiet background music")
        try:
            subprocess.run([
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", music_path,
                "-filter_complex", 
                f"[1:a]aloop=loop=-1:size=2e+09,volume=0.03[bg_music];"
                f"[0:a][bg_music]amix=inputs=2:duration=first:weights='1.0 0.5'[audio_out]",
                "-map", "0:v",
                "-map", "[audio_out]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                "-shortest",
                output_path
            ], check=True)
            logging.info("✅ Fallback background music added")
        except Exception as fallback_error:
            logging.error(f"❌ Fallback failed: {fallback_error}")
            raise

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

def process_video(input_video, output_video, extra_video, background_music=None):
    base_name = Path(input_video).stem  
    auto_edited = f"auto_{base_name}.mp4"
    audio_path = f"temp_{base_name}.wav"
    ass_path = f"subtitles_{base_name}.ass"
    hello_ass_path = f"hello_world_{base_name}.ass"
    final_with_subs = f"final_subs_{base_name}.mp4"
    final_with_music = f"final_music_{base_name}.mp4"

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

        # Add background music with proper ducking if provided
        if background_music and os.path.exists(background_music):
            add_background_music_with_ducking(
                final_with_subs, 
                background_music, 
                final_with_music, 
                words,
                music_volume=0.12,     # Low background volume
                ducked_volume=0.03     # Very low during speech
            )
            video_to_merge = final_with_music
        else:
            video_to_merge = final_with_subs

        # Merge with extra video
        merge_with_extra(video_to_merge, extra_video, output_video)

        logging.info(f"✅ Processing complete: {output_video}")

    except Exception as e:
        logging.error(f"❌ Failed processing {input_video}: {e}")
    finally:
        # Clean up temporary files
        temp_files = [audio_path, ass_path, hello_ass_path, auto_edited, final_with_subs]
        if background_music:
            temp_files.append(final_with_music)
        
        for temp_file in temp_files:
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

    # Optional background music selection
    background_music = filedialog.askopenfilename(
        title="Select Background Music (Optional - Cancel to skip)", 
        filetypes=[("Audio Files", "*.mp3 *.wav *.aac *.m4a *.ogg")]
    )
    
    if background_music:
        logging.info(f"🎵 Background music selected: {os.path.basename(background_music)}")
    else:
        logging.info("🔇 No background music selected")

    output_dir = filedialog.askdirectory(title="Select Output Folder")
    if not output_dir:
        logging.warning("⚠️ No output folder selected.")
        return

    for input_video in input_videos:
        base = Path(input_video).stem
        output_path = os.path.join(output_dir, f"{base}_final.mp4")
        process_video(input_video, output_path, extra_video, background_music)

    logging.info("🎉 All videos processed successfully!")

if __name__ == "__main__":
    main()