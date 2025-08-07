import os
import subprocess
import json
import threading
import queue
import shutil
from pathlib import Path
import logging
from tkinter import ttk, filedialog, messagebox, colorchooser
import tkinter as tk
from faster_whisper import WhisperModel

# Configure logging
logging.basicConfig(level=logging.INFO, format="🔹 %(message)s")

class VideoProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Video Processor Pro")
        self.root.geometry("950x750")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.input_videos = []
        self.extra_video = None
        self.background_music = None
        self.output_dir = None
        self.processing = False
        self.progress_queue = queue.Queue()
        
        # Add stop event for thread control
        self.stop_event = threading.Event()
        
        # Load video titles
        try:
            with open("video_titles.json", "r", encoding="utf-8") as f:
                self.video_title_map = json.load(f)
        except FileNotFoundError:
            self.video_title_map = []
            
        self.setup_ui()
        self.check_progress()
        
    def setup_ui(self):
        # Main title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill='x', padx=10, pady=10)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🎬 Video Processor Pro", 
                              font=("Arial", 20, "bold"), fg='white', bg='#2c3e50')
        title_label.pack(expand=True)
        
        # Main content frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # File selection section
        files_frame = tk.LabelFrame(main_frame, text="📁 File Selection", 
                                   font=("Arial", 12, "bold"), bg='#f0f0f0')
        files_frame.pack(fill='x', pady=10)
        
        # Input videos
        tk.Button(files_frame, text="🎥 Select Main Videos", 
                 command=self.select_input_videos, bg='#3498db', fg='white',
                 font=("Arial", 10, "bold"), padx=20, pady=5).pack(pady=5)
        
        self.input_label = tk.Label(files_frame, text="No videos selected", 
                                   bg='#f0f0f0', wraplength=800)
        self.input_label.pack(pady=2)
        
        # Extra video
        tk.Button(files_frame, text="➕ Select Extra Video to Merge", 
                 command=self.select_extra_video, bg='#e67e22', fg='white',
                 font=("Arial", 10, "bold"), padx=20, pady=5).pack(pady=5)
        
        self.extra_label = tk.Label(files_frame, text="No extra video selected", 
                                   bg='#f0f0f0', wraplength=800)
        self.extra_label.pack(pady=2)
        
        # Background music (optional)
        music_frame = tk.Frame(files_frame, bg='#f0f0f0')
        music_frame.pack(pady=5)
        
        tk.Button(music_frame, text="🎵 Select Background Music (Optional)", 
                 command=self.select_background_music, bg='#9b59b6', fg='white',
                 font=("Arial", 10, "bold"), padx=20, pady=5).pack(side='left')
        
        tk.Button(music_frame, text="❌ Clear Music", 
                 command=self.clear_background_music, bg='#e74c3c', fg='white',
                 font=("Arial", 9), padx=10, pady=5).pack(side='left', padx=(10, 0))
        
        self.music_label = tk.Label(files_frame, text="No background music selected", 
                                   bg='#f0f0f0', wraplength=800)
        self.music_label.pack(pady=2)
        
        # Output directory
        tk.Button(files_frame, text="📂 Select Output Folder", 
                 command=self.select_output_dir, bg='#27ae60', fg='white',
                 font=("Arial", 10, "bold"), padx=20, pady=5).pack(pady=5)
        
        self.output_label = tk.Label(files_frame, text="No output folder selected", 
                                    bg='#f0f0f0', wraplength=800)
        self.output_label.pack(pady=2)
        
        # Processing options
        options_frame = tk.LabelFrame(main_frame, text="⚙️ Processing Options", 
                                     font=("Arial", 12, "bold"), bg='#f0f0f0')
        options_frame.pack(fill='x', pady=10)
        
        # Options row 1
        options_row1 = tk.Frame(options_frame, bg='#f0f0f0')
        options_row1.pack(fill='x', padx=10, pady=5)
        
        # Quality preset
        tk.Label(options_row1, text="Quality:", font=("Arial", 10), bg='#f0f0f0').pack(side='left')
        self.quality_var = tk.StringVar(value="fast")
        quality_combo = ttk.Combobox(options_row1, textvariable=self.quality_var, 
                                    values=["ultrafast", "fast", "medium", "slow"], 
                                    state="readonly", width=12)
        quality_combo.pack(side='left', padx=(5, 20))
        
        # Music volume
        tk.Label(options_row1, text="Music Volume:", font=("Arial", 10), bg='#f0f0f0').pack(side='left')
        self.volume_var = tk.DoubleVar(value=0.15)
        volume_scale = tk.Scale(options_row1, from_=0.0, to=0.5, resolution=0.05, 
                               orient='horizontal', variable=self.volume_var, length=120)
        volume_scale.pack(side='left', padx=5)
        
        # Options row 2
        options_row2 = tk.Frame(options_frame, bg='#f0f0f0')
        options_row2.pack(fill='x', padx=10, pady=5)
        
        # Auto-editing checkbox
        self.auto_edit_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_row2, text="✂️ Auto-Edit Videos", 
                      variable=self.auto_edit_var, bg='#f0f0f0', font=("Arial", 10)).pack(side='left')
        
        # Enable GPU acceleration
        self.gpu_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_row2, text="🚀 GPU Acceleration", 
                      variable=self.gpu_var, bg='#f0f0f0', font=("Arial", 10)).pack(side='left', padx=(20, 0))
        
        # Enable music ducking
        self.ducking_var = tk.BooleanVar(value=True)
        tk.Checkbutton(options_row2, text="🎵 Smart Music Ducking", 
                      variable=self.ducking_var, bg='#f0f0f0', font=("Arial", 10)).pack(side='left', padx=(20, 0))
        
        # Subtitle customization section
        subtitle_frame = tk.LabelFrame(main_frame, text="📝 Subtitle Customization", 
                                      font=("Arial", 12, "bold"), bg='#f0f0f0')
        subtitle_frame.pack(fill='x', pady=10)
        
        # Subtitle color selection
        color_row = tk.Frame(subtitle_frame, bg='#f0f0f0')
        color_row.pack(fill='x', padx=10, pady=5)
        
        tk.Label(color_row, text="Subtitle Color:", font=("Arial", 10), bg='#f0f0f0').pack(side='left')
        
        # Color preview and hex input
        self.subtitle_color = "#FFFFFF"
        self.color_preview = tk.Label(color_row, text="  ", bg=self.subtitle_color, 
                                     relief='solid', borderwidth=2, width=4, height=1)
        self.color_preview.pack(side='left', padx=(10, 5))
        
        # Color picker button
        tk.Button(color_row, text="🎨 Pick Color", command=self.pick_subtitle_color,
                 bg='#f39c12', fg='white', font=("Arial", 9)).pack(side='left', padx=5)
        
        # Hex input
        tk.Label(color_row, text="Hex:", font=("Arial", 10), bg='#f0f0f0').pack(side='left', padx=(10, 5))
        self.hex_var = tk.StringVar(value=self.subtitle_color)
        self.hex_entry = tk.Entry(color_row, textvariable=self.hex_var, width=8, font=("Arial", 9))
        self.hex_entry.pack(side='left', padx=5)
        self.hex_entry.bind('<KeyRelease>', self.on_hex_change)
        
        # Apply hex button
        tk.Button(color_row, text="Apply", command=self.apply_hex_color,
                 bg='#27ae60', fg='white', font=("Arial", 9)).pack(side='left', padx=5)
        
        # Preset colors
        preset_frame = tk.Frame(subtitle_frame, bg='#f0f0f0')
        preset_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(preset_frame, text="Quick Colors:", font=("Arial", 10), bg='#f0f0f0').pack(side='left')
        
        preset_colors = [
            ("#FFFFFF", "White"),
            ("#FFFF00", "Yellow"),
            ("#FF0000", "Red"),
            ("#00FF00", "Green"),
            ("#0000FF", "Blue"),
            ("#FF00FF", "Magenta"),
            ("#00FFFF", "Cyan"),
            ("#FFA500", "Orange")
        ]
        
        for color, name in preset_colors:
            btn = tk.Button(preset_frame, text="  ", bg=color, width=3, height=1,
                           relief='solid', borderwidth=1,
                           command=lambda c=color: self.set_subtitle_color(c))
            btn.pack(side='left', padx=2)
        
        # Process and Stop buttons frame
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(pady=20)
        
        # Process button
        self.process_btn = tk.Button(button_frame, text="🚀 START PROCESSING", 
                                    command=self.start_processing, bg='#e74c3c', fg='white',
                                    font=("Arial", 14, "bold"), pady=10, padx=20)
        self.process_btn.pack(side='left', padx=(0, 10))
        
        # Stop button (initially disabled)
        self.stop_btn = tk.Button(button_frame, text="⏹️ STOP PROCESSING", 
                                 command=self.stop_processing, bg='#e67e22', fg='white',
                                 font=("Arial", 14, "bold"), pady=10, padx=20, state='disabled')
        self.stop_btn.pack(side='left')
        
        # Progress section
        progress_frame = tk.LabelFrame(main_frame, text="📊 Progress", 
                                      font=("Arial", 12, "bold"), bg='#f0f0f0')
        progress_frame.pack(fill='both', expand=True, pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=800)
        self.progress_bar.pack(pady=10)
        
        self.status_label = tk.Label(progress_frame, text="Ready to process", 
                                    bg='#f0f0f0', font=("Arial", 10))
        self.status_label.pack(pady=5)
        
        # Log text area
        log_frame = tk.Frame(progress_frame, bg='#f0f0f0')
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, bg='#2c3e50', fg='white', 
                               font=("Consolas", 9))
        scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def pick_subtitle_color(self):
        """Open color picker dialog"""
        color = colorchooser.askcolor(title="Choose Subtitle Color", 
                                     initialcolor=self.subtitle_color)
        if color[1]:
            self.set_subtitle_color(color[1])
    
    def set_subtitle_color(self, color_hex):
        """Set subtitle color and update UI"""
        self.subtitle_color = color_hex.upper()
        self.color_preview.config(bg=self.subtitle_color)
        self.hex_var.set(self.subtitle_color)
    
    def on_hex_change(self, event):
        """Update color preview when hex is typed"""
        hex_value = self.hex_var.get().strip()
        if len(hex_value) == 7 and hex_value.startswith('#'):
            try:
                self.root.winfo_rgb(hex_value)
                self.color_preview.config(bg=hex_value)
            except:
                pass
    
    def apply_hex_color(self):
        """Apply the hex color from entry"""
        hex_value = self.hex_var.get().strip().upper()
        if not hex_value.startswith('#'):
            hex_value = '#' + hex_value
        
        if len(hex_value) == 7:
            try:
                self.root.winfo_rgb(hex_value)
                self.set_subtitle_color(hex_value)
            except:
                messagebox.showerror("Invalid Color", "Please enter a valid hex color (e.g., #FFFFFF)")
        else:
            messagebox.showerror("Invalid Format", "Hex color must be 6 characters (e.g., #FFFFFF)")
        
    def log_message(self, message):
        """Add message to log display"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def select_input_videos(self):
        files = filedialog.askopenfilenames(
            title="Select Main Input Videos",
            filetypes=[("Video Files", "*.mp4 *.mov *.mkv *.avi *.m4v")]
        )
        if files:
            self.input_videos = list(files)
            self.input_label.config(text=f"✅ {len(files)} videos selected: {', '.join([os.path.basename(f) for f in files[:3]])}{'...' if len(files) > 3 else ''}")
            
    def select_extra_video(self):
        file = filedialog.askopenfilename(
            title="Select Extra Video to Merge",
            filetypes=[("Video Files", "*.mp4 *.mov *.mkv *.avi *.m4v")]
        )
        if file:
            self.extra_video = file
            self.extra_label.config(text=f"✅ Extra video: {os.path.basename(file)}")
            
    def select_background_music(self):
        file = filedialog.askopenfilename(
            title="Select Background Music (Optional)",
            filetypes=[("Audio Files", "*.mp3 *.wav *.aac *.m4a *.ogg *.flac")]
        )
        if file:
            self.background_music = file
            self.music_label.config(text=f"✅ Background music: {os.path.basename(file)}")
            
    def clear_background_music(self):
        self.background_music = None
        self.music_label.config(text="No background music selected")
            
    def select_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Folder")
        if directory:
            self.output_dir = directory
            self.output_label.config(text=f"✅ Output folder: {directory}")
            
    def validate_inputs(self):
        """Validate all required inputs"""
        if not self.input_videos:
            messagebox.showerror("Error", "Please select main input videos")
            return False
        if not self.extra_video:
            messagebox.showerror("Error", "Please select extra video to merge")
            return False
        if not self.output_dir:
            messagebox.showerror("Error", "Please select output folder")
            return False
        return True
        
    def start_processing(self):
        if not self.validate_inputs():
            return
            
        if self.processing:
            messagebox.showwarning("Warning", "Processing already in progress!")
            return
        
        # Reset stop event
        self.stop_event.clear()
        
        self.processing = True
        self.process_btn.config(state='disabled', text="⏳ PROCESSING...")
        self.stop_btn.config(state='normal')  # Enable stop button
        self.progress_var.set(0)
        self.log_text.delete(1.0, tk.END)
        
        # Start processing in separate thread
        thread = threading.Thread(target=self.process_videos_thread)
        thread.daemon = True
        thread.start()
    
    def stop_processing(self):
        """Stop the processing gracefully"""
        if not self.processing:
            return
        
        # Confirm stop action
        if messagebox.askquestion("Stop Processing", 
                                 "Are you sure you want to stop processing?\nCurrent video will be completed, but remaining videos will be skipped.",
                                 icon='warning') == 'yes':
            self.stop_event.set()  # Signal the worker thread to stop
            self.log_message("🛑 Stop requested by user. Finishing current video...")
            self.stop_btn.config(state='disabled', text="⏳ STOPPING...")
        
    def process_videos_thread(self):
        """Process videos in background thread with stop functionality"""
        try:
            processor = OptimizedVideoProcessor(self.progress_queue, self.video_title_map, self.stop_event)
            processor.process_all_videos(
                self.input_videos,
                self.extra_video,
                self.output_dir,
                self.background_music,
                self.quality_var.get(),
                self.gpu_var.get(),
                self.volume_var.get(),
                self.ducking_var.get(),
                self.auto_edit_var.get(),
                self.subtitle_color
            )
            
            if self.stop_event.is_set():
                self.progress_queue.put(("STOPPED", "🛑 Processing stopped by user"))
            else:
                self.progress_queue.put(("COMPLETE", "🎉 All videos processed successfully!"))
                
        except Exception as e:
            if self.stop_event.is_set():
                self.progress_queue.put(("STOPPED", "🛑 Processing stopped by user"))
            else:
                self.progress_queue.put(("ERROR", f"❌ Processing failed: {str(e)}"))
        finally:
            self.processing = False
            
    def check_progress(self):
        """Check for progress updates from worker thread"""
        try:
            while True:
                msg_type, message = self.progress_queue.get_nowait()
                
                if msg_type == "PROGRESS":
                    self.progress_var.set(message)
                elif msg_type == "STATUS":
                    self.status_label.config(text=message)
                    self.log_message(message)
                elif msg_type == "COMPLETE":
                    self.progress_var.set(100)
                    self.status_label.config(text=message)
                    self.log_message(message)
                    self.process_btn.config(state='normal', text="🚀 START PROCESSING")
                    self.stop_btn.config(state='disabled', text="⏹️ STOP PROCESSING")
                    messagebox.showinfo("Success", "All videos processed successfully!")
                elif msg_type == "STOPPED":
                    self.status_label.config(text=message)
                    self.log_message(message)
                    self.process_btn.config(state='normal', text="🚀 START PROCESSING")
                    self.stop_btn.config(state='disabled', text="⏹️ STOP PROCESSING")
                    messagebox.showinfo("Stopped", "Processing stopped by user")
                elif msg_type == "ERROR":
                    self.status_label.config(text=message)
                    self.log_message(message)
                    self.process_btn.config(state='normal', text="🚀 START PROCESSING")
                    self.stop_btn.config(state='disabled', text="⏹️ STOP PROCESSING")
                    messagebox.showerror("Error", message)
                    
        except queue.Empty:
            pass
        
        self.root.after(100, self.check_progress)

class OptimizedVideoProcessor:
    def __init__(self, progress_queue, video_title_map, stop_event):
        self.progress_queue = progress_queue
        self.video_title_map = video_title_map
        self.whisper_model = None
        self.stop_event = stop_event  # Add stop event
        
    def log(self, message):
        """Send log message to GUI"""
        logging.info(message)
        self.progress_queue.put(("STATUS", message))
        
    def update_progress(self, current, total):
        """Update progress bar"""
        progress = (current / total) * 100
        self.progress_queue.put(("PROGRESS", progress))
        
    def check_stop(self):
        """Check if stop was requested"""
        return self.stop_event.is_set()
        
    def get_whisper_model(self):
        """Initialize Whisper model once and reuse"""
        if self.whisper_model is None:
            self.log("🧠 Loading Whisper model...")
            try:
                self.whisper_model = WhisperModel("large-v3", compute_type="int8")
            except Exception as e:
                self.log(f"⚠️ Using tiny model due to: {e}")
                self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        return self.whisper_model
    
    def hex_to_ass_color(self, hex_color):
        """Convert hex color to ASS subtitle format (BGR format)"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"&H00{b:02X}{g:02X}{r:02X}"
        
    def format_ass_time(self, seconds):
        """Format time for ASS subtitles (H:MM:SS.CC)"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds * 100) % 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
        
    def check_ffmpeg_availability(self):
        """Check if ffmpeg and auto-editor are available"""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            subprocess.run(["auto-editor", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.log(f"❌ Required tools not found: {e}")
            raise Exception("FFmpeg or auto-editor not found. Please install them first.")
            
    def get_video_duration(self, file_path):
        """Enhanced method to get video duration"""
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', file_path
            ], capture_output=True, text=True, check=True, timeout=30)
            
            duration = float(result.stdout.strip())
            return duration if duration > 0 else 0
            
        except Exception as e:
            self.log(f"⚠️ Could not get video duration for {os.path.basename(file_path)}: {e}")
            try:
                result = subprocess.run([
                    'ffmpeg', '-i', file_path, '-f', 'null', '-'
                ], capture_output=True, text=True, timeout=30)
                
                for line in result.stderr.split('\n'):
                    if 'Duration:' in line:
                        time_str = line.split('Duration: ')[1].split(',')[0].strip()
                        h, m, s = time_str.split(':')
                        return int(h) * 3600 + int(m) * 60 + float(s)
            except:
                pass
                
            return 120
            
    def transcribe_audio_optimized(self, audio_path):
        """Optimized transcription with error handling and stop check"""
        try:
            if self.check_stop():
                return []
                
            self.log(f"🧠 Transcribing: {os.path.basename(audio_path)}")
            model = self.get_whisper_model()
            
            segments, _ = model.transcribe(
                audio_path, 
                beam_size=1,
                best_of=1,
                word_timestamps=True, 
                language="en",
                condition_on_previous_text=False
            )
            
            words = []
            for segment in segments:
                if self.check_stop():  # Check for stop during transcription
                    break
                    
                if hasattr(segment, 'words') and segment.words:
                    for w in segment.words:
                        if w.word.strip():
                            words.append({
                                "word": w.word.strip(), 
                                "start": w.start, 
                                "end": w.end
                            })
            
            self.log(f"✅ Transcribed {len(words)} words")
            return words
            
        except Exception as e:
            self.log(f"❌ Transcription failed: {e}")
            return []
        
    def generate_ass_subtitles(self, words, ass_path, subtitle_color="#FFFFFF"):
        """Generate ASS subtitle file with custom styling and color"""
        try:
            if self.check_stop():
                return
                
            ass_color = self.hex_to_ass_color(subtitle_color)
            
            with open(ass_path, "w", encoding="utf-8") as f:
                f.write(f"""[Script Info]
Title: One Word at a Time Subs
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,24,{ass_color},&H00000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
                
                for w in words:
                    if self.check_stop():
                        break
                        
                    word = w["word"].strip().upper()
                    start, end = w["start"], w["end"]
                    if word and end > start:
                        start_time = self.format_ass_time(start)
                        end_time = self.format_ass_time(end)
                        f.write(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{word}\n")
                        
            self.log(f"✅ Generated ASS subtitles with {len(words)} words in color {subtitle_color}")
                        
        except Exception as e:
            self.log(f"❌ ASS subtitle generation failed: {e}")
            raise
                    
    def create_speech_segments(self, words, merge_gap=0.5):
        """Create speech segments for music ducking"""
        if not words:
            return []
            
        segments = []
        if words:
            sorted_words = sorted(words, key=lambda x: x["start"])
            current_start = sorted_words[0]["start"]
            current_end = sorted_words[0]["end"]
            
            for word in sorted_words[1:]:
                if word["start"] - current_end <= merge_gap:
                    current_end = max(current_end, word["end"])
                else:
                    segments.append((max(0, current_start - 0.2), current_end + 0.2))
                    current_start = word["start"]
                    current_end = word["end"]
                    
            segments.append((max(0, current_start - 0.2), current_end + 0.2))
            
        return segments
        
    def _copy_file_safely(self, src, dst):
        """Helper method to safely copy files"""
        try:
            shutil.copy2(src, dst)
            self.log(f"📋 Copied original video to output: {os.path.basename(dst)}")
        except Exception as copy_error:
            self.log(f"❌ Failed to copy video: {copy_error}")
            raise
    
    def add_background_music_with_ducking(self, video_path, music_path, output_path, 
                                         words, volume=0.15, enable_ducking=True):
        """Fixed background music addition with better error handling and stop check"""
        try:
            if self.check_stop():
                return False
                
            self.log(f"🎵 Adding background music: {os.path.basename(music_path)}")
            
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            if not os.path.exists(music_path):
                raise FileNotFoundError(f"Music file not found: {music_path}")
            
            video_duration = self.get_video_duration(video_path)
            self.log(f"📏 Video duration: {video_duration:.2f} seconds")
            
            if not enable_ducking or not words:
                self.log("🎵 Adding background music without ducking...")
                
                cmd = [
                    "ffmpeg", "-y", "-loglevel", "warning",
                    "-i", video_path,
                    "-stream_loop", "-1", "-i", music_path,
                    "-filter_complex", 
                    f"[1:a]volume={volume}[music];"
                    f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[audio_out]",
                    "-map", "0:v", "-map", "[audio_out]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    output_path
                ]
            else:
                self.log("🎵 Adding background music with smart ducking...")
                cmd = [
                    "ffmpeg", "-y", "-loglevel", "warning",
                    "-i", video_path,
                    "-stream_loop", "-1", "-i", music_path,
                    "-filter_complex", 
                    f"[1:a]volume={volume}[music];"
                    f"[0:a]asplit[original][sidechain];"
                    f"[music][sidechain]sidechaincompress=threshold=0.003:ratio=20:attack=5:release=50[ducked_music];"
                    f"[original][ducked_music]amix=inputs=2:duration=first[audio_out]",
                    "-map", "0:v", "-map", "[audio_out]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    output_path
                ]
            
            # Run process and check for stop periodically
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Poll process and check for stop
            while process.poll() is None:
                if self.check_stop():
                    process.terminate()
                    process.wait()
                    self.log("🛑 Music processing stopped by user")
                    return False
                import time
                time.sleep(0.5)
            
            if process.returncode == 0:
                if os.path.exists(output_path):
                    output_size = os.path.getsize(output_path)
                    input_size = os.path.getsize(video_path)
                    
                    if output_size < input_size * 0.5:
                        self.log("⚠️ Output file seems too small, there might be an issue")
                        
                    self.log(f"✅ Background music added successfully (Size: {output_size/1024/1024:.1f}MB)")
                    return True
                else:
                    raise FileNotFoundError("Output file was not created")
            else:
                raise subprocess.CalledProcessError(process.returncode, cmd)
                
        except Exception as e:
            if self.check_stop():
                return False
            self.log(f"⚠️ Music processing failed: {e}")
            self.log("⚠️ Continuing without background music")
            self._copy_file_safely(video_path, output_path)
            return False
    
    def merge_videos_fast(self, main_video, extra_video, output_path):
        """Fixed video merging with proper audio sync and stop check"""
        temp_dir = Path("temp_processing")
        concat_file = temp_dir / "concat_list.txt"
        temp_main = temp_dir / "temp_main.mp4"
        temp_extra = temp_dir / "temp_extra.mp4"
        
        try:
            if self.check_stop():
                return
                
            self.log("🔄 Preparing videos for merge...")
            
            # Normalize main video with stop check
            process = subprocess.Popen([
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", main_video,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "128k",
                "-r", "30", "-vsync", "cfr",
                str(temp_main)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            while process.poll() is None:
                if self.check_stop():
                    process.terminate()
                    process.wait()
                    return
                import time
                time.sleep(0.5)
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "ffmpeg")
            
            if self.check_stop():
                return
            
            # Normalize extra video with stop check
            process = subprocess.Popen([
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", extra_video,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "128k",
                "-r", "30", "-vsync", "cfr",
                str(temp_extra)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            while process.poll() is None:
                if self.check_stop():
                    process.terminate()
                    process.wait()
                    return
                import time
                time.sleep(0.5)
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "ffmpeg")
            
            if self.check_stop():
                return
            
            # Create concat file
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{os.path.abspath(temp_main).replace(os.sep, '/')}'\n")
                f.write(f"file '{os.path.abspath(temp_extra).replace(os.sep, '/')}'\n")
            
            self.log("🔗 Merging normalized videos...")
            
            # Merge videos with stop check
            process = subprocess.Popen([
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "concat", "-safe", "0", "-i", str(concat_file),
                "-c", "copy", "-avoid_negative_ts", "make_zero",
                output_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            while process.poll() is None:
                if self.check_stop():
                    process.terminate()
                    process.wait()
                    return
                import time
                time.sleep(0.5)
            
            if process.returncode != 0:
                # Fallback method
                if self.check_stop():
                    return
                    
                self.log("⚠️ Using fallback merge method...")
                process = subprocess.Popen([
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-i", str(temp_main),
                    "-i", str(temp_extra),
                    "-filter_complex", 
                    "[0:v:0][0:a:0][1:v:0][1:a:0]concat=n=2:v=1:a=1[outv][outa]",
                    "-map", "[outv]", "-map", "[outa]",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k",
                    "-avoid_negative_ts", "make_zero",
                    output_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                while process.poll() is None:
                    if self.check_stop():
                        process.terminate()
                        process.wait()
                        return
                    import time
                    time.sleep(0.5)
                    
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, "ffmpeg fallback")
                    
        except Exception as e:
            if self.check_stop():
                return
            self.log(f"❌ Video merging failed: {e}")
            raise
        finally:
            # Cleanup temp files
            for temp_file in [concat_file, temp_main, temp_extra]:
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except:
                        pass
    
    def process_single_video(self, input_video, output_path, extra_video, background_music, 
                           quality_preset, use_gpu, music_volume, enable_ducking, 
                           enable_auto_edit, subtitle_color):
        """Updated processing with auto-edit control, subtitle color and stop check"""
        base_name = Path(input_video).stem
        clean_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not clean_name:
            clean_name = f"video_{hash(base_name) % 10000}"
            
        temp_dir = Path("temp_processing")
        temp_dir.mkdir(exist_ok=True)
        
        # Temporary files
        auto_edited = temp_dir / f"auto_{clean_name}.mp4"
        audio_path = temp_dir / f"audio_{clean_name}.wav"
        ass_path = temp_dir / f"subs_{clean_name}.ass"
        final_with_subs = temp_dir / f"subs_{clean_name}.mp4"
        final_with_music = temp_dir / f"music_{clean_name}.mp4"
        
        try:
            if self.check_stop():
                return
                
            self.check_ffmpeg_availability()
            
            # Step 1: Auto-edit (conditional based on user choice)
            if enable_auto_edit:
                self.log(f"✂️ Auto-editing: {os.path.basename(input_video)}")
                try:
                    process = subprocess.Popen([
                        "auto-editor", input_video, "-o", str(auto_edited),
                        "--no-open", "--frame-rate", "30", 
                        "--silent-speed", "99999",
                        "--video-codec", "libx264"
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    while process.poll() is None:
                        if self.check_stop():
                            process.terminate()
                            process.wait()
                            return
                        import time
                        time.sleep(1)
                    
                    if process.returncode == 0:
                        self.log("✅ Auto-editing completed successfully")
                    else:
                        raise subprocess.CalledProcessError(process.returncode, "auto-editor")
                        
                except Exception as e:
                    if self.check_stop():
                        return
                    self.log(f"⚠️ Auto-editor issue: {e}, using original video")
                    shutil.copy2(input_video, auto_edited)
            else:
                self.log("ℹ️ Auto-editing disabled, using original video")
                shutil.copy2(input_video, auto_edited)
            
            if self.check_stop():
                return
            
            # Step 2: Extract audio and transcribe
            self.log("🔊 Extracting audio for transcription...")
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", str(auto_edited), "-vn",
                "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", 
                str(audio_path)
            ], check=True, timeout=120)
            
            if self.check_stop():
                return
            
            words = self.transcribe_audio_optimized(str(audio_path))
            
            if self.check_stop():
                return
            
            # Step 3: Add subtitles with custom color if transcription successful
            current_video = auto_edited
            if words:
                try:
                    self.generate_ass_subtitles(words, str(ass_path), subtitle_color)
                    
                    if self.check_stop():
                        return
                        
                    self.log(f"📝 Adding ASS subtitles with color {subtitle_color}...")
                    
                    subtitle_filter = f"ass={str(ass_path).replace('\\', '/')}"
                    
                    ffmpeg_cmd = [
                        "ffmpeg", "-y", "-loglevel", "error",
                        "-i", str(auto_edited),
                        "-vf", subtitle_filter,
                    ]
                    
                    if use_gpu:
                        try:
                            test_cmd = ["ffmpeg", "-f", "lavfi", "-i", "testsrc2=duration=1:size=320x240:rate=1", 
                                       "-c:v", "h264_nvenc", "-f", "null", "-"]
                            subprocess.run(test_cmd, capture_output=True, check=True, timeout=10)
                            ffmpeg_cmd.extend(["-c:v", "h264_nvenc", "-preset", "fast"])
                            self.log("🚀 Using GPU acceleration for subtitles")
                        except:
                            ffmpeg_cmd.extend(["-c:v", "libx264", "-preset", quality_preset, "-crf", "23"])
                    else:
                        ffmpeg_cmd.extend(["-c:v", "libx264", "-preset", quality_preset, "-crf", "23"])
                        
                    ffmpeg_cmd.extend(["-c:a", "copy", str(final_with_subs)])
                    
                    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    while process.poll() is None:
                        if self.check_stop():
                            process.terminate()
                            process.wait()
                            return
                        import time
                        time.sleep(0.5)
                    
                    if process.returncode == 0:
                        current_video = final_with_subs
                        self.log(f"✅ Custom colored subtitles ({subtitle_color}) added successfully")
                    else:
                        raise subprocess.CalledProcessError(process.returncode, "ffmpeg subtitles")
                    
                except Exception as e:
                    if self.check_stop():
                        return
                    self.log(f"⚠️ Subtitle processing failed: {e}")
                    current_video = auto_edited
            
            if self.check_stop():
                return
            
            # Step 4: Add background music BEFORE merging
            if background_music and os.path.exists(background_music):
                self.log("🎵 Processing background music...")
                success = self.add_background_music_with_ducking(
                    str(current_video), background_music, 
                    str(final_with_music), words, music_volume, enable_ducking
                )
                if success and not self.check_stop():
                    current_video = final_with_music
                    self.log("✅ Background music added successfully")
                elif not self.check_stop():
                    self.log("⚠️ Background music failed, continuing without it")
            else:
                self.log("ℹ️ No background music selected")
            
            if self.check_stop():
                return
            
            # Step 5: Merge with extra video (final step)
            self.log("🔗 Merging with extra video...")
            self.merge_videos_fast(str(current_video), extra_video, output_path)
            
            if not self.check_stop():
                self.log(f"✅ Successfully completed: {os.path.basename(output_path)}")
            
        except Exception as e:
            if self.check_stop():
                return
            self.log(f"❌ Processing failed for {os.path.basename(input_video)}: {e}")
            raise
        finally:
            # Cleanup
            for temp_file in [auto_edited, audio_path, ass_path, final_with_subs, final_with_music]:
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except:
                        pass
                    
    def process_all_videos(self, input_videos, extra_video, output_dir, 
                          background_music, quality_preset, use_gpu, music_volume, enable_ducking,
                          enable_auto_edit, subtitle_color):
        """Process all videos with enhanced options and stop functionality"""
        total_videos = len(input_videos)
        successful = 0
        failed = []
        
        # Create temp directory
        temp_dir = Path("temp_processing")
        temp_dir.mkdir(exist_ok=True)
        
        # Log processing settings
        self.log(f"🎬 Processing {total_videos} videos with settings:")
        self.log(f"   Auto-Edit: {'✅ Enabled' if enable_auto_edit else '❌ Disabled'}")
        self.log(f"   Subtitle Color: {subtitle_color}")
        self.log(f"   Quality: {quality_preset}")
        self.log(f"   GPU: {'✅ Enabled' if use_gpu else '❌ Disabled'}")
        
        try:
            for i, input_video in enumerate(input_videos, 1):
                if self.check_stop():
                    self.log(f"🛑 Processing stopped. Completed {successful}/{total_videos} videos.")
                    break
                    
                try:
                    self.log(f"📹 Processing video {i}/{total_videos}: {os.path.basename(input_video)}")
                    self.update_progress((i-1) * 100 / total_videos, 100)
                    
                    # Generate output filename
                    base_name = Path(input_video).stem
                    output_path = os.path.join(output_dir, f"{base_name}_processed.mp4")
                    
                    # Check if output already exists
                    if os.path.exists(output_path):
                        self.log(f"⚠️ Output file exists, overwriting: {os.path.basename(output_path)}")
                    
                    # Process the video with new parameters
                    self.process_single_video(
                        input_video, output_path, extra_video, 
                        background_music, quality_preset, use_gpu, 
                        music_volume, enable_ducking, enable_auto_edit, subtitle_color
                    )
                    
                    if not self.check_stop():
                        successful += 1
                        self.log(f"✅ {successful}/{total_videos} videos completed successfully")
                    
                except Exception as e:
                    if self.check_stop():
                        break
                    failed.append((input_video, str(e)))
                    self.log(f"❌ Failed to process {os.path.basename(input_video)}: {e}")
                    continue
                    
            # Final progress update
            if not self.check_stop():
                self.update_progress(100, 100)
            
            # Summary
            if self.check_stop():
                self.log(f"🛑 Processing stopped by user. Completed: {successful}, Failed: {len(failed)}")
            else:
                self.log(f"🏁 Processing complete! Success: {successful}, Failed: {len(failed)}")
                
            if failed:
                self.log("❌ Failed videos:")
                for video, error in failed:
                    self.log(f"   - {os.path.basename(video)}: {error}")
                    
        finally:
            # Cleanup temp directory
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

def check_dependencies():
    """Check if all required dependencies are installed"""
    missing = []
    
    # Check FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("FFmpeg")
    
    # Check auto-editor
    try:
        subprocess.run(["auto-editor", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("auto-editor")
    
    # Check Python packages
    try:
        import faster_whisper
    except ImportError:
        missing.append("faster-whisper (pip install faster-whisper)")
    
    return missing

def main():
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        root = tk.Tk()
        root.withdraw()
        
        message = "Missing required dependencies:\n\n" + "\n".join(f"• {dep}" for dep in missing_deps)
        message += "\n\nPlease install them before running the application."
        
        messagebox.showerror("Missing Dependencies", message)
        return
    
    # Start the application
    root = tk.Tk()
    
    # Set window icon if available
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Create application
    app = VideoProcessorGUI(root)
    
    # Handle window closing
    def on_closing():
        if app.processing:
            if messagebox.askokcancel("Quit", "Processing is still running. Are you sure you want to quit?"):
                app.stop_event.set()  # Signal stop before closing
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")

if __name__ == "__main__":
    main()
