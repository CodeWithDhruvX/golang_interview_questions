import os
import subprocess
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from pathlib import Path
import logging
import threading
import time
import shutil
from datetime import datetime
import sys

# Configure logging
def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"video_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file

class DependencyChecker:
    @staticmethod
    def check_dependencies():
        """Check if required dependencies are available"""
        required_tools = {
            'ffmpeg': 'FFmpeg is required for video processing',
            'ffprobe': 'FFprobe is required for video analysis',
            'auto-editor': 'Auto-editor is required for automatic editing'
        }
        
        missing = []
        for tool, description in required_tools.items():
            if not shutil.which(tool):
                missing.append(f"{tool}: {description}")
        
        return missing

class Word:
    def __init__(self, word, start, end):
        self.word = word
        self.start = float(start)
        self.end = float(end)

class VideoProcessor:
    def __init__(self):
        self.whisper_model = None
    
    def get_whisper_model(self):
        """Lazy load Whisper model to save memory"""
        if self.whisper_model is None:
            try:
                from faster_whisper import WhisperModel
                self.whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")
                logging.info("Whisper model loaded successfully")
            except ImportError:
                raise ImportError("faster-whisper is not installed. Please install it with: pip install faster-whisper")
            except Exception as e:
                raise RuntimeError(f"Failed to load Whisper model: {e}")
        return self.whisper_model
    
    @staticmethod
    def format_time(seconds):
        """Format seconds to ASS subtitle time format"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds * 100) % 100)
        return f"{h}:{m:02}:{s:02}.{cs:02}"

    @staticmethod
    def get_video_duration(file_path):
        """Get video duration using ffprobe"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'json', str(file_path)
            ], capture_output=True, text=True, check=True, timeout=30, encoding='utf-8', errors='ignore')
            
            duration_json = json.loads(result.stdout)
            duration = float(duration_json["format"]["duration"])
            logging.info(f"Video duration: {duration:.2f}s for {file_path}")
            return duration
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Timeout getting duration for {file_path}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFprobe failed for {file_path}: {e.stderr}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise RuntimeError(f"Invalid duration data for {file_path}: {e}")

    def transcribe_audio(self, audio_path, progress_callback=None):
        """Transcribe audio file to words with timestamps"""
        try:
            logging.info(f"Starting transcription: {audio_path}")
            if progress_callback:
                progress_callback("Loading Whisper model...")
            
            model = self.get_whisper_model()
            
            if progress_callback:
                progress_callback("Transcribing audio...")
            
            segments, _ = model.transcribe(
                str(audio_path), 
                beam_size=5, 
                word_timestamps=True, 
                language="en",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            words = []
            for segment in segments:
                if hasattr(segment, 'words') and segment.words:
                    for w in segment.words:
                        if w.word and w.word.strip():
                            words.append({
                                "word": w.word.strip(), 
                                "start": float(w.start), 
                                "end": float(w.end)
                            })
            
            logging.info(f"Transcription completed: {len(words)} words found")
            return words
            
        except Exception as e:
            logging.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}")

    @staticmethod
    def generate_ass(words, ass_path, title_text=""):
        """Generate ASS subtitle file"""
        try:
            with open(ass_path, "w", encoding="utf-8") as f:
                f.write("""[Script Info]
Title: One Word at a Time Subs
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,24,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,90,1
Style: HelloStyle,Impact,18,&H000000FF,&H00FFFF00,-1,0,0,0,100,100,0,0,1,3,0,8,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text

""")
                # Add title if provided
                if title_text:
                    f.write(f"Dialogue: 0,{VideoProcessor.format_time(0)},{VideoProcessor.format_time(15)},HelloStyle,,0,0,0,,{title_text.upper()}\n")
                
                # Add word-by-word subtitles
                for w in words:
                    word = w["word"].strip().upper()
                    start = w["start"]
                    end = w["end"]
                    if word:
                        text = f"{{\\fad(100,100)\\c&HFFFFFF&}}{word}"
                        f.write(f"Dialogue: 0,{VideoProcessor.format_time(start)},{VideoProcessor.format_time(end)},Default,,0,0,0,,{text}\n")
            
            logging.info(f"ASS file generated: {ass_path}")
            
        except Exception as e:
            logging.error(f"Failed to generate ASS file: {e}")
            raise RuntimeError(f"Failed to generate subtitles: {e}")

    @staticmethod
    def get_title_for_video(input_video, title_map_file="video_titles.json"):
        """Get title for video from mapping file"""
        try:
            if os.path.exists(title_map_file):
                with open(title_map_file, "r", encoding="utf-8") as f:
                    video_title_map = json.load(f)
                
                for entry in video_title_map:
                    if os.path.normpath(entry.get("slide_topic", "")) == os.path.normpath(input_video):
                        return entry.get("title_text", "Video Processing")
        except Exception as e:
            logging.warning(f"Could not load title mapping: {e}")
        
        # Default title based on filename
        return Path(input_video).stem.replace("_", " ").title()

    @staticmethod
    def create_speech_segments(words, video_duration, merge_gap=0.8, fade_buffer=0.4):
        """Create optimized speech segments for ducking"""
        if not words:
            return []
        
        # Sort words by start time
        sorted_words = sorted(words, key=lambda x: x["start"])
        
        # Merge close words
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
        
        # Add buffers and ensure no overlaps
        final_segments = []
        for start, end in merged_segments:
            buffered_start = max(0, start - fade_buffer)
            buffered_end = min(video_duration, end + fade_buffer)
            
            if final_segments and buffered_start <= final_segments[-1][1]:
                final_segments[-1] = (final_segments[-1][0], max(final_segments[-1][1], buffered_end))
            else:
                final_segments.append((buffered_start, buffered_end))
        
        return final_segments

    @staticmethod
    def add_background_music_with_ducking(video_path, music_path, output_path, words, 
                                        music_volume=0.15, ducked_volume=0.04, progress_callback=None):
        """Add background music with auto-ducking"""
        try:
            if progress_callback:
                progress_callback("Adding background music with ducking...")
            
            logging.info("Adding background music with auto-ducking...")
            
            video_duration = VideoProcessor.get_video_duration(video_path)
            speech_segments = VideoProcessor.create_speech_segments(words, video_duration)
            
            if not speech_segments:
                logging.info("No speech detected, adding music at low volume")
                cmd = [
                    "ffmpeg", "-y", "-v", "warning",
                    "-i", str(video_path),
                    "-i", str(music_path),
                    "-filter_complex", 
                    f"[1:a]aloop=loop=-1:size=2e+09,volume={ducked_volume}[bg_music];"
                    f"[0:a][bg_music]amix=inputs=2:duration=first:dropout_transition=2,volume=1.0[audio_out]",
                    "-map", "0:v",
                    "-map", "[audio_out]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-shortest",
                    str(output_path)
                ]
            else:
                logging.info(f"Speech segments detected: {len(speech_segments)}")
                
                # Build filter for ducking
                filter_parts = [f"[1:a]aloop=loop=-1:size=2e+09,volume={music_volume}[bg_normal]"]
                current_label = "bg_normal"
                
                for i, (start, end) in enumerate(speech_segments):
                    next_label = f"bg_step_{i}"
                    filter_parts.append(
                        f"[{current_label}]volume=enable='between(t,{start:.3f},{end:.3f})':volume={ducked_volume/music_volume:.3f}[{next_label}]"
                    )
                    current_label = next_label
                
                filter_parts.append(f"[0:a][{current_label}]amix=inputs=2:duration=first:weights='1.0 0.8'[audio_out]")
                filter_complex = ";".join(filter_parts)
                
                cmd = [
                    "ffmpeg", "-y", "-v", "warning",
                    "-i", str(video_path),
                    "-i", str(music_path),
                    "-filter_complex", filter_complex,
                    "-map", "0:v",
                    "-map", "[audio_out]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-shortest",
                    str(output_path)
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300, encoding='utf-8', errors='ignore')
            logging.info("Background music with ducking applied successfully")
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout while adding background music")
        except subprocess.CalledProcessError as e:
            logging.error(f"FFmpeg error: {e.stderr}")
            raise RuntimeError(f"Failed to add background music: {e.stderr}")
        except Exception as e:
            logging.error(f"Music ducking failed: {e}")
            raise RuntimeError(f"Failed to add background music: {e}")

    @staticmethod
    def safe_run_command(cmd, timeout=300, step_name="Processing"):
        """Safely run subprocess command with proper error handling"""
        try:
            logging.info(f"{step_name}: {' '.join(cmd[:3])}...")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True, 
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            return result
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Timeout during {step_name}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logging.error(f"{step_name} failed: {error_msg}")
            raise RuntimeError(f"{step_name} failed: {error_msg}")

class VideoProcessorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Video Processor v2.0")
        self.geometry("900x700")
        self.resizable(True, True)
        self.minsize(800, 600)
        
        # Initialize variables
        self.input_videos = []
        self.extra_video = ""
        self.background_music = ""
        self.output_dir = ""
        self.is_processing = False
        self.processor = VideoProcessor()
        
        # Setup logging first
        try:
            self.log_file = setup_logging()
        except Exception as e:
            print(f"Logging setup failed: {e}")
            self.log_file = None
        
        # Create styles and GUI
        try:
            self.create_styles()
        except Exception as e:
            logging.warning(f"Style creation failed: {e}")
        
        try:
            self.create_widgets()
            self.center_window()
        except Exception as e:
            logging.error(f"Widget creation failed: {e}")
            messagebox.showerror("Startup Error", f"Failed to create interface: {e}")
            return
        
        # Check dependencies after GUI is created
        try:
            self.check_dependencies()
        except Exception as e:
            logging.warning(f"Dependency check failed: {e}")
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def check_dependencies(self):
        """Check if all required dependencies are available"""
        missing = DependencyChecker.check_dependencies()
        if missing:
            error_msg = "Missing required dependencies:\n\n" + "\n".join(missing)
            error_msg += "\n\nPlease install the missing tools before proceeding."
            messagebox.showerror("Missing Dependencies", error_msg)

    def create_styles(self):
        """Create custom styles for ttk widgets"""
        try:
            style = ttk.Style()
            
            # Use default theme if clam is not available
            available_themes = style.theme_names()
            if 'clam' in available_themes:
                style.theme_use('clam')
            elif 'alt' in available_themes:
                style.theme_use('alt')
            else:
                style.theme_use(available_themes[0])
            
            # Configure custom styles safely
            try:
                style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
            except:
                style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
            
            try:
                style.configure('Heading.TLabel', font=('Arial', 11, 'bold'), foreground='#34495e')
            except:
                style.configure('Heading.TLabel', font=('Arial', 11, 'bold'))
            
            try:
                style.configure('Success.TLabel', background='#d4edda', foreground='#155724')
            except:
                style.configure('Success.TLabel', foreground='green')
            
            try:
                style.configure('Warning.TLabel', background='#fff3cd', foreground='#856404')
            except:
                style.configure('Warning.TLabel', foreground='orange')
            
            try:
                style.configure('Error.TLabel', background='#f8d7da', foreground='#721c24')
            except:
                style.configure('Error.TLabel', foreground='red')
            
            # Configure progressbar style more safely
            try:
                style.configure('Custom.Horizontal.TProgressbar', 
                              troughcolor='#ecf0f1', 
                              background='#3498db',
                              borderwidth=1,
                              relief='flat')
            except:
                # Fallback to default progressbar style
                pass
                
        except Exception as e:
            logging.warning(f"Could not configure custom styles: {e}")
            # Continue with default styles

    def center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """Create and layout all GUI widgets"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Main processing tab
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="🎬 Processing")
        
        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="⚙️ Settings")
        
        # Logs tab
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="📋 Logs")
        
        self.create_main_tab(main_frame)
        self.create_settings_tab(settings_frame)
        self.create_logs_tab(logs_frame)

    def create_main_tab(self, parent):
        """Create main processing tab"""
        # Create main container with scrollbar
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Main content
        main_content = ttk.Frame(scrollable_frame)
        main_content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_content, text="🎬 Advanced Video Processor", style='Title.TLabel')
        title_label.pack(pady=(0, 20))

        # File selection section
        self.create_file_selection_section(main_content)
        
        # Progress section
        self.create_progress_section(main_content)
        
        # Control buttons
        self.create_control_buttons(main_content)

    def create_file_selection_section(self, parent):
        """Create file selection section"""
        # Main videos
        videos_frame = ttk.LabelFrame(parent, text="📹 Main Input Videos", padding=10)
        videos_frame.pack(fill='x', pady=(0, 15))
        
        self.lbl_main = ttk.Label(videos_frame, text="No files selected", wraplength=650)
        self.lbl_main.pack(fill='x', pady=(0, 5))
        
        btn_frame1 = ttk.Frame(videos_frame)
        btn_frame1.pack(fill='x')
        
        self.btn_select_main = ttk.Button(btn_frame1, text="📁 Browse Videos", 
                                         command=self.select_main_videos)
        self.btn_select_main.pack(side='left', padx=(0, 10))
        
        self.btn_clear_main = ttk.Button(btn_frame1, text="🗑️ Clear", 
                                        command=self.clear_main_videos)
        self.btn_clear_main.pack(side='left')

        # Extra video
        extra_frame = ttk.LabelFrame(parent, text="➕ Extra Video to Merge", padding=10)
        extra_frame.pack(fill='x', pady=(0, 15))
        
        self.lbl_extra = ttk.Label(extra_frame, text="No file selected", wraplength=650)
        self.lbl_extra.pack(fill='x', pady=(0, 5))
        
        btn_frame2 = ttk.Frame(extra_frame)
        btn_frame2.pack(fill='x')
        
        self.btn_select_extra = ttk.Button(btn_frame2, text="📁 Browse Video", 
                                          command=self.select_extra_video)
        self.btn_select_extra.pack(side='left', padx=(0, 10))
        
        self.btn_clear_extra = ttk.Button(btn_frame2, text="🗑️ Clear", 
                                         command=self.clear_extra_video)
        self.btn_clear_extra.pack(side='left')

        # Background music
        music_frame = ttk.LabelFrame(parent, text="🎵 Background Music (Optional)", padding=10)
        music_frame.pack(fill='x', pady=(0, 15))
        
        self.lbl_music = ttk.Label(music_frame, text="No file selected", wraplength=650)
        self.lbl_music.pack(fill='x', pady=(0, 5))
        
        btn_frame3 = ttk.Frame(music_frame)
        btn_frame3.pack(fill='x')
        
        self.btn_select_music = ttk.Button(btn_frame3, text="📁 Browse Music", 
                                          command=self.select_background_music)
        self.btn_select_music.pack(side='left', padx=(0, 10))
        
        self.btn_clear_music = ttk.Button(btn_frame3, text="🗑️ Clear", 
                                         command=self.clear_background_music)
        self.btn_clear_music.pack(side='left')

        # Output folder
        output_frame = ttk.LabelFrame(parent, text="📂 Output Folder", padding=10)
        output_frame.pack(fill='x', pady=(0, 15))
        
        self.lbl_output = ttk.Label(output_frame, text="No folder selected", wraplength=650)
        self.lbl_output.pack(fill='x', pady=(0, 5))
        
        btn_frame4 = ttk.Frame(output_frame)
        btn_frame4.pack(fill='x')
        
        self.btn_select_output = ttk.Button(btn_frame4, text="📁 Browse Folder", 
                                           command=self.select_output_folder)
        self.btn_select_output.pack(side='left', padx=(0, 10))
        
        self.btn_open_output = ttk.Button(btn_frame4, text="📂 Open Folder", 
                                         command=self.open_output_folder)
        self.btn_open_output.pack(side='left')

    def create_progress_section(self, parent):
        """Create progress monitoring section"""
        progress_frame = ttk.LabelFrame(parent, text="📊 Progress", padding=10)
        progress_frame.pack(fill='x', pady=(0, 15))
        
        # Status label
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to process")
        self.lbl_status = ttk.Label(progress_frame, textvariable=self.status_var, 
                                   wraplength=650, style='Success.TLabel')
        self.lbl_status.pack(fill='x', pady=(0, 10))
        
        # Overall progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.pack(fill='x', pady=(0, 5))
        
        # Progress percentage
        self.progress_text = ttk.Label(progress_frame, text="0%")
        self.progress_text.pack()

    def create_control_buttons(self, parent):
        """Create control buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=(20, 0))
        
        self.btn_start = ttk.Button(button_frame, text="🚀 Start Processing", 
                                   command=self.start_processing)
        self.btn_start.pack(side='left', padx=(0, 10))
        
        self.btn_stop = ttk.Button(button_frame, text="⏹️ Stop", 
                                  command=self.stop_processing, state='disabled')
        self.btn_stop.pack(side='left', padx=(0, 10))
        
        self.btn_validate = ttk.Button(button_frame, text="✅ Validate Files", 
                                      command=self.validate_files)
        self.btn_validate.pack(side='left')

    def create_settings_tab(self, parent):
        """Create settings/preferences tab"""
        settings_content = ttk.Frame(parent)
        settings_content.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(settings_content, text="⚙️ Processing Settings", style='Title.TLabel').pack(pady=(0, 20))
        
        # Audio settings
        audio_frame = ttk.LabelFrame(settings_content, text="🎵 Audio Settings", padding=10)
        audio_frame.pack(fill='x', pady=(0, 15))
        
        # Music volume
        ttk.Label(audio_frame, text="Background Music Volume:").pack(anchor='w')
        self.music_volume = tk.DoubleVar(value=0.12)
        music_scale = ttk.Scale(audio_frame, from_=0.01, to=0.5, variable=self.music_volume, orient='horizontal')
        music_scale.pack(fill='x', pady=(0, 10))
        
        # Ducked volume
        ttk.Label(audio_frame, text="Ducked Volume (during speech):").pack(anchor='w')
        self.ducked_volume = tk.DoubleVar(value=0.03)
        ducked_scale = ttk.Scale(audio_frame, from_=0.01, to=0.2, variable=self.ducked_volume, orient='horizontal')
        ducked_scale.pack(fill='x', pady=(0, 10))

        # Video settings
        video_frame = ttk.LabelFrame(settings_content, text="🎬 Video Settings", padding=10)
        video_frame.pack(fill='x', pady=(0, 15))
        
        # Quality preset
        ttk.Label(video_frame, text="Quality Preset:").pack(anchor='w')
        self.quality_preset = tk.StringVar(value="fast")
        quality_combo = ttk.Combobox(video_frame, textvariable=self.quality_preset, 
                                    values=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"])
        quality_combo.pack(fill='x', pady=(0, 10))
        
        # CRF value
        ttk.Label(video_frame, text="CRF (Quality):").pack(anchor='w')
        self.crf_value = tk.IntVar(value=23)
        crf_scale = ttk.Scale(video_frame, from_=15, to=35, variable=self.crf_value, orient='horizontal')
        crf_scale.pack(fill='x')

    def create_logs_tab(self, parent):
        """Create logs viewing tab"""
        logs_content = ttk.Frame(parent)
        logs_content.pack(fill='both', expand=True, padx=20, pady=20)
        
        ttk.Label(logs_content, text="📋 Processing Logs", style='Title.TLabel').pack(pady=(0, 10))
        
        # Log controls
        log_controls = ttk.Frame(logs_content)
        log_controls.pack(fill='x', pady=(0, 10))
        
        ttk.Button(log_controls, text="🔄 Refresh", command=self.refresh_logs).pack(side='left', padx=(0, 10))
        ttk.Button(log_controls, text="🗑️ Clear", command=self.clear_logs).pack(side='left', padx=(0, 10))
        ttk.Button(log_controls, text="💾 Save", command=self.save_logs).pack(side='left')
        
        # Log display
        self.log_display = scrolledtext.ScrolledText(logs_content, height=20, state='disabled', 
                                                   wrap=tk.WORD, font=('Consolas', 9))
        self.log_display.pack(fill='both', expand=True)
        
        # Load initial logs
        try:
            self.refresh_logs()
        except Exception as e:
            logging.warning(f"Initial log refresh failed: {e}")

    # File selection methods
    def select_main_videos(self):
        """Select main input videos"""
        files = filedialog.askopenfilenames(
            title="Select Main Input Videos", 
            filetypes=[
                ("Video Files", "*.mp4 *.mov *.mkv *.avi *.wmv *.flv *.webm"),
                ("All Files", "*.*")
            ]
        )
        if files:
            self.input_videos = list(files)
            self.update_main_videos_display()
            self.update_status_display()

    def clear_main_videos(self):
        """Clear main video selection"""
        self.input_videos = []
        self.update_main_videos_display()
        self.update_status_display()

    def update_main_videos_display(self):
        """Update main videos display"""
        if not self.input_videos:
            self.lbl_main.config(text="No files selected")
        else:
            file_names = [Path(f).name for f in self.input_videos]
            if len(file_names) > 3:
                display_text = f"Selected {len(file_names)} files: " + ", ".join(file_names[:3]) + "..."
            else:
                display_text = "Selected: " + ", ".join(file_names)
            self.lbl_main.config(text=display_text)

    def select_extra_video(self):
        """Select extra video to merge"""
        file = filedialog.askopenfilename(
            title="Select Extra Video to Merge", 
            filetypes=[
                ("Video Files", "*.mp4 *.mov *.mkv *.avi *.wmv *.flv *.webm"),
                ("All Files", "*.*")
            ]
        )
        if file:
            self.extra_video = file
            self.lbl_extra.config(text=Path(file).name)
            self.update_status_display()

    def clear_extra_video(self):
        """Clear extra video selection"""
        self.extra_video = ""
        self.lbl_extra.config(text="No file selected")
        self.update_status_display()

    def select_background_music(self):
        """Select background music"""
        file = filedialog.askopenfilename(
            title="Select Background Music (Optional)", 
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.aac *.m4a *.ogg *.flac"),
                ("All Files", "*.*")
            ]
        )
        if file:
            self.background_music = file
            self.lbl_music.config(text=Path(file).name)

    def clear_background_music(self):
        """Clear background music selection"""
        self.background_music = ""
        self.lbl_music.config(text="No file selected")

    def select_output_folder(self):
        """Select output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir = folder
            self.lbl_output.config(text=folder)
            self.update_status_display()

    def open_output_folder(self):
        """Open output folder in file explorer"""
        if self.output_dir and os.path.exists(self.output_dir):
            if sys.platform == "win32":
                os.startfile(self.output_dir)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.output_dir])
            else:
                subprocess.run(["xdg-open", self.output_dir])
        else:
            messagebox.showwarning("Warning", "Please select an output folder first.")

    def update_status_display(self):
        """Update status display based on selections"""
        if not self.is_processing:
            if self.input_videos and self.extra_video and self.output_dir:
                self.status_var.set("✅ Ready to process")
                self.lbl_status.config(style='Success.TLabel')
            else:
                missing = []
                if not self.input_videos:
                    missing.append("main videos")
                if not self.extra_video:
                    missing.append("extra video")
                if not self.output_dir:
                    missing.append("output folder")
                self.status_var.set(f"⚠️ Missing: {', '.join(missing)}")
                self.lbl_status.config(style='Warning.TLabel')

    def validate_files(self):
        """Validate selected files"""
        issues = []
        
        # Check main videos
        for video in self.input_videos:
            if not os.path.exists(video):
                issues.append(f"Main video not found: {Path(video).name}")
            elif not self.is_valid_video_file(video):
                issues.append(f"Invalid video format: {Path(video).name}")
        
        # Check extra video
        if self.extra_video:
            if not os.path.exists(self.extra_video):
                issues.append(f"Extra video not found: {Path(self.extra_video).name}")
            elif not self.is_valid_video_file(self.extra_video):
                issues.append(f"Invalid extra video format: {Path(self.extra_video).name}")
        
        # Check background music
        if self.background_music:
            if not os.path.exists(self.background_music):
                issues.append(f"Music file not found: {Path(self.background_music).name}")
            elif not self.is_valid_audio_file(self.background_music):
                issues.append(f"Invalid audio format: {Path(self.background_music).name}")
        
        # Check output directory
        if self.output_dir:
            if not os.path.exists(self.output_dir):
                try:
                    os.makedirs(self.output_dir, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create output directory: {e}")
            elif not os.access(self.output_dir, os.W_OK):
                issues.append("Output directory is not writable")
        
        if issues:
            messagebox.showerror("Validation Issues", "\n".join(issues))
        else:
            messagebox.showinfo("Validation", "All files validated successfully!")

    @staticmethod
    def is_valid_video_file(file_path):
        """Check if file is a valid video"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', str(file_path)
            ], capture_output=True, text=True, timeout=10, encoding='utf-8', errors='ignore')
            return result.returncode == 0 and 'video' in result.stdout
        except:
            return False

    @staticmethod
    def is_valid_audio_file(file_path):
        """Check if file is a valid audio"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', str(file_path)
            ], capture_output=True, text=True, timeout=10, encoding='utf-8', errors='ignore')
            return result.returncode == 0 and 'audio' in result.stdout
        except:
            return False

    # Processing control methods
    def start_processing(self):
        """Start video processing"""
        # Validation
        if not self.input_videos:
            messagebox.showwarning("Warning", "Please select at least one main input video.")
            return
        if not self.extra_video:
            messagebox.showwarning("Warning", "Please select an extra video to merge.")
            return
        if not self.output_dir:
            messagebox.showwarning("Warning", "Please select an output folder.")
            return
        
        if self.is_processing:
            messagebox.showinfo("Info", "Processing is already in progress.")
            return

        # Create output directory if it doesn't exist
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create output directory: {e}")
            return

        # Update UI for processing state
        self.is_processing = True
        self.btn_start.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.progress_var.set(0)
        self.set_controls_state('disabled')
        
        # Start processing in separate thread
        self.processing_thread = threading.Thread(target=self.process_all_videos, daemon=True)
        self.processing_thread.start()

    def stop_processing(self):
        """Stop processing (placeholder for future implementation)"""
        if messagebox.askyesno("Stop Processing", "Are you sure you want to stop processing?\nThis may leave temporary files."):
            # Note: Actual stopping would require more complex threading control
            logging.warning("Processing stop requested by user")
            messagebox.showinfo("Stop", "Stop request noted. Processing will complete current video.")

    def set_controls_state(self, state):
        """Enable/disable file selection controls"""
        controls = [
            self.btn_select_main, self.btn_clear_main,
            self.btn_select_extra, self.btn_clear_extra,
            self.btn_select_music, self.btn_clear_music,
            self.btn_select_output, self.btn_validate
        ]
        for control in controls:
            control.config(state=state)

    def update_progress(self, current, total, message=""):
        """Update progress bar and status"""
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
            self.progress_text.config(text=f"{progress:.1f}%")
        
        if message:
            self.status_var.set(message)
            # Use simpler style updates
            if "✅" in message or "Ready" in message:
                self.lbl_status.config(style='Success.TLabel')
            elif "⚠️" in message or "Missing" in message:
                self.lbl_status.config(style='Warning.TLabel')
            elif "❌" in message or "Failed" in message:
                self.lbl_status.config(style='Error.TLabel')
            else:
                # Reset to default style for processing messages
                try:
                    self.lbl_status.config(style='TLabel')
                except:
                    pass
        
        self.update_idletasks()

    def process_all_videos(self):
        """Process all selected videos"""
        try:
            total_videos = len(self.input_videos)
            successful = 0
            failed = 0
            
            for idx, input_video in enumerate(self.input_videos):
                try:
                    self.update_progress(idx, total_videos, 
                                       f"🔄 Processing video {idx + 1} of {total_videos}: {Path(input_video).name}")
                    
                    base = Path(input_video).stem
                    output_path = os.path.join(self.output_dir, f"{base}_final.mp4")
                    
                    self.process_single_video(input_video, output_path)
                    successful += 1
                    
                    self.update_progress(idx + 1, total_videos, 
                                       f"✅ Completed {idx + 1} of {total_videos}")
                    
                except Exception as e:
                    failed += 1
                    logging.error(f"Failed to process {input_video}: {e}")
                    self.update_progress(idx + 1, total_videos, 
                                       f"❌ Failed: {Path(input_video).name}")
                    continue
            
            # Final status
            if failed == 0:
                final_msg = f"✅ All {total_videos} video(s) processed successfully!"
                self.lbl_status.config(style='Success.TLabel')
                messagebox.showinfo("Success", f"{final_msg}\nOutput saved to: {self.output_dir}")
            else:
                final_msg = f"⚠️ Completed with issues: {successful} successful, {failed} failed"
                self.lbl_status.config(style='Warning.TLabel')
                messagebox.showwarning("Completed with Issues", final_msg)
            
            self.status_var.set(final_msg)
            
        except Exception as e:
            error_msg = f"❌ Processing failed: {str(e)}"
            self.status_var.set(error_msg)
            self.lbl_status.config(style='Error.TLabel')
            messagebox.showerror("Error", f"Processing failed: {str(e)}")
            logging.error(f"Processing error: {e}")
        
        finally:
            # Reset UI state
            self.is_processing = False
            self.btn_start.config(state='normal')
            self.btn_stop.config(state='disabled')
            self.set_controls_state('normal')
            self.progress_var.set(100)
            self.progress_text.config(text="100%")

    def process_single_video(self, input_video, output_video):
        """Process a single video with all steps"""
        base_name = Path(input_video).stem
        temp_dir = Path("temp") / base_name
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Temporary file paths
        auto_edited = temp_dir / f"auto_{base_name}.mp4"
        audio_path = temp_dir / f"audio_{base_name}.wav"
        ass_path = temp_dir / f"subtitles_{base_name}.ass"
        final_with_subs = temp_dir / f"final_subs_{base_name}.mp4"
        final_with_music = temp_dir / f"final_music_{base_name}.mp4"

        try:
            # Step 1: Auto-editing
            logging.info(f"⚙️ Auto-editing: {input_video}")
            self.processor.safe_run_command([
                "auto-editor", str(input_video), "-o", str(auto_edited),
                "--no-open", "--frame-rate", "30", "--silent-speed", "99999"
            ], step_name="Auto-editing")

            # Step 2: Extract audio
            logging.info(f"🔊 Extracting audio from: {auto_edited}")
            self.processor.safe_run_command([
                "ffmpeg", "-y", "-v", "warning", "-i", str(auto_edited), "-vn",
                "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(audio_path)
            ], step_name="Audio extraction")

            # Step 3: Transcribe and generate subtitles
            words = self.processor.transcribe_audio(audio_path, 
                                                   progress_callback=lambda msg: self.status_var.set(f"🧠 {msg}"))
            
            title_text = self.processor.get_title_for_video(input_video)
            self.processor.generate_ass(words, ass_path, title_text)

            # Step 4: Burn subtitles - FIXED PATH HANDLING FOR WINDOWS
            logging.info("🎬 Burning subtitles...")
            # Convert Windows path to use forward slashes for FFmpeg
            ass_path_fixed = str(ass_path).replace('\\', '/')
            self.processor.safe_run_command([
                "ffmpeg", "-y", "-v", "warning", "-i", str(auto_edited),
                "-filter_complex", f"ass='{ass_path_fixed}'",
                "-map", "0:a", "-c:v", "libx264", 
                "-crf", str(self.crf_value.get()), 
                "-preset", self.quality_preset.get(),
                "-c:a", "aac", "-shortest", str(final_with_subs)
            ], step_name="Subtitle burning")

            # Step 5: Add background music if provided
            video_to_merge = final_with_subs
            if self.background_music and os.path.exists(self.background_music):
                self.processor.add_background_music_with_ducking(
                    final_with_subs, 
                    self.background_music, 
                    final_with_music, 
                    words,
                    music_volume=self.music_volume.get(),
                    ducked_volume=self.ducked_volume.get(),
                    progress_callback=lambda msg: self.status_var.set(f"🎵 {msg}")
                )
                video_to_merge = final_with_music

            # Step 6: Merge with extra video
            logging.info("🔗 Merging with extra video...")
            self.merge_videos_improved(video_to_merge, self.extra_video, output_video)

            logging.info(f"✅ Processing complete: {output_video}")

        finally:
            # Clean up temporary files
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logging.warning(f"Failed to clean up temp directory: {e}")

    def merge_videos_improved(self, main_video, extra_video, output_path):
        """Improved video merging with better error handling"""
        try:
            # Create a list file for concatenation
            list_file = Path("temp") / "concat_list.txt"
            list_file.parent.mkdir(exist_ok=True)
            
            with open(list_file, 'w', encoding='utf-8') as f:
                f.write(f"file '{os.path.abspath(main_video)}'\n")
                f.write(f"file '{os.path.abspath(extra_video)}'\n")
            
            # Use ffmpeg concat demuxer for better compatibility
            self.processor.safe_run_command([
                "ffmpeg", "-y", "-v", "warning", "-f", "concat", "-safe", "0",
                "-i", str(list_file), "-c", "copy", str(output_path)
            ], step_name="Video merging")
            
            # Clean up list file
            if list_file.exists():
                list_file.unlink()
                
        except Exception as e:
            logging.error(f"Video merging failed: {e}")
            raise RuntimeError(f"Failed to merge videos: {e}")

    # Log management methods
    def refresh_logs(self):
        """Refresh log display"""
        try:
            if self.log_file and os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                self.log_display.config(state='normal')
                self.log_display.delete(1.0, tk.END)
                self.log_display.insert(1.0, content)
                self.log_display.config(state='disabled')
                self.log_display.see(tk.END)
            else:
                self.log_display.config(state='normal')
                self.log_display.delete(1.0, tk.END)
                self.log_display.insert(1.0, "Log file not available or not created yet.")
                self.log_display.config(state='disabled')
        except Exception as e:
            logging.error(f"Failed to refresh logs: {e}")
            try:
                self.log_display.config(state='normal')
                self.log_display.delete(1.0, tk.END)
                self.log_display.insert(1.0, f"Error loading logs: {e}")
                self.log_display.config(state='disabled')
            except:
                pass

    def clear_logs(self):
        """Clear log display"""
        self.log_display.config(state='normal')
        self.log_display.delete(1.0, tk.END)
        self.log_display.config(state='disabled')

    def save_logs(self):
        """Save logs to file"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save Logs",
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            if file_path:
                content = self.log_display.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Logs saved to: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save logs: {e}")

    def on_closing(self):
        """Handle application closing"""
        if self.is_processing:
            if messagebox.askyesno("Exit", "Processing is in progress. Exit anyway?"):
                logging.info("Application closed during processing")
                self.destroy()
        else:
            self.destroy()


def main():
    """Main application entry point"""
    try:
        # Check Python version
        if sys.version_info < (3, 7):
            try:
                messagebox.showerror("Python Version Error", 
                                   "Python 3.7 or higher is required.")
            except:
                print("Python 3.7 or higher is required.")
            return
        
        # Initialize tkinter first to catch display issues
        root = tk.Tk()
        root.withdraw()  # Hide the root window temporarily
        
        # Test if GUI is available
        try:
            root.winfo_screenwidth()
        except tk.TclError as e:
            print(f"GUI not available: {e}")
            print("This application requires a graphical display.")
            return
        
        root.destroy()  # Clean up test window
        
        # Create and run application
        app = VideoProcessorApp()
        
        # Start the main loop with error handling
        try:
            app.mainloop()
        except KeyboardInterrupt:
            logging.info("Application interrupted by user")
        except Exception as e:
            logging.error(f"Runtime error: {e}")
            try:
                messagebox.showerror("Runtime Error", f"Application error: {e}")
            except:
                print(f"Application error: {e}")
        
    except Exception as e:
        error_msg = f"Application startup failed: {e}"
        logging.error(error_msg)
        try:
            messagebox.showerror("Startup Error", error_msg)
        except:
            print(error_msg)


if __name__ == "__main__":
    main()