import os
import subprocess
import json
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
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
import gc

logging.basicConfig(level=logging.INFO, format="🔹 %(message)s")

# Global list to track temporary files for cleanup
TEMP_FILES = []
ACTIVE_PROCESSES = []

def cleanup_resources():
    """Clean up all temporary files and processes"""
    global TEMP_FILES, ACTIVE_PROCESSES
    
    # Terminate any active processes
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
            ACTIVE_PROCESSES.remove(proc)
    
    # Clean up temporary files
    for temp_file in TEMP_FILES[:]:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.debug(f"Cleaned up: {temp_file}")
        except Exception as e:
            logging.warning(f"Could not remove {temp_file}: {e}")
        finally:
            TEMP_FILES.remove(temp_file)
    
    # Force garbage collection
    gc.collect()

# Register cleanup function
atexit.register(cleanup_resources)

# Handle Ctrl+C gracefully
def signal_handler(signum, frame):
    logging.info("Received interrupt signal, cleaning up...")
    cleanup_resources()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Load video titles
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
    """Run subprocess with proper resource management and timeout"""
    global ACTIVE_PROCESSES
    
    proc = None
    try:
        # Set default kwargs for Popen
        popen_kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE, 
            'text': True
        }
        
        # Add any additional kwargs (excluding timeout and check)
        for k, v in kwargs.items():
            if k not in ['timeout', 'check', 'capture_output']:
                popen_kwargs[k] = v
        
        # Start process
        proc = subprocess.Popen(cmd, **popen_kwargs)
        ACTIVE_PROCESSES.append(proc)
        
        # Wait for completion with timeout
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            logging.warning(f"Process timed out after {timeout}s: {' '.join(cmd[:3])}")
            proc.kill()
            stdout, stderr = proc.communicate()
            raise subprocess.TimeoutExpired(cmd, timeout, output=stdout, stderr=stderr)
        
        # Remove from active processes
        if proc in ACTIVE_PROCESSES:
            ACTIVE_PROCESSES.remove(proc)
        
        # Check return code if requested
        check_flag = kwargs.get('check', True)
        if check_flag and proc.returncode != 0:
            error_msg = f"Command failed with return code {proc.returncode}: {' '.join(cmd[:5])}"
            if stderr:
                error_msg += f"\nError output: {stderr[:500]}"
            raise subprocess.CalledProcessError(proc.returncode, cmd, stdout, stderr)
        
        # Create result object similar to subprocess.run
        class Result:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr
        
        return Result(proc.returncode, stdout, stderr)
        
    except Exception as e:
        # Clean up process if it exists
        if proc is not None:
            try:
                if proc in ACTIVE_PROCESSES:
                    ACTIVE_PROCESSES.remove(proc)
                if proc.poll() is None:  # Process still running
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
            '-of', 'json', file_path
        ], timeout=30)
        
        duration_json = json.loads(result.stdout)
        duration = float(duration_json["format"]["duration"])
        
        # Validate duration
        if duration <= 0 or duration > 86400:  # Max 24 hours
            logging.warning(f"Invalid duration {duration}s, using default")
            return 300.0
        
        return duration
        
    except Exception as e:
        logging.warning(f"Could not get video duration: {e}")
        return 300.0  # Default 5 minutes

def transcribe_audio_fixed(audio_path, progress_callback=None, max_duration=1800):
    """
    Fixed transcription with proper resource management and loop prevention
    """
    logging.info(f"🧠 Transcribing: {audio_path}")
    
    # Validate input file
    if not os.path.exists(audio_path):
        logging.error(f"Audio file not found: {audio_path}")
        return []
    
    model = None
    try:
        # Get audio duration with validation
        try:
            probe = ffmpeg.probe(audio_path)
            duration = float(probe['format']['duration'])
        except Exception as e:
            logging.warning(f"Could not get audio duration: {e}, using default")
            duration = 300.0
        
        # Prevent processing of extremely long files (max 30 minutes)
        if duration > max_duration:
            logging.warning(f"Audio too long ({duration}s), truncating to {max_duration}s")
            duration = max_duration
        
        if duration <= 0:
            logging.error("Invalid audio duration")
            return []
        
        logging.info(f"Audio duration: {duration:.1f} seconds")
        
        # Initialize model with better settings
        model = WhisperModel("small", device="cpu", compute_type="int8")
        all_words = []
        
        # For shorter files, process in one go
        if duration <= 180:  # 3 minutes or less
            logging.info("Processing short audio file in single pass")
            try:
                segments, _ = model.transcribe(
                    audio_path, 
                    beam_size=5, 
                    word_timestamps=True, 
                    language="en",
                    condition_on_previous_text=False
                )
                
                for segment in segments:
                    if not hasattr(segment, 'words') or not segment.words:
                        continue
                        
                    for w in segment.words:
                        if w.word and w.word.strip() and hasattr(w, 'start') and hasattr(w, 'end'):
                            if w.start >= 0 and w.end > w.start and w.end - w.start <= 10:
                                all_words.append({
                                    "word": w.word.strip(),
                                    "start": w.start,
                                    "end": w.end
                                })
                
                if progress_callback:
                    try:
                        progress_callback()
                    except:
                        pass
                        
            except Exception as e:
                logging.error(f"Single-pass transcription failed: {e}")
                return []
        
        else:
            # For longer files, use chunked processing with strict limits
            chunk_duration = 90  # 1.5 minutes per chunk
            max_chunks = min(10, int(duration / chunk_duration) + 1)  # Maximum 10 chunks
            
            if max_chunks > 10:
                chunk_duration = duration / 10  # Adjust chunk size
                max_chunks = 10
            
            logging.info(f"Processing in {max_chunks} chunks of {chunk_duration:.1f}s each")
            
            for i in range(max_chunks):
                start_time = i * chunk_duration
                end_time = min(start_time + chunk_duration, duration)
                
                # Skip if chunk is too small
                if end_time - start_time < 5.0:
                    logging.info(f"Skipping chunk {i+1} (too small: {end_time - start_time:.1f}s)")
                    continue
                
                logging.info(f"Processing chunk {i+1}/{max_chunks} ({start_time:.1f}s - {end_time:.1f}s)")
                
                # Create unique temporary file
                chunk_path = f"temp_chunk_{i}_{int(time.time())}_{os.getpid()}.wav"
                TEMP_FILES.append(chunk_path)
                
                try:
                    # Extract chunk with strict timeout
                    run_subprocess_safe([
                        "ffmpeg", "-y", "-i", audio_path,
                        "-ss", str(start_time), "-t", str(min(chunk_duration, end_time - start_time)),
                        "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                        chunk_path
                    ], timeout=90)  # 90 second timeout for extraction
                    
                    # Verify chunk was created and has content
                    if not os.path.exists(chunk_path):
                        logging.warning(f"Chunk {i+1} was not created, skipping")
                        continue
                        
                    chunk_size = os.path.getsize(chunk_path)
                    if chunk_size < 1000:  # Less than 1KB
                        logging.warning(f"Chunk {i+1} too small ({chunk_size} bytes), skipping")
                        continue
                    
                    # Transcribe chunk with timeout protection
                    segments, _ = model.transcribe(
                        chunk_path, 
                        beam_size=5, 
                        word_timestamps=True, 
                        language="en",
                        condition_on_previous_text=False
                    )
                    
                    # Process segments with validation
                    word_count = 0
                    for segment in segments:
                        if not hasattr(segment, 'words') or not segment.words:
                            continue
                            
                        for w in segment.words:
                            if w.word and w.word.strip() and hasattr(w, 'start') and hasattr(w, 'end'):
                                # Validate timestamps
                                if w.start < 0 or w.end < w.start or w.end - w.start > 10:
                                    continue
                                    
                                adjusted_word = {
                                    "word": w.word.strip(),
                                    "start": w.start + start_time,
                                    "end": w.end + start_time
                                }
                                all_words.append(adjusted_word)
                                word_count += 1
                    
                    logging.info(f"Chunk {i+1} processed: {word_count} words")
                    
                except Exception as e:
                    logging.warning(f"Failed to process chunk {i+1}: {e}")
                    
                finally:
                    # Clean up chunk immediately
                    if os.path.exists(chunk_path):
                        try:
                            os.remove(chunk_path)
                            if chunk_path in TEMP_FILES:
                                TEMP_FILES.remove(chunk_path)
                        except Exception as e:
                            logging.warning(f"Could not remove chunk file: {e}")
                    
                    # Update progress
                    if progress_callback:
                        try:
                            progress_callback()
                        except:
                            pass
        
        # Sort and validate final results
        if all_words:
            all_words = sorted([w for w in all_words if w['start'] < w['end']], key=lambda x: x["start"])
            logging.info(f"Transcription complete: {len(all_words)} words total")
        else:
            logging.warning("No words extracted from transcription")
        
        return all_words
        
    except Exception as e:
        logging.error(f"Transcription failed: {e}")
        return []
    
    finally:
        # Ensure cleanup
        if model is not None:
            try:
                del model
            except:
                pass
        gc.collect()

def group_words_into_subtitles_fixed(words, max_words_per_group=6, min_duration=1.5, max_duration=4.0, min_gap=0.3):
    """
    FIXED: Improved word grouping with better timing and longer subtitle durations
    """
    if not words:
        return []
    
    groups = []
    current_group = []
    current_start = words[0]["start"]
    
    for i, word in enumerate(words):
        # Validate word data
        if not isinstance(word, dict) or 'word' not in word or 'start' not in word or 'end' not in word:
            continue
            
        # Check if we should start a new group
        should_start_new = False
        
        if current_group:
            # Calculate current group duration if we add this word
            potential_duration = word["end"] - current_start
            
            # Check for natural breaks
            prev_word = words[i-1] if i > 0 else None
            if prev_word:
                gap = word["start"] - prev_word["end"]
                has_natural_break = (
                    prev_word["word"].strip().endswith(('.', '!', '?', ',')) or
                    gap > min_gap * 3  # Increased gap threshold
                )
            else:
                has_natural_break = False
            
            should_start_new = (
                len(current_group) >= max_words_per_group or
                potential_duration >= max_duration or
                (has_natural_break and len(current_group) >= 3 and potential_duration >= min_duration)
            )
        
        if should_start_new and current_group:
            # Finalize current group with minimum duration enforcement
            group_duration = current_group[-1]["end"] - current_start
            
            # Extend subtitle duration if too short
            if group_duration < min_duration:
                extended_end = current_start + min_duration
                # Make sure we don't overlap with next word
                if i < len(words) and extended_end > words[i]["start"]:
                    extended_end = max(current_group[-1]["end"], words[i]["start"] - 0.1)
            else:
                extended_end = current_group[-1]["end"]
            
            text = " ".join([w["word"].strip() for w in current_group if w.get("word", "").strip()])
            if text.strip():  # Only add non-empty groups
                groups.append(SubtitleGroup(
                    words=current_group.copy(),
                    start=current_start,
                    end=extended_end,
                    text=text.strip()
                ))
            current_group = []
            current_start = word["start"]
        
        current_group.append(word)
    
    # Handle remaining words with minimum duration
    if current_group:
        group_duration = current_group[-1]["end"] - current_start
        
        # Extend duration if too short
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
    
    # Post-process to ensure no overlaps and minimum gaps
    for i in range(len(groups) - 1):
        current_group = groups[i]
        next_group = groups[i + 1]
        
        # Ensure minimum gap between subtitles
        min_gap_between = 0.1
        if current_group.end + min_gap_between > next_group.start:
            # Adjust current group end time
            groups[i].end = max(current_group.start + 0.5, next_group.start - min_gap_between)
    
    logging.info(f"Created {len(groups)} subtitle groups with improved timing")
    return groups

def generate_highlighted_subtitle_ass_fixed(subtitle_groups, ass_path):
    """
    FIXED: Generate highlighted subtitle ASS with better formatting and timing
    """
    try:
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("""[Script Info]
Title: Bottom Center Subtitles
ScriptType: v4.00+
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: BottomCenter,Arial,18,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,3,2,1,2,40,40,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
            
            for i, group in enumerate(subtitle_groups):
                # Clean and format text
                text = group.text.strip()
                if not text:
                    continue
                
                # Validate and fix timing
                start_time = max(0, group.start)
                end_time = max(start_time + 1.5, group.end)  # Minimum 1.5 second duration
                
                # Escape special characters for ASS format
                text_escaped = text.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
                
                # Create formatted text with fade effects and better styling
                formatted_text = f"{{\\fad(200,200)\\bord2\\shad1\\c&HFFFFFF&\\3c&H000000&\\4c&H000000&}} {text_escaped}"
                
                f.write(f"Dialogue: 0,{format_time(start_time)},{format_time(end_time)},BottomCenter,,0,0,0,,{formatted_text}\n")
                
        logging.info(f"Generated ASS file with {len(subtitle_groups)} subtitles")
                
    except Exception as e:
        logging.error(f"Failed to generate ASS file: {e}")
        raise

def create_drawtext_subtitles_fixed(subtitle_groups, video_path, output_path, max_filters=8):
    """
    FIXED: Optimized drawtext subtitles with better timing and resource management
    """
    if not subtitle_groups:
        return False
    
    filter_file = None
    try:
        # Process more groups but with reasonable limits
        groups_to_process = subtitle_groups[:max_filters] if len(subtitle_groups) > max_filters else subtitle_groups
        
        # Create temporary filter file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            filter_file = f.name
            TEMP_FILES.append(filter_file)
            
            drawtext_filters = []
            for i, group in enumerate(groups_to_process):
                # Clean and escape text
                text = group.text.strip()
                if not text:
                    continue
                
                # Better text cleaning while preserving readability
                text = re.sub(r'[^\w\s\.\,\!\?\-\'\"\(\)]', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                text_escaped = text.replace("'", "\\'").replace(":", "\\:").replace('\\', '\\\\')
                
                # FIXED: Ensure minimum duration and proper timing
                start_time = max(0, group.start)
                duration = max(1.5, group.end - group.start)  # Minimum 1.5 seconds
                end_time = start_time + duration
                
                # Better positioning and styling
                drawtext_filter = (
                    f"drawtext=text='{text_escaped}'"
                    f":fontsize=36"
                    f":fontcolor=white"
                    f":borderw=2"
                    f":bordercolor=black"
                    f":shadowx=1"  
                    f":shadowy=1"
                    f":shadowcolor=black@0.8"
                    f":box=1"
                    f":boxcolor=black@0.7"
                    f":boxborderw=8"
                    f":x=(w-text_w)/2"
                    f":y=h-text_h-40"
                    f":enable='between(t,{start_time:.3f},{end_time:.3f})'"
                )
                drawtext_filters.append(drawtext_filter)
            
            if drawtext_filters:
                filter_complex = ",".join(drawtext_filters)
                f.write(filter_complex)
                logging.info(f"Created filter with {len(drawtext_filters)} drawtext commands")
            else:
                return False
        
        if drawtext_filters:
            # Execute with extended timeout for longer videos
            run_subprocess_safe([
                "ffmpeg", "-y", "-i", video_path,
                "-filter_complex_script", filter_file,
                "-map", "0:a", "-c:v", "libx264", "-crf", "23", "-preset", "medium",
                "-c:a", "copy", "-movflags", "+faststart", output_path
            ], timeout=900)  # 15 minute timeout
            
            return True
    
    except Exception as e:
        logging.warning(f"Drawtext optimization failed: {e}")
        return False
    
    finally:
        # Clean up filter file
        if filter_file and os.path.exists(filter_file):
            try:
                os.remove(filter_file)
                if filter_file in TEMP_FILES:
                    TEMP_FILES.remove(filter_file)
            except:
                pass

def get_title_for_video(input_video):
    """Get title for video from mapping"""
    for entry in VIDEO_TITLE_MAP:
        if os.path.normpath(entry["slide_topic"]) == os.path.normpath(input_video):
            return entry["title_text"]
    return "Video Tutorial"

def generate_hello_world_ass(ass_path, video_duration, title_text):
    """Generate title overlay ASS with validation"""
    try:
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write("""[Script Info]
Title: Title Overlay
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: TitleStyle,Arial,56,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,3,2,8,20,20,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
            # Validate duration and title
            if video_duration <= 0:
                video_duration = 10
            
            display_duration = min(15, max(3, video_duration * 0.2))
            clean_title = re.sub(r'[^\w\s\.\,\!\?\-]', '', title_text).strip()
            
            if clean_title:
                f.write(f"Dialogue: 0,{format_time(0)},{format_time(display_duration)},TitleStyle,,0,0,0,,{{\\fad(500,500)}}{clean_title.upper()}\n")
                
    except Exception as e:
        logging.error(f"Failed to generate title ASS: {e}")
        raise

def add_background_music_simple(video_path, music_path, output_path, music_volume=0.15):
    """
    Simplified background music addition without complex ducking
    """
    try:
        run_subprocess_safe([
            "ffmpeg", "-y", "-i", video_path, "-i", music_path,
            "-filter_complex",
            f"[1:a]aloop=loop=-1:size=2e+09,volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", output_path
        ], timeout=600)
        
    except Exception as e:
        logging.error(f"Background music addition failed: {e}")
        raise

def process_video(input_video, output_video, background_music, subtitle_individual, subtitle_highlighted, add_title, use_auto_editor, use_transcription, progress_callback=None):
    """
    FIXED: Main video processing function with improved subtitle timing
    """
    # Generate unique temporary file names
    timestamp = int(time.time())
    pid = os.getpid()
    base_name = Path(input_video).stem
    
    temp_files = {
        'auto_edited': f"auto_{base_name}_{timestamp}_{pid}.mp4",
        'audio_path': f"temp_{base_name}_{timestamp}_{pid}.wav", 
        'highlighted_ass': f"highlighted_{base_name}_{timestamp}_{pid}.ass",
        'title_ass': f"title_{base_name}_{timestamp}_{pid}.ass",
        'final_subs': f"final_subs_{base_name}_{timestamp}_{pid}.mp4",
        'final_music': f"final_music_{base_name}_{timestamp}_{pid}.mp4"
    }
    
    # Add to global temp files list
    TEMP_FILES.extend(temp_files.values())
    
    try:
        # Validate input
        if not os.path.exists(input_video):
            raise FileNotFoundError(f"Input video not found: {input_video}")
        
        # If no processing options selected, copy input to output
        if not (subtitle_individual or subtitle_highlighted or add_title or background_music or use_auto_editor):
            logging.info(f"📋 No processing options selected, copying {input_video} to {output_video}")
            run_subprocess_safe([
                "ffmpeg", "-y", "-i", input_video,
                "-c:v", "copy", "-c:a", "copy", output_video
            ], timeout=300)
            if progress_callback:
                progress_callback()
            return

        # Apply auto-editor if enabled
        video_to_process = input_video
        if use_auto_editor:
            logging.info(f"⚙️ Auto-editing: {input_video}")
            try:
                run_subprocess_safe([
                    "auto-editor", input_video, "-o", temp_files['auto_edited'],
                    "--no-open", "--frame-rate", "30", "--silent-speed", "99999"
                ], timeout=600)
                video_to_process = temp_files['auto_edited']
                if progress_callback:
                    progress_callback()
            except Exception as e:
                logging.warning(f"Auto-editor failed, using original video: {e}")

        # Transcription and subtitle generation
        words = []
        subtitle_groups = []
        if use_transcription and (subtitle_individual or subtitle_highlighted or background_music):
            logging.info(f"🔊 Extracting audio from: {video_to_process}")
            
            # Extract audio with timeout
            run_subprocess_safe([
                "ffmpeg", "-y", "-i", video_to_process,
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", 
                temp_files['audio_path']
            ], timeout=120)
            
            if progress_callback:
                progress_callback()
            
            # Use fixed transcription
            words = transcribe_audio_fixed(temp_files['audio_path'], progress_callback)
            
            if subtitle_highlighted and words:
                # FIXED: Use the improved grouping function
                subtitle_groups = group_words_into_subtitles_fixed(words)
                logging.info(f"Generated {len(subtitle_groups)} subtitle groups from {len(words)} words")

        # Generate subtitle files
        if subtitle_highlighted and use_transcription and subtitle_groups:
            logging.info("Generating highlighted group subtitles with fixed timing")
            # FIXED: Use the improved ASS generation
            generate_highlighted_subtitle_ass_fixed(subtitle_groups, temp_files['highlighted_ass'])
        
        if add_title:
            duration = get_video_duration(video_to_process)
            title_text = get_title_for_video(input_video)
            generate_hello_world_ass(temp_files['title_ass'], duration, title_text)

        # Apply subtitles and overlays
        if subtitle_highlighted or add_title:
            logging.info("🎬 Applying subtitles and overlays")
            
            # FIXED: Always use ASS subtitles for better compatibility and timing
            filter_parts = []
            if subtitle_highlighted and use_transcription and subtitle_groups:
                filter_parts.append(f"subtitles={temp_files['highlighted_ass']}")
            if add_title:
                filter_parts.append(f"subtitles={temp_files['title_ass']}")
            
            if filter_parts:
                filter_complex = ",".join(filter_parts)
                run_subprocess_safe([
                    "ffmpeg", "-y", "-i", video_to_process,
                    "-filter_complex", filter_complex,
                    "-map", "0:a", "-c:v", "libx264", "-crf", "23", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", temp_files['final_subs']
                ], timeout=1200)  # Extended timeout for subtitle processing
            else:
                # No valid subtitles, just copy
                run_subprocess_safe([
                    "ffmpeg", "-y", "-i", video_to_process,
                    "-c:v", "copy", "-c:a", "copy", temp_files['final_subs']
                ], timeout=300)
            
            if progress_callback:
                progress_callback()
        else:
            # No subtitles or title, just copy
            run_subprocess_safe([
                "ffmpeg", "-y", "-i", video_to_process,
                "-c:v", "copy", "-c:a", "copy", temp_files['final_subs']
            ], timeout=300)
            if progress_callback:
                progress_callback()

        # Add background music if specified
        if background_music and os.path.exists(background_music):
            logging.info("🎵 Adding background music")
            add_background_music_simple(
                temp_files['final_subs'], background_music, temp_files['final_music']
            )
            # Move final result
            if os.path.exists(temp_files['final_music']):
                os.rename(temp_files['final_music'], output_video)
            else:
                raise Exception("Failed to create final video with music")
        else:
            # Move subtitled video to final output
            if os.path.exists(temp_files['final_subs']):
                os.rename(temp_files['final_subs'], output_video)
            else:
                raise Exception("Failed to create final video")

        if progress_callback:
            progress_callback()
        
        logging.info(f"✅ Successfully processed: {output_video}")

    except Exception as e:
        logging.error(f"❌ Error processing {input_video}: {e}")
        raise
    
    finally:
        # Clean up temporary files immediately
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
        self.root.title("Video Processor - Fixed Subtitle Timing")
        self.root.geometry("650x580")
        self.root.resizable(True, True)
        
        self.input_videos = []
        self.background_music = ""
        self.output_dir = ""
        self.is_processing = False
        self.processing_thread = None
        
        # Create GUI elements
        self.create_widgets()
        
        # Center the window
        self.center_window()

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root)
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
        
        # Transcription option
        self.use_transcription_var = tk.BooleanVar(value=True)
        transcription_cb = ttk.Checkbutton(
            options_frame, 
            text="🎤 Generate Subtitles (Transcription Required)", 
            variable=self.use_transcription_var,
            command=self.on_transcription_toggle
        )
        transcription_cb.pack(anchor="w", pady=(0, 5))
        
        # Subtitle options (indented to show dependency)
        subtitle_frame = ttk.Frame(options_frame)
        subtitle_frame.pack(fill="x", padx=(20, 0), pady=(0, 5))
        
        self.subtitle_individual_var = tk.BooleanVar(value=False)
        self.individual_cb = ttk.Checkbutton(
            subtitle_frame, 
            text="📝 Individual Word Subtitles (Disabled - Causes Issues)", 
            variable=self.subtitle_individual_var,
            state="disabled"  # Disabled to prevent issues
        )
        self.individual_cb.pack(anchor="w", pady=2)
        
        self.subtitle_highlighted_var = tk.BooleanVar(value=True)
        self.highlighted_cb = ttk.Checkbutton(
            subtitle_frame, 
            text="🔤 Highlighted Group Subtitles (FIXED - Better Timing)", 
            variable=self.subtitle_highlighted_var
        )
        self.highlighted_cb.pack(anchor="w", pady=2)
        
        # Other options
        self.add_title_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="📋 Add Title Overlay", variable=self.add_title_var).pack(anchor="w", pady=2)
        
        self.use_auto_editor_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="✂️ Use Auto-Editor (Remove Silence)", variable=self.use_auto_editor_var).pack(anchor="w", pady=2)

        # Subtitle Settings Frame
        subtitle_settings_frame = ttk.LabelFrame(main_frame, text="🎬 Subtitle Settings (Advanced)", padding=10)
        subtitle_settings_frame.pack(fill="x", pady=(0, 10))
        
        # Min duration setting
        duration_frame = ttk.Frame(subtitle_settings_frame)
        duration_frame.pack(fill="x", pady=2)
        ttk.Label(duration_frame, text="Minimum subtitle duration:").pack(side="left")
        self.min_duration_var = tk.DoubleVar(value=1.5)
        duration_spinbox = ttk.Spinbox(duration_frame, from_=0.5, to=5.0, increment=0.1, 
                                     textvariable=self.min_duration_var, width=8)
        duration_spinbox.pack(side="right")
        ttk.Label(duration_frame, text="seconds").pack(side="right", padx=(0, 5))
        
        # Max words setting
        words_frame = ttk.Frame(subtitle_settings_frame)
        words_frame.pack(fill="x", pady=2)
        ttk.Label(words_frame, text="Max words per subtitle:").pack(side="left")
        self.max_words_var = tk.IntVar(value=6)
        words_spinbox = ttk.Spinbox(words_frame, from_=3, to=12, increment=1, 
                                  textvariable=self.max_words_var, width=8)
        words_spinbox.pack(side="right")

        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progress", padding=10)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 5))
        
        self.status_label = ttk.Label(progress_frame, text="Ready to process videos", foreground="green")
        self.status_label.pack(anchor="w")

        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        self.process_button = ttk.Button(
            button_frame, 
            text="🚀 Process Videos", 
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

    def on_transcription_toggle(self):
        """Handle transcription checkbox toggle"""
        if not self.use_transcription_var.get():
            # Disable subtitle options if transcription is disabled
            self.subtitle_highlighted_var.set(False)
            self.highlighted_cb.configure(state="disabled")
        else:
            # Re-enable subtitle options
            self.highlighted_cb.configure(state="normal")
            self.subtitle_highlighted_var.set(True)  # Default to highlighted

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
            step_size = 100 / (len(self.input_videos) * 4)  # 4 steps per video
            new_value = min(current_value + step_size, 100)
            self.progress["value"] = new_value
        except:
            pass  # Ignore errors during progress update

    def cancel_processing(self):
        """Cancel the current processing"""
        if self.is_processing:
            logging.info("🛑 Cancellation requested by user")
            self.is_processing = False
            self.status_label.config(text="Cancellation requested...", foreground="orange")
            
            # Clean up resources
            cleanup_resources()

    def start_processing(self):
        """Start video processing with validation"""
        if self.is_processing:
            return
        
        # Validation
        if not self.input_videos:
            messagebox.showerror("Error", "Please select at least one video file")
            return
        
        if not self.output_dir:
            messagebox.showerror("Error", "Please select an output folder")
            return
        
        # Check if any processing option is selected
        has_processing = (
            self.use_transcription_var.get() or 
            self.add_title_var.get() or 
            self.background_music or 
            self.use_auto_editor_var.get()
        )
        
        if not has_processing:
            result = messagebox.askyesno(
                "No Processing Options", 
                "No processing options are selected. Videos will be copied as-is. Continue?"
            )
            if not result:
                return

        # Start processing
        self.is_processing = True
        self.process_button.config(state="disabled", text="Processing...")
        self.cancel_button.config(state="normal")
        self.status_label.config(text="Initializing processing...", foreground="orange")
        self.progress["value"] = 0
        self.progress["maximum"] = 100
        self.root.update()

        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=self.process_videos, daemon=True)
        self.processing_thread.start()

    def process_videos(self):
        """FIXED: Process all selected videos with improved subtitle settings"""
        successful = 0
        failed = 0
        
        try:
            for i, input_video in enumerate(self.input_videos, 1):
                # Check for cancellation before processing each video
                if not self.is_processing:
                    logging.info("Processing cancelled by user")
                    break
                
                try:
                    # Validate input file exists
                    if not os.path.exists(input_video):
                        raise FileNotFoundError(f"Input video not found: {input_video}")
                    
                    # Update status
                    video_name = os.path.basename(input_video)
                    self.root.after(0, lambda v=video_name, i=i: self.status_label.config(
                        text=f"Processing {i}/{len(self.input_videos)}: {v[:40]}...", 
                        foreground="blue"
                    ))
                    
                    # Generate output path
                    base_name = Path(input_video).stem
                    output_path = os.path.join(self.output_dir, f"{base_name}_processed.mp4")
                    
                    # Ensure unique output filename
                    counter = 1
                    while os.path.exists(output_path):
                        output_path = os.path.join(
                            self.output_dir, 
                            f"{base_name}_processed_{counter}.mp4"
                        )
                        counter += 1
                    
                    # Create a cancellation-aware progress callback
                    def progress_with_cancel_check():
                        if self.is_processing:
                            self.root.after(0, self.update_progress)
                        return self.is_processing  # Return False to signal cancellation
                    
                    # Process video with cancellation support and custom settings
                    start_time = time.time()
                    logging.info(f"Starting processing of {video_name}")
                    
                    # FIXED: Pass custom subtitle settings to processing function
                    process_video_with_settings(
                        input_video=input_video,
                        output_video=output_path,
                        background_music=self.background_music if self.background_music else None,
                        subtitle_individual=False,  # Disabled to prevent issues
                        subtitle_highlighted=self.subtitle_highlighted_var.get(),
                        add_title=self.add_title_var.get(),
                        use_auto_editor=self.use_auto_editor_var.get(),
                        use_transcription=self.use_transcription_var.get(),
                        progress_callback=progress_with_cancel_check,
                        min_subtitle_duration=self.min_duration_var.get(),
                        max_words_per_subtitle=self.max_words_var.get()
                    )
                    
                    # Check if processing was cancelled during execution
                    if not self.is_processing:
                        logging.info(f"Processing cancelled during {video_name}")
                        # Remove partial output file if it exists
                        if os.path.exists(output_path):
                            try:
                                os.remove(output_path)
                            except:
                                pass
                        break
                    
                    # Verify output was created
                    if not os.path.exists(output_path):
                        raise Exception("Output file was not created")
                    
                    processing_time = time.time() - start_time
                    successful += 1
                    logging.info(f"✅ Successfully processed: {video_name} ({processing_time:.1f}s)")
                    
                except Exception as e:
                    failed += 1
                    error_msg = f"Failed to process {os.path.basename(input_video)}: {str(e)}"
                    logging.error(f"❌ {error_msg}")
                    
                    # Show error dialog (non-blocking)
                    self.root.after(0, lambda msg=error_msg: threading.Thread(
                        target=lambda: messagebox.showerror("Processing Error", msg),
                        daemon=True
                    ).start())
                    
                    self.root.after(0, lambda v=os.path.basename(input_video): self.status_label.config(
                        text=f"Error processing {v}", 
                        foreground="red"
                    ))
                    
                    # Don't break the loop, continue with next video
                    continue
                
                # Update progress for completed video
                progress_value = (i / len(self.input_videos)) * 100
                self.root.after(0, lambda p=progress_value: setattr(self.progress, 'value', p))
            
        except Exception as e:
            logging.error(f"Critical error in processing loop: {e}")
            self.root.after(0, lambda: messagebox.showerror("Critical Error", f"Processing failed: {e}"))
        
        finally:
            # Clean up resources
            cleanup_resources()
            
            # Final status update
            self.root.after(0, lambda: self.progress.configure(value=100))
            
            if not self.is_processing:
                # Processing was cancelled
                final_message = f"Processing cancelled. {successful} completed, {failed} failed"
                self.root.after(0, lambda: self.status_label.config(text=final_message, foreground="orange"))
                if successful > 0 or failed > 0:
                    self.root.after(0, lambda: messagebox.showwarning("Cancelled", final_message))
            elif failed == 0 and successful > 0:
                final_message = f"🎉 All {successful} videos processed successfully!"
                self.root.after(0, lambda: self.status_label.config(text=final_message, foreground="green"))
                self.root.after(0, lambda: messagebox.showinfo("Success", final_message))
            elif successful > 0:
                final_message = f"Processing completed: {successful} successful, {failed} failed"
                self.root.after(0, lambda: self.status_label.config(text=final_message, foreground="orange"))
                self.root.after(0, lambda: messagebox.showwarning("Partial Success", final_message))
            else:
                final_message = f"No videos were processed successfully"
                self.root.after(0, lambda: self.status_label.config(text=final_message, foreground="red"))
                self.root.after(0, lambda: messagebox.showerror("Processing Failed", final_message))
            
            # Re-enable interface
            self.root.after(0, lambda: self.process_button.config(state="normal", text="🚀 Process Videos"))
            self.root.after(0, lambda: self.cancel_button.config(state="disabled"))
            self.root.after(0, lambda: setattr(self, "is_processing", False))

def process_video_with_settings(input_video, output_video, background_music, subtitle_individual, subtitle_highlighted, add_title, use_auto_editor, use_transcription, progress_callback=None, min_subtitle_duration=1.5, max_words_per_subtitle=6):
    """
    FIXED: Main video processing function with customizable subtitle settings
    """
    # Generate unique temporary file names
    timestamp = int(time.time())
    pid = os.getpid()
    base_name = Path(input_video).stem
    
    temp_files = {
        'auto_edited': f"auto_{base_name}_{timestamp}_{pid}.mp4",
        'audio_path': f"temp_{base_name}_{timestamp}_{pid}.wav", 
        'highlighted_ass': f"highlighted_{base_name}_{timestamp}_{pid}.ass",
        'title_ass': f"title_{base_name}_{timestamp}_{pid}.ass",
        'final_subs': f"final_subs_{base_name}_{timestamp}_{pid}.mp4",
        'final_music': f"final_music_{base_name}_{timestamp}_{pid}.mp4"
    }
    
    # Add to global temp files list
    TEMP_FILES.extend(temp_files.values())
    
    try:
        # Validate input
        if not os.path.exists(input_video):
            raise FileNotFoundError(f"Input video not found: {input_video}")
        
        # If no processing options selected, copy input to output
        if not (subtitle_individual or subtitle_highlighted or add_title or background_music or use_auto_editor):
            logging.info(f"📋 No processing options selected, copying {input_video} to {output_video}")
            run_subprocess_safe([
                "ffmpeg", "-y", "-i", input_video,
                "-c:v", "copy", "-c:a", "copy", output_video
            ], timeout=300)
            if progress_callback:
                progress_callback()
            return

        # Apply auto-editor if enabled
        video_to_process = input_video
        if use_auto_editor:
            logging.info(f"⚙️ Auto-editing: {input_video}")
            try:
                run_subprocess_safe([
                    "auto-editor", input_video, "-o", temp_files['auto_edited'],
                    "--no-open", "--frame-rate", "30", "--silent-speed", "99999"
                ], timeout=600)
                video_to_process = temp_files['auto_edited']
                if progress_callback:
                    progress_callback()
            except Exception as e:
                logging.warning(f"Auto-editor failed, using original video: {e}")

        # Transcription and subtitle generation
        words = []
        subtitle_groups = []
        if use_transcription and (subtitle_individual or subtitle_highlighted or background_music):
            logging.info(f"🔊 Extracting audio from: {video_to_process}")
            
            # Extract audio with timeout
            run_subprocess_safe([
                "ffmpeg", "-y", "-i", video_to_process,
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", 
                temp_files['audio_path']
            ], timeout=120)
            
            if progress_callback:
                progress_callback()
            
            # Use fixed transcription
            words = transcribe_audio_fixed(temp_files['audio_path'], progress_callback)
            
            if subtitle_highlighted and words:
                # FIXED: Use the improved grouping function with custom settings
                subtitle_groups = group_words_into_subtitles_fixed(
                    words, 
                    max_words_per_group=max_words_per_subtitle,
                    min_duration=min_subtitle_duration
                )
                logging.info(f"Generated {len(subtitle_groups)} subtitle groups with min duration {min_subtitle_duration}s")

        # Generate subtitle files
        if subtitle_highlighted and use_transcription and subtitle_groups:
            logging.info("Generating highlighted group subtitles with fixed timing")
            # FIXED: Use the improved ASS generation
            generate_highlighted_subtitle_ass_fixed(subtitle_groups, temp_files['highlighted_ass'])
        
        if add_title:
            duration = get_video_duration(video_to_process)
            title_text = get_title_for_video(input_video)
            generate_hello_world_ass(temp_files['title_ass'], duration, title_text)

        # Apply subtitles and overlays
        if subtitle_highlighted or add_title:
            logging.info("🎬 Applying subtitles and overlays")
            
            # FIXED: Always use ASS subtitles for better compatibility and timing
            filter_parts = []
            if subtitle_highlighted and use_transcription and subtitle_groups:
                filter_parts.append(f"subtitles={temp_files['highlighted_ass']}")
            if add_title:
                filter_parts.append(f"subtitles={temp_files['title_ass']}")
            
            if filter_parts:
                filter_complex = ",".join(filter_parts)
                run_subprocess_safe([
                    "ffmpeg", "-y", "-i", video_to_process,
                    "-filter_complex", filter_complex,
                    "-map", "0:a", "-c:v", "libx264", "-crf", "23", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", temp_files['final_subs']
                ], timeout=1200)  # Extended timeout for subtitle processing
            else:
                # No valid subtitles, just copy
                run_subprocess_safe([
                    "ffmpeg", "-y", "-i", video_to_process,
                    "-c:v", "copy", "-c:a", "copy", temp_files['final_subs']
                ], timeout=300)
            
            if progress_callback:
                progress_callback()
        else:
            # No subtitles or title, just copy
            run_subprocess_safe([
                "ffmpeg", "-y", "-i", video_to_process,
                "-c:v", "copy", "-c:a", "copy", temp_files['final_subs']
            ], timeout=300)
            if progress_callback:
                progress_callback()

        # Add background music if specified
        if background_music and os.path.exists(background_music):
            logging.info("🎵 Adding background music")
            add_background_music_simple(
                temp_files['final_subs'], background_music, temp_files['final_music']
            )
            # Move final result
            if os.path.exists(temp_files['final_music']):
                os.rename(temp_files['final_music'], output_video)
            else:
                raise Exception("Failed to create final video with music")
        else:
            # Move subtitled video to final output
            if os.path.exists(temp_files['final_subs']):
                os.rename(temp_files['final_subs'], output_video)
            else:
                raise Exception("Failed to create final video")

        if progress_callback:
            progress_callback()
        
        logging.info(f"✅ Successfully processed: {output_video}")

    except Exception as e:
        logging.error(f"❌ Error processing {input_video}: {e}")
        raise
    
    finally:
        # Clean up temporary files immediately
        for temp_file in temp_files.values():
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    if temp_file in TEMP_FILES:
                        TEMP_FILES.remove(temp_file)
                    logging.debug(f"Cleaned up: {temp_file}")
                except Exception as e:
                    logging.warning(f"Could not remove {temp_file}: {e}")

def main():
    """Main application entry point"""
    # Check for required dependencies
    required_tools = ["ffmpeg", "ffprobe"]
    missing_tools = []
    
    for tool in required_tools:
        try:
            subprocess.run([tool, "-version"], capture_output=True, check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            missing_tools.append(tool)
    
    if missing_tools:
        error_msg = f"Missing required tools: {', '.join(missing_tools)}\n\nPlease install FFmpeg and ensure it's in your PATH."
        print(f"❌ {error_msg}")
        
        # Try to show GUI error if possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing Dependencies", error_msg)
            return
        except:
            pass
        return
    
    # Initialize and run GUI
    try:
        root = tk.Tk()
        
        # Configure modern styling if available
        try:
            style = ttk.Style()
            if "clam" in style.theme_names():
                style.theme_use("clam")
        except:
            pass
        
        app = VideoProcessorGUI(root)
        
        # Handle window closing
        def on_closing():
            if app.is_processing:
                if messagebox.askokcancel("Processing in Progress", 
                                        "Video processing is in progress. Closing now may corrupt output files. Are you sure?"):
                    app.is_processing = False
                    cleanup_resources()
                    root.destroy()
            else:
                cleanup_resources()
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the GUI
        logging.info("🚀 Video Processor started with FIXED subtitle timing")
        root.mainloop()
        
    except Exception as e:
        error_msg = f"Failed to start application: {e}"
        logging.error(error_msg)
        print(f"❌ {error_msg}")
    
    finally:
        # Final cleanup
        cleanup_resources()

if __name__ == "__main__":
    main()