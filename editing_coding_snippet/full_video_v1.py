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
    """Generate ASS file for individual word highlighting with modern styling"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: One Word at a Time Subs
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: WordHighlight,Segoe UI,54,&H00FFFFFF,&H64000000,-1,0,0,0,100,100,2,0,1,4,2,2,50,50,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text

""")
        for w in words:
            word = w["word"].strip().upper()
            start = w["start"]
            end = w["end"]
            if not word:
                continue
            # Enhanced animation with scale and glow effects
            text = f"{{\\fad(200,200)\\t(\\fscx120\\fscy120)\\t(0.3s,\\fscx100\\fscy100)\\blur2}}{word}"
            f.write(f"Dialogue: 0,{format_time(start)},{format_time(end)},WordHighlight,,0,0,0,,{text}\n")

def generate_animated_rounded_subtitle_ass(subtitle_groups, ass_path):
    """Generate ASS file for breathing/pulsing rounded corner subtitles that stay in position"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: Breathing Rounded Box Subtitles
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: BreathingBox,Arial,38,&H00FFFFFF,&HE0000000,-1,0,0,0,100,100,2,0,3,18,6,2,50,50,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text

""")
        for i, group in enumerate(subtitle_groups):
            duration = group.end - group.start
            fade_in = 0.2
            fade_out = 0.2
            
            # Create breathing animation that stays in the same position
            # The subtitle will grow from 85% to 105% and back continuously
            breathing_cycles = max(1, int(duration * 0.8))  # Number of breathing cycles
            
            text = (
                f"{{\\blur2\\bord22\\3c&H000000&\\4c&H000000&\\shad4\\4a&H60&"
                f"\\pos(960,920)"  # Fixed position - stays in same place
                f"\\fad({int(fade_in*1000)},{int(fade_out*1000)})"
                f"\\t(0,{int((duration/breathing_cycles/2)*1000)},\\fscx105\\fscy105)"  # Grow
                f"\\t({int((duration/breathing_cycles/2)*1000)},{int((duration/breathing_cycles)*1000)},\\fscx95\\fscy95)"  # Shrink
                f"\\t({int((duration/breathing_cycles)*1000)},{int((duration/breathing_cycles*1.5)*1000)},\\fscx105\\fscy105)"  # Grow again
                f"\\t({int((duration/breathing_cycles*1.5)*1000)},{int(duration*1000)},\\fscx100\\fscy100)}}"  # Return to normal
                f"  {group.text}  "
            )
            f.write(f"Dialogue: 0,{format_time(group.start)},{format_time(group.end)},BreathingBox,,0,0,0,,{text}\n")

def create_advanced_drawtext_subtitles(subtitle_groups, video_path, output_path):
    """Create subtitles using drawtext with breathing/pulsing rounded corner animation"""
    
    drawtext_filters = []
    
    for i, group in enumerate(subtitle_groups):
        text_escaped = group.text.replace("'", "\\'").replace(":", "\\:")
        duration = group.end - group.start
        fade_in = min(0.2, duration * 0.1)
        fade_out = min(0.2, duration * 0.1)
        
        # Create breathing/pulsing effect - scale oscillates between 0.95 and 1.05
        # Using sine wave for smooth breathing animation
        scale_factor = "0.95+0.1*sin(2*PI*t*1.2)"  # Breathing at 1.2 Hz
        
        # Advanced drawtext with rounded corners and breathing animation
        drawtext_filter = (
            f"drawtext=text='{text_escaped}'"
            f":fontsize=38*({scale_factor})"  # Font size breathes with scale
            f":fontcolor=white"
            f":box=1"
            f":boxcolor=black@0.88"
            f":boxborderw=20*({scale_factor})"  # Border also breathes
            f":x=(w-text_w)/2"
            f":y=h-120"  # Fixed position - stays in same place
            f":enable='between(t,{group.start:.2f},{group.end:.2f})'"
            f":alpha='if(lt(t,{group.start + fade_in:.2f}),(t-{group.start:.2f})/{fade_in:.2f},if(gt(t,{group.end - fade_out:.2f}),({group.end:.2f}-t)/{fade_out:.2f},1))'"
        )
        drawtext_filters.append(drawtext_filter)
    
    if drawtext_filters:
        filter_complex = ",".join(drawtext_filters)
        
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", video_path,
                "-filter_complex", filter_complex,
                "-map", "0:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-c:a", "copy", "-shortest", output_path
            ], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.warning(f"Advanced drawtext method failed: {e}")
            return False
    return False

def get_title_for_video(input_video):
    for entry in VIDEO_TITLE_MAP:
        if os.path.normpath(entry["slide_topic"]) == os.path.normpath(input_video):
            return entry["title_text"]
    return "Go Routines Simplified"

def generate_animated_title_ass(ass_path, video_duration, title_text):
    """Generate animated title with modern effects"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("""[Script Info]
Title: Animated Title Overlay
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitleStyle,Segoe UI,72,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,4,0,1,6,4,8,40,40,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        # Animated title with slide-in from left and glow effect
        animated_title = (
            f"{{\\move(-400,200,960,200,0,1500)\\fad(500,1000)"
            f"\\t(0,1500,\\fscx120\\fscy120\\blur2)"
            f"\\t(12000,15000,\\fscx100\\fscy100\\blur4)}}"
            f"{title_text.upper()}"
        )
        f.write(f"Dialogue: 0,{format_time(0)},{format_time(15)},TitleStyle,,0,0,0,,{animated_title}\n")

def create_speech_segments_advanced(words, video_duration, merge_gap=0.5, fade_buffer=0.3, min_segment_duration=0.5):
    """Improved speech detection with better merging and fade handling"""
    if not words:
        return []
    
    sorted_words = sorted(words, key=lambda x: x["start"])
    segments = []
    
    current_start = sorted_words[0]["start"]
    current_end = sorted_words[0]["end"]
    
    for word in sorted_words[1:]:
        gap = word["start"] - current_end
        
        if gap <= merge_gap:
            current_end = max(current_end, word["end"])
        else:
            if current_end - current_start >= min_segment_duration:
                segments.append((current_start, current_end))
            current_start = word["start"]
            current_end = word["end"]
    
    if current_end - current_start >= min_segment_duration:
        segments.append((current_start, current_end))
    
    # Apply fade buffers and merge overlapping segments
    buffered_segments = []
    for start, end in segments:
        buffered_start = max(0, start - fade_buffer)
        buffered_end = min(video_duration, end + fade_buffer)
        buffered_segments.append((buffered_start, buffered_end))
    
    if not buffered_segments:
        return []
    
    merged_segments = [buffered_segments[0]]
    for start, end in buffered_segments[1:]:
        last_start, last_end = merged_segments[-1]
        
        if start <= last_end:
            merged_segments[-1] = (last_start, max(last_end, end))
        else:
            merged_segments.append((start, end))
    
    return merged_segments

def add_background_music_with_enhanced_ducking(video_path, music_path, output_path, words, 
                                              music_volume=0.12, ducked_volume=0.04):
    """Enhanced audio ducking with smooth transitions"""
    video_duration = get_video_duration(video_path)
    speech_segments = create_speech_segments_advanced(words, video_duration)

    if not speech_segments:
        logging.info("No speech detected, adding background music at normal volume")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-i", music_path,
            "-filter_complex",
            f"[1:a]aloop=loop=-1:size=2e+09,volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", output_path
        ], check=True)
        return

    # Create smooth ducking with crossfade transitions
    volume_keyframes = []
    last_end = 0
    
    for start, end in speech_segments:
        if start > last_end:
            # Normal volume between segments
            volume_keyframes.append(f"{last_end}:{music_volume}")
            volume_keyframes.append(f"{start-0.1}:{music_volume}")
        
        # Duck down for speech with smooth transition
        volume_keyframes.append(f"{start}:{ducked_volume}")
        volume_keyframes.append(f"{end}:{ducked_volume}")
        volume_keyframes.append(f"{end+0.2}:{music_volume}")
        last_end = end + 0.2

    # Final segment
    if last_end < video_duration:
        volume_keyframes.append(f"{video_duration}:{music_volume}")

    # Create smooth volume curve
    volume_points = "|".join(volume_keyframes) if volume_keyframes else f"0:{music_volume}"
    
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-i", music_path,
            "-filter_complex",
            f"[1:a]aloop=loop=-1:size=2e+09,volume='{volume_points}:eval=frame'[bg];[0:a][bg]amix=inputs=2:duration=first:weights='1.0 0.85'[aout]",
            "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", output_path
        ], check=True)
    except subprocess.CalledProcessError as e:
        logging.warning(f"Enhanced ducking failed, using fallback: {e}")
        # Fallback to simple method
        add_background_music_simple(video_path, music_path, output_path, words, music_volume, ducked_volume)

def add_background_music_simple(video_path, music_path, output_path, words, music_volume=0.12, ducked_volume=0.04):
    """Simple and reliable background music with basic ducking"""
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-i", music_path,
        "-filter_complex",
        f"[1:a]aloop=loop=-1:size=2e+09,volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first,compand=attacks=0.3:decays=0.5:points=-80/-80|-20/-15|-10/-8|0/-4[aout]",
        "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", output_path
    ], check=True)

def process_video(input_video, output_video, background_music=None, subtitle_style="animated_rounded"):
    """
    Process video with enhanced subtitle styles:
    - 'individual': One word at a time with animation
    - 'animated_rounded': Grouped words with animated rounded boxes
    - 'both': Both styles layered
    """
    base_name = Path(input_video).stem  
    auto_edited = f"auto_{base_name}.mp4"
    audio_path = f"temp_{base_name}.wav"
    individual_ass_path = f"individual_{base_name}.ass"
    rounded_ass_path = f"rounded_{base_name}.ass"
    title_ass_path = f"title_{base_name}.ass"
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
        
        if subtitle_style in ["animated_rounded", "both"]:
            subtitle_groups = group_words_into_subtitles(words)
            generate_animated_rounded_subtitle_ass(subtitle_groups, rounded_ass_path)

        # Generate animated title overlay
        duration = get_video_duration(auto_edited)
        title_text = get_title_for_video(input_video)
        generate_animated_title_ass(title_ass_path, duration, title_text)

        # Build and apply subtitle filters
        logging.info("🎬 Burning animated subtitles and overlay")
        
        # Try advanced drawtext method first for best quality rounded corners
        if subtitle_style == "animated_rounded" and subtitle_groups:
            success = create_advanced_drawtext_subtitles(subtitle_groups, auto_edited, final_with_subs)
            if success:
                # Add title overlay on top
                temp_with_title = f"temp_title_{base_name}.mp4"
                subprocess.run([
                    "ffmpeg", "-y", "-i", final_with_subs,
                    "-filter_complex", f"subtitles={title_ass_path}",
                    "-map", "0:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                    "-c:a", "copy", "-shortest", temp_with_title
                ], check=True)
                # Safe file replacement
                if os.path.exists(final_with_subs):
                    os.remove(final_with_subs)
                os.rename(temp_with_title, final_with_subs)
            else:
                # Fallback to ASS method
                logging.info("Using ASS fallback for subtitle rendering")
                filter_complex = f"subtitles={rounded_ass_path},subtitles={title_ass_path}"
                subprocess.run([
                    "ffmpeg", "-y", "-i", auto_edited,
                    "-filter_complex", filter_complex,
                    "-map", "0:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "256k", "-shortest", final_with_subs
                ], check=True)
        else:
            # Use ASS method for other styles
            if subtitle_style == "individual":
                filter_complex = f"subtitles={individual_ass_path},subtitles={title_ass_path}"
            elif subtitle_style == "both":
                filter_complex = f"subtitles={rounded_ass_path},subtitles={individual_ass_path},subtitles={title_ass_path}"
            else:
                filter_complex = f"subtitles={title_ass_path}"
            
            subprocess.run([
                "ffmpeg", "-y", "-i", auto_edited,
                "-filter_complex", filter_complex,
                "-map", "0:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-c:a", "aac", "-b:a", "256k", "-shortest", final_with_subs
            ], check=True)

        # Add background music with enhanced ducking
        if background_music and os.path.exists(background_music):
            logging.info("🎵 Adding background music with enhanced ducking")
            add_background_music_with_enhanced_ducking(
                final_with_subs, background_music, final_with_music, words
            )
            # Safe file replacement
            if os.path.exists(output_video):
                os.remove(output_video)
            os.rename(final_with_music, output_video)
        else:
            # Safe file replacement
            if os.path.exists(output_video):
                os.remove(output_video)
            os.rename(final_with_subs, output_video)

        logging.info(f"✅ Done: {output_video}")
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        raise
    finally:
        # Cleanup temporary files
        temp_files = [
            audio_path, individual_ass_path, rounded_ass_path, 
            title_ass_path, auto_edited, final_with_subs, final_with_music,
            f"temp_title_{base_name}.mp4"
        ]
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                    logging.debug(f"🗑️ Cleaned up: {f}")
                except Exception as cleanup_error:
                    logging.debug(f"⚠️ Could not clean up {f}: {cleanup_error}")
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
        "Choose subtitle style:\n- 'individual' (animated one word at a time)\n- 'animated_rounded' (animated grouped with rounded box)\n- 'both' (layered styles)",
        initialvalue="animated_rounded"
    )
    
    style_root.destroy()
    
    if subtitle_style not in ["individual", "animated_rounded", "both"]:
        subtitle_style = "animated_rounded"
    
    logging.info(f"🎨 Using subtitle style: {subtitle_style}")

    # Process each video
    for i, input_video in enumerate(input_videos, 1):
        logging.info(f"📹 Processing video {i}/{len(input_videos)}: {os.path.basename(input_video)}")
        base = Path(input_video).stem
        output_path = os.path.join(output_dir, f"{base}_enhanced_final.mp4")
        
        # Remove existing output file if it exists
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                logging.info(f"🗑️ Removed existing output file: {os.path.basename(output_path)}")
            except Exception as e:
                logging.warning(f"⚠️ Could not remove existing file {output_path}: {e}")
        
        try:
            process_video(input_video, output_path, background_music, subtitle_style)
        except Exception as e:
            logging.error(f"❌ Failed to process {input_video}: {e}")
            continue

    logging.info("🎉 All videos processed with enhanced animations!")

if __name__ == "__main__":
    main()