import os
import json
import time
import threading
from datetime import datetime
import pytz
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter.ttk import Progressbar
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from PIL import Image, ImageTk
import webbrowser

# Constants
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
CATEGORY_MAP = {
    "Film & Animation": "1", "Autos & Vehicles": "2", "Music": "10", "Pets & Animals": "15",
    "Sports": "17", "Travel & Events": "19", "Gaming": "20", "People & Blogs": "22", "Comedy": "23",
    "Entertainment": "24", "News & Politics": "25", "Howto & Style": "26", "Education": "27",
    "Science & Technology": "28", "Nonprofits & Activism": "29"
}

class YouTubeUploaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Bulk Uploader Pro")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Variables
        self.youtube_service = None
        self.client_secret_path = tk.StringVar()
        self.metadata_path = tk.StringVar()
        self.upload_thread = None
        self.is_uploading = False
        self.video_queue = []
        self.current_video_index = 0
        self.successful_uploads = 0
        self.failed_uploads = 0
        
        self.setup_ui()
        self.center_window()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
    def setup_ui(self):
        """Setup the main user interface"""
        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="YouTube Bulk Uploader Pro", 
                               font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Setup sections
        self.setup_file_selection(main_frame)
        self.setup_authentication_section(main_frame)
        self.setup_video_management(main_frame)
        self.setup_upload_controls(main_frame)
        self.setup_progress_section(main_frame)
        self.setup_log_section(main_frame)
        self.setup_status_bar(main_frame)
        
    def setup_file_selection(self, parent):
        """Setup file selection section"""
        # File Selection Frame
        file_frame = ttk.LabelFrame(parent, text="File Selection", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # Client Secret File
        ttk.Label(file_frame, text="Client Secret:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(file_frame, textvariable=self.client_secret_path, state='readonly').grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(file_frame, text="Browse", 
                  command=self.select_client_secret).grid(row=0, column=2)
        
        # Metadata File
        ttk.Label(file_frame, text="Metadata JSON:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        ttk.Entry(file_frame, textvariable=self.metadata_path, state='readonly').grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))
        ttk.Button(file_frame, text="Browse", 
                  command=self.select_metadata_file).grid(row=1, column=2, pady=(10, 0))
        
        # Quick actions
        actions_frame = ttk.Frame(file_frame)
        actions_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(actions_frame, text="Create Sample Metadata", 
                  command=self.create_sample_metadata).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(actions_frame, text="Validate Metadata", 
                  command=self.validate_metadata).pack(side=tk.LEFT)
        
    def setup_authentication_section(self, parent):
        """Setup authentication section"""
        auth_frame = ttk.LabelFrame(parent, text="Authentication", padding="10")
        auth_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.auth_status = ttk.Label(auth_frame, text="Not Authenticated", foreground="red")
        self.auth_status.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(auth_frame, text="Authenticate", 
                  command=self.authenticate_youtube).grid(row=0, column=1, padx=(10, 0))
        ttk.Button(auth_frame, text="Clear Credentials", 
                  command=self.clear_credentials).grid(row=0, column=2, padx=(10, 0))
        
    def setup_video_management(self, parent):
        """Setup video management section"""
        video_frame = ttk.LabelFrame(parent, text="Video Queue", padding="10")
        video_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        video_frame.columnconfigure(0, weight=1)
        video_frame.rowconfigure(0, weight=1)
        
        # Video list with scrollbar
        list_frame = ttk.Frame(video_frame)
        list_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview for video list
        columns = ('Status', 'Title', 'Category', 'Privacy', 'File')
        self.video_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        # Configure columns
        self.video_tree.heading('Status', text='Status')
        self.video_tree.heading('Title', text='Title')
        self.video_tree.heading('Category', text='Category')
        self.video_tree.heading('Privacy', text='Privacy')
        self.video_tree.heading('File', text='File')
        
        self.video_tree.column('Status', width=80)
        self.video_tree.column('Title', width=200)
        self.video_tree.column('Category', width=120)
        self.video_tree.column('Privacy', width=80)
        self.video_tree.column('File', width=150)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.video_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.video_tree.xview)
        self.video_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.video_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Video management buttons
        button_frame = ttk.Frame(video_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Load Videos", 
                  command=self.load_videos).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Remove Selected", 
                  command=self.remove_selected_video).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Clear All", 
                  command=self.clear_video_queue).pack(side=tk.LEFT)
        
    def setup_upload_controls(self, parent):
        """Setup upload control section"""
        control_frame = ttk.LabelFrame(parent, text="Upload Controls", padding="10")
        control_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Upload options
        options_frame = ttk.Frame(control_frame)
        options_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # Delay between uploads
        ttk.Label(options_frame, text="Delay between uploads (seconds):").grid(row=0, column=0, sticky=tk.W)
        self.delay_var = tk.StringVar(value="10")
        delay_spin = ttk.Spinbox(options_frame, from_=1, to=300, textvariable=self.delay_var, width=10)
        delay_spin.grid(row=0, column=1, padx=(10, 20), sticky=tk.W)
        
        # Auto-retry failed uploads
        self.retry_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Auto-retry failed uploads", 
                       variable=self.retry_var).grid(row=0, column=2, sticky=tk.W)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        self.start_button = ttk.Button(button_frame, text="Start Upload", 
                                      command=self.start_upload, state='disabled')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.pause_button = ttk.Button(button_frame, text="Pause", 
                                      command=self.pause_upload, state='disabled')
        self.pause_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                     command=self.stop_upload, state='disabled')
        self.stop_button.pack(side=tk.LEFT)
        
    def setup_progress_section(self, parent):
        """Setup progress tracking section"""
        progress_frame = ttk.LabelFrame(parent, text="Upload Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # Overall progress
        ttk.Label(progress_frame, text="Overall Progress:").grid(row=0, column=0, sticky=tk.W)
        self.overall_progress = Progressbar(progress_frame, mode='determinate')
        self.overall_progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 10))
        
        # Current video progress
        ttk.Label(progress_frame, text="Current Video:").grid(row=2, column=0, sticky=tk.W)
        self.current_progress = Progressbar(progress_frame, mode='determinate')
        self.current_progress.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(5, 10))
        
        # Statistics
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        self.stats_label = ttk.Label(stats_frame, text="Ready to upload")
        self.stats_label.pack(side=tk.LEFT)
        
        self.current_video_label = ttk.Label(stats_frame, text="")
        self.current_video_label.pack(side=tk.RIGHT)
        
    def setup_log_section(self, parent):
        """Setup logging section"""
        log_frame = ttk.LabelFrame(parent, text="Upload Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(log_controls, text="Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT)
        ttk.Button(log_controls, text="Save Log", 
                  command=self.save_log).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(log_controls, text="Auto-scroll", 
                  command=self.toggle_autoscroll).pack(side=tk.RIGHT)
        
        self.autoscroll = True
        
    def setup_status_bar(self, parent):
        """Setup status bar"""
        self.status_bar = ttk.Label(parent, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        if self.autoscroll:
            self.log_text.see(tk.END)
        
        # Also update status bar
        self.status_bar.config(text=message)
        self.root.update_idletasks()
        
    def select_client_secret(self):
        """Select client secret file"""
        file_path = filedialog.askopenfilename(
            title="Select client_secret.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.client_secret_path.set(file_path)
            self.log_message(f"Client secret selected: {os.path.basename(file_path)}")
            
    def select_metadata_file(self):
        """Select metadata JSON file"""
        file_path = filedialog.askopenfilename(
            title="Select metadata.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.metadata_path.set(file_path)
            self.log_message(f"Metadata file selected: {os.path.basename(file_path)}")
            self.load_videos()
            
    def create_sample_metadata(self):
        """Create a sample metadata file"""
        sample_data = {
            "videos": [
                {
                    "title": "Sample Video Title",
                    "description": "Sample video description with details about the content.",
                    "tags": ["sample", "tutorial", "youtube"],
                    "categoryName": "Education",
                    "privacyStatus": "public",
                    "videoFile": "path/to/your/video.mp4",
                    "thumbnail": "path/to/your/thumbnail.jpg",
                    "playlistNames": ["My Playlist"],
                    "publishAt": "2025-08-05 10:00:00",
                    "madeForKids": False
                }
            ]
        }
        
        file_path = filedialog.asksaveasfilename(
            title="Save sample metadata",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(sample_data, f, indent=2, ensure_ascii=False)
                self.log_message(f"Sample metadata created: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", "Sample metadata file created successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create sample file: {e}")
                
    def validate_metadata(self):
        """Validate the selected metadata file"""
        if not self.metadata_path.get():
            messagebox.showwarning("Warning", "Please select a metadata file first")
            return
            
        try:
            with open(self.metadata_path.get(), 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if "videos" not in data:
                raise ValueError("Missing 'videos' key in metadata")
                
            videos = data["videos"]
            if not isinstance(videos, list) or len(videos) == 0:
                raise ValueError("No videos found in metadata")
                
            # Validate each video
            required_fields = ["title", "description", "videoFile", "privacyStatus"]
            for i, video in enumerate(videos):
                for field in required_fields:
                    if field not in video:
                        raise ValueError(f"Missing required field '{field}' in video {i+1}")
                        
                # Check if video file exists
                if not os.path.exists(video["videoFile"]):
                    self.log_message(f"Warning: Video file not found: {video['videoFile']}")
                    
            self.log_message(f"Metadata validation successful: {len(videos)} videos found")
            messagebox.showinfo("Validation Success", f"Metadata is valid!\nFound {len(videos)} videos to upload.")
            
        except Exception as e:
            self.log_message(f"Metadata validation failed: {e}")
            messagebox.showerror("Validation Error", f"Metadata validation failed:\n{e}")
            
    def authenticate_youtube(self):
        """Authenticate with YouTube API"""
        if not self.client_secret_path.get():
            messagebox.showwarning("Warning", "Please select client secret file first")
            return
            
        def auth_thread():
            try:
                self.log_message("Starting authentication...")
                self.youtube_service = self.get_authenticated_service(self.client_secret_path.get())
                
                # Test the connection
                request = self.youtube_service.channels().list(part="snippet", mine=True)
                response = request.execute()
                
                if response.get("items"):
                    channel_name = response["items"][0]["snippet"]["title"]
                    self.log_message(f"Authentication successful! Connected to: {channel_name}")
                    self.auth_status.config(text=f"Authenticated: {channel_name}", foreground="green")
                    self.check_upload_ready()
                else:
                    raise Exception("No channel found")
                    
            except Exception as e:
                self.log_message(f"Authentication failed: {e}")
                self.auth_status.config(text="Authentication Failed", foreground="red")
                messagebox.showerror("Authentication Error", f"Failed to authenticate:\n{e}")
                
        # Run authentication in separate thread
        auth_thread = threading.Thread(target=auth_thread, daemon=True)
        auth_thread.start()
        
    def clear_credentials(self):
        """Clear saved credentials"""
        token_file = "token.json"
        if os.path.exists(token_file):
            os.remove(token_file)
            self.log_message("Credentials cleared")
            self.auth_status.config(text="Not Authenticated", foreground="red")
            self.youtube_service = None
            self.check_upload_ready()
        else:
            messagebox.showinfo("Info", "No credentials to clear")
            
    def load_videos(self):
        """Load videos from metadata file"""
        if not self.metadata_path.get():
            return
            
        try:
            with open(self.metadata_path.get(), 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.video_queue = data.get("videos", [])
            self.update_video_tree()
            self.log_message(f"Loaded {len(self.video_queue)} videos from metadata")
            self.check_upload_ready()
            
        except Exception as e:
            self.log_message(f"Failed to load videos: {e}")
            messagebox.showerror("Error", f"Failed to load videos:\n{e}")
            
    def update_video_tree(self):
        """Update the video tree display"""
        # Clear existing items
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
            
        # Add videos to tree
        for i, video in enumerate(self.video_queue):
            status = "Pending"
            title = video.get("title", "Untitled")
            category = video.get("categoryName", "Unknown")
            privacy = video.get("privacyStatus", "public")
            filename = os.path.basename(video.get("videoFile", ""))
            
            self.video_tree.insert("", tk.END, values=(status, title, category, privacy, filename))
            
    def remove_selected_video(self):
        """Remove selected video from queue"""
        selection = self.video_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a video to remove")
            return
            
        # Get selected index
        item = selection[0]
        index = self.video_tree.index(item)
        
        # Remove from queue and tree
        del self.video_queue[index]
        self.video_tree.delete(item)
        
        self.log_message(f"Removed video from queue (index {index})")
        self.check_upload_ready()
        
    def clear_video_queue(self):
        """Clear all videos from queue"""
        if messagebox.askyesno("Confirm", "Clear all videos from queue?"):
            self.video_queue.clear()
            self.update_video_tree()
            self.log_message("Video queue cleared")
            self.check_upload_ready()
            
    def check_upload_ready(self):
        """Check if ready to start upload"""
        ready = (self.youtube_service is not None and 
                len(self.video_queue) > 0 and 
                not self.is_uploading)
        
        self.start_button.config(state='normal' if ready else 'disabled')
        
    def start_upload(self):
        """Start the upload process"""
        if self.is_uploading:
            return
            
        self.is_uploading = True
        self.current_video_index = 0
        self.successful_uploads = 0
        self.failed_uploads = 0
        
        # Update UI
        self.start_button.config(state='disabled')
        self.pause_button.config(state='normal')
        self.stop_button.config(state='normal')
        
        # Start upload thread
        self.upload_thread = threading.Thread(target=self.upload_worker, daemon=True)
        self.upload_thread.start()
        
        self.log_message("Upload process started")
        
    def pause_upload(self):
        """Pause/Resume upload process"""
        # Implementation for pause/resume functionality
        pass
        
    def stop_upload(self):
        """Stop the upload process"""
        self.is_uploading = False
        self.start_button.config(state='normal')
        self.pause_button.config(state='disabled')
        self.stop_button.config(state='disabled')
        self.log_message("Upload process stopped")
        
    def upload_worker(self):
        """Worker thread for uploading videos"""
        try:
            total_videos = len(self.video_queue)
            
            for i, video in enumerate(self.video_queue):
                if not self.is_uploading:
                    break
                    
                self.current_video_index = i
                
                # Update UI
                self.root.after(0, self.update_progress_ui, i, total_videos, video)
                
                # Upload video
                success = self.upload_single_video(video, i)
                
                if success:
                    self.successful_uploads += 1
                    self.root.after(0, self.update_video_status, i, "✅ Success", "green")
                else:
                    self.failed_uploads += 1
                    self.root.after(0, self.update_video_status, i, "❌ Failed", "red")
                    
                # Update statistics
                self.root.after(0, self.update_stats_ui)
                
                # Delay between uploads
                if i < total_videos - 1 and self.is_uploading:
                    delay = int(self.delay_var.get())
                    self.log_message(f"Waiting {delay} seconds before next upload...")
                    time.sleep(delay)
                    
        except Exception as e:
            self.log_message(f"Upload worker error: {e}")
        finally:
            self.root.after(0, self.upload_completed)
            
    def upload_single_video(self, video_data, index):
        """Upload a single video"""
        try:
            self.log_message(f"Uploading: {video_data['title']}")
            
            # Check if video file exists
            video_file = video_data["videoFile"]
            if not os.path.exists(video_file):
                self.log_message(f"Video file not found: {video_file}")
                return False
                
            category_id = CATEGORY_MAP.get(video_data.get("categoryName", "People & Blogs"), "22")
            
            request_body = {
                "snippet": {
                    "title": video_data["title"],
                    "description": video_data["description"],
                    "tags": video_data.get("tags", []),
                    "categoryId": category_id,
                    "defaultLanguage": "en",
                    "defaultAudioLanguage": "en"
                },
                "status": {
                    "privacyStatus": video_data.get("privacyStatus", "public"),
                    "selfDeclaredMadeForKids": video_data.get("madeForKids", False),
                    "embeddable": True,
                    "publicStatsViewable": True,
                }
            }
            
            # Handle scheduled publishing
            if video_data.get("publishAt"):
                utc_publish_time = self.convert_ist_to_utc(video_data["publishAt"])
                if utc_publish_time:
                    request_body["status"]["publishAt"] = utc_publish_time
                    request_body["status"]["privacyStatus"] = "private"
                    
            # Upload video
            media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
            request = self.youtube_service.videos().insert(
                part="snippet,status",
                body=request_body,
                media_body=media
            )
            
            response = None
            while response is None:
                if not self.is_uploading:
                    return False
                    
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    self.root.after(0, self.update_current_progress, progress)
                    
            video_id = response["id"]
            self.log_message(f"✅ Upload successful: {video_data['title']} (ID: {video_id})")
            
            # Handle thumbnail and playlists
            self.handle_post_upload(video_id, video_data)
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Upload failed: {e}")
            return False
            
    def handle_post_upload(self, video_id, video_data):
        """Handle thumbnail upload and playlist addition"""
        try:
            # Upload thumbnail
            if video_data.get("thumbnail") and os.path.exists(video_data["thumbnail"]):
                self.youtube_service.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(video_data["thumbnail"])
                ).execute()
                self.log_message("✅ Thumbnail uploaded")
                
            # Add to playlists
            playlist_names = video_data.get("playlistNames", [])
            if isinstance(playlist_names, str):
                playlist_names = [playlist_names]
                
            for playlist_name in playlist_names:
                playlist_id = self.get_or_create_playlist(playlist_name)
                if playlist_id:
                    self.add_to_playlist(video_id, playlist_id)
                    
        except Exception as e:
            self.log_message(f"⚠️ Post-upload error: {e}")
            
    def get_or_create_playlist(self, playlist_name):
        """Get playlist ID or create new playlist"""
        try:
            # Search for existing playlist
            request = self.youtube_service.playlists().list(part="snippet", mine=True, maxResults=50)
            response = request.execute()
            
            for playlist in response.get("items", []):
                if playlist["snippet"]["title"] == playlist_name:
                    return playlist["id"]
                    
            # Create new playlist
            create_request = self.youtube_service.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": playlist_name,
                        "description": f"Playlist for {playlist_name}",
                        "defaultLanguage": "en"
                    },
                    "status": {"privacyStatus": "public"}
                }
            )
            return create_request.execute()["id"]
            
        except Exception as e:
            self.log_message(f"❌ Playlist error: {e}")
            return None
            
    def add_to_playlist(self, video_id, playlist_id):
        """Add video to playlist"""
        try:
            self.youtube_service.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id}
                    }
                }
            ).execute()
            self.log_message("✅ Added to playlist")
        except Exception as e:
            self.log_message(f"❌ Playlist addition failed: {e}")
            
    def update_progress_ui(self, current, total, video):
        """Update progress UI elements"""
        # Overall progress
        overall_progress = (current / total) * 100 if total > 0 else 0
        self.overall_progress['value'] = overall_progress
        
        # Reset current video progress
        self.current_progress['value'] = 0
        
        # Update labels
        self.current_video_label.config(text=f"Uploading: {video['title']}")
        
    def update_current_progress(self, progress):
        """Update current video progress"""
        self.current_progress['value'] = progress
        
    def update_video_status(self, index, status, color):
        """Update video status in tree"""
        item = self.video_tree.get_children()[index]
        values = list(self.video_tree.item(item, 'values'))
        values[0] = status
        self.video_tree.item(item, values=values)
        
    def update_stats_ui(self):
        """Update statistics display"""
        total = len(self.video_queue)
        completed = self.successful_uploads + self.failed_uploads
        self.stats_label.config(
            text=f"Completed: {completed}/{total} | Success: {self.successful_uploads} | Failed: {self.failed_uploads}"
        )
        
    def upload_completed(self):
        """Handle upload completion"""
        self.is_uploading = False
        self.start_button.config(state='normal')
        self.pause_button.config(state='disabled')
        self.stop_button.config(state='disabled')
        
        # Reset progress bars
        self.overall_progress['value'] = 100
        self.current_progress['value'] = 0
        self.current_video_label.config(text="Upload completed")
        
        # Show completion message
        total = len(self.video_queue)
        message = f"Upload completed!\n\nSuccessful: {self.successful_uploads}/{total}\nFailed: {self.failed_uploads}/{total}"
        messagebox.showinfo("Upload Complete", message)
        
        self.log_message("🎉 All uploads completed!")
        
    def convert_ist_to_utc(self, ist_time_str):
        """Convert IST time to UTC format"""
        try:
            ist = pytz.timezone("Asia/Kolkata")
            local_time = datetime.strptime(ist_time_str, "%Y-%m-%d %H:%M:%S")
            local_time = ist.localize(local_time)
            utc_time = local_time.astimezone(pytz.utc)
            return utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            self.log_message(f"⚠️ Time conversion error: {e}")
            return None
            
    def get_authenticated_service(self, client_secret_file):
        """Get authenticated YouTube service"""
        creds = None
        token_file = "token.json"
        
        if os.path.exists(token_file):
            try:
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            except:
                if os.path.exists(token_file):
                    os.remove(token_file)
                creds = None
                
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_file, "w") as token:
                    token.write(creds.to_json())
            except:
                creds = None
                if os.path.exists(token_file):
                    os.remove(token_file)
                    
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0, prompt='consent')
            with open(token_file, "w") as token:
                token.write(creds.to_json())
                
        return build("youtube", "v3", credentials=creds)
        
    def clear_log(self):
        """Clear the log text"""
        self.log_text.delete(1.0, tk.END)
        
    def save_log(self):
        """Save log to file"""
        content = self.log_text.get(1.0, tk.END)
        if content.strip():
            file_path = filedialog.asksaveasfilename(
                title="Save log file",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    messagebox.showinfo("Success", "Log saved successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save log: {e}")
        else:
            messagebox.showwarning("Warning", "No log content to save")
            
    def toggle_autoscroll(self):
        """Toggle autoscroll for log"""
        self.autoscroll = not self.autoscroll
        status = "enabled" if self.autoscroll else "disabled"
        self.log_message(f"Auto-scroll {status}")

def main():
    root = tk.Tk()
    app = YouTubeUploaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
