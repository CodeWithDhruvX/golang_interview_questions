import os
import subprocess
import json
import tkinter as tk
from tkinter import filedialog, simpledialog
from pathlib import Path
import logging
from faster_whisper import WhisperModel
import ffmpeg
import re

logging.basicConfig(level=logging.INFO, format="🔹 %(message)s")

with open("video_titles.json", "r", encoding="utf-8") as f:
    VIDEO_TITLE_MAP = json.load(f)

class Word:
    def __init__(self, word, start, end):
        self.word = word
        self.start = float(start)
        self.end = float(end)

class SubtitleGroup:
    def __init__(self, words, start, end, text):
        self.words = words
        self.start = start
        self.end = end
        self.text = text

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds * 100) % 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"

def format_srt_time(seconds):
    """Format time for SRT format"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds * 1000) % 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def get_video_duration(file_path):
    result = subprocess.run([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'json', file_path
    ], capture_output=True, text=True, check=True)
    duration_json = json.loads(result.stdout)
    return float(duration_json["format"]["duration"])

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

def group_words_into_subtitles(words, max_words_per_group=4, max_duration=3.0):
    """Group words into subtitle segments for better readability"""
    if not words:
        return []
    
    groups = []
    current_group = []
    current_start = words[0]["start"]
    
    for word in words:
        current_group.append(word)
        
        # Check if we should end this group
        group_duration = word["end"] - current_start
        should_end_group = (
            len(current_group) >= max_words_per_group or
            group_duration >= max_duration or
            word["word"].endswith(('.', '!', '?', ','))
        )
        
        if should_end_group:
            if current_group:
                text = " ".join([w["word"] for w in current_group])
                groups.append(SubtitleGroup(
                    words=current_group.copy(),
                    start=current_start,
                    end=word["end"],
                    text=text
                ))
                current_group = []
                # Start next group
                next_word_idx = words.index(word) + 1
                if next_word_idx < len(words):
                    current_start = words[next_word_idx]["start"]
    
    # Handle remaining words
    if current_group:
        text = " ".join([w["word"] for w in current_group])
        groups.append(SubtitleGroup(
            words=current_group,
            start=current_start,
            end=current_group[-1]["end"],
            text=text
        ))
    
    return groups

def generate_individual_word_ass(words, ass_path):
    """Generate ASS file for individual word highlighting (like your original code)"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: One Word at a Time Subs
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H64000000,-1,0,0,0,100,100,0,0,1,3,3,2,50,50,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text

""")
        for w in words:
            word = w["word"].strip().upper()
            start = w["start"]
            end = w["end"]
            if not word:
                continue
            text = f"{{\\fad(100,100)}}{word}"
            f.write(f"Dialogue: 0,{format_time(start)},{format_time(end)},Default,,0,0,0,,{text}\n")

def generate_highlighted_subtitle_ass(subtitle_groups, ass_path):
    """Generate ASS file for dark box subtitles matching the image style"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: Dark Box Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: DarkBox,Arial,40,&H00FFFFFF,&HFF000000,0,0,0,0,100,100,4,0,3,8,0,2,100,100,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text

""")
        for group in subtitle_groups:
            # Create dark box effect - thick black border creates the box effect
            # Adding padding with spaces and using thick border
            text = f"{{\\bord16\\3c&H000000&\\4c&H000000&\\shad0\\fad(150,150)}}   {group.text}   "
            f.write(f"Dialogue: 0,{format_time(group.start)},{format_time(group.end)},DarkBox,,0,0,0,,{text}\n")

def create_drawtext_subtitles(subtitle_groups, video_path, output_path):
    """Create subtitles using drawtext filter for dark box effect like in the image"""
    
    # Build drawtext filters for each subtitle group
    drawtext_filters = []
    
    for i, group in enumerate(subtitle_groups):
        # Create dark box background with white text
        text_escaped = group.text.replace("'", "\\'").replace(":", "\\:")
        
        # Dark box with white text - this creates the exact effect from your image
        drawtext_filter = (
            f"drawtext=text='{text_escaped}'"
            f":fontsize=36"
            f":fontcolor=white"
            f":box=1"
            f":boxcolor=black@0.8"
            f":boxborderw=20"
            f":x=(w-text_w)/2"
            f":y=h-text_h-60"
            f":enable='between(t,{group.start:.2f},{group.end:.2f})'"
        )
        drawtext_filters.append(drawtext_filter)
    
    # Combine all drawtext filters
    if drawtext_filters:
        filter_complex = ",".join(drawtext_filters)
        
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", video_path,
                "-filter_complex", filter_complex,
                "-map", "0:a", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                "-c:a", "copy", "-shortest", output_path
            ], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.warning(f"Drawtext method failed: {e}")
            return False
    return False

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
Style: HelloStyle,Arial,64,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,3,2,8,20,20,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        f.write(f"Dialogue: 0,{format_time(0)},{format_time(15)},HelloStyle,,0,0,0,,{title_text.upper()}\n")

def create_speech_segments_advanced(words, video_duration, merge_gap=0.5, fade_buffer=0.3, min_segment_duration=0.5):
    """Improved speech detection with better merging and fade handling"""
    if not words:
        return []
    
    # Sort words by start time
    sorted_words = sorted(words, key=lambda x: x["start"])
    segments = []
    
    # Initial grouping
    current_start = sorted_words[0]["start"]
    current_end = sorted_words[0]["end"]
    
    for word in sorted_words[1:]:
        gap = word["start"] - current_end
        
        if gap <= merge_gap:
            # Extend current segment
            current_end = max(current_end, word["end"])
        else:
            # Close current segment and start new one
            if current_end - current_start >= min_segment_duration:
                segments.append((current_start, current_end))
            current_start = word["start"]
            current_end = word["end"]
    
    # Add final segment
    if current_end - current_start >= min_segment_duration:
        segments.append((current_start, current_end))
    
    # Apply fade buffers and merge overlapping segments
    buffered_segments = []
    for start, end in segments:
        buffered_start = max(0, start - fade_buffer)
        buffered_end = min(video_duration, end + fade_buffer)
        buffered_segments.append((buffered_start, buffered_end))
    
    # Merge overlapping buffered segments
    if not buffered_segments:
        return []
    
    merged_segments = [buffered_segments[0]]
    for start, end in buffered_segments[1:]:
        last_start, last_end = merged_segments[-1]
        
        if start <= last_end:
            # Merge overlapping segments
            merged_segments[-1] = (last_start, max(last_end, end))
        else:
            merged_segments.append((start, end))
    
    return merged_segments

def add_background_music_with_advanced_ducking(video_path, music_path, output_path, words, 
                                               music_volume=0.12, ducked_volume=0.04):
    """Enhanced audio ducking with reliable volume control"""
    video_duration = get_video_duration(video_path)
    speech_segments = create_speech_segments_advanced(words, video_duration)

    if not speech_segments:
        logging.info("No speech detected, adding background music at normal volume")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-i", music_path,
            "-filter_complex",
            f"[1:a]aloop=loop=-1:size=2e+09,volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", output_path
        ], check=True)
        return

    # Create simple but effective ducking using volume keyframes
    volume_expressions = []
    
    # Start with normal volume
    current_volume = music_volume
    
    for start, end in speech_segments:
        # Ensure we have valid time ranges
        if start >= end or start < 0 or end > video_duration:
            continue
            
        # Duck down during speech
        volume_expressions.append(f"between(t,{start:.2f},{end:.2f})*{ducked_volume}")
        
    # Create the volume filter expression
    if volume_expressions:
        # Base volume when not speaking
        volume_expr = f"{music_volume}"
        # Add ducking for each speech segment
        for expr in volume_expressions:
            volume_expr = f"if({expr},{ducked_volume},{volume_expr})"
    else:
        volume_expr = str(music_volume)

    # Simplified filter chain
    filter_complex = f"[1:a]aloop=loop=-1:size=2e+09,volume='{volume_expr}'[bg];[0:a][bg]amix=inputs=2:duration=first:weights='1.0 0.8'[aout]"

    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-i", music_path,
            "-filter_complex", filter_complex,
            "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", output_path
        ], check=True)
    except subprocess.CalledProcessError as e:
        logging.warning(f"Advanced ducking failed, falling back to simple method: {e}")
        # Fallback to simple ducking
        add_background_music_simple(video_path, music_path, output_path, words, music_volume, ducked_volume)

def add_background_music_simple(video_path, music_path, output_path, words, music_volume=0.12, ducked_volume=0.04):
    """Simple and reliable background music with basic ducking"""
    video_duration = get_video_duration(video_path)
    speech_segments = create_speech_segments_advanced(words, video_duration)

    if not speech_segments:
        logging.info("No speech segments found, using constant background music")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-i", music_path,
            "-filter_complex",
            f"[1:a]aloop=loop=-1:size=2e+09,volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first[aout]",
            "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", output_path
        ], check=True)
        return

    # Use simple segment-based ducking
    try:
        # Create a simpler ducking approach using compand
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-i", music_path,
            "-filter_complex",
            f"[1:a]aloop=loop=-1:size=2e+09,volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first,compand=attacks=0.1:decays=0.2:points=-80/-80|-20/-20|-10/-10|0/-3[aout]",
            "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", output_path
        ], check=True)
    except subprocess.CalledProcessError:
        # Final fallback - basic mix without ducking
        logging.warning("Ducking failed, using basic mix")
        avg_volume = (music_volume + ducked_volume) / 2
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-i", music_path,
            "-filter_complex",
            f"[1:a]aloop=loop=-1:size=2e+09,volume={avg_volume}[bg];[0:a][bg]amix=inputs=2:duration=first[aout]",
            "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", output_path
        ], check=True)

def process_video(input_video, output_video, background_music=None, subtitle_style="highlighted"):
    """
    Process video with options for subtitle style:
    - 'individual': One word at a time (original style)
    - 'highlighted': Grouped words with highlighted box (like your image)
    - 'both': Both styles layered
    """
    base_name = Path(input_video).stem  
    auto_edited = f"auto_{base_name}.mp4"
    audio_path = f"temp_{base_name}.wav"
    individual_ass_path = f"individual_{base_name}.ass"
    highlighted_ass_path = f"highlighted_{base_name}.ass"
    hello_ass_path = f"hello_world_{base_name}.ass"
    final_with_subs = f"final_subs_{base_name}.mp4"
    final_with_music = f"final_music_{base_name}.mp4"

    try:
        logging.info(f"⚙️ Auto-editing: {input_video}")
        subprocess.run([
            "auto-editor", input_video, "-o", auto_edited,
            "--no-open", "--frame-rate", "30", "--silent-speed", "99999"
        ], check=True)

        logging.info(f"🔊 Extracting audio")
        subprocess.run([
            "ffmpeg", "-y", "-i", auto_edited, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path
        ], check=True)

        # Transcribe and generate subtitles
        words = transcribe_audio(audio_path)
        subtitle_groups = []
        
        # Generate different subtitle styles
        if subtitle_style in ["individual", "both"]:
            generate_individual_word_ass(words, individual_ass_path)
        
        if subtitle_style in ["highlighted", "both"]:
            subtitle_groups = group_words_into_subtitles(words)
            generate_highlighted_subtitle_ass(subtitle_groups, highlighted_ass_path)

        # Generate title overlay
        duration = get_video_duration(auto_edited)
        title_text = get_title_for_video(input_video)
        generate_hello_world_ass(hello_ass_path, duration, title_text)

        # Build filter complex for subtitle burning
        logging.info("🎬 Burning subtitles and overlay")
        
        # Try drawtext method first for highlighted subtitles (more reliable for dark boxes)
        if subtitle_style == "highlighted" and subtitle_groups:
            success = create_drawtext_subtitles(subtitle_groups, auto_edited, final_with_subs)
            if not success:
                logging.info("Drawtext failed, falling back to ASS subtitles")
                # Fallback to ASS method
                filter_complex = f"subtitles={highlighted_ass_path},subtitles={hello_ass_path}"
                subprocess.run([
                    "ffmpeg", "-y", "-i", auto_edited,
                    "-filter_complex", filter_complex,
                    "-map", "0:a", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", final_with_subs
                ], check=True)
        else:
            # Use ASS method for other styles
            if subtitle_style == "individual":
                filter_complex = f"subtitles={individual_ass_path},subtitles={hello_ass_path}"
            elif subtitle_style == "both":
                filter_complex = f"subtitles={highlighted_ass_path},subtitles={individual_ass_path},subtitles={hello_ass_path}"
            else:
                filter_complex = f"subtitles={hello_ass_path}"
            
            subprocess.run([
                "ffmpeg", "-y", "-i", auto_edited,
                "-filter_complex", filter_complex,
                "-map", "0:a", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                "-c:a", "aac", "-b:a", "192k", "-shortest", final_with_subs
            ], check=True)

        # Add background music with improved ducking
        if background_music and os.path.exists(background_music):
            logging.info("🎵 Adding background music with ducking")
            add_background_music_with_advanced_ducking(
                final_with_subs, background_music, final_with_music, words
            )
            os.rename(final_with_music, output_video)
        else:
            os.rename(final_with_subs, output_video)

        logging.info(f"✅ Done: {output_video}")
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        raise
    finally:
        # Cleanup temporary files
        temp_files = [
            audio_path, individual_ass_path, highlighted_ass_path, 
            hello_ass_path, auto_edited, final_with_subs, final_with_music
        ]
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass

def main():
    root = tk.Tk()
    root.withdraw()

    # Get input videos
    input_videos = filedialog.askopenfilenames(
        title="Select Input Videos", 
        filetypes=[("Video Files", "*.mp4 *.mov *.mkv *.avi")]
    )
    if not input_videos:
        logging.warning("⚠️ No videos selected.")
        return

    # Get background music
    background_music = filedialog.askopenfilename(
        title="Select Background Music (Optional)", 
        filetypes=[("Audio Files", "*.mp3 *.wav *.aac *.m4a *.ogg *.flac")]
    )
    if background_music:
        logging.info(f"🎵 Music: {os.path.basename(background_music)}")
    else:
        logging.info("🔇 No background music selected")

    # Get output directory
    output_dir = filedialog.askdirectory(title="Select Output Folder")
    if not output_dir:
        logging.warning("⚠️ No output folder selected.")
        return

    # Ask for subtitle style
    style_root = tk.Tk()
    style_root.withdraw()
    
    subtitle_style = tk.simpledialog.askstring(
        "Subtitle Style",
        "Choose subtitle style:\n- 'individual' (one word at a time)\n- 'highlighted' (grouped with box highlight)\n- 'both' (layered styles)",
        initialvalue="highlighted"
    )
    
    style_root.destroy()
    
    if subtitle_style not in ["individual", "highlighted", "both"]:
        subtitle_style = "highlighted"
    
    logging.info(f"🎨 Using subtitle style: {subtitle_style}")

    # Process each video
    for i, input_video in enumerate(input_videos, 1):
        logging.info(f"📹 Processing video {i}/{len(input_videos)}: {os.path.basename(input_video)}")
        base = Path(input_video).stem
        output_path = os.path.join(output_dir, f"{base}_final.mp4")
        
        try:
            process_video(input_video, output_path, background_music, subtitle_style)
        except Exception as e:
            logging.error(f"❌ Failed to process {input_video}: {e}")
            continue

    logging.info("🎉 All videos processed!")

if __name__ == "__main__":
    main()