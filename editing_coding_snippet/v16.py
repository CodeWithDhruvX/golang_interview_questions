import os
import subprocess
import json
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, colorchooser, font
from pathlib import Path
import logging
from faster_whisper import WhisperModel
import ffmpeg
import re
import threading
import tempfile
import time
import atexit
import signal
import sys
import gc

logging.basicConfig(level=logging.INFO, format="🔹 %(message)s")

# Global lists to track temporary files and processes for cleanup
TEMP_FILES = []
ACTIVE_PROCESSES = []

def cleanup_resources():
    """Clean up all temporary files and processes"""
    global TEMP_FILES, ACTIVE_PROCESSES
    
    for proc in ACTIVE_PROCESSES[:]:
        try:
            if proc.poll() is None:  # Process is still running
                proc.terminate()
                proc.wait(timeout=5)
        except:
            try:
                proc.kill()
            except:
                pass
        finally:
            if proc in ACTIVE_PROCESSES:
                ACTIVE_PROCESSES.remove(proc)
    
    for temp_file in TEMP_FILES[:]:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.debug(f"Cleaned up: {temp_file}")
        except Exception as e:
            logging.warning(f"Could not remove {temp_file}: {e}")
        finally:
            if temp_file in TEMP_FILES:
                TEMP_FILES.remove(temp_file)
    
    gc.collect()

atexit.register(cleanup_resources)

def signal_handler(signum, frame):
    logging.info("Received interrupt signal, cleaning up...")
    cleanup_resources()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    with open("video_titles.json", "r", encoding="utf-8") as f:
        VIDEO_TITLE_MAP = json.load(f)
except FileNotFoundError:
    VIDEO_TITLE_MAP = []
    logging.warning("video_titles.json not found, using default titles")

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

def rgb_to_bgr_hex(rgb_color):
    """Convert RGB color tuple to BGR hex format for ASS subtitles"""
    r, g, b = rgb_color
    return f"&H00{b:02X}{g:02X}{r:02X}"

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds * 100) % 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds * 1000) % 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def run_subprocess_safe(cmd, timeout=300, **kwargs):
    """Run subprocess with proper encoding handling and resource management"""
    global ACTIVE_PROCESSES
    
    proc = None
    try:
        popen_kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'text': True,
            'encoding': 'utf-8',
            'errors': 'replace'
        }
        
        if sys.platform.startswith('win'):
            popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        
        for k, v in kwargs.items():
            if k not in ['timeout', 'check', 'capture_output', 'encoding', 'errors']:
                popen_kwargs[k] = v
        
        proc = subprocess.Popen(cmd, **popen_kwargs)
        ACTIVE_PROCESSES.append(proc)
        
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            logging.warning(f"Process timed out after {timeout}s: {' '.join(str(x) for x in cmd[:3])}")
            proc.kill()
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                stdout, stderr = '', 'Process killed due to timeout'
            raise subprocess.TimeoutExpired(cmd, timeout, output=stdout, stderr=stderr)
        
        if proc in ACTIVE_PROCESSES:
            ACTIVE_PROCESSES.remove(proc)
        
        check_flag = kwargs.get('check', True)
        if check_flag and proc.returncode != 0:
            cmd_str = ' '.join(str(x) for x in cmd[:5])
            error_msg = f"Command failed with return code {proc.returncode}: {cmd_str}"
            if stderr:
                stderr_safe = stderr[:500] if isinstance(stderr, str) else str(stderr)[:500]
                error_msg += f"\nError output: {stderr_safe}"
            raise subprocess.CalledProcessError(proc.returncode, cmd, stdout, stderr)
        
        class Result:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout if stdout else ""
                self.stderr = stderr if stderr else ""
        
        return Result(proc.returncode, stdout, stderr)
        
    except Exception as e:
        if proc is not None:
            try:
                if proc in ACTIVE_PROCESSES:
                    ACTIVE_PROCESSES.remove(proc)
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=5)
            except:
                pass
        raise

def get_video_duration(file_path):
    """Get video duration with better error handling"""
    try:
        result = run_subprocess_safe([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
            '-of', 'json', str(file_path)
        ], timeout=30)
        
        if result.stdout:
            duration_json = json.loads(result.stdout)
            duration = float(duration_json["format"]["duration"])
            
            if duration <= 0 or duration > 86400:
                logging.warning(f"Invalid duration {duration}s, using default")
                return 300.0
            
            return duration
        else:
            logging.warning("No duration information from ffprobe")
            return 300.0
        
    except Exception as e:
        logging.warning(f"Could not get video duration: {e}")
        return 300.0

def transcribe_audio_improved(audio_path, progress_callback=None, max_duration=3600):
    """
    FIXED: More robust transcription with proper timestamp synchronization for long videos
    """
    logging.info(f"🧠 Starting transcription: {audio_path}")
    
    if not os.path.exists(audio_path):
        logging.error(f"Audio file not found: {audio_path}")
        return []
    
    model = None
    all_words = []
    
    try:
        try:
            probe = ffmpeg.probe(str(audio_path))
            duration = float(probe['format']['duration'])
            logging.info(f"Audio duration: {duration:.1f} seconds")
        except Exception as e:
            logging.warning(f"Could not get audio duration: {e}")
            duration = 300.0
        
        if duration <= 0:
            logging.error("Invalid audio duration")
            return []
        
        logging.info("Loading Whisper model...")
        model = WhisperModel("base", device="cpu", compute_type="int8", num_workers=1)
        
        if duration <= 600:
            logging.info("Processing audio in single pass (≤10 minutes)")
            
            try:
                segments, info = model.transcribe(
                    str(audio_path),
                    beam_size=5,
                    word_timestamps=True,
                    language="en",
                    condition_on_previous_text=False,
                    temperature=0.0,
                    compression_ratio_threshold=2.4,
                    log_prob_threshold=-1.0,
                    no_speech_threshold=0.6,
                    initial_prompt="This is a tutorial video with clear speech."
                )
                
                word_count = 0
                for segment in segments:
                    if hasattr(segment, 'words') and segment.words:
                        for w in segment.words:
                            if (w.word and w.word.strip() and 
                                hasattr(w, 'start') and hasattr(w, 'end') and
                                w.start >= 0 and w.end > w.start and w.end - w.start <= 15):
                                
                                all_words.append({
                                    "word": w.word.strip(),
                                    "start": float(w.start),
                                    "end": float(w.end)
                                })
                                word_count += 1
                
                logging.info(f"Single-pass transcription complete: {word_count} words")
                
                if progress_callback:
                    progress_callback()
                    
            except Exception as e:
                logging.error(f"Single-pass transcription failed: {e}")
                return []
        
        else:
            chunk_duration = 180
            overlap_duration = 10
            
            chunks = []
            current_start = 0
            
            while current_start < duration:
                chunk_end = min(current_start + chunk_duration, duration)
                
                if chunk_end < duration:
                    overlap_end = min(chunk_end + overlap_duration, duration)
                else:
                    overlap_end = chunk_end
                
                chunks.append({
                    'start': current_start,
                    'end': overlap_end,
                    'processing_end': chunk_end,
                    'chunk_id': len(chunks)
                })
                
                current_start = chunk_end
            
            total_chunks = len(chunks)
            logging.info(f"Processing long audio in {total_chunks} overlapping chunks of {chunk_duration}s each")
            
            for chunk_info in chunks:
                start_time = chunk_info['start']
                end_time = chunk_info['end']
                processing_end = chunk_info['processing_end']
                chunk_id = chunk_info['chunk_id']
                
                logging.info(f"Processing chunk {chunk_id + 1}/{total_chunks}: {start_time:.1f}s - {end_time:.1f}s (process until {processing_end:.1f}s)")
                
                chunk_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                        chunk_path = temp_file.name
                    
                    TEMP_FILES.append(chunk_path)
                    
                    chunk_timeout = min(300, int((end_time - start_time) * 2))
                    
                    run_subprocess_safe([
                        "ffmpeg", "-y", "-i", str(audio_path),
                        "-ss", str(start_time), 
                        "-t", str(end_time - start_time),
                        "-acodec", "pcm_s16le", 
                        "-ar", "16000", 
                        "-ac", "1",
                        "-avoid_negative_ts", "make_zero",
                        chunk_path
                    ], timeout=chunk_timeout)
                    
                    if not os.path.exists(chunk_path) or os.path.getsize(chunk_path) < 1000:
                        logging.warning(f"Chunk {chunk_id + 1} failed to create or too small, skipping")
                        continue
                    
                    segments, info = model.transcribe(
                        chunk_path,
                        beam_size=5,
                        word_timestamps=True,
                        language="en",
                        condition_on_previous_text=False,
                        temperature=0.0,
                        compression_ratio_threshold=2.4,
                        log_prob_threshold=-1.0,
                        no_speech_threshold=0.6,
                        initial_prompt="This is a tutorial video with clear speech."
                    )
                    
                    chunk_words = 0
                    for segment in segments:
                        if hasattr(segment, 'words') and segment.words:
                            for w in segment.words:
                                if (w.word and w.word.strip() and 
                                    hasattr(w, 'start') and hasattr(w, 'end') and
                                    w.start >= 0 and w.end > w.start and w.end - w.start <= 15):
                                    
                                    adjusted_start = float(w.start) + start_time
                                    adjusted_end = float(w.end) + start_time
                                    
                                    if adjusted_start < processing_end:
                                        is_duplicate = False
                                        for existing_word in all_words[-10:]:
                                            if (abs(existing_word["start"] - adjusted_start) < 0.1 and 
                                                existing_word["word"].strip().lower() == w.word.strip().lower()):
                                                is_duplicate = True
                                                break
                                        
                                        if not is_duplicate:
                                            adjusted_word = {
                                                "word": w.word.strip(),
                                                "start": adjusted_start,
                                                "end": adjusted_end
                                            }
                                            all_words.append(adjusted_word)
                                            chunk_words += 1
                    
                    logging.info(f"Chunk {chunk_id + 1} complete: {chunk_words} words extracted")
                    
                    if progress_callback:
                        progress_callback()
                
                except Exception as e:
                    logging.warning(f"Failed to process chunk {chunk_id + 1}: {e}")
                    continue
                
                finally:
                    if chunk_path and os.path.exists(chunk_path):
                        try:
                            os.remove(chunk_path)
                            if chunk_path in TEMP_FILES:
                                TEMP_FILES.remove(chunk_path)
                        except Exception as e:
                            logging.warning(f"Could not remove chunk: {e}")
                
                time.sleep(0.1)
        
        if all_words:
            all_words = sorted(all_words, key=lambda x: x["start"])
            
            filtered_words = []
            for i, word in enumerate(all_words):
                should_include = True
                
                if filtered_words:
                    last_word = filtered_words[-1]
                    
                    if word["start"] < last_word["end"]:
                        if word["word"].strip().lower() == last_word["word"].strip().lower():
                            should_include = False
                        elif word["start"] < last_word["start"] + 0.1:
                            should_include = False
                        else:
                            filtered_words[-1]["end"] = min(last_word["end"], word["start"] - 0.05)
                
                if should_include:
                    filtered_words.append(word)
            
            all_words = filtered_words
            
            for i in range(len(all_words) - 1):
                current_word = all_words[i]
                next_word = all_words[i + 1]
                
                if current_word["end"] > next_word["start"]:
                    midpoint = (current_word["end"] + next_word["start"]) / 2
                    all_words[i]["end"] = midpoint - 0.025
                    all_words[i + 1]["start"] = midpoint + 0.025
            
            logging.info(f"FIXED: Transcription complete with synchronized timestamps: {len(all_words)} valid words extracted")
        
        return all_words
        
    except Exception as e:
        logging.error(f"Transcription failed: {e}")
        return []
    
    finally:
        if model is not None:
            try:
                del model
            except:
                pass
        gc.collect()
        logging.info("Transcription cleanup complete")

def group_words_into_subtitles_improved(words, max_words_per_group=4, min_duration=1.5, max_duration=5.0, min_gap=0.2):
    """
    IMPROVED: Better subtitle grouping with natural breaks and timing optimization
    """
    if not words:
        return []
    
    groups = []
    current_group = []
    current_start = words[0]["start"]
    
    end_punctuation = ('.', '!', '?', ';')
    pause_punctuation = (',', ':', '--')
    
    for i, word in enumerate(words):
        if not isinstance(word, dict) or not all(k in word for k in ['word', 'start', 'end']):
            continue
        
        should_start_new = False
        
        if current_group:
            potential_duration = word["end"] - current_start
            
            prev_word = words[i-1] if i > 0 else None
            gap = word["start"] - prev_word["end"] if prev_word else 0
            
            has_strong_break = False
            has_weak_break = False
            
            if prev_word:
                prev_text = prev_word["word"].strip()
                has_strong_break = (
                    prev_text.endswith(end_punctuation) or
                    gap > 1.0
                )
                has_weak_break = (
                    prev_text.endswith(pause_punctuation) or
                    gap > 0.5
                )
            
            should_start_new = (
                len(current_group) >= max_words_per_group or
                potential_duration >= max_duration or
                (has_strong_break and len(current_group) >= 2 and potential_duration >= min_duration) or
                (has_weak_break and len(current_group) >= 3 and potential_duration >= min_duration * 1.2) or
                gap > 2.0
            )
        
        if should_start_new and current_group:
            group_duration = current_group[-1]["end"] - current_start
            
            if group_duration < min_duration:
                extended_end = current_start + min_duration
                if i < len(words) and extended_end > words[i]["start"]:
                    extended_end = max(current_group[-1]["end"], words[i]["start"] - 0.1)
            else:
                extended_end = current_group[-1]["end"]
            
            text = " ".join([w["word"].strip() for w in current_group if w.get("word", "").strip()])
            
            if text.strip():
                groups.append(SubtitleGroup(
                    words=current_group.copy(),
                    start=current_start,
                    end=extended_end,
                    text=text.strip()
                ))
            
            current_group = []
            current_start = word["start"]
        
        current_group.append(word)
    
    if current_group:
        group_duration = current_group[-1]["end"] - current_start
        
        if group_duration < min_duration:
            extended_end = current_start + min_duration
        else:
            extended_end = current_group[-1]["end"]
        
        text = " ".join([w["word"].strip() for w in current_group if w.get("word", "").strip()])
        if text.strip():
            groups.append(SubtitleGroup(
                words=current_group,
                start=current_start,
                end=extended_end,
                text=text.strip()
            ))
    
    for i in range(len(groups) - 1):
        current_group = groups[i]
        next_group = groups[i + 1]
        
        min_gap_between = 0.1
        if current_group.end + min_gap_between > next_group.start:
            groups[i].end = max(current_group.start + min_duration * 0.8, next_group.start - min_gap_between)
    
    logging.info(f"Created {len(groups)} subtitle groups with improved timing")
    return groups

def safe_text_escape(text):
    """Safely escape text for ASS format"""
    if not isinstance(text, str):
        text = str(text)
    
    text = re.sub(r'[^\w\s\.\,\!\?\-\'\"\(\)\:\;]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    text = text.replace('\\', '\\\\')
    text = text.replace('{', '\\{')
    text = text.replace('}', '\\}')
    
    return text

def generate_highlighted_subtitle_ass_improved(subtitle_groups, ass_path, subtitle_color=(255, 255, 255), border_color=(0, 0, 0), font_family="Roboto Bold", font_size=18, alignment=2):
    """
    ENHANCED: Generate YouTube-friendly ASS subtitles with customizable colors,
    font, size, alignment, transparent box background, and smooth fade animation.
    """
    try:
        # Check if font is available, fall back to Arial if not
        available_fonts = font.families()
        selected_font = font_family
        if font_family not in available_fonts:
            logging.warning(f"Font '{font_family}' not found, falling back to Arial")
            selected_font = "Arial"
        
        primary_color = rgb_to_bgr_hex(subtitle_color)
        outline_color = rgb_to_bgr_hex(border_color)
        
        with open(ass_path, "w", encoding="utf-8", errors='replace') as f:
            f.write(f"""[Script Info]
Title: Enhanced Subtitles
ScriptType: v4.00+
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{selected_font},{font_size},{primary_color},&H000000FF,{outline_color},&H66000000,-1,0,0,0,100,100,0,0,3,2,1,{alignment},50,50,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
            for group in subtitle_groups:
                text = safe_text_escape(group.text.strip())
                if not text:
                    continue

                start_time = max(0, group.start)
                end_time = max(start_time + 1.0, group.end)

                formatted_text = f"{{\\fad(300,300)\\bord2\\shad1}}{text}"

                f.write(f"Dialogue: 0,{format_time(start_time)},{format_time(end_time)},Default,,0,0,0,,{formatted_text}\n")

        logging.info(f"✅ Generated ASS file with {len(subtitle_groups)} styled subtitles (Font: {selected_font}, Size: {font_size}, Alignment: {alignment})")

    except Exception as e:
        logging.error(f"❌ Failed to generate ASS file: {e}")
        raise

def get_title_for_video(input_video):
    """Get title for video from mapping"""
    input_path = os.path.normpath(str(input_video))
    for entry in VIDEO_TITLE_MAP:
        if os.path.normpath(str(entry.get("slide_topic", ""))) == input_path:
            return entry.get("title_text", "Video Tutorial")
    return "Video Tutorial"

def generate_hello_world_ass(ass_path, video_duration, title_text, font_family="Arial", font_size=56, alignment=8):
    """Generate title overlay ASS with customizable font, size, and alignment"""
    try:
        # Check if font is available, fall back to Arial if not
        available_fonts = font.families()
        selected_font = font_family
        if font_family not in available_fonts:
            logging.warning(f"Font '{font_family}' not found, falling back to Arial")
            selected_font = "Arial"
        
        with open(ass_path, "w", encoding="utf-8", errors='replace') as f:
            f.write(f"""[Script Info]
Title: Title Overlay
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitleStyle,{selected_font},{font_size},&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,3,2,{alignment},20,20,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
            if video_duration <= 0:
                video_duration = 10
            
            display_duration = min(15, max(3, video_duration * 0.2))
            clean_title = safe_text_escape(str(title_text))
            
            if clean_title:
                f.write(f"Dialogue: 0,{format_time(0)},{format_time(display_duration)},TitleStyle,,0,0,0,,{{\\fad(500,500)}}{clean_title.upper()}\n")
                
    except Exception as e:
        logging.error(f"Failed to generate title ASS: {e}")
        raise

def add_background_music_simple(video_path, music_path, output_path, music_volume=0.15):
    """Add background music with extended timeout and customizable volume"""
    try:
        timeout = 1800
        
        run_subprocess_safe([
            "ffmpeg", "-y", "-i", str(video_path), "-i", str(music_path),
            "-filter_complex",
            f"[1:a]aloop=loop=-1:size=2e+09,volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", str(output_path)
        ], timeout=timeout)
        
        logging.info(f"Background music added with volume: {music_volume}")
        
    except Exception as e:
        logging.error(f"Background music addition failed: {e}")
        raise

def process_video_with_settings(input_video, output_video, background_music, subtitle_individual, subtitle_highlighted, add_title, use_auto_editor, use_transcription, progress_callback=None, min_subtitle_duration=1.5, max_words_per_subtitle=4, subtitle_color=(255, 255, 255), border_color=(0, 0, 0), music_volume=0.15, subtitle_font="Roboto Bold", subtitle_font_size=18, subtitle_alignment=2, title_font="Arial", title_font_size=56, title_alignment=8):
    """
    ENHANCED: Main processing function with customizable subtitle colors, fonts, sizes, alignments, and music volume
    """
    timestamp = int(time.time())
    pid = os.getpid()
    base_name = Path(input_video).stem
    safe_base_name = re.sub(r'[^\w\-_\.]', '_', base_name)
    
    temp_files = {
        'auto_edited': f"auto_{safe_base_name}_{timestamp}_{pid}.mp4",
        'audio_path': f"temp_{safe_base_name}_{timestamp}_{pid}.wav", 
        'highlighted_ass': f"highlighted_{safe_base_name}_{timestamp}_{pid}.ass",
        'title_ass': f"title_{safe_base_name}_{timestamp}_{pid}.ass",
        'final_subs': f"final_subs_{safe_base_name}_{timestamp}_{pid}.mp4",
        'final_music': f"final_music_{safe_base_name}_{timestamp}_{pid}.mp4"
    }
    
    TEMP_FILES.extend(temp_files.values())
    
    try:
        if not os.path.exists(input_video):
            raise FileNotFoundError(f"Input video not found: {input_video}")
        
        video_duration = get_video_duration(input_video)
        base_timeout = max(600, int(video_duration * 2))
        
        logging.info(f"ENHANCED: Processing video: {video_duration:.1f}s duration, subtitle font: {subtitle_font}, size: {subtitle_font_size}, alignment: {subtitle_alignment}, title font: {title_font}, size: {title_font_size}, alignment: {title_alignment}")
        
        if not (subtitle_individual or subtitle_highlighted or add_title or background_music or use_auto_editor):
            logging.info("No processing options selected, copying file")
            run_subprocess_safe([
                "ffmpeg", "-y", "-i", str(input_video),
                "-c:v", "copy", "-c:a", "copy", str(output_video)
            ], timeout=base_timeout)
            if progress_callback:
                progress_callback()
            return

        video_to_process = input_video
        if use_auto_editor:
            logging.info("Applying auto-editor...")
            try:
                auto_editor_timeout = max(1200, int(video_duration * 3))
                run_subprocess_safe([
                    "auto-editor", str(input_video), "-o", temp_files['auto_edited'],
                    "--no-open", "--frame-rate", "30", "--silent-speed", "99999"
                ], timeout=auto_editor_timeout)
                video_to_process = temp_files['auto_edited']
                if progress_callback:
                    progress_callback()
            except Exception as e:
                logging.warning(f"Auto-editor failed: {e}")
        
        words = []
        subtitle_groups = []
        
        if use_transcription and (subtitle_individual or subtitle_highlighted or background_music):
            logging.info("ENHANCED: Starting synchronized transcription process...")
            
            audio_timeout = max(300, int(video_duration))
            run_subprocess_safe([
                "ffmpeg", "-y", "-i", str(video_to_process),
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", 
                temp_files['audio_path']
            ], timeout=audio_timeout)
            
            if progress_callback:
                progress_callback()
            
            words = transcribe_audio_improved(temp_files['audio_path'], progress_callback)
            
            if subtitle_highlighted and words:
                subtitle_groups = group_words_into_subtitles_improved(
                    words, 
                    max_words_per_group=max_words_per_subtitle,
                    min_duration=min_subtitle_duration
                )
                logging.info(f"ENHANCED: Generated {len(subtitle_groups)} synchronized subtitle groups")

        if subtitle_highlighted and use_transcription and subtitle_groups:
            logging.info(f"Generating synchronized subtitle file with custom settings: {subtitle_color}, {border_color}, {subtitle_font}, {subtitle_font_size}, {subtitle_alignment}")
            generate_highlighted_subtitle_ass_improved(
                subtitle_groups, 
                temp_files['highlighted_ass'], 
                subtitle_color, 
                border_color,
                subtitle_font,
                subtitle_font_size,
                subtitle_alignment
            )
        
        if add_title:
            title_text = get_title_for_video(input_video)
            generate_hello_world_ass(
                temp_files['title_ass'], 
                video_duration, 
                title_text,
                title_font,
                title_font_size,
                title_alignment
            )

        if subtitle_highlighted or add_title:
            logging.info("Applying synchronized subtitles and overlays...")
            
            filter_parts = []
            if subtitle_highlighted and use_transcription and subtitle_groups:
                ass_path = temp_files['highlighted_ass'].replace('\\', '\\\\').replace(':', '\\:')
                filter_parts.append(f"subtitles={ass_path}")
            if add_title:
                title_path = temp_files['title_ass'].replace('\\', '\\\\').replace(':', '\\:')
                filter_parts.append(f"subtitles={title_path}")
            
            if filter_parts:
                filter_complex = ",".join(filter_parts)
                subtitle_timeout = max(1800, int(video_duration * 4))
                
                run_subprocess_safe([
                    "ffmpeg", "-y", "-i", str(video_to_process),
                    "-filter_complex", filter_complex,
                    "-map", "0:a", "-c:v", "libx264", "-crf", "23", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", temp_files['final_subs']
                ], timeout=subtitle_timeout)
            else:
                run_subprocess_safe([
                    "ffmpeg", "-y", "-i", str(video_to_process),
                    "-c:v", "copy", "-c:a", "copy", temp_files['final_subs']
                ], timeout=base_timeout)
            
            if progress_callback:
                progress_callback()
        else:
            run_subprocess_safe([
                "ffmpeg", "-y", "-i", str(video_to_process),
                "-c:v", "copy", "-c:a", "copy", temp_files['final_subs']
            ], timeout=base_timeout)
            if progress_callback:
                progress_callback()

        if background_music and os.path.exists(background_music):
            logging.info(f"Adding background music with volume: {music_volume}")
            music_timeout = max(1800, int(video_duration * 3))
            add_background_music_simple(
                temp_files['final_subs'], background_music, temp_files['final_music'], music_volume
            )
            if os.path.exists(temp_files['final_music']):
                os.rename(temp_files['final_music'], output_video)
            else:
                raise Exception("Failed to create final video with music")
        else:
            if os.path.exists(temp_files['final_subs']):
                os.rename(temp_files['final_subs'], output_video)
            else:
                raise Exception("Failed to create final video")

        if progress_callback:
            progress_callback()
        
        logging.info(f"✅ ENHANCED: Successfully processed with custom settings: {output_video}")
        
    except Exception as e:
        logging.error(f"❌ Error processing {input_video}: {e}")
        raise
    
    finally:
        for temp_file in temp_files.values():
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    if temp_file in TEMP_FILES:
                        TEMP_FILES.remove(temp_file)
                    logging.debug(f"Cleaned up: {temp_file}")
                except Exception as e:
                    logging.warning(f"Could not remove {temp_file}: {e}")

class VideoProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Video Processor - Customizable Subtitles & Music")
        self.root.geometry("700x900")  # Increased height to accommodate new controls
        self.root.resizable(True, True)
        
        self.input_videos = []
        self.background_music = ""
        self.output_dir = ""
        self.is_processing = False
        self.processing_thread = None
        
        # Default settings
        self.subtitle_color = (255, 255, 255)
        self.border_color = (0, 0, 0)
        self.subtitle_font = "Roboto Bold"
        self.subtitle_font_size = 18
        self.subtitle_alignment = 2  # Center-bottom
        self.title_font = "Arial"
        self.title_font_size = 56
        self.title_alignment = 8  # Top-center
        
        # Available fonts and alignments
        self.available_fonts = sorted(["Arial", "Roboto", "Times New Roman", "Helvetica", 
                                     "Verdana", "Courier New", "Georgia", "Trebuchet MS"])
        self.alignment_options = {
            "Top-Left": 7, "Top-Center": 8, "Top-Right": 9,
            "Middle-Left": 4, "Middle-Center": 5, "Middle-Right": 6,
            "Bottom-Left": 1, "Bottom-Center": 2, "Bottom-Right": 3
        }
        
        self.create_widgets()
        self.center_window()

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex string for display"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def choose_subtitle_color(self):
        """Open color chooser for subtitle color"""
        color = colorchooser.askcolor(
            initialcolor=self.rgb_to_hex(self.subtitle_color),
            title="Choose Subtitle Color"
        )
        if color[0]:
            self.subtitle_color = tuple(int(c) for c in color[0])
            self.subtitle_color_label.config(
                text=f"Subtitle Color: RGB{self.subtitle_color}",
                background=self.rgb_to_hex(self.subtitle_color),
                foreground="white" if sum(self.subtitle_color) < 400 else "black"
            )

    def choose_border_color(self):
        """Open color chooser for border color"""
        color = colorchooser.askcolor(
            initialcolor=self.rgb_to_hex(self.border_color),
            title="Choose Border Color"
        )
        if color[0]:
            self.border_color = tuple(int(c) for c in color[0])
            self.border_color_label.config(
                text=f"Border Color: RGB{self.border_color}",
                background=self.rgb_to_hex(self.border_color),
                foreground="white" if sum(self.border_color) < 400 else "black"
            )

    def save_config(self):
        """Save current configuration to a JSON file"""
        try:
            config = {
                'use_transcription': self.use_transcription_var.get(),
                'subtitle_highlighted': self.subtitle_highlighted_var.get(),
                'add_title': self.add_title_var.get(),
                'use_auto_editor': self.use_auto_editor_var.get(),
                'subtitle_color': self.subtitle_color,
                'border_color': self.border_color,
                'min_subtitle_duration': self.min_duration_var.get(),
                'max_words_per_subtitle': self.max_words_var.get(),
                'music_volume': self.music_volume_var.get(),
                'output_dir': self.output_dir,
                'background_music': self.background_music,
                'subtitle_font': self.subtitle_font,
                'subtitle_font_size': self.subtitle_font_size,
                'subtitle_alignment': self.subtitle_alignment,
                'title_font': self.title_font,
                'title_font_size': self.title_font_size,
                'title_alignment': self.title_alignment
            }
            
            file_path = filedialog.asksaveasfilename(
                title="Save Configuration",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                messagebox.showinfo("Success", "Configuration saved successfully!")
                logging.info(f"Configuration saved to {file_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
            logging.error(f"Failed to save configuration: {e}")

    def load_config(self):
        """Load configuration from a JSON file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Load Configuration",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Apply configuration
                self.use_transcription_var.set(config.get('use_transcription', True))
                self.subtitle_highlighted_var.set(config.get('subtitle_highlighted', True))
                self.add_title_var.set(config.get('add_title', False))
                self.use_auto_editor_var.set(config.get('use_auto_editor', False))
                self.subtitle_color = tuple(config.get('subtitle_color', (255, 255, 255)))
                self.border_color = tuple(config.get('border_color', (0, 0, 0)))
                self.min_duration_var.set(config.get('min_subtitle_duration', 1.5))
                self.max_words_var.set(config.get('max_words_per_subtitle', 5))
                self.music_volume_var.set(config.get('music_volume', 0.15))
                self.subtitle_font = config.get('subtitle_font', 'Roboto Bold')
                self.subtitle_font_size = config.get('subtitle_font_size', 18)
                self.subtitle_alignment = config.get('subtitle_alignment', 2)
                self.title_font = config.get('title_font', 'Arial')
                self.title_font_size = config.get('title_font_size', 56)
                self.title_alignment = config.get('title_alignment', 8)
                
                # Update output directory if it exists
                output_dir = config.get('output_dir', '')
                if output_dir and os.path.isdir(output_dir):
                    self.output_dir = output_dir
                    self.output_label.config(text=f"📁 {self.output_dir}", foreground="blue")
                
                # Update background music if it exists
                background_music = config.get('background_music', '')
                if background_music and os.path.exists(background_music):
                    self.background_music = background_music
                    filename = os.path.basename(self.background_music)
                    self.music_label.config(text=f"♪ {filename}", foreground="blue")
                
                # Update GUI elements
                self.subtitle_color_label.config(
                    text=f"Subtitle Color: RGB{self.subtitle_color}",
                    background=self.rgb_to_hex(self.subtitle_color),
                    foreground="white" if sum(self.subtitle_color) < 400 else "black"
                )
                self.border_color_label.config(
                    text=f"Border Color: RGB{self.border_color}",
                    background=self.rgb_to_hex(self.border_color),
                    foreground="white" if sum(self.border_color) < 400 else "black"
                )
                self.subtitle_font_var.set(self.subtitle_font)
                self.subtitle_font_size_var.set(self.subtitle_font_size)
                self.subtitle_alignment_var.set(
                    next(k for k, v in self.alignment_options.items() if v == self.subtitle_alignment)
                )
                self.title_font_var.set(self.title_font)
                self.title_font_size_var.set(self.title_font_size)
                self.title_alignment_var.set(
                    next(k for k, v in self.alignment_options.items() if v == self.title_alignment)
                )
                
                # Update transcription toggle state
                self.on_transcription_toggle()
                
                messagebox.showinfo("Success", "Configuration loaded successfully!")
                logging.info(f"Configuration loaded from {file_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
            logging.error(f"Failed to load configuration: {e}")

    def create_widgets(self):
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Input Selection Frame
        input_frame = ttk.LabelFrame(main_frame, text="📁 Input Selection", padding=15)
        input_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(input_frame, text="Select Videos", command=self.select_videos).pack(fill="x", pady=(0, 5))
        self.video_label = ttk.Label(input_frame, text="No videos selected", foreground="gray")
        self.video_label.pack(fill="x", pady=(0, 10))
        
        ttk.Button(input_frame, text="Select Background Music (Optional)", command=self.select_music).pack(fill="x", pady=(0, 5))
        self.music_label = ttk.Label(input_frame, text="No music selected", foreground="gray")
        self.music_label.pack(fill="x", pady=(0, 10))
        
        ttk.Button(input_frame, text="Select Output Folder", command=self.select_output).pack(fill="x", pady=(0, 5))
        self.output_label = ttk.Label(input_frame, text="No output folder selected", foreground="gray")
        self.output_label.pack(fill="x")

        # Processing Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ Processing Options", padding=15)
        options_frame.pack(fill="x", pady=(0, 10))
        
        self.use_transcription_var = tk.BooleanVar(value=True)
        transcription_cb = ttk.Checkbutton(
            options_frame, 
            text="🎤 Generate Subtitles (ENHANCED - Synchronized for Long Videos)", 
            variable=self.use_transcription_var,
            command=self.on_transcription_toggle
        )
        transcription_cb.pack(anchor="w", pady=(0, 5))
        
        subtitle_frame = ttk.Frame(options_frame)
        subtitle_frame.pack(fill="x", padx=(20, 0), pady=(0, 5))
        
        self.subtitle_individual_var = tk.BooleanVar(value=False)
        self.individual_cb = ttk.Checkbutton(
            subtitle_frame, 
            text="📝 Individual Word Subtitles (Disabled)", 
            variable=self.subtitle_individual_var,
            state="disabled"
        )
        self.individual_cb.pack(anchor="w", pady=2)
        
        self.subtitle_highlighted_var = tk.BooleanVar(value=True)
        self.highlighted_cb = ttk.Checkbutton(
            subtitle_frame, 
            text="🔤 Synchronized Group Subtitles (ENHANCED - Custom Fonts & Alignment)", 
            variable=self.subtitle_highlighted_var
        )
        self.highlighted_cb.pack(anchor="w", pady=2)
        
        self.add_title_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="📋 Add Title Overlay", variable=self.add_title_var).pack(anchor="w", pady=2)
        
        self.use_auto_editor_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="✂️ Use Auto-Editor (Remove Silence)", variable=self.use_auto_editor_var).pack(anchor="w", pady=2)

        # ENHANCED Subtitle Customization Frame
        subtitle_custom_frame = ttk.LabelFrame(main_frame, text="🎨 Subtitle Appearance", padding=15)
        subtitle_custom_frame.pack(fill="x", pady=(0, 10))
        
        # Color Selection
        color_frame = ttk.Frame(subtitle_custom_frame)
        color_frame.pack(fill="x", pady=(0, 10))
        
        subtitle_color_frame = ttk.Frame(color_frame)
        subtitle_color_frame.pack(fill="x", pady=2)
        
        ttk.Button(
            subtitle_color_frame, 
            text="Choose Subtitle Color", 
            command=self.choose_subtitle_color
        ).pack(side="left", padx=(0, 10))
        
        self.subtitle_color_label = ttk.Label(
            subtitle_color_frame, 
            text=f"Subtitle Color: RGB{self.subtitle_color}",
            background=self.rgb_to_hex(self.subtitle_color),
            foreground="black",
            relief="solid",
            padding=5
        )
        self.subtitle_color_label.pack(side="left", fill="x", expand=True)
        
        border_color_frame = ttk.Frame(color_frame)
        border_color_frame.pack(fill="x", pady=2)
        
        ttk.Button(
            border_color_frame, 
            text="Choose Border Color", 
            command=self.choose_border_color
        ).pack(side="left", padx=(0, 10))
        
        self.border_color_label = ttk.Label(
            border_color_frame, 
            text=f"Border Color: RGB{self.border_color}",
            background=self.rgb_to_hex(self.border_color),
            foreground="white",
            relief="solid",
            padding=5
        )
        self.border_color_label.pack(side="left", fill="x", expand=True)

        # Subtitle Font and Alignment
        subtitle_font_frame = ttk.Frame(subtitle_custom_frame)
        subtitle_font_frame.pack(fill="x", pady=2)
        ttk.Label(subtitle_font_frame, text="Subtitle Font:").pack(side="left")
        self.subtitle_font_var = tk.StringVar(value=self.subtitle_font)
        subtitle_font_combo = ttk.Combobox(
            subtitle_font_frame, 
            textvariable=self.subtitle_font_var, 
            values=self.available_fonts,
            state="readonly",
            width=20
        )
        subtitle_font_combo.pack(side="right")
        subtitle_font_combo.bind("<<ComboboxSelected>>", lambda e: setattr(self, "subtitle_font", self.subtitle_font_var.get()))

        subtitle_size_frame = ttk.Frame(subtitle_custom_frame)
        subtitle_size_frame.pack(fill="x", pady=2)
        ttk.Label(subtitle_size_frame, text="Subtitle Font Size:").pack(side="left")
        self.subtitle_font_size_var = tk.IntVar(value=self.subtitle_font_size)
        subtitle_size_spinbox = ttk.Spinbox(
            subtitle_size_frame, 
            from_=10, to=36, increment=1,
            textvariable=self.subtitle_font_size_var,
            width=8,
            command=lambda: setattr(self, "subtitle_font_size", self.subtitle_font_size_var.get())
        )
        subtitle_size_spinbox.pack(side="right")
        
        subtitle_align_frame = ttk.Frame(subtitle_custom_frame)
        subtitle_align_frame.pack(fill="x", pady=2)
        ttk.Label(subtitle_align_frame, text="Subtitle Alignment:").pack(side="left")
        self.subtitle_alignment_var = tk.StringVar(value="Bottom-Center")
        subtitle_align_combo = ttk.Combobox(
            subtitle_align_frame, 
            textvariable=self.subtitle_alignment_var, 
            values=list(self.alignment_options.keys()),
            state="readonly",
            width=20
        )
        subtitle_align_combo.pack(side="right")
        subtitle_align_combo.bind("<<ComboboxSelected>>", lambda e: setattr(self, "subtitle_alignment", self.alignment_options[self.subtitle_alignment_var.get()]))

        # Title Font and Alignment
        title_font_frame = ttk.Frame(subtitle_custom_frame)
        title_font_frame.pack(fill="x", pady=2)
        ttk.Label(title_font_frame, text="Title Font:").pack(side="left")
        self.title_font_var = tk.StringVar(value=self.title_font)
        title_font_combo = ttk.Combobox(
            title_font_frame, 
            textvariable=self.title_font_var, 
            values=self.available_fonts,
            state="readonly",
            width=20
        )
        title_font_combo.pack(side="right")
        title_font_combo.bind("<<ComboboxSelected>>", lambda e: setattr(self, "title_font", self.title_font_var.get()))

        title_size_frame = ttk.Frame(subtitle_custom_frame)
        title_size_frame.pack(fill="x", pady=2)
        ttk.Label(title_size_frame, text="Title Font Size:").pack(side="left")
        self.title_font_size_var = tk.IntVar(value=self.title_font_size)
        title_size_spinbox = ttk.Spinbox(
            title_size_frame, 
            from_=24, to=72, increment=1,
            textvariable=self.title_font_size_var,
            width=8,
            command=lambda: setattr(self, "title_font_size", self.title_font_size_var.get())
        )
        title_size_spinbox.pack(side="right")
        
        title_align_frame = ttk.Frame(subtitle_custom_frame)
        title_align_frame.pack(fill="x", pady=2)
        ttk.Label(title_align_frame, text="Title Alignment:").pack(side="left")
        self.title_alignment_var = tk.StringVar(value="Top-Center")
        title_align_combo = ttk.Combobox(
            title_align_frame, 
            textvariable=self.title_alignment_var, 
            values=list(self.alignment_options.keys()),
            state="readonly",
            width=20
        )
        title_align_combo.pack(side="right")
        title_align_combo.bind("<<ComboboxSelected>>", lambda e: setattr(self, "title_alignment", self.alignment_options[self.title_alignment_var.get()]))

        # Enhanced Settings Frame
        settings_frame = ttk.LabelFrame(main_frame, text="🎬 Subtitle & Audio Settings", padding=10)
        settings_frame.pack(fill="x", pady=(0, 10))
        
        duration_frame = ttk.Frame(settings_frame)
        duration_frame.pack(fill="x", pady=2)
        ttk.Label(duration_frame, text="Minimum subtitle duration:").pack(side="left")
        self.min_duration_var = tk.DoubleVar(value=1.5)
        duration_spinbox = ttk.Spinbox(duration_frame, from_=1.0, to=5.0, increment=0.1, 
                                     textvariable=self.min_duration_var, width=8)
        duration_spinbox.pack(side="right")
        ttk.Label(duration_frame, text="seconds").pack(side="right", padx=(0, 5))
        
        words_frame = ttk.Frame(settings_frame)
        words_frame.pack(fill="x", pady=2)
        ttk.Label(words_frame, text="Max words per subtitle:").pack(side="left")
        self.max_words_var = tk.IntVar(value=5)
        words_spinbox = ttk.Spinbox(words_frame, from_=3, to=8, increment=1, 
                                  textvariable=self.max_words_var, width=8)
        words_spinbox.pack(side="right")
        
        volume_frame = ttk.Frame(settings_frame)
        volume_frame.pack(fill="x", pady=2)
        ttk.Label(volume_frame, text="Background music volume:").pack(side="left")
        self.music_volume_var = tk.DoubleVar(value=0.15)
        volume_spinbox = ttk.Spinbox(volume_frame, from_=0.05, to=1.0, increment=0.05, 
                                   textvariable=self.music_volume_var, width=8, format="%.2f")
        volume_spinbox.pack(side="right")
        ttk.Label(volume_frame, text="(0.05 - 1.0)").pack(side="right", padx=(0, 5))
        
        info_label = ttk.Label(settings_frame, text="✅ ENHANCED: Custom fonts, sizes, alignments, colors, and volumes", 
                              foreground="green", font=("Arial", 8, "bold"))
        info_label.pack(pady=(5, 0))

        # Configuration Buttons Frame
        config_frame = ttk.LabelFrame(main_frame, text="💾 Configuration", padding=10)
        config_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(config_frame, text="💾 Save Config", command=self.save_config).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(config_frame, text="📂 Load Config", command=self.load_config).pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progress", padding=10)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 5))
        
        self.status_label = ttk.Label(progress_frame, text="Ready to process videos (ENHANCED - Custom fonts & settings)", foreground="green")
        self.status_label.pack(anchor="w")

        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        self.process_button = ttk.Button(
            button_frame, 
            text="✅ Process Videos (ENHANCED)", 
            command=self.start_processing
        )
        self.process_button.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.cancel_button = ttk.Button(
            button_frame, 
            text="❌ Cancel", 
            command=self.cancel_processing,
            state="disabled"
        )
        self.cancel_button.pack(side="right", padx=(5, 0))

        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def on_transcription_toggle(self):
        """Handle transcription checkbox toggle"""
        if not self.use_transcription_var.get():
            self.subtitle_highlighted_var.set(False)
            self.highlighted_cb.configure(state="disabled")
        else:
            self.highlighted_cb.configure(state="normal")
            self.subtitle_highlighted_var.set(True)

    def select_videos(self):
        filetypes = [
            ("Video Files", "*.mp4 *.mov *.mkv *.avi *.wmv *.flv *.webm"),
            ("MP4 Files", "*.mp4"),
            ("MOV Files", "*.mov"),
            ("All Files", "*.*")
        ]
        
        self.input_videos = filedialog.askopenfilenames(
            title="Select Input Videos",
            filetypes=filetypes
        )
        
        if self.input_videos:
            count = len(self.input_videos)
            self.video_label.config(
                text=f"{count} video(s) selected", 
                foreground="blue"
            )
        else:
            self.video_label.config(text="No videos selected", foreground="gray")

    def select_music(self):
        filetypes = [
            ("Audio Files", "*.mp3 *.wav *.aac *.m4a *.ogg *.flac *.wma"),
            ("MP3 Files", "*.mp3"),
            ("WAV Files", "*.wav"),
            ("All Files", "*.*")
        ]
        
        self.background_music = filedialog.askopenfilename(
            title="Select Background Music (Optional)",
            filetypes=filetypes
        )
        
        if self.background_music:
            filename = os.path.basename(self.background_music)
            self.music_label.config(text=f"♪ {filename}", foreground="blue")
        else:
            self.music_label.config(text="No music selected", foreground="gray")

    def select_output(self):
        self.output_dir = filedialog.askdirectory(title="Select Output Folder")
        
        if self.output_dir:
            self.output_label.config(text=f"📁 {self.output_dir}", foreground="blue")
        else:
            self.output_label.config(text="No output folder selected", foreground="gray")

    def update_progress(self):
        """Update progress bar - thread safe"""
        try:
            current_value = self.progress["value"]
            step_size = 100 / (len(self.input_videos) * 5)
            new_value = min(current_value + step_size, 100)
            self.progress["value"] = new_value
        except:
            pass

    def cancel_processing(self):
        """Cancel the current processing"""
        if self.is_processing:
            logging.info("🛑 Cancellation requested by user")
            self.is_processing = False
            self.status_label.config(text="Cancellation requested...", foreground="orange")
            cleanup_resources()

    def start_processing(self):
        """Start video processing with validation"""
        if self.is_processing:
            return
        
        if not self.input_videos:
            messagebox.showerror("Error", "Please select at least one video file")
            return
        
        if not self.output_dir:
            messagebox.showerror("Error", "Please select an output folder")
            return
        
        has_processing = (
            self.use_transcription_var.get() or 
            self.add_title_var.get() or 
            self.background_music or 
            self.use_auto_editor_var.get()
        )
        
        if not has_processing:
            result = messagebox.askyesno(
                "No Processing Options", 
                "No processing options selected. Videos will be copied as-is. Continue?"
            )
            if not result:
                return

        self.is_processing = True
        self.process_button.config(state="disabled", text="Processing ENHANCED...")
        self.cancel_button.config(state="normal")
        self.status_label.config(text="Initializing ENHANCED processing with custom settings...", foreground="orange")
        self.progress["value"] = 0
        self.progress["maximum"] = 100
        self.root.update()

        self.processing_thread = threading.Thread(target=self.process_videos, daemon=True)
        self.processing_thread.start()

    def process_videos(self):
        """Process all videos with ENHANCED customizable settings"""
        successful = 0
        failed = 0
        
        try:
            for i, input_video in enumerate(self.input_videos, 1):
                if not self.is_processing:
                    logging.info("Processing cancelled by user")
                    break
                
                try:
                    if not os.path.exists(input_video):
                        raise FileNotFoundError(f"Input video not found: {input_video}")
                    
                    video_name = os.path.basename(input_video)
                    self.root.after(0, lambda v=video_name, i=i: self.status_label.config(
                        text=f"ENHANCED processing {i}/{len(self.input_videos)}: {v[:40]}...", 
                        foreground="blue"
                    ))
                    
                    base_name = Path(input_video).stem
                    safe_base_name = re.sub(r'[^\w\-_\.]', '_', base_name)
                    output_path = os.path.join(self.output_dir, f"{safe_base_name}_enhanced.mp4")
                    
                    counter = 1
                    while os.path.exists(output_path):
                        output_path = os.path.join(
                            self.output_dir, 
                            f"{safe_base_name}_enhanced_{counter}.mp4"
                        )
                        counter += 1
                    
                    def progress_callback():
                        if self.is_processing:
                            self.root.after(0, self.update_progress)
                        return self.is_processing
                    
                    start_time = time.time()
                    logging.info(f"Starting ENHANCED processing of {video_name} with custom settings")
                    
                    process_video_with_settings(
                        input_video=input_video,
                        output_video=output_path,
                        background_music=self.background_music if self.background_music else None,
                        subtitle_individual=False,
                        subtitle_highlighted=self.subtitle_highlighted_var.get(),
                        add_title=self.add_title_var.get(),
                        use_auto_editor=self.use_auto_editor_var.get(),
                        use_transcription=self.use_transcription_var.get(),
                        progress_callback=progress_callback,
                        min_subtitle_duration=self.min_duration_var.get(),
                        max_words_per_subtitle=self.max_words_var.get(),
                        subtitle_color=self.subtitle_color,
                        border_color=self.border_color,
                        music_volume=self.music_volume_var.get(),
                        subtitle_font=self.subtitle_font,
                        subtitle_font_size=self.subtitle_font_size,
                        subtitle_alignment=self.subtitle_alignment,
                        title_font=self.title_font,
                        title_font_size=self.title_font_size,
                        title_alignment=self.title_alignment
                    )
                    
                    if not self.is_processing:
                        logging.info(f"Processing cancelled during {video_name}")
                        if os.path.exists(output_path):
                            try:
                                os.remove(output_path)
                            except:
                                pass
                        break
                    
                    if not os.path.exists(output_path):
                        raise Exception("Output file was not created")
                    
                    processing_time = time.time() - start_time
                    successful += 1
                    logging.info(f"✅ ENHANCED processing complete: {video_name} ({processing_time:.1f}s)")
                    
                except Exception as e:
                    failed += 1
                    error_msg = f"Failed to process {os.path.basename(input_video)}: {str(e)}"
                    logging.error(f"❌ {error_msg}")
                    
                    self.root.after(0, lambda msg=error_msg: threading.Thread(
                        target=lambda: messagebox.showerror("Processing Error", msg),
                        daemon=True
                    ).start())
                    
                    self.root.after(0, lambda v=os.path.basename(input_video): self.status_label.config(
                        text=f"Error processing {v}", 
                        foreground="red"
                    ))
                    continue
                
                progress_value = (i / len(self.input_videos)) * 100
                self.root.after(0, lambda p=progress_value: setattr(self.progress, 'value', p))
            
        except Exception as e:
            logging.error(f"Critical error in ENHANCED processing: {e}")
            self.root.after(0, lambda: messagebox.showerror("Critical Error", f"ENHANCED processing failed: {e}"))
        
        finally:
            cleanup_resources()
            self.root.after(0, lambda: self.progress.configure(value=100))
            
            if not self.is_processing:
                final_message = f"Processing cancelled. {successful} completed, {failed} failed."
                self.root.after(0, lambda: self.status_label.config(text=final_message, foreground="orange"))
                if successful > 0 or failed > 0:
                    self.root.after(0, lambda: messagebox.showwarning("Cancelled", final_message))
            elif failed == 0 and successful > 0:
                final_message = f"✅ All {successful} videos processed with ENHANCED features!"
                self.root.after(0, lambda: self.status_label.config(text=final_message, foreground="green"))
                self.root.after(0, lambda: messagebox.showinfo("Success", final_message))
            elif successful > 0:
                final_message = f"ENHANCED processing completed: {successful} successful, {failed} failed."
                self.root.after(0, lambda: self.status_label.config(text=final_message, foreground="orange"))
                self.root.after(0, lambda: messagebox.showwarning("Partial Success", final_message))
            else:
                final_message = "No videos were processed successfully."
                self.root.after(0, lambda: self.status_label.config(text=final_message, foreground="red"))
                self.root.after(0, lambda: messagebox.showerror("Processing Failed", final_message))
            
            self.root.after(0, lambda: self.process_button.config(state="normal", text="✅ Process Videos (ENHANCED)"))
            self.root.after(0, lambda: self.cancel_button.config(state="disabled"))
            self.root.after(0, lambda: setattr(self, "is_processing", False))

def main():
    """ENHANCED main application entry point with customizable subtitle settings"""
    required_tools = ["ffmpeg", "ffprobe"]
    missing_tools = []
    
    for tool in required_tools:
        try:
            subprocess.run([tool, "-version"], capture_output=True, check=True, timeout=10, 
                         encoding='utf-8', errors='replace')
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            missing_tools.append(tool)
    
    if missing_tools:
        error_msg = f"Missing required tools: {', '.join(missing_tools)}\n\nPlease install FFmpeg and ensure it's in your PATH."
        print(f"❌ {error_msg}")
        
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing Dependencies", error_msg)
            return
        except:
            pass
        return
    
    try:
        root = tk.Tk()
        
        try:
            style = ttk.Style()
            if "clam" in style.theme_names():
                style.theme_use("clam")
        except:
            pass
        
        app = VideoProcessorGUI(root)
        
        def on_closing():
            if app.is_processing:
                if messagebox.askokcancel("Processing in Progress", 
                                        "ENHANCED video processing is in progress. Closing now may corrupt output files. Are you sure?"):
                    app.is_processing = False
                    cleanup_resources()
                    root.destroy()
            else:
                cleanup_resources()
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        logging.info("✅ ENHANCED Video Processor started - Custom fonts, sizes, alignments, colors, and volumes")
        root.mainloop()
        
    except Exception as e:
        error_msg = f"Failed to start ENHANCED application: {e}"
        logging.error(error_msg)
        print(f"❌ {error_msg}")
    
    finally:
        cleanup_resources()

if __name__ == "__main__":
    main()