import os
import sys
import threading
import numpy as np
import librosa
import soundfile as sf
from scipy import signal, ndimage
import noisereduce as nr
from sklearn.cluster import KMeans
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
from pathlib import Path
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

@dataclass
class AudioProfile:
    """Audio content profile for smart processing"""
    content_type: str
    noise_level: float
    speech_ratio: float
    music_ratio: float
    dynamic_range: float
    recommended_settings: Dict[str, Any]

class SmartAudioAnalyzer:
    """AI-powered audio content analyzer"""
    
    def __init__(self):
        self.sample_rate = 44100
        
    def analyze_audio_content(self, audio: np.ndarray, sr: int) -> AudioProfile:
        """Analyze audio content and determine optimal processing settings"""
        
        # Voice activity detection
        voice_activity = self._detect_voice_activity(audio, sr)
        speech_ratio = np.mean(voice_activity)
        
        # Music detection
        music_ratio = self._detect_music_content(audio, sr)
        
        # Noise level estimation
        noise_level = self._estimate_noise_level(audio, sr)
        
        # Dynamic range
        dynamic_range = np.max(audio) - np.min(audio)
        
        # Content type classification
        content_type = self._classify_content_type(speech_ratio, music_ratio)
        
        # Generate recommended settings
        recommended_settings = self._generate_smart_settings(
            content_type, noise_level, speech_ratio, music_ratio, dynamic_range
        )
        
        return AudioProfile(
            content_type=content_type,
            noise_level=noise_level,
            speech_ratio=speech_ratio,
            music_ratio=music_ratio,
            dynamic_range=dynamic_range,
            recommended_settings=recommended_settings
        )
    
    def _detect_voice_activity(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Detect voice activity using spectral features"""
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.01 * sr)     # 10ms hop
        
        frames = librosa.util.frame(audio, frame_length=frame_length, hop_length=hop_length)
        energy = np.sum(frames**2, axis=0)
        
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Voice activity based on energy and ZCR thresholds
        energy_threshold = np.percentile(energy, 30)
        zcr_threshold = np.percentile(zcr, 70)
        
        voice_activity = (energy > energy_threshold) & (zcr < zcr_threshold)
        return voice_activity
    
    def _detect_music_content(self, audio: np.ndarray, sr: int) -> float:
        """Detect music content ratio"""
        spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
        
        centroid_var = np.var(spectral_centroid)
        bandwidth_mean = np.mean(spectral_bandwidth)
        
        music_score = min(1.0, (bandwidth_mean / 2000) * (1 / (1 + centroid_var / 1000)))
        return music_score
    
    def _estimate_noise_level(self, audio: np.ndarray, sr: int) -> float:
        """Estimate background noise level"""
        frame_length = int(0.1 * sr)  # 100ms frames
        frames = librosa.util.frame(audio, frame_length=frame_length, hop_length=frame_length//2)
        frame_energy = np.sum(frames**2, axis=0)
        
        noise_threshold = np.percentile(frame_energy, 10)
        noise_frames = frames[:, frame_energy <= noise_threshold]
        
        if noise_frames.size > 0:
            noise_level = np.std(noise_frames)
        else:
            noise_level = np.std(audio) * 0.1
        
        return float(noise_level)
    
    def _classify_content_type(self, speech_ratio: float, music_ratio: float) -> str:
        """Classify audio content type"""
        if speech_ratio > 0.7 and music_ratio < 0.3:
            return "speech"
        elif music_ratio > 0.6:
            return "music"
        elif speech_ratio > 0.4 and music_ratio > 0.3:
            return "mixed"
        else:
            return "general"
    
    def _generate_smart_settings(self, content_type: str, noise_level: float, 
                                speech_ratio: float, music_ratio: float, 
                                dynamic_range: float) -> Dict[str, Any]:
        """Generate optimal processing settings based on content analysis"""
        
        base_settings = {
            "noise_reduction_strength": 0.6,
            "gate_threshold": -40,
            "gate_ratio": 4.0,
            "compressor_threshold": -12,
            "compressor_ratio": 3.0,
            "eq_low_cut": 80,
            "eq_high_cut": 15000,
            "limiter_threshold": -1.0,
            "normalize_target": -16.0
        }
        
        # Adjust settings based on content type
        if content_type == "speech":
            base_settings.update({
                "noise_reduction_strength": 0.8,
                "gate_threshold": -45,
                "compressor_threshold": -18,
                "compressor_ratio": 4.0,
                "eq_low_cut": 100,
                "normalize_target": -16.0
            })
        elif content_type == "music":
            base_settings.update({
                "noise_reduction_strength": 0.4,
                "gate_threshold": -50,
                "compressor_threshold": -8,
                "compressor_ratio": 2.5,
                "eq_low_cut": 40,
                "eq_high_cut": 20000,
                "normalize_target": -14.0
            })
        elif content_type == "mixed":
            base_settings.update({
                "noise_reduction_strength": 0.7,
                "gate_threshold": -35,
                "compressor_threshold": -15,
                "compressor_ratio": 3.5,
                "eq_low_cut": 60,
                "normalize_target": -16.0
            })
        
        # Adjust based on noise level
        if noise_level > 0.05:
            base_settings["noise_reduction_strength"] = min(0.9, base_settings["noise_reduction_strength"] + 0.2)
            base_settings["gate_threshold"] = max(-50, base_settings["gate_threshold"] - 5)
        
        # Adjust based on dynamic range
        if dynamic_range < 0.1:
            base_settings["compressor_ratio"] = max(1.5, base_settings["compressor_ratio"] - 1.0)
        elif dynamic_range > 0.8:
            base_settings["compressor_ratio"] = min(6.0, base_settings["compressor_ratio"] + 1.0)
        
        return base_settings

class ProfessionalAudioProcessor:
    """Professional-grade audio processing engine"""
    
    def __init__(self):
        self.analyzer = SmartAudioAnalyzer()
        
    def process_audio(self, audio: np.ndarray, sr: int, 
                     progress_callback: Optional[callable] = None) -> np.ndarray:
        """Apply professional audio processing chain"""
        
        if progress_callback:
            progress_callback("🔍 Analyzing audio content...")
        
        # Analyze audio content
        profile = self.analyzer.analyze_audio_content(audio, sr)
        settings = profile.recommended_settings
        
        if progress_callback:
            progress_callback(f"📊 Detected: {profile.content_type.upper()} content")
        
        processed_audio = audio.copy()
        
        # Professional processing chain
        if progress_callback:
            progress_callback("🔧 Removing DC offset...")
        processed_audio = self._remove_dc_offset(processed_audio)
        
        if progress_callback:
            progress_callback("🎛️ Applying advanced noise reduction...")
        processed_audio = self._advanced_noise_reduction(processed_audio, sr, settings)
        
        if progress_callback:
            progress_callback("🚪 Applying intelligent noise gate...")
        processed_audio = self._apply_noise_gate(processed_audio, sr, settings)
        
        if progress_callback:
            progress_callback("🎚️ Applying smart EQ...")
        processed_audio = self._apply_eq(processed_audio, sr, settings)
        
        if progress_callback:
            progress_callback("🎯 Applying dynamic compression...")
        processed_audio = self._apply_compression(processed_audio, sr, settings)
        
        if progress_callback:
            progress_callback("✨ Applying de-esser and exciter...")
        processed_audio = self._apply_deesser(processed_audio, sr)
        processed_audio = self._apply_exciter(processed_audio, sr)
        
        if progress_callback:
            progress_callback("🔒 Applying limiter...")
        processed_audio = self._apply_limiter(processed_audio, sr, settings)
        
        if progress_callback:
            progress_callback("📏 Normalizing to YouTube standards...")
        processed_audio = self._normalize_audio(processed_audio, settings)
        
        return processed_audio, profile
    
    def _remove_dc_offset(self, audio: np.ndarray) -> np.ndarray:
        """Remove DC offset"""
        return audio - np.mean(audio)
    
    def _advanced_noise_reduction(self, audio: np.ndarray, sr: int, settings: Dict) -> np.ndarray:
        """Advanced multi-band noise reduction"""
        strength = settings.get("noise_reduction_strength", 0.6)
        
        # Multi-band noise reduction
        nyquist = sr // 2
        bands = [(0, 200), (200, 1000), (1000, 4000), (4000, nyquist)]
        processed_bands = []
        
        for low, high in bands:
            # Bandpass filter
            sos = signal.butter(4, [max(1, low), min(nyquist-1, high)], 
                              btype='band', fs=sr, output='sos')
            band_audio = signal.sosfilt(sos, audio)
            
            # Adaptive noise reduction
            band_strength = strength
            if low < 200:  # Low frequencies - more aggressive
                band_strength *= 1.3
            elif high > 4000:  # High frequencies - moderate
                band_strength *= 0.9
            
            # Apply spectral subtraction
            reduced_band = nr.reduce_noise(y=band_audio, sr=sr, prop_decrease=band_strength)
            processed_bands.append(reduced_band)
        
        return np.sum(processed_bands, axis=0)
    
    def _apply_noise_gate(self, audio: np.ndarray, sr: int, settings: Dict) -> np.ndarray:
        """Apply intelligent noise gate"""
        threshold = settings.get("gate_threshold", -40)
        ratio = settings.get("gate_ratio", 4.0)
        
        threshold_linear = 10**(threshold/20)
        
        # Calculate smooth envelope
        envelope = np.abs(signal.hilbert(audio))
        window_size = int(0.01 * sr)  # 10ms
        envelope_smooth = ndimage.uniform_filter1d(envelope, size=window_size, mode='constant')
        
        # Apply gate with smooth transitions
        gate_reduction = np.ones_like(envelope_smooth)
        below_threshold = envelope_smooth < threshold_linear
        gate_reduction[below_threshold] = 1.0 / ratio
        
        # Smooth gate transitions
        gate_reduction = ndimage.uniform_filter1d(gate_reduction, size=window_size//2, mode='constant')
        
        return audio * gate_reduction
    
    def _apply_eq(self, audio: np.ndarray, sr: int, settings: Dict) -> np.ndarray:
        """Apply intelligent EQ"""
        low_cut = settings.get("eq_low_cut", 80)
        high_cut = settings.get("eq_high_cut", 15000)
        
        # High-pass filter (remove rumble)
        if low_cut > 20:
            sos_hp = signal.butter(4, low_cut, btype='high', fs=sr, output='sos')
            audio = signal.sosfilt(sos_hp, audio)
        
        # Low-pass filter (remove harsh highs)
        if high_cut < sr//2 - 1000:
            sos_lp = signal.butter(4, high_cut, btype='low', fs=sr, output='sos')
            audio = signal.sosfilt(sos_lp, audio)
        
        # Speech presence boost (2-4 kHz)
        sos_presence = signal.butter(2, [2000, 4000], btype='band', fs=sr, output='sos')
        presence = signal.sosfilt(sos_presence, audio)
        audio = audio + 0.12 * presence
        
        return audio
    
    def _apply_compression(self, audio: np.ndarray, sr: int, settings: Dict) -> np.ndarray:
        """Apply professional compression"""
        threshold = settings.get("compressor_threshold", -12)
        ratio = settings.get("compressor_ratio", 3.0)
        attack_time = 0.003  # 3ms
        release_time = 0.1   # 100ms
        
        # Convert to dB
        audio_db = 20 * np.log10(np.abs(audio) + 1e-10)
        
        # Calculate gain reduction
        gain_reduction = np.zeros_like(audio_db)
        above_threshold = audio_db > threshold
        gain_reduction[above_threshold] = (audio_db[above_threshold] - threshold) * (1 - 1/ratio)
        
        # Smooth gain reduction (attack/release)
        attack_samples = int(attack_time * sr)
        release_samples = int(release_time * sr)
        
        smoothed_gain = np.zeros_like(gain_reduction)
        for i in range(1, len(gain_reduction)):
            if gain_reduction[i] > smoothed_gain[i-1]:  # Attack
                alpha = 1 - np.exp(-1 / attack_samples)
            else:  # Release
                alpha = 1 - np.exp(-1 / release_samples)
            
            smoothed_gain[i] = alpha * gain_reduction[i] + (1 - alpha) * smoothed_gain[i-1]
        
        # Apply compression
        compressed_gain = 10**(-smoothed_gain/20)
        return audio * compressed_gain
    
    def _apply_deesser(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply de-esser to reduce sibilance"""
        # Detect sibilant frequencies (5-10 kHz)
        sos = signal.butter(4, [5000, 10000], btype='band', fs=sr, output='sos')
        sibilant_band = signal.sosfilt(sos, audio)
        
        # Calculate sibilant energy
        sibilant_energy = np.abs(signal.hilbert(sibilant_band))
        threshold = np.percentile(sibilant_energy, 85)
        
        # Apply de-essing
        reduction = np.ones_like(sibilant_energy)
        excessive_sibilance = sibilant_energy > threshold
        reduction[excessive_sibilance] = 0.4
        
        # Smooth reduction
        window_size = int(0.005 * sr)  # 5ms
        reduction_smooth = ndimage.uniform_filter1d(reduction, size=window_size, mode='constant')
        
        # Apply only to sibilant frequencies
        deessed_sibilant = sibilant_band * reduction_smooth
        
        return audio - sibilant_band + deessed_sibilant
    
    def _apply_exciter(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply harmonic exciter for presence"""
        # Generate harmonics of high frequencies
        sos = signal.butter(4, 3000, btype='high', fs=sr, output='sos')
        high_freq = signal.sosfilt(sos, audio)
        
        # Generate subtle harmonics
        harmonics = np.tanh(high_freq * 1.5) * 0.08
        
        return audio + harmonics
    
    def _apply_limiter(self, audio: np.ndarray, sr: int, settings: Dict) -> np.ndarray:
        """Apply transparent limiting"""
        threshold = settings.get("limiter_threshold", -1.0)
        threshold_linear = 10**(threshold/20)
        
        # Lookahead limiting
        lookahead_samples = int(0.005 * sr)  # 5ms lookahead
        
        # Calculate peak envelope with lookahead
        audio_padded = np.pad(audio, (lookahead_samples, 0), mode='constant')
        envelope = np.abs(signal.hilbert(audio_padded))
        
        # Find peaks that exceed threshold
        peak_reduction = np.ones_like(envelope)
        exceeding_peaks = envelope > threshold_linear
        peak_reduction[exceeding_peaks] = threshold_linear / envelope[exceeding_peaks]
        
        # Smooth limiting
        window_size = int(0.001 * sr)  # 1ms
        peak_reduction_smooth = ndimage.uniform_filter1d(peak_reduction, size=window_size, mode='constant')
        
        # Apply limiting with lookahead compensation
        limited_audio = audio * peak_reduction_smooth[lookahead_samples:]
        
        return limited_audio
    
    def _normalize_audio(self, audio: np.ndarray, settings: Dict) -> np.ndarray:
        """Normalize to YouTube standards"""
        target_db = settings.get("normalize_target", -16.0)
        
        # Peak normalization with headroom
        current_peak_db = 20 * np.log10(np.max(np.abs(audio)) + 1e-10)
        gain_db = target_db - current_peak_db
        gain_linear = 10**(gain_db/20)
        
        return audio * gain_linear

class VideoAudioEnhancer:
    """Main video processing class"""
    
    def __init__(self):
        self.processor = ProfessionalAudioProcessor()
        
    def extract_audio_from_video(self, video_path: str, temp_audio_path: str) -> bool:
        """Extract audio from video using FFmpeg"""
        try:
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',
                '-ar', '44100',
                '-ac', '2',  # Stereo
                '-y',  # Overwrite
                temp_audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def replace_video_audio(self, video_path: str, enhanced_audio_path: str, 
                          output_path: str) -> bool:
        """Replace video audio with enhanced version"""
        try:
            cmd = [
                'ffmpeg', '-i', video_path, '-i', enhanced_audio_path,
                '-c:v', 'copy',  # Copy video stream without re-encoding
                '-c:a', 'aac',   # Encode audio as AAC
                '-b:a', '192k',  # Audio bitrate
                '-map', '0:v:0', # Map video from first input
                '-map', '1:a:0', # Map audio from second input
                '-y',            # Overwrite output
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception:
            return False
    
    def process_video(self, video_path: str, output_path: str, 
                     progress_callback: Optional[callable] = None) -> bool:
        """Process video with enhanced audio"""
        
        try:
            if progress_callback:
                progress_callback("🎬 Extracting audio from video...")
            
            # Create temp audio file
            temp_audio_original = "temp_original_audio.wav"
            temp_audio_enhanced = "temp_enhanced_audio.wav"
            
            # Extract audio
            if not self.extract_audio_from_video(video_path, temp_audio_original):
                raise Exception("Failed to extract audio from video")
            
            if progress_callback:
                progress_callback("🎵 Loading audio for processing...")
            
            # Load audio
            audio, sr = librosa.load(temp_audio_original, sr=44100)
            
            # Process audio
            enhanced_audio, profile = self.processor.process_audio(audio, sr, progress_callback)
            
            if progress_callback:
                progress_callback("💾 Saving enhanced audio...")
            
            # Save enhanced audio
            sf.write(temp_audio_enhanced, enhanced_audio, sr)
            
            if progress_callback:
                progress_callback("🎬 Combining enhanced audio with video...")
            
            # Replace audio in video
            if not self.replace_video_audio(video_path, temp_audio_enhanced, output_path):
                raise Exception("Failed to combine enhanced audio with video")
            
            # Cleanup temp files
            for temp_file in [temp_audio_original, temp_audio_enhanced]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            if progress_callback:
                progress_callback(f"✅ Video processing complete! Content type: {profile.content_type.upper()}")
            
            return True
            
        except Exception as e:
            # Cleanup temp files on error
            for temp_file in ["temp_original_audio.wav", "temp_enhanced_audio.wav"]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            if progress_callback:
                progress_callback(f"❌ Error: {str(e)}")
            
            return False

class SimpleVideoProcessorGUI:
    """Simple GUI for video processing"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Audio Enhancer - AI Powered")
        self.root.geometry("600x500")
        self.root.configure(bg='#1a1a1a')
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_dark_theme()
        
        self.enhancer = VideoAudioEnhancer()
        self.video_files = []
        self.output_directory = ""
        
        self.setup_gui()
        
    def configure_dark_theme(self):
        """Configure dark theme"""
        self.style.configure('Dark.TFrame', background='#1a1a1a')
        self.style.configure('Dark.TLabel', background='#1a1a1a', foreground='#ffffff', font=('Arial', 10))
        self.style.configure('Dark.TButton', background='#404040', foreground='#ffffff', font=('Arial', 10, 'bold'))
        self.style.configure('Title.TLabel', background='#1a1a1a', foreground='#00ff88', font=('Arial', 16, 'bold'))
        
    def setup_gui(self):
        """Setup the GUI"""
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎥 AI Video Audio Enhancer", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        subtitle_label = ttk.Label(main_frame, text="Professional audio enhancement for YouTube videos", style='Dark.TLabel')
        subtitle_label.pack(pady=(0, 30))
        
        # Video selection section
        video_section = ttk.Frame(main_frame, style='Dark.TFrame')
        video_section.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        ttk.Label(video_section, text="📁 Select Video Files:", style='Dark.TLabel', font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Video selection buttons
        btn_frame = ttk.Frame(video_section, style='Dark.TFrame')
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="🎬 Add Videos", command=self.select_videos, style='Dark.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="🗑️ Clear All", command=self.clear_videos, style='Dark.TButton').pack(side=tk.LEFT)
        
        # Video list
        self.video_listbox = tk.Listbox(video_section, height=8, bg='#2a2a2a', fg='#ffffff', 
                                       selectbackground='#404040', font=('Arial', 9))
        scrollbar = ttk.Scrollbar(video_section, orient=tk.VERTICAL, command=self.video_listbox.yview)
        self.video_listbox.configure(yscrollcommand=scrollbar.set)
        
        list_frame = ttk.Frame(video_section, style='Dark.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.video_listbox.pack(in_=list_frame, side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(in_=list_frame, side=tk.RIGHT, fill=tk.Y)
        
        # Output directory section
        output_section = ttk.Frame(main_frame, style='Dark.TFrame')
        output_section.pack(fill=tk.X, pady=(20, 20))
        
        ttk.Label(output_section, text="💾 Save Enhanced Videos To:", style='Dark.TLabel', font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        output_frame = ttk.Frame(output_section, style='Dark.TFrame')
        output_frame.pack(fill=tk.X)
        
        self.output_var = tk.StringVar()
        output_entry = tk.Entry(output_frame, textvariable=self.output_var, font=('Arial', 10), 
                               bg='#2a2a2a', fg='#ffffff', insertbackground='#ffffff')
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        
        ttk.Button(output_frame, text="📂 Browse", command=self.select_output_directory, style='Dark.TButton').pack(side=tk.RIGHT, padx=(10, 0))
        
        # Process button
        self.process_btn = ttk.Button(main_frame, text="🚀 ENHANCE VIDEOS", 
                                     command=self.start_processing, style='Dark.TButton')
        self.process_btn.pack(pady=(30, 20))
        
        # Progress section
        progress_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_var = tk.StringVar(value="Ready to enhance your videos with AI-powered audio processing")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var, style='Dark.TLabel')
        self.progress_label.pack(anchor=tk.W, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X)
        
        # Info section
        info_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        info_frame.pack(fill=tk.X)
        
        info_text = """✨ AI Features: Auto content detection • Advanced noise reduction • Speech enhancement
🎯 YouTube Ready: Optimized loudness • Professional dynamics • Broadcast quality"""
        
        ttk.Label(info_frame, text=info_text, style='Dark.TLabel', justify=tk.CENTER).pack()
        
    def select_videos(self):
        """Select video files"""
        file_types = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select Video Files for Audio Enhancement",
            filetypes=file_types
        )
        
        for file in files:
            if file not in self.video_files:
                self.video_files.append(file)
                filename = os.path.basename(file)
                self.video_listbox.insert(tk.END, f"🎬 {filename}")
                
    def clear_videos(self):
        """Clear video list"""
        self.video_files.clear()
        self.video_listbox.delete(0, tk.END)
        
    def select_output_directory(self):
        """Select output directory"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_directory = directory
            self.output_var.set(directory)
            
    def start_processing(self):
        """Start video processing"""
        if not self.video_files:
            messagebox.showerror("Error", "Please select at least one video file.")
            return
            
        if not self.output_directory:
            messagebox.showerror("Error", "Please select an output directory.")
            return
            
        # Start processing in thread
        self.process_btn.config(state='disabled')
        self.progress_bar.start()
        
        threading.Thread(target=self.process_videos_worker, daemon=True).start()
        
    def process_videos_worker(self):
        """Worker thread for processing videos"""
        try:
            successful = 0
            total = len(self.video_files)
            
            for i, video_path in enumerate(self.video_files):
                filename = os.path.basename(video_path)
                name_without_ext = os.path.splitext(filename)[0]
                output_path = os.path.join(self.output_directory, f"{name_without_ext}_enhanced.mp4")
                
                def progress_callback(message):
                    self.progress_var.set(f"[{i+1}/{total}] {filename}: {message}")
                    self.root.update()
                
                progress_callback("Starting processing...")
                
                # Process the video
                success = self.enhancer.process_video(video_path, output_path, progress_callback)
                
                if success:
                    successful += 1
                    progress_callback("✅ Complete!")
                else:
                    progress_callback("❌ Failed!")
                
                time.sleep(1)  # Brief pause between files
            
            # Show completion message
            self.progress_var.set(f"🎉 Processing complete! {successful}/{total} videos enhanced successfully")
            
            if successful > 0:
                messagebox.showinfo("Success!", 
                    f"Video enhancement complete!\n\n"
                    f"✅ Successfully processed: {successful}/{total} videos\n"
                    f"📁 Enhanced videos saved to: {self.output_directory}\n\n"
                    f"🎵 Features applied:\n"
                    f"• AI content detection\n"
                    f"• Advanced noise reduction\n"
                    f"• Professional audio enhancement\n"
                    f"• YouTube-optimized loudness\n"
                    f"• Background noise removal")
            else:
                messagebox.showerror("Error", "No videos were processed successfully. Please check your files and try again.")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during processing:\n{str(e)}")
            self.progress_var.set("❌ Processing failed")
            
        finally:
            self.progress_bar.stop()
            self.process_btn.config(state='normal')

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['librosa', 'soundfile', 'noisereduce', 'scipy', 'numpy', 'sklearn']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages. Please install them using:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    # Check for FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg is required but not found. Please install FFmpeg:")
        print("Windows: Download from https://ffmpeg.org/download.html")
        print("macOS: brew install ffmpeg")
        print("Linux: sudo apt-get install ffmpeg")
        return False
    
    return True

def main():
    """Main application entry point"""
    print("🎬 YouTube Video Audio Enhancer")
    print("=" * 40)
    
    if not check_dependencies():
        input("\nPress Enter to exit...")
        return
    
    print("✅ All dependencies found!")
    print("🚀 Starting application...")
    
    root = tk.Tk()
    app = SimpleVideoProcessorGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")

if __name__ == "__main__":
    main()