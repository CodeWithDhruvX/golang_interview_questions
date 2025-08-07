import os
import subprocess
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import moviepy as mp

class VideoAudioTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Video Audio Tool")
        self.root.geometry("400x300")
        self.setup_gui()
    
    def setup_gui(self):
        # Title
        title_label = tk.Label(self.root, text="Video Audio Tool", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Extract Audio Button
        extract_btn = tk.Button(
            self.root, 
            text="Extract Audio from Videos", 
            command=self.extract_audio_from_videos,
            width=25,
            height=2,
            font=("Arial", 10)
        )
        extract_btn.pack(pady=10)
        
        # Replace Audio Button
        replace_btn = tk.Button(
            self.root, 
            text="Replace Audio in Videos", 
            command=self.replace_audio_in_videos,
            width=25,
            height=2,
            font=("Arial", 10)
        )
        replace_btn.pack(pady=10)
        
        # Exit Button
        exit_btn = tk.Button(
            self.root, 
            text="Exit", 
            command=self.root.quit,
            width=25,
            height=1,
            font=("Arial", 10)
        )
        exit_btn.pack(pady=20)
    
    def extract_audio_from_videos(self):
        """Extract audio from selected video files"""
        # Select video files
        video_files = filedialog.askopenfilenames(
            title="Select Video Files", 
            filetypes=[
                ("Video Files", "*.mp4;*.mkv;*.avi;*.mov;*.flv"),
                ("MP4 files", "*.mp4"),
                ("MKV files", "*.mkv"),
                ("AVI files", "*.avi"),
                ("MOV files", "*.mov"),
                ("FLV files", "*.flv"),
                ("All files", "*.*")
            ]
        )
        
        if not video_files:
            messagebox.showinfo("Info", "No files selected.")
            return

        # Select output folder
        output_dir = filedialog.askdirectory(title="Select Output Folder")
        if not output_dir:
            messagebox.showinfo("Info", "No output folder selected.")
            return

        # Process each video file
        success_count = 0
        error_count = 0
        
        for video_path in video_files:
            try:
                print(f"Processing: {os.path.basename(video_path)}")
                video = mp.VideoFileClip(video_path)
                
                if video.audio is None:
                    print(f"Warning: No audio track found in {os.path.basename(video_path)}")
                    error_count += 1
                    continue
                
                output_file = os.path.join(
                    output_dir, 
                    os.path.splitext(os.path.basename(video_path))[0] + ".wav"
                )
                
                video.audio.write_audiofile(output_file, codec='pcm_s16le', logger=None)
                video.close()  # Important: close the clip to free resources
                
                print(f"Extracted: {output_file}")
                success_count += 1
                
            except Exception as e:
                print(f"Error processing {video_path}: {e}")
                error_count += 1
        
        # Show completion message
        message = f"Audio extraction completed!\nSuccess: {success_count}\nErrors: {error_count}"
        messagebox.showinfo("Extraction Complete", message)
    
    def replace_audio_in_videos(self):
        """Replace audio in selected video files"""
        # Select video files
        video_paths = filedialog.askopenfilenames(
            title="Select Video Files", 
            filetypes=[
                ("Video Files", "*.mkv;*.mp4;*.avi;*.mov"),
                ("MKV files", "*.mkv"),
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("MOV files", "*.mov"),
                ("All files", "*.*")
            ]
        )
        
        # Select audio files
        audio_paths = filedialog.askopenfilenames(
            title="Select Audio Files", 
            filetypes=[
                ("Audio Files", "*.wav;*.mp3;*.aac;*.flac"),
                ("WAV files", "*.wav"),
                ("MP3 files", "*.mp3"),
                ("AAC files", "*.aac"),
                ("FLAC files", "*.flac"),
                ("All files", "*.*")
            ]
        )

        if not video_paths or not audio_paths:
            messagebox.showinfo("Info", "File selection canceled or incomplete.")
            return

        # Select output folder
        output_folder = filedialog.askdirectory(title="Select Output Folder")
        if not output_folder:
            messagebox.showinfo("Info", "Output folder selection canceled.")
            return

        # Get output format
        output_format = simpledialog.askstring(
            "Output Format", 
            "Enter output format (mp4/mkv/avi):", 
            initialvalue="mp4"
        )
        
        if not output_format or output_format.strip().lower() not in ["mp4", "mkv", "avi"]:
            messagebox.showinfo("Info", "Invalid format selected. Defaulting to MP4.")
            output_format = "mp4"
        else:
            output_format = output_format.strip().lower()

        # Create dictionaries for matching files by name
        video_dict = {os.path.splitext(os.path.basename(v))[0]: v for v in video_paths}
        audio_dict = {os.path.splitext(os.path.basename(a))[0]: a for a in audio_paths}

        # Process matched files
        success_count = 0
        error_count = 0
        unmatched_videos = []

        for name, video_path in video_dict.items():
            if name in audio_dict:
                audio_path = audio_dict[name]
                output_path = os.path.join(output_folder, f"{name}_output.{output_format}")
                
                if self.replace_audio(video_path, audio_path, output_path):
                    success_count += 1
                else:
                    error_count += 1
            else:
                unmatched_videos.append(name)
                print(f"No matching audio found for {name}")

        # Show completion message
        message = f"Audio replacement completed!\nSuccess: {success_count}\nErrors: {error_count}"
        if unmatched_videos:
            message += f"\nUnmatched videos: {len(unmatched_videos)}"
        
        messagebox.showinfo("Replacement Complete", message)
    
    def replace_audio(self, video_path, audio_path, output_path):
        """Replace audio in a single video file using FFmpeg"""
        try:
            print(f"Processing: {os.path.basename(video_path)} -> {os.path.basename(audio_path)}")
            
            command = [
                "ffmpeg", "-i", video_path, "-i", audio_path,
                "-c:v", "copy", "-c:a", "aac", "-strict", "experimental",
                "-map", "0:v:0", "-map", "1:a:0", "-y",  # -y to overwrite output files
                output_path
            ]
            
            # Run with minimal output
            result = subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                text=True
            )
            
            print(f"Successfully created: {os.path.basename(output_path)}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error processing {video_path}: {e}")
            print(f"FFmpeg error output: {e.stderr}")
            return False
        except FileNotFoundError:
            print("Error: FFmpeg not found. Please make sure FFmpeg is installed and in your PATH.")
            messagebox.showerror("Error", "FFmpeg not found. Please install FFmpeg and add it to your PATH.")
            return False
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main function to run the application"""
    try:
        app = VideoAudioTool()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Error", f"Application error: {e}")

if __name__ == "__main__":
    main()