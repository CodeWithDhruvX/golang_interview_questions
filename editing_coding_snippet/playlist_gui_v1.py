import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import csv
import webbrowser
from datetime import datetime
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import threading
import pyperclip
import re

class YouTubePlaylistManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("YouTube Playlist Manager")
        self.root.geometry("1200x800")
        
        # YouTube API setup
        self.youtube = None
        self.credentials = None
        self.scopes = ['https://www.googleapis.com/auth/youtube']
        
        # Data storage
        self.playlists = {}
        self.current_playlist_id = None
        self.current_playlist_items = {}  # Store playlist items with their IDs
        
        # Setup GUI
        self.setup_gui()
        
        # Try to load existing credentials
        self.load_credentials()
        
    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top frame for authentication and controls
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Authentication section
        auth_frame = ttk.LabelFrame(top_frame, text="Authentication", padding=10)
        auth_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(auth_frame, text="Load Credentials JSON", command=self.load_credentials_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(auth_frame, text="Authenticate", command=self.authenticate).pack(side=tk.LEFT, padx=(0, 5))
        
        self.auth_status = ttk.Label(auth_frame, text="Not Authenticated", foreground="red")
        self.auth_status.pack(side=tk.LEFT, padx=(10, 0))
        
        # Control buttons frame
        control_frame = ttk.LabelFrame(top_frame, text="Playlist Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="Create Playlist", command=self.create_playlist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Import Playlist", command=self.import_playlist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Delete Playlist", command=self.delete_playlist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Refresh Playlists", command=self.refresh_playlists).pack(side=tk.LEFT, padx=(0, 5))
        
        # Export buttons
        export_frame = ttk.Frame(control_frame)
        export_frame.pack(side=tk.RIGHT)
        ttk.Button(export_frame, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="Export JSON", command=self.export_json).pack(side=tk.LEFT)
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Playlists
        left_frame = ttk.LabelFrame(content_frame, text="Playlists", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Playlist listbox with scrollbar
        playlist_scroll_frame = ttk.Frame(left_frame)
        playlist_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.playlist_listbox = tk.Listbox(playlist_scroll_frame, width=30)
        playlist_scrollbar = ttk.Scrollbar(playlist_scroll_frame, orient=tk.VERTICAL, command=self.playlist_listbox.yview)
        self.playlist_listbox.configure(yscrollcommand=playlist_scrollbar.set)
        
        self.playlist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        playlist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.playlist_listbox.bind('<<ListboxSelect>>', self.on_playlist_select)
        
        # Playlist info with copy buttons
        info_frame = ttk.Frame(left_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.playlist_info = ttk.Label(info_frame, text="Select a playlist to view details")
        self.playlist_info.pack()
        
        # Copy buttons frame
        copy_frame = ttk.Frame(info_frame)
        copy_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(copy_frame, text="Copy ID", command=self.copy_playlist_id).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(copy_frame, text="Copy Title", command=self.copy_playlist_title).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(copy_frame, text="Copy URL", command=self.copy_playlist_url).pack(side=tk.LEFT)
        
        # View playlist on YouTube button
        ttk.Button(left_frame, text="View on YouTube", command=self.view_playlist_on_youtube).pack(pady=(5, 0))
        
        # Right panel - Videos
        right_frame = ttk.LabelFrame(content_frame, text="Videos", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Video controls
        video_control_frame = ttk.Frame(right_frame)
        video_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # First row of controls
        control_row1 = ttk.Frame(video_control_frame)
        control_row1.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(control_row1, text="Add Video", command=self.add_video).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_row1, text="Remove Video", command=self.remove_video).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_row1, text="Move Up", command=self.move_video_up).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_row1, text="Move Down", command=self.move_video_down).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_row1, text="Watch Video", command=self.watch_video).pack(side=tk.LEFT, padx=(0, 5))
        
        # Second row of controls
        control_row2 = ttk.Frame(video_control_frame)
        control_row2.pack(fill=tk.X)
        
        ttk.Button(control_row2, text="Move to Playlist", command=self.move_to_playlist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_row2, text="Copy to Playlist", command=self.copy_to_playlist).pack(side=tk.LEFT, padx=(0, 5))
        
        # Videos treeview
        video_frame = ttk.Frame(right_frame)
        video_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for videos
        columns = ('Title', 'Channel', 'Duration', 'Views', 'Published')
        self.video_tree = ttk.Treeview(video_frame, columns=columns, show='tree headings')
        
        # Configure columns
        self.video_tree.heading('#0', text='#')
        self.video_tree.column('#0', width=50, minwidth=50)
        
        for col in columns:
            self.video_tree.heading(col, text=col)
            if col == 'Title':
                self.video_tree.column(col, width=300, minwidth=200)
            elif col == 'Channel':
                self.video_tree.column(col, width=150, minwidth=100)
            elif col == 'Views':
                self.video_tree.column(col, width=100, minwidth=80)
            else:
                self.video_tree.column(col, width=120, minwidth=80)
        
        # Scrollbars for treeview
        tree_scroll_y = ttk.Scrollbar(video_frame, orient=tk.VERTICAL, command=self.video_tree.yview)
        tree_scroll_x = ttk.Scrollbar(video_frame, orient=tk.HORIZONTAL, command=self.video_tree.xview)
        self.video_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        self.video_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
    def load_credentials_file(self):
        """Load credentials from JSON file"""
        file_path = filedialog.askopenfilename(
            title="Select Credentials JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.credentials_file = file_path
                self.update_status("Credentials file loaded. Click 'Authenticate' to proceed.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load credentials file: {str(e)}")
    
    def load_credentials(self):
        """Load saved credentials if they exist"""
        if os.path.exists('token.json'):
            try:
                self.credentials = Credentials.from_authorized_user_file('token.json', self.scopes)
                if self.credentials and self.credentials.valid:
                    self.youtube = build('youtube', 'v3', credentials=self.credentials)
                    self.auth_status.config(text="Authenticated", foreground="green")
                    self.refresh_playlists()
                elif self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    self.youtube = build('youtube', 'v3', credentials=self.credentials)
                    self.save_credentials()
                    self.auth_status.config(text="Authenticated", foreground="green")
                    self.refresh_playlists()
            except Exception as e:
                self.update_status(f"Error loading saved credentials: {str(e)}")
    
    def authenticate(self):
        """Authenticate with YouTube API"""
        if not hasattr(self, 'credentials_file'):
            messagebox.showerror("Error", "Please load credentials JSON file first!")
            return
        
        try:
            flow = Flow.from_client_secrets_file(self.credentials_file, self.scopes)
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            
            auth_url, _ = flow.authorization_url(prompt='consent')
            webbrowser.open(auth_url)
            
            auth_code = simpledialog.askstring("Authentication", "Enter the authorization code:")
            
            if auth_code:
                flow.fetch_token(code=auth_code)
                self.credentials = flow.credentials
                self.youtube = build('youtube', 'v3', credentials=self.credentials)
                
                self.save_credentials()
                self.auth_status.config(text="Authenticated", foreground="green")
                self.update_status("Authentication successful!")
                self.refresh_playlists()
            
        except Exception as e:
            messagebox.showerror("Authentication Error", f"Failed to authenticate: {str(e)}")
    
    def save_credentials(self):
        """Save credentials to file"""
        with open('token.json', 'w') as token:
            token.write(self.credentials.to_json())
    
    def refresh_playlists(self):
        """Refresh playlists from YouTube"""
        if not self.youtube:
            messagebox.showerror("Error", "Please authenticate first!")
            return
        
        def fetch_playlists():
            try:
                self.update_status("Fetching playlists...")
                request = self.youtube.playlists().list(
                    part="snippet,contentDetails",
                    mine=True,
                    maxResults=50
                )
                response = request.execute()
                
                self.playlists = {}
                self.playlist_listbox.delete(0, tk.END)
                
                for item in response['items']:
                    playlist_id = item['id']
                    title = item['snippet']['title']
                    video_count = item['contentDetails']['itemCount']
                    
                    self.playlists[playlist_id] = {
                        'title': title,
                        'video_count': video_count,
                        'description': item['snippet'].get('description', ''),
                        'published': item['snippet']['publishedAt']
                    }
                    
                    display_text = f"{title} ({video_count} videos)"
                    self.playlist_listbox.insert(tk.END, display_text)
                
                self.update_status(f"Loaded {len(self.playlists)} playlists")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch playlists: {str(e)}")
                self.update_status("Error fetching playlists")
        
        threading.Thread(target=fetch_playlists, daemon=True).start()
    
    def on_playlist_select(self, event):
        """Handle playlist selection"""
        selection = self.playlist_listbox.curselection()
        if selection:
            index = selection[0]
            playlist_id = list(self.playlists.keys())[index]
            self.current_playlist_id = playlist_id
            playlist = self.playlists[playlist_id]
            
            info_text = f"Title: {playlist['title']}\nVideos: {playlist['video_count']}\nCreated: {playlist['published'][:10]}"
            self.playlist_info.config(text=info_text)
            
            self.load_playlist_videos(playlist_id)
    
    def load_playlist_videos(self, playlist_id):
        """Load videos for selected playlist"""
        def fetch_videos():
            try:
                self.update_status("Loading videos...")
                
                # Clear existing videos
                for item in self.video_tree.get_children():
                    self.video_tree.delete(item)
                
                self.current_playlist_items = {}
                
                request = self.youtube.playlistItems().list(
                    part="snippet,contentDetails,id",
                    playlistId=playlist_id,
                    maxResults=50
                )
                response = request.execute()
                
                video_ids = []
                for item in response['items']:
                    video_id = item['contentDetails']['videoId']
                    playlist_item_id = item['id']
                    video_ids.append(video_id)
                    # Store playlist item ID for reordering
                    self.current_playlist_items[video_id] = {
                        'playlist_item_id': playlist_item_id,
                        'position': len(video_ids) - 1
                    }
                
                # Get video statistics
                if video_ids:
                    video_request = self.youtube.videos().list(
                        part="statistics,contentDetails,snippet",
                        id=','.join(video_ids)
                    )
                    video_response = video_request.execute()
                    video_stats = {item['id']: item for item in video_response['items']}
                
                for i, item in enumerate(response['items']):
                    video_id = item['contentDetails']['videoId']
                    snippet = item['snippet']
                    
                    title = snippet['title']
                    channel = snippet['channelTitle']
                    published = snippet['publishedAt'][:10]
                    
                    # Get video stats
                    stats = video_stats.get(video_id, {})
                    views = stats.get('statistics', {}).get('viewCount', 'N/A')
                    duration = stats.get('contentDetails', {}).get('duration', 'N/A')
                    
                    # Format views
                    if views != 'N/A':
                        views = f"{int(views):,}"
                    
                    # Format duration
                    if duration != 'N/A':
                        duration = self.format_duration(duration)
                    
                    self.video_tree.insert('', 'end', text=str(i+1), 
                                         values=(title, channel, duration, views, published),
                                         tags=(video_id,))
                
                self.update_status(f"Loaded {len(response['items'])} videos")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load videos: {str(e)}")
                self.update_status("Error loading videos")
        
        threading.Thread(target=fetch_videos, daemon=True).start()
    
    def format_duration(self, duration):
        """Format ISO 8601 duration to readable format"""
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return duration
        
        hours, minutes, seconds = match.groups()
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
        seconds = int(seconds) if seconds else 0
        
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def move_video_up(self):
        """Move selected video up in playlist"""
        selection = self.video_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a video to move!")
            return
        
        if not self.current_playlist_id:
            messagebox.showwarning("Warning", "Please select a playlist first!")
            return
        
        item = self.video_tree.item(selection[0])
        video_id = item['tags'][0] if item['tags'] else None
        current_position = int(item['text']) - 1
        
        if current_position == 0:
            messagebox.showinfo("Info", "Video is already at the top!")
            return
        
        if video_id and video_id in self.current_playlist_items:
            self.move_video_to_position(video_id, current_position - 1)
    
    def move_video_down(self):
        """Move selected video down in playlist"""
        selection = self.video_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a video to move!")
            return
        
        if not self.current_playlist_id:
            messagebox.showwarning("Warning", "Please select a playlist first!")
            return
        
        item = self.video_tree.item(selection[0])
        video_id = item['tags'][0] if item['tags'] else None
        current_position = int(item['text']) - 1
        total_videos = len(self.video_tree.get_children())
        
        if current_position == total_videos - 1:
            messagebox.showinfo("Info", "Video is already at the bottom!")
            return
        
        if video_id and video_id in self.current_playlist_items:
            self.move_video_to_position(video_id, current_position + 1)
    
    def move_video_to_position(self, video_id, new_position):
        """Move video to specific position"""
        def move_video():
            try:
                self.update_status("Moving video...")
                
                playlist_item_id = self.current_playlist_items[video_id]['playlist_item_id']
                
                # Update the position using the YouTube API
                request = self.youtube.playlistItems().update(
                    part="snippet",
                    body={
                        "id": playlist_item_id,
                        "snippet": {
                            "playlistId": self.current_playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id
                            },
                            "position": new_position
                        }
                    }
                )
                response = request.execute()
                
                # Reload the playlist to reflect changes
                self.load_playlist_videos(self.current_playlist_id)
                self.update_status("Video moved successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to move video: {str(e)}")
                self.update_status("Error moving video")
        
        threading.Thread(target=move_video, daemon=True).start()
    
    def move_to_playlist(self):
        """Move selected video to another playlist"""
        selection = self.video_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a video to move!")
            return
        
        item = self.video_tree.item(selection[0])
        video_id = item['tags'][0] if item['tags'] else None
        video_title = item['values'][0] if item['values'] else "Unknown"
        
        if not video_id:
            messagebox.showerror("Error", "Could not get video ID!")
            return
        
        # Create playlist selection dialog
        self.show_playlist_selection_dialog(video_id, video_title, move=True)
    
    def copy_to_playlist(self):
        """Copy selected video to another playlist"""
        selection = self.video_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a video to copy!")
            return
        
        item = self.video_tree.item(selection[0])
        video_id = item['tags'][0] if item['tags'] else None
        video_title = item['values'][0] if item['values'] else "Unknown"
        
        if not video_id:
            messagebox.showerror("Error", "Could not get video ID!")
            return
        
        # Create playlist selection dialog
        self.show_playlist_selection_dialog(video_id, video_title, move=False)
    
    def show_playlist_selection_dialog(self, video_id, video_title, move=False):
        """Show dialog to select target playlist"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{'Move' if move else 'Copy'} Video to Playlist")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Video info
        info_frame = ttk.Frame(dialog, padding=10)
        info_frame.pack(fill=tk.X)
        
        ttk.Label(info_frame, text=f"{'Moving' if move else 'Copying'} video:", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(info_frame, text=video_title, wraplength=350).pack(anchor=tk.W, pady=(5, 10))
        
        # Playlist selection
        ttk.Label(info_frame, text="Select target playlist:", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W)
        
        # Playlist listbox
        list_frame = ttk.Frame(dialog, padding=(10, 0, 10, 10))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        playlist_list = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=playlist_list.yview)
        playlist_list.configure(yscrollcommand=scrollbar.set)
        
        playlist_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate playlist list (exclude current playlist)
        playlist_ids = []
        for playlist_id, playlist_data in self.playlists.items():
            if playlist_id != self.current_playlist_id:
                playlist_list.insert(tk.END, f"{playlist_data['title']} ({playlist_data['video_count']} videos)")
                playlist_ids.append(playlist_id)
        
        # Buttons
        button_frame = ttk.Frame(dialog, padding=10)
        button_frame.pack(fill=tk.X)
        
        def on_confirm():
            selection = playlist_list.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a playlist!")
                return
            
            target_playlist_id = playlist_ids[selection[0]]
            target_playlist_title = self.playlists[target_playlist_id]['title']
            
            dialog.destroy()
            
            if move:
                self.execute_move_video(video_id, video_title, target_playlist_id, target_playlist_title)
            else:
                self.execute_copy_video(video_id, video_title, target_playlist_id, target_playlist_title)
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text=f"{'Move' if move else 'Copy'}", command=on_confirm).pack(side=tk.RIGHT)
    
    def execute_move_video(self, video_id, video_title, target_playlist_id, target_playlist_title):
        """Execute moving video to another playlist"""
        def move_video():
            try:
                self.update_status(f"Moving video to {target_playlist_title}...")
                
                # Add video to target playlist
                add_request = self.youtube.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": target_playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id
                            }
                        }
                    }
                )
                add_request.execute()
                
                # Remove from current playlist
                if video_id in self.current_playlist_items:
                    playlist_item_id = self.current_playlist_items[video_id]['playlist_item_id']
                    delete_request = self.youtube.playlistItems().delete(id=playlist_item_id)
                    delete_request.execute()
                
                messagebox.showinfo("Success", f"Video moved to '{target_playlist_title}' successfully!")
                self.load_playlist_videos(self.current_playlist_id)
                self.update_status("Video moved successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to move video: {str(e)}")
                self.update_status("Error moving video")
        
        threading.Thread(target=move_video, daemon=True).start()
    
    def execute_copy_video(self, video_id, video_title, target_playlist_id, target_playlist_title):
        """Execute copying video to another playlist"""
        def copy_video():
            try:
                self.update_status(f"Copying video to {target_playlist_title}...")
                
                # Add video to target playlist
                request = self.youtube.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": target_playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id
                            }
                        }
                    }
                )
                response = request.execute()
                
                messagebox.showinfo("Success", f"Video copied to '{target_playlist_title}' successfully!")
                self.update_status("Video copied successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy video: {str(e)}")
                self.update_status("Error copying video")
        
        threading.Thread(target=copy_video, daemon=True).start()
    
    def copy_playlist_id(self):
        """Copy current playlist ID to clipboard"""
        if self.current_playlist_id:
            try:
                pyperclip.copy(self.current_playlist_id)
                self.update_status("Playlist ID copied to clipboard!")
            except:
                # Fallback if pyperclip is not available
                self.root.clipboard_clear()
                self.root.clipboard_append(self.current_playlist_id)
                self.update_status("Playlist ID copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "Please select a playlist first!")
    
    def copy_playlist_title(self):
        """Copy current playlist title to clipboard"""
        if self.current_playlist_id:
            title = self.playlists[self.current_playlist_id]['title']
            try:
                pyperclip.copy(title)
                self.update_status("Playlist title copied to clipboard!")
            except:
                # Fallback if pyperclip is not available
                self.root.clipboard_clear()
                self.root.clipboard_append(title)
                self.update_status("Playlist title copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "Please select a playlist first!")
    
    def copy_playlist_url(self):
        """Copy current playlist URL to clipboard"""
        if self.current_playlist_id:
            url = f"https://www.youtube.com/playlist?list={self.current_playlist_id}"
            try:
                pyperclip.copy(url)
                self.update_status("Playlist URL copied to clipboard!")
            except:
                # Fallback if pyperclip is not available
                self.root.clipboard_clear()
                self.root.clipboard_append(url)
                self.update_status("Playlist URL copied to clipboard!")
        else:
            messagebox.showwarning("Warning", "Please select a playlist first!")
    
    def create_playlist(self):
        """Create a new playlist"""
        if not self.youtube:
            messagebox.showerror("Error", "Please authenticate first!")
            return
        
        title = simpledialog.askstring("Create Playlist", "Enter playlist title:")
        if not title:
            return
        
        description = simpledialog.askstring("Create Playlist", "Enter playlist description (optional):") or ""
        
        try:
            request = self.youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description
                    },
                    "status": {
                        "privacyStatus": "private"
                    }
                }
            )
            response = request.execute()
            
            messagebox.showinfo("Success", f"Playlist '{title}' created successfully!")
            self.refresh_playlists()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create playlist: {str(e)}")
    
    def delete_playlist(self):
        """Delete selected playlist"""
        if not self.current_playlist_id:
            messagebox.showwarning("Warning", "Please select a playlist first!")
            return
        
        playlist_title = self.playlists[self.current_playlist_id]['title']
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete playlist '{playlist_title}'?"):
            try:
                request = self.youtube.playlists().delete(id=self.current_playlist_id)
                request.execute()
                
                messagebox.showinfo("Success", f"Playlist '{playlist_title}' deleted successfully!")
                self.refresh_playlists()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete playlist: {str(e)}")
    
    def add_video(self):
        """Add video to current playlist"""
        if not self.current_playlist_id:
            messagebox.showwarning("Warning", "Please select a playlist first!")
            return
        
        video_url = simpledialog.askstring("Add Video", "Enter YouTube video URL or ID:")
        if not video_url:
            return
        
        # Extract video ID from URL
        video_id = self.extract_video_id(video_url)
        if not video_id:
            messagebox.showerror("Error", "Invalid YouTube video URL or ID!")
            return
        
        try:
            request = self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": self.current_playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )
            response = request.execute()
            
            messagebox.showinfo("Success", "Video added to playlist!")
            self.load_playlist_videos(self.current_playlist_id)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add video: {str(e)}")
    
    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        if len(url) == 11 and url.isalnum():
            return url
        
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def remove_video(self):
        """Remove selected video from playlist"""
        selection = self.video_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a video to remove!")
            return
        
        item = self.video_tree.item(selection[0])
        video_id = item['tags'][0] if item['tags'] else None
        video_title = item['values'][0] if item['values'] else "Unknown"
        
        if not video_id or video_id not in self.current_playlist_items:
            messagebox.showerror("Error", "Could not find video in playlist!")
            return
        
        if messagebox.askyesno("Confirm Remove", f"Are you sure you want to remove '{video_title}' from the playlist?"):
            try:
                playlist_item_id = self.current_playlist_items[video_id]['playlist_item_id']
                request = self.youtube.playlistItems().delete(id=playlist_item_id)
                request.execute()
                
                messagebox.showinfo("Success", "Video removed from playlist!")
                self.load_playlist_videos(self.current_playlist_id)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove video: {str(e)}")
    
    def watch_video(self):
        """Open selected video on YouTube"""
        selection = self.video_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a video to watch!")
            return
        
        item = self.video_tree.item(selection[0])
        video_id = item['tags'][0] if item['tags'] else None
        
        if video_id:
            webbrowser.open(f"https://www.youtube.com/watch?v={video_id}")
    
    def view_playlist_on_youtube(self):
        """Open current playlist on YouTube"""
        if not self.current_playlist_id:
            messagebox.showwarning("Warning", "Please select a playlist first!")
            return
        
        webbrowser.open(f"https://www.youtube.com/playlist?list={self.current_playlist_id}")
    
    def import_playlist(self):
        """Import playlist from URL"""
        playlist_url = simpledialog.askstring("Import Playlist", "Enter YouTube playlist URL:")
        if not playlist_url:
            return
        
        # Extract playlist ID from URL
        playlist_id = self.extract_playlist_id(playlist_url)
        if not playlist_id:
            messagebox.showerror("Error", "Invalid YouTube playlist URL!")
            return
        
        try:
            # Get playlist details
            request = self.youtube.playlists().list(
                part="snippet",
                id=playlist_id
            )
            response = request.execute()
            
            if not response['items']:
                messagebox.showerror("Error", "Playlist not found or not accessible!")
                return
            
            playlist_title = response['items'][0]['snippet']['title']
            
            # Create new playlist
            new_title = simpledialog.askstring("Import Playlist", f"Enter title for imported playlist:", initialvalue=f"Imported - {playlist_title}")
            if not new_title:
                return
            
            create_request = self.youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": new_title,
                        "description": f"Imported from: {playlist_url}"
                    },
                    "status": {
                        "privacyStatus": "private"
                    }
                }
            )
            new_playlist = create_request.execute()
            new_playlist_id = new_playlist['id']
            
            # Get all videos from source playlist
            videos_request = self.youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50
            )
            videos_response = videos_request.execute()
            
            # Add videos to new playlist
            for item in videos_response['items']:
                video_id = item['contentDetails']['videoId']
                
                add_request = self.youtube.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": new_playlist_id,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id
                            }
                        }
                    }
                )
                add_request.execute()
            
            messagebox.showinfo("Success", f"Playlist imported successfully with {len(videos_response['items'])} videos!")
            self.refresh_playlists()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import playlist: {str(e)}")
    
    def extract_playlist_id(self, url):
        """Extract playlist ID from YouTube URL"""
        patterns = [
            r'list=([a-zA-Z0-9_-]+)',
            r'playlist\?list=([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def export_csv(self):
        """Export current playlist to CSV"""
        if not self.current_playlist_id:
            messagebox.showwarning("Warning", "Please select a playlist first!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save CSV Export"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Position', 'Title', 'Channel', 'Duration', 'Views', 'Published', 'Video ID', 'Video URL'])
                    
                    for item in self.video_tree.get_children():
                        values = self.video_tree.item(item)
                        position = values['text']
                        title, channel, duration, views, published = values['values']
                        video_id = values['tags'][0] if values['tags'] else ''
                        video_url = f'https://www.youtube.com/watch?v={video_id}' if video_id else ''
                        
                        writer.writerow([position, title, channel, duration, views, published, video_id, video_url])
                
                messagebox.showinfo("Success", f"Playlist exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")
    
    def export_json(self):
        """Export current playlist to JSON"""
        if not self.current_playlist_id:
            messagebox.showwarning("Warning", "Please select a playlist first!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save JSON Export"
        )
        
        if file_path:
            try:
                export_data = {
                    'playlist_info': self.playlists[self.current_playlist_id],
                    'playlist_id': self.current_playlist_id,
                    'playlist_url': f'https://www.youtube.com/playlist?list={self.current_playlist_id}',
                    'exported_at': datetime.now().isoformat(),
                    'videos': []
                }
                
                for item in self.video_tree.get_children():
                    values = self.video_tree.item(item)
                    position = values['text']
                    title, channel, duration, views, published = values['values']
                    video_id = values['tags'][0] if values['tags'] else ''
                    
                    export_data['videos'].append({
                        'position': position,
                        'title': title,
                        'channel': channel,
                        'duration': duration,
                        'views': views,
                        'published': published,
                        'video_id': video_id,
                        'video_url': f'https://www.youtube.com/watch?v={video_id}' if video_id else ''
                    })
                
                with open(file_path, 'w', encoding='utf-8') as jsonfile:
                    json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", f"Playlist exported to {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export JSON: {str(e)}")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    # Install pyperclip if not available
    try:
        import pyperclip
    except ImportError:
        print("pyperclip not found. Install it with: pip install pyperclip")
        print("Clipboard functionality will use tkinter fallback.")
    
    app = YouTubePlaylistManager()
    app.run()