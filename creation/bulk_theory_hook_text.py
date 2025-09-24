#!/usr/bin/env python3
"""
Kubernetes Theory to Markdown Converter
Converts JSON theory snippets to individual markdown files with live preview
"""

import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import webbrowser
import tempfile
from pathlib import Path
import re

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

class MarkdownConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Kubernetes Theory to Markdown Converter")
        self.root.geometry("1000x700")
        
        self.json_data = None
        self.output_folder = None
        self.preview_files = []
        
        self.setup_ui()
        self.load_default_data()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Kubernetes Theory to Markdown Converter", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input section
        ttk.Label(main_frame, text="JSON Data:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(button_frame, text="Load JSON File", 
                  command=self.load_json_file).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Use Default Data", 
                  command=self.load_default_data).pack(side=tk.LEFT)
        
        # JSON preview
        self.json_text = scrolledtext.ScrolledText(main_frame, height=8, width=80)
        self.json_text.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), 
                           pady=(0, 10))
        
        # Output folder section
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder_frame, text="Output Folder:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.folder_var = tk.StringVar(value="theory_hooks")
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=50)
        self.folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(folder_frame, text="Browse", 
                  command=self.browse_folder).grid(row=0, column=2)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Buttons
        button_frame2 = ttk.Frame(main_frame)
        button_frame2.grid(row=5, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(button_frame2, text="Convert to Markdown", 
                  command=self.convert_to_markdown).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame2, text="Preview in Browser", 
                  command=self.preview_markdown).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame2, text="Open Output Folder", 
                  command=self.open_output_folder).pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

    def load_default_data(self):
        """Load the default Kubernetes theory data"""
        default_data = {
            "snippets": [
                {
                    "title": "What is Kubernetes?",
                    "theory": "### What is Kubernetes?\n\nKubernetes (often abbreviated as **K8s**) is an open-source **container orchestration platform**. It automates deployment, scaling, and management of containerized applications.\n\n- **Core Idea:** Instead of manually managing containers, Kubernetes schedules, monitors, and heals them across clusters of machines.\n- **Key Features:**\n  - Automatic scaling\n  - Load balancing\n  - Self-healing (restart failed containers)\n  - Declarative configuration\n\n**Pitfall:** Many candidates overcomplicate this definition. Keep it simple: *Kubernetes = Operating system for containers.*"
                },
                {
                    "title": "Why do we use Kubernetes?",
                    "theory": "### Why do we use Kubernetes?\n\nWe use Kubernetes to solve the **scaling and reliability problems** of running many containers.\n\n- **Without Kubernetes:** You would need to manually start, stop, and connect containers.\n- **With Kubernetes:**\n  - Automates scaling (add/remove containers as needed)\n  - Handles failures with self-healing\n  - Provides service discovery & networking\n  - Supports rolling updates without downtime\n\n**Pitfall:** Don't just say \"because it's popular.\" Instead, focus on how it **simplifies container management at scale.**"
                },
                {
                    "title": "What is a Pod in Kubernetes?",
                    "theory": "### What is a Pod in Kubernetes?\n\nA **Pod** is the **smallest deployable unit** in Kubernetes.\n\n- **Contains:** One or more tightly coupled containers.\n- **Purpose:** Runs together, shares storage, network, and namespace.\n- **Analogy:** A Pod is like a **box** holding one or more toys (containers) that always move together.\n\n**Example:**\n- A web app container + sidecar logging container in the same Pod.\n\n**Pitfall:** Don't confuse Pods with Containers. Containers run inside Pods, not the other way around."
                },
                {
                    "title": "Kubernetes in One Sentence",
                    "theory": "### Kubernetes in One Sentence\n\nKubernetes is **the operating system for containers** — it automates running, scaling, and managing containerized apps.\n\n- **Analogy:** Like a conductor orchestrating many instruments, Kubernetes coordinates many containers.\n- **Interview Tip:** Keep it one line: *\"Kubernetes = Orchestrator for containers.\"*\n\n**Pitfall:** Avoid drowning in jargon. One crisp analogy is better than long technical detail."
                },
                {
                    "title": "Kubernetes Pitfall: Overcomplicating Answers",
                    "theory": "### Kubernetes Pitfall: Overcomplicating Answers\n\n**Common mistake:** Candidates overload answers with jargon: etcd, kubelet, ingress, scheduler.\n\n**Correct Approach:**\n- Use a simple 3-step structure: **Definition → Purpose → Analogy**.\n- Example: *\"Kubernetes is a container orchestrator. It automates scaling and healing. Think autopilot for containers.\"*\n\n**Pitfall:** Don't try to impress by listing every component — clarity beats detail."
                },
                {
                    "title": "Pods vs Containers",
                    "theory": "### Pods vs Containers\n\n- **Container:** A single lightweight environment for running an app (e.g., `nginx`).\n- **Pod:** A wrapper that contains one or more containers with shared storage and IP.\n\n**Key Difference:**\n- Container = Application instance.\n- Pod = Group of containers + metadata.\n\n**Analogy:** Pod = house, Container = people living inside.\n\n**Pitfall:** Saying \"Pod and Container are the same.\" Always highlight that a Pod can host multiple containers."
                },
                {
                    "title": "Why not just Docker? Why Kubernetes?",
                    "theory": "### Why not just Docker? Why Kubernetes?\n\n- **Docker:** Runs a single container.\n- **Kubernetes:** Manages many containers across multiple servers.\n\n**Core Benefits of Kubernetes:**\n- Auto-scaling\n- Load balancing\n- Self-healing\n- Rolling updates\n\n**Interview Trick:** Use the phrase: *\"Docker runs one. Kubernetes manages many.\"*\n\n**Pitfall:** Avoid saying Kubernetes replaces Docker. They work together — Docker (or container runtime) runs containers, Kubernetes orchestrates them."
                },
                {
                    "title": "Pod Analogy That Always Works",
                    "theory": "### Pod Analogy That Always Works\n\nA Pod is like a **box** that can hold one or more toys (containers). Wherever the box goes, the toys go together.\n\n- **Pod = wrapper for containers**\n- **Example:**\n  - One Pod can contain: web server + logging sidecar\n\n**Interview Tip:** Use analogies for clarity. Many interviewers value simple explanations.\n\n**Pitfall:** Don't skip that Pods can hold multiple containers, not just one."
                },
                {
                    "title": "30-Second Kubernetes Cheat Sheet",
                    "theory": "### 30-Second Kubernetes Cheat Sheet\n\n- **Kubernetes:** Orchestrator for containers.\n- **Pod:** Smallest deployable unit (holds containers).\n- **Service:** Connects Pods, provides stable networking.\n- **Deployment:** Manages desired Pod state.\n- **Node:** Machine that runs Pods.\n\n**Quick Interview Flow:**\n1. Define Kubernetes in one line.\n2. Name key objects (Pod, Service, Deployment).\n3. Add one analogy (e.g., orchestra conductor).\n\n**Pitfall:** Don't overload details — stick to basics for clarity."
                },
                {
                    "title": "Trick Question: Is Kubernetes a Programming Language?",
                    "theory": "### Trick Question: Is Kubernetes a Programming Language?\n\n**Answer:** No. Kubernetes is an **orchestration platform**, not a programming language.\n\n- **Role:** Automates deployment, scaling, and management of containers.\n- **Misconception:** Some think Kubernetes is like Python or Java. It's not — it's an infrastructure management tool.\n\n**Interview Tip:** Answer confidently: *\"No. Kubernetes is an orchestration tool for containers, not a language.\"*\n\n**Pitfall:** Don't just say \"No.\" Explain what it actually is."
                }
            ]
        }
        
        self.json_data = default_data
        self.json_text.delete(1.0, tk.END)
        self.json_text.insert(1.0, json.dumps(default_data, indent=2))
        self.status_var.set("Default Kubernetes theory data loaded")

    def load_json_file(self):
        """Load JSON data from a file"""
        file_path = filedialog.askopenfilename(
            title="Select JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.json_data = json.load(f)
                
                self.json_text.delete(1.0, tk.END)
                self.json_text.insert(1.0, json.dumps(self.json_data, indent=2))
                self.status_var.set(f"Loaded JSON file: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load JSON file:\n{str(e)}")

    def browse_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.folder_var.set(folder)

    def sanitize_filename(self, title):
        """Convert title to safe filename"""
        # Remove special characters and replace spaces with underscores
        filename = re.sub(r'[<>:"/\\|?*]', '', title)
        filename = re.sub(r'\s+', '_', filename.strip())
        return filename.lower()

    def convert_to_markdown(self):
        """Convert JSON data to markdown files"""
        try:
            # Validate input
            if not self.json_data:
                messagebox.showerror("Error", "Please load JSON data first")
                return
            
            if 'snippets' not in self.json_data:
                messagebox.showerror("Error", "JSON data must contain 'snippets' array")
                return
            
            # Get output folder
            output_folder = self.folder_var.get().strip()
            if not output_folder:
                output_folder = "theory_hooks"
            
            # Create output directory
            os.makedirs(output_folder, exist_ok=True)
            
            # Start progress indication
            self.progress.start()
            self.status_var.set("Converting to markdown files...")
            
            # Convert each snippet
            converted_files = []
            for i, snippet in enumerate(self.json_data['snippets']):
                title = snippet.get('title', f'snippet_{i+1}')
                theory = snippet.get('theory', '')
                
                # Create filename
                filename = self.sanitize_filename(title) + '.md'
                filepath = os.path.join(output_folder, filename)
                
                # Write markdown file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(theory)
                
                converted_files.append((title, filepath))
            
            # Stop progress
            self.progress.stop()
            
            # Update status
            self.status_var.set(f"Successfully converted {len(converted_files)} files to {output_folder}/")
            self.output_folder = output_folder
            
            # Show success message
            messagebox.showinfo("Success", 
                f"Successfully converted {len(converted_files)} theory snippets to markdown files!\n\n"
                f"Output folder: {output_folder}\n"
                f"Files created: {len(converted_files)}")
            
        except Exception as e:
            self.progress.stop()
            messagebox.showerror("Error", f"Failed to convert files:\n{str(e)}")
            self.status_var.set("Conversion failed")

    def preview_markdown(self):
        """Preview markdown files in browser"""
        if not self.output_folder or not os.path.exists(self.output_folder):
            messagebox.showwarning("Warning", "Please convert to markdown files first")
            return
        
        try:
            # Get all markdown files
            md_files = [f for f in os.listdir(self.output_folder) if f.endswith('.md')]
            
            if not md_files:
                messagebox.showwarning("Warning", "No markdown files found in output folder")
                return
            
            # Create HTML preview
            self.create_html_preview(md_files)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create preview:\n{str(e)}")

    def create_html_preview(self, md_files):
        """Create HTML preview of all markdown files"""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Kubernetes Theory Preview</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }
                .container {
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }
                .file-section {
                    margin: 30px 0;
                    padding: 20px;
                    border: 1px solid #e1e8ed;
                    border-radius: 8px;
                    background: #fdfdfd;
                }
                .file-title {
                    background: #3498db;
                    color: white;
                    padding: 10px 15px;
                    margin: -20px -20px 20px -20px;
                    border-radius: 8px 8px 0 0;
                    font-weight: bold;
                }
                .navigation {
                    background: #34495e;
                    padding: 15px;
                    margin: -30px -30px 30px -30px;
                    border-radius: 8px 8px 0 0;
                }
                .nav-link {
                    color: #ecf0f1;
                    text-decoration: none;
                    margin-right: 20px;
                    padding: 5px 10px;
                    border-radius: 4px;
                    transition: background 0.3s;
                }
                .nav-link:hover {
                    background: #2c3e50;
                }
                h3 { color: #2980b9; }
                code {
                    background: #f1f2f6;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: 'Monaco', 'Consolas', monospace;
                }
                ul, ol { margin: 15px 0; }
                li { margin: 5px 0; }
                strong { color: #2c3e50; }
                em { color: #7f8c8d; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚢 Kubernetes Theory Guide</h1>
                <div class="navigation">
        """
        
        # Add navigation links
        for md_file in sorted(md_files):
            title = md_file.replace('.md', '').replace('_', ' ').title()
            anchor = md_file.replace('.md', '').replace('_', '-')
            html_content += f'<a href="#{anchor}" class="nav-link">{title}</a>'
        
        html_content += """
                </div>
        """
        
        # Add content for each file
        for md_file in sorted(md_files):
            filepath = os.path.join(self.output_folder, md_file)
            anchor = md_file.replace('.md', '').replace('_', '-')
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple markdown to HTML conversion
                html_section = self.simple_md_to_html(content)
                
                html_content += f"""
                <div class="file-section" id="{anchor}">
                    <div class="file-title">📄 {md_file}</div>
                    {html_section}
                </div>
                """
                
            except Exception as e:
                html_content += f"""
                <div class="file-section" id="{anchor}">
                    <div class="file-title">📄 {md_file}</div>
                    <p style="color: red;">Error loading file: {str(e)}</p>
                </div>
                """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        # Save and open HTML file
        preview_path = os.path.join(tempfile.gettempdir(), 'k8s_theory_preview.html')
        with open(preview_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        webbrowser.open(f'file://{preview_path}')
        self.status_var.set("Preview opened in browser")

    def simple_md_to_html(self, markdown_content):
        """Simple markdown to HTML conversion"""
        if MARKDOWN_AVAILABLE:
            try:
                return markdown.markdown(markdown_content)
            except:
                pass
        
        # Fallback: basic conversion
        html = markdown_content
        
        # Headers
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # Code
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        
        # Lists
        lines = html.split('\n')
        in_list = False
        result_lines = []
        
        for line in lines:
            if re.match(r'^- ', line):
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                result_lines.append(f'<li>{line[2:]}</li>')
            else:
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                result_lines.append(line)
        
        if in_list:
            result_lines.append('</ul>')
        
        html = '\n'.join(result_lines)
        
        # Paragraphs
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f'<p>{html}</p>'
        html = html.replace('<p></p>', '')
        
        return html

    def open_output_folder(self):
        """Open the output folder in file explorer"""
        if not self.output_folder or not os.path.exists(self.output_folder):
            messagebox.showwarning("Warning", "Output folder doesn't exist yet")
            return
        
        try:
            # Cross-platform folder opening
            if os.name == 'nt':  # Windows
                os.startfile(self.output_folder)
            elif os.name == 'posix':  # macOS and Linux
                os.system(f'open "{self.output_folder}"' if os.uname().sysname == 'Darwin' 
                         else f'xdg-open "{self.output_folder}"')
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{str(e)}")

def main():
    root = tk.Tk()
    app = MarkdownConverter(root)
    
    # Install markdown if not available
    if not MARKDOWN_AVAILABLE:
        messagebox.showinfo("Info", 
            "For better HTML rendering, install the markdown package:\n"
            "pip install markdown\n\n"
            "The app will work with basic conversion for now.")
    
    root.mainloop()

if __name__ == "__main__":
    main()