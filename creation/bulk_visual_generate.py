import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import tkinter.font as tkfont
import webbrowser
from pathlib import Path
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid

class CombinedMarkdownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Markdown File Generator & HTML Converter")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Variables for HTML converter
        self.current_files = []
        self.output_html = ""
        self.batch_results = []
        self.cancel_batch = False
        
        # Create a default font
        self.default_font = tkfont.Font(family="Arial", size=10)
        self.title_font = tkfont.Font(family="Arial", size=16, weight="bold")
        
        self.setup_styles()
        self.setup_ui()
        
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        # Only configure padding, avoid font settings for ttk
        style.configure("Toolbutton.TButton", padding=6)

    def setup_ui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create Content tab
        self.content_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.content_frame, text="Content")
        self.setup_content_tab()
        
        # Create Visuals tab
        self.visuals_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.visuals_frame, text="Visuals")
        self.setup_visuals_tab()
        
        # Create Script tab
        self.script_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.script_frame, text="Script")
        self.setup_script_tab()
        
    def setup_content_tab(self):
        """Setup the content generation tab"""
        main_frame = ttk.Frame(self.content_frame, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Markdown File Generator", 
                               font=self.title_font)
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Folder selection
        ttk.Label(main_frame, text="Folder:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.folder_entry = tk.Entry(main_frame, width=50, font=self.default_font)
        self.folder_entry.grid(row=1, column=1, padx=5, pady=5)
        self.folder_entry.insert(0, "content")
        ttk.Button(main_frame, text="Browse", command=self.browse_folder).grid(row=1, column=2, padx=5, pady=5)
        
        # Text area
        self.content_text_area = tk.Text(main_frame, width=100, height=25, font=self.default_font)
        self.content_text_area.grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        self.add_content_sample_text()
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(buttons_frame, text="Clear Text", command=self.clear_content_text, 
                  style="Toolbutton.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Generate Files", command=self.generate_files, 
                  style="Toolbutton.TButton").pack(side=tk.RIGHT, padx=5)
        
        # Status bar for content tab
        self.content_status_var = tk.StringVar()
        self.content_status_var.set("Ready to generate markdown files")
        content_status_bar = ttk.Label(main_frame, textvariable=self.content_status_var, 
                                      relief=tk.SUNKEN, anchor=tk.W)
        content_status_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def setup_visuals_tab(self):
        """Setup the HTML converter tab with enhanced functionality from code 2"""
        main_frame = ttk.Frame(self.visuals_frame, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Markdown to HTML Converter with Mermaid Support", 
                               font=self.title_font)
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Mode selection
        mode_frame = ttk.LabelFrame(main_frame, text="Processing Mode", padding="5")
        mode_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.processing_mode = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="Single File/Text Mode", 
                       variable=self.processing_mode, value="single",
                       command=self.toggle_mode).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="Batch Processing Mode", 
                       variable=self.processing_mode, value="batch",
                       command=self.toggle_mode).pack(side=tk.LEFT)
        
        # Left panel - Input
        input_frame = ttk.LabelFrame(main_frame, text="Markdown Input", padding="5")
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(2, weight=1)
        
        # Single mode buttons
        self.single_buttons = ttk.Frame(input_frame)
        self.single_buttons.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(self.single_buttons, text="Load MD File", 
                  command=self.load_markdown_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(self.single_buttons, text="Paste from Clipboard", 
                  command=self.paste_from_clipboard).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(self.single_buttons, text="Clear", 
                  command=self.clear_input).pack(side=tk.LEFT, padx=(0, 5))
        
        # Batch mode buttons
        self.batch_buttons = ttk.Frame(input_frame)
        self.batch_buttons.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(self.batch_buttons, text="Select Multiple MD Files", 
                  command=self.load_multiple_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(self.batch_buttons, text="Select Folder", 
                  command=self.select_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(self.batch_buttons, text="Clear Selection", 
                  command=self.clear_file_selection).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(self.batch_buttons, text="Cancel Batch", 
                  command=self.cancel_batch_operation).pack(side=tk.LEFT, padx=(0, 5))
        
        # File list for batch mode
        self.file_list_frame = ttk.LabelFrame(input_frame, text="Selected Files", padding="5")
        self.file_list_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        self.file_list_frame.columnconfigure(0, weight=1)
        self.file_list_frame.rowconfigure(0, weight=1)
        
        self.file_listbox = tk.Listbox(self.file_list_frame, height=6, font=self.default_font)
        file_scrollbar = ttk.Scrollbar(self.file_list_frame, orient="vertical")
        self.file_listbox.config(yscrollcommand=file_scrollbar.set)
        file_scrollbar.config(command=self.file_listbox.yview)
        
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        file_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Input text area
        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, 
                                                   width=50, height=20,
                                                   font=('Consolas', 10))
        self.input_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Right panel - Preview/Output
        output_frame = ttk.LabelFrame(main_frame, text="HTML Preview", padding="5")
        output_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(2, weight=1)
        
        # Single mode output buttons
        self.single_output_buttons = ttk.Frame(output_frame)
        self.single_output_buttons.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(self.single_output_buttons, text="Convert to HTML", 
                  command=self.convert_to_html).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(self.single_output_buttons, text="Save HTML", 
                  command=self.save_html).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(self.single_output_buttons, text="Preview in Browser", 
                  command=self.preview_in_browser).pack(side=tk.LEFT, padx=(0, 5))
        
        # Batch mode output buttons
        self.batch_output_buttons = ttk.Frame(output_frame)
        self.batch_output_buttons.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(self.batch_output_buttons, text="Convert All Files", 
                  command=self.batch_convert).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(self.batch_output_buttons, text="Save All HTML", 
                  command=self.batch_save_html).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(self.batch_output_buttons, text="Export Report", 
                  command=self.export_batch_report).pack(side=tk.LEFT, padx=(0, 5))
        
        # Progress bar for batch operations
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(output_frame, variable=self.progress_var, 
                                            maximum=100, length=300)
        self.progress_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, 
                                                    width=50, height=20,
                                                    font=('Consolas', 9))
        self.output_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar for visuals tab
        self.visuals_status_var = tk.StringVar()
        self.visuals_status_var.set("Ready")
        visuals_status_bar = ttk.Label(main_frame, textvariable=self.visuals_status_var, 
                                      relief=tk.SUNKEN, anchor=tk.W)
        visuals_status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Initialize UI state
        self.toggle_mode()
        self.add_visuals_sample_text()

    def setup_script_tab(self):
        """Setup the script generation tab"""
        main_frame = ttk.Frame(self.script_frame, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Script File Generator", 
                               font=self.title_font)
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Folder selection
        ttk.Label(main_frame, text="Folder:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.script_folder_entry = tk.Entry(main_frame, width=50, font=self.default_font)
        self.script_folder_entry.grid(row=1, column=1, padx=5, pady=5)
        self.script_folder_entry.insert(0, "content")
        ttk.Button(main_frame, text="Browse", command=self.browse_script_folder).grid(row=1, column=2, padx=5, pady=5)
        
        # Text area
        self.script_text_area = tk.Text(main_frame, width=100, height=25, font=self.default_font)
        self.script_text_area.grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        self.add_script_sample_text()
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(buttons_frame, text="Clear Text", command=self.clear_script_text, 
                  style="Toolbutton.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Generate Script", command=self.generate_script, 
                  style="Toolbutton.TButton").pack(side=tk.RIGHT, padx=5)
        
        # Status bar for script tab
        self.script_status_var = tk.StringVar()
        self.script_status_var.set("Ready to generate script file")
        script_status_bar = ttk.Label(main_frame, textvariable=self.script_status_var, 
                                      relief=tk.SUNKEN, anchor=tk.W)
        script_status_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

    # Content Tab Methods
    def browse_folder(self):
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, selected_folder)

    def clear_content_text(self):
        self.content_text_area.delete("1.0", tk.END)
        self.content_status_var.set("Text area cleared")

    def add_content_sample_text(self):
        sample = """# Question 1: What is Python?

**Introduction:**
Python is a versatile programming language known for its simplicity and readability.

**Key Points:**

1. **Ease of Use**
   * Simple syntax
   * Readable code
   * Great for beginners

2. **Applications**
   * Web development
   * Data science
   * Automation

**Conclusion:**
Python is a powerful tool for developers of all levels.
"""
        self.content_text_area.insert("1.0", sample)

    def generate_files(self):
        folder_path = Path(self.folder_entry.get() or "content")
        content = self.content_text_area.get("1.0", tk.END).strip()
        
        if not content:
            messagebox.showerror("Error", "Text area is empty.")
            return

        # Ensure folder exists
        folder_path.mkdir(parents=True, exist_ok=True)

        # Split content into questions
        pattern = r"(?m)^# Question (\d+):"
        matches = list(re.finditer(pattern, content))

        if not matches:
            messagebox.showerror("Error", "No questions found in content.")
            return

        for i, match in enumerate(matches):
            question_number = match.group(1)
            start = match.start()
            end = matches[i+1].start() if i + 1 < len(matches) else len(content)
            question_content = content[start:end].strip()

            file_path = folder_path / f"question{question_number}.md"
            try:
                with file_path.open("w", encoding="utf-8") as f:
                    f.write(question_content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to write file {file_path}: {str(e)}")
                return

        self.content_status_var.set(f"Generated {len(matches)} files in '{folder_path}'")
        messagebox.showinfo("Success", f"Generated {len(matches)} files in '{folder_path}'.")

    # Enhanced Visuals Tab Methods (from code 2)
    def toggle_mode(self):
        """Toggle between single and batch processing modes"""
        mode = self.processing_mode.get()
        
        if mode == "single":
            self.single_buttons.grid()
            self.input_text.grid()
            self.single_output_buttons.grid()
            self.batch_buttons.grid_remove()
            self.file_list_frame.grid_remove()
            self.batch_output_buttons.grid_remove()
            self.progress_bar.grid_remove()
        else:
            self.single_buttons.grid_remove()
            self.input_text.grid_remove()
            self.single_output_buttons.grid_remove()
            self.batch_buttons.grid()
            self.file_list_frame.grid()
            self.batch_output_buttons.grid()
            self.progress_bar.grid()
            
    def add_visuals_sample_text(self):
        sample = """# Question 16: How do you define and use struct tags?

**Introduction:**
Today, we're diving into struct tags in Go. Struct tags let you add extra metadata to struct fields. They're useful for serialization, validation, and more.

**Key Points:**

1. **Defining Struct Tags**

   * Add tags using backticks after a field.
   * Example: `Name string json:"name"`
   * Tags are just strings interpreted by libraries.
   *Visual placeholder:*

   ```mermaid
   graph LR
   Field --> "Struct Tag (metadata)"
   ```

   *(On-screen text: "Field + Tag = Metadata")*

2. **Using Struct Tags in JSON**

   * Tags tell encoding/json how to serialize fields.
   * `json:"name"` maps the field to a JSON key.
   * This avoids sending field names directly.
   *Visual placeholder:*

   ```mermaid
   graph TD
   Struct --> JSON_Output["JSON: name:value"]
   ```

   *(On-screen text: "Struct to JSON using tags")*

**Conclusion:**
Struct tags are small but powerful. They help libraries understand your data. Start adding tags today to simplify serialization and validation.
"""
        self.input_text.insert("1.0", sample)
        
    def load_markdown_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Markdown File",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", content)
                self.current_files = [file_path]
                self.visuals_status_var.set(f"Loaded: {Path(file_path).name}")
            except UnicodeDecodeError:
                messagebox.showerror("Error", f"Failed to load file: Invalid encoding")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
                
    def load_multiple_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Multiple Markdown Files",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_paths:
            self.current_files = list(file_paths)
            self.update_file_list()
            self.visuals_status_var.set(f"Selected {len(file_paths)} files")
            
    def select_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder with Markdown Files")
        
        if folder_path:
            folder = Path(folder_path)
            md_files = []
            for ext in ['*.md', '*.txt', '*.markdown']:
                md_files.extend(folder.glob(ext))
                md_files.extend(folder.glob('**/' + ext))  # Include subdirectories
            
            if md_files:
                self.current_files = [str(f) for f in md_files]
                self.update_file_list()
                self.visuals_status_var.set(f"Found {len(md_files)} markdown files in folder")
            else:
                messagebox.showinfo("No Files Found", "No markdown files found in the selected folder.")
                
    def update_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for file_path in self.current_files:
            self.file_listbox.insert(tk.END, Path(file_path).name)
            
    def clear_file_selection(self):
        self.current_files = []
        self.update_file_list()
        self.visuals_status_var.set("File selection cleared")
        
    def paste_from_clipboard(self):
        try:
            clipboard_content = self.root.clipboard_get()
            if clipboard_content:
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", clipboard_content)
                self.visuals_status_var.set("Content pasted from clipboard")
            else:
                messagebox.showinfo("Clipboard Empty", "No content found in clipboard.")
        except tk.TclError:
            messagebox.showwarning("Clipboard Error", "Could not access clipboard content.")
            
    def clear_input(self):
        self.input_text.delete("1.0", tk.END)
        self.visuals_status_var.set("Input cleared")
        
    def convert_to_html(self):
        markdown_content = self.input_text.get("1.0", tk.END).strip()
        
        if not markdown_content:
            messagebox.showwarning("Warning", "Please enter some markdown content first.")
            return
            
        try:
            html_content = self.markdown_to_html(markdown_content)
            self.output_html = html_content
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", html_content)
            self.visuals_status_var.set("Conversion completed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
            
    def batch_convert(self):
        if not self.current_files:
            messagebox.showwarning("Warning", "Please select markdown files first.")
            return
            
        self.cancel_batch = False
        threading.Thread(target=self._batch_convert_worker, daemon=True).start()
        
    def _batch_convert_worker(self):
        self.batch_results = []
        total_files = len(self.current_files)
        
        self.root.after(0, lambda: self.progress_var.set(0))
        self.root.after(0, lambda: self.visuals_status_var.set("Starting batch conversion..."))
        
        with ThreadPoolExecutor() as executor:
            futures = []
            for file_path in self.current_files:
                if self.cancel_batch:
                    break
                futures.append(executor.submit(self._convert_file, file_path))
            
            for i, future in enumerate(futures):
                if self.cancel_batch:
                    break
                result = future.result()
                self.batch_results.append(result)
                progress = ((i + 1) / total_files) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda i=i: self.visuals_status_var.set(f"Processed file {i+1} of {total_files}"))
        
        if not self.cancel_batch:
            self.root.after(0, self._show_batch_results)
        else:
            self.root.after(0, lambda: self.visuals_status_var.set("Batch conversion cancelled"))
        
    def _convert_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            html_content = self.markdown_to_html(content)
            return {
                'file_path': file_path,
                'success': True,
                'html_content': html_content,
                'error': None
            }
        except Exception as e:
            return {
                'file_path': file_path,
                'success': False,
                'html_content': None,
                'error': str(e)
            }
            
    def _show_batch_results(self):
        successful = sum(1 for r in self.batch_results if r['success'])
        failed = len(self.batch_results) - successful
        
        result_text = f"Batch Conversion Results:\n"
        result_text += f"Successfully converted: {successful} files\n"
        result_text += f"Failed: {failed} files\n\n"
        
        if failed > 0:
            result_text += "Failed files:\n"
            for result in self.batch_results:
                if not result['success']:
                    result_text += f"- {Path(result['file_path']).name}: {result['error']}\n"
                    
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", result_text)
        self.visuals_status_var.set(f"Batch conversion completed: {successful} successful, {failed} failed")
        
    def cancel_batch_operation(self):
        self.cancel_batch = True
        self.visuals_status_var.set("Cancelling batch operation...")
        
    def batch_save_html(self):
        if not self.batch_results:
            messagebox.showwarning("Warning", "Please convert files first.")
            return
            
        output_dir = filedialog.askdirectory(title="Select Output Directory for HTML Files")
        if not output_dir:
            return
            
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        successful_saves = 0
        
        for result in self.batch_results:
            if result['success']:
                try:
                    input_file = Path(result['file_path'])
                    output_file = output_dir / f"{input_file.stem}.html"
                    
                    with output_file.open('w', encoding='utf-8') as file:
                        file.write(result['html_content'])
                    
                    successful_saves += 1
                except Exception as e:
                    print(f"Failed to save {result['file_path']}: {e}")
                    
        messagebox.showinfo("Batch Save Complete", 
                           f"Successfully saved {successful_saves} HTML files to:\n{output_dir}")
        self.visuals_status_var.set(f"Saved {successful_saves} HTML files")
        
    def export_batch_report(self):
        if not self.batch_results:
            messagebox.showwarning("Warning", "No batch results to export.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Batch Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write("Markdown to HTML Batch Conversion Report\n")
                    file.write("=" * 50 + "\n\n")
                    successful = sum(1 for r in self.batch_results if r['success'])
                    failed = len(self.batch_results) - successful
                    
                    file.write(f"Total files processed: {len(self.batch_results)}\n")
                    file.write(f"Successfully converted: {successful}\n")
                    file.write(f"Failed conversions: {failed}\n\n")
                    file.write("Detailed Results:\n")
                    file.write("-" * 30 + "\n")
                    
                    for i, result in enumerate(self.batch_results, 1):
                        file.write(f"{i}. {Path(result['file_path']).name}\n")
                        if result['success']:
                            file.write("   Status: SUCCESS\n")
                        else:
                            file.write(f"   Status: FAILED - {result['error']}\n")
                        file.write(f"   Full path: {result['file_path']}\n\n")
                        
                messagebox.showinfo("Report Saved", f"Batch report saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save report: {str(e)}")
        
    def markdown_to_html(self, markdown_content):
        """Convert markdown content to HTML with Mermaid support and enhanced styling"""
        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Converted Markdown Document</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.6.1/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Helvetica Neue', Helvetica, 'Segoe UI', Arial, freesans, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: #333;
            background-color: #fff;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        h1 {{
            font-size: 2.25em;
            font-weight: 300;
            padding-bottom: 0.3em;
            border-bottom: 2px solid #e1e4e8;
            color: #1a73e8;
            margin-top: 1.5em;
        }}
        
        h2 {{
            font-size: 1.75em;
            font-weight: 400;
            margin-top: 1.5em;
            color: #1f2937;
        }}
        
        h3 {{
            font-size: 1.5em;
            font-weight: 500;
            margin-top: 1.2em;
            color: #374151;
        }}
        
        .video-section {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
            border-left: 4px solid #1a73e8;
        }}
        
        .introduction, .conclusion {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            border-left: 3px solid #2196f3;
        }}
        
        .key-points {{
            background: #f8f9fa;
            border: 1px solid #e1e4e8;
            border-radius: 5px;
            padding: 20px;
            margin: 15px 0;
        }}
        
        .on-screen-cue {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 3px;
            padding: 8px 12px;
            margin: 10px 0;
            font-style: italic;
            color: #856404;
            display: inline-block;
        }}
        
        .visual-placeholder {{
            background: #e8f5e8;
            border: 1px solid #4caf50;
            border-radius: 3px;
            padding: 8px 12px;
            margin: 10px 0;
            font-style: italic;
            color: #2e7d32;
        }}
        
        ol.main-points {{
            counter-reset: item;
            padding-left: 0;
        }}
        
        ol.main-points > li {{
            display: block;
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 3px solid #1a73e8;
        }}
        
        ol.main-points > li:before {{
            content: counter(item) ". ";
            counter-increment: item;
            font-weight: bold;
            color: #1a73e8;
            font-size: 1.1em;
        }}
        
        ol.main-points > li h3 {{
            display: inline;
            margin: 0;
            color: #1a73e8;
        }}
        
        ol.main-points > li ul {{
            margin-top: 10px;
        }}
        
        code {{
            background: #f1f3f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #d73a49;
        }}
        
        pre {{
            background: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 16px;
            overflow: auto;
        }}
        
        pre code {{
            background: none;
            padding: 0;
            color: #24292e;
        }}
        
        ul, ol {{
            padding-left: 2em;
        }}
        
        li {{
            margin-bottom: 8px;
        }}
        
        .mermaid {{
            text-align: center;
            margin: 20px 0;
            background: #fff;
            border: 1px solid #e1e4e8;
            border-radius: 5px;
            padding: 20px;
        }}
        
        hr {{
            border: none;
            height: 2px;
            background: linear-gradient(to right, #1a73e8, #4285f4, #1a73e8);
            margin: 40px 0;
        }}
        
        blockquote {{
            border-left: 4px solid #dfe2e5;
            padding: 0 16px;
            color: #6a737d;
            margin: 16px 0;
        }}
        
        strong {{
            color: #1a73e8;
            font-weight: 600;
        }}
        
        em {{
            color: #586069;
            font-style: italic;
        }}
    </style>
</head>
<body>
{content}
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
    </script>
</body>
</html>"""
        
        # Convert markdown to HTML using enhanced processing
        html_content = self.process_markdown(markdown_content)
        return html_template.format(content=html_content)
        
    def process_markdown(self, text):
        """Convert markdown syntax to HTML with enhanced features"""
        # Preserve line breaks in original text
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Handle mermaid code blocks first
        mermaid_pattern = r'```mermaid\s*\n(.*?)\n\s*```'
        text = re.sub(mermaid_pattern, lambda m: f'<div class="mermaid">{m.group(1).strip()}</div>', text, flags=re.DOTALL)
        
        # Handle regular code blocks
        code_pattern = r'```(\w+)?\s*\n(.*?)\n\s*```'
        text = re.sub(code_pattern, lambda m: f'<pre><code class="language-{m.group(1) or ""}">{m.group(2).strip()}</code></pre>', text, flags=re.DOTALL)
        
        # Handle headers
        text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
        
        # Rest of the method remains unchanged
        # Handle horizontal rules
        text = re.sub(r'^---+\s*$', '<hr>', text, flags=re.MULTILINE)
        
        # Handle special video content patterns
        text = re.sub(r'\*\*Introduction:\*\*\s*(.*?)(?=\n\s*\*\*[A-Z]|\n\s*\d+\.|\n\s*$)', 
                    r'<div class="introduction"><strong>Introduction:</strong>\1</div>', text, flags=re.DOTALL)
        text = re.sub(r'\*\*Conclusion:\*\*\s*(.*?)(?=\n\s*\*\*[A-Z]|\n\s*---|\n\s*$)', 
                    r'<div class="conclusion"><strong>Conclusion:</strong>\1</div>', text, flags=re.DOTALL)
        text = re.sub(r'\*\*Key Points:\*\*', r'<div class="key-points"><strong>Key Points:</strong>', text)
        
        # Handle on-screen cues with flexible patterns
        text = re.sub(r'\*\(On-screen[^)]*: ([^)]+)\)\*', r'<div class="on-screen-cue">On-screen: \1</div>', text)
        text = re.sub(r'\(On-screen[^)]*: ([^)]+)\)', r'<div class="on-screen-cue">On-screen: \1</div>', text)
        
        # Handle Visual placeholder patterns
        text = re.sub(r'\*Visual placeholder:\*', r'<div class="visual-placeholder"><strong>Visual placeholder:</strong></div>', text)
        
        # Process line by line for better control
        lines = text.split('\n')
        result_lines = []
        in_list = False
        in_numbered_list = False
        in_key_points = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Check for Key Points section
            if '<strong>Key Points:</strong>' in line:
                in_key_points = True
                result_lines.append(line)
                i += 1
                continue
            
            # Handle numbered list items (1., 2., etc.)
            if re.match(r'^\s*\d+\.\s+\*\*(.*?)\*\*', stripped):
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                if not in_numbered_list:
                    result_lines.append('<ol class="main-points">')
                    in_numbered_list = True
                
                # Extract the numbered item
                match = re.match(r'^\s*\d+\.\s+\*\*(.*?)\*\*(.*)', stripped)
                if match:
                    title = match.group(1)
                    rest = match.group(2)
                    result_lines.append(f'<li><h3>{title}</h3>{rest}')
                    
                    # Look ahead for bullet points under this numbered item
                    j = i + 1
                    sub_items = []
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if next_line.startswith('* ') or next_line.startswith('- '):
                            sub_items.append(next_line[2:])
                            j += 1
                        elif next_line and not re.match(r'^\s*\d+\.', next_line):
                            # Continue with content for this numbered item
                            if not next_line.startswith('<') and next_line:
                                sub_items.append(next_line)
                            j += 1
                        else:
                            break
                    
                    if sub_items:
                        result_lines.append('<ul>')
                        for item in sub_items:
                            result_lines.append(f'<li>{item}</li>')
                        result_lines.append('</ul>')
                    
                    result_lines.append('</li>')
                    i = j - 1
                    
            # Handle regular bullet points
            elif stripped.startswith('* ') or stripped.startswith('- '):
                if in_numbered_list:
                    result_lines.append('</ol>')
                    in_numbered_list = False
                if not in_list:
                    result_lines.append('<ul>')
                    in_list = True
                result_lines.append(f'<li>{stripped[2:]}</li>')
                
            else:
                # Close any open lists
                if in_list:
                    result_lines.append('</ul>')
                    in_list = False
                if in_numbered_list:
                    result_lines.append('</ol>')
                    in_numbered_list = False
                    
                # Add the line as is
                result_lines.append(line)
            
            i += 1
        
        # Close any remaining open lists
        if in_list:
            result_lines.append('</ul>')
        if in_numbered_list:
            result_lines.append('</ol>')
        if in_key_points:
            result_lines.append('</div>')
            
        text = '\n'.join(result_lines)
        
        # Handle bold and italic (after list processing)
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        
        # Handle inline code with backticks
        text = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', text)
        
        # Convert remaining text to paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        html_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Don't wrap if it's already HTML
                if (para.startswith('<') and para.endswith('>')) or \
                '<div class=' in para or '<h' in para or '<ul>' in para or '<ol>' in para:
                    html_paragraphs.append(para)
                elif para:
                    html_paragraphs.append(f'<p>{para}</p>')
                    
        return '\n\n'.join(html_paragraphs)
    
    def save_html(self):
        if not self.output_html:
            messagebox.showwarning("Warning", "Please convert markdown to HTML first.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save HTML File",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.output_html)
                self.visuals_status_var.set(f"Saved: {Path(file_path).name}")
                messagebox.showinfo("Success", f"HTML file saved successfully!\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                
    def preview_in_browser(self):
        if not self.output_html:
            messagebox.showwarning("Warning", "Please convert markdown to HTML first.")
            return
            
        try:
            temp_dir = Path(tempfile.gettempdir())
            temp_file = temp_dir / f"markdown_preview_{uuid.uuid4()}.html"
            
            with temp_file.open('w', encoding='utf-8') as file:
                file.write(self.output_html)
                
            webbrowser.open(f'file://{temp_file}')
            self.visuals_status_var.set("Preview opened in browser")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open preview: {str(e)}")

    # Script Tab Methods
    def browse_script_folder(self):
        selected_folder = filedialog.askdirectory()
        if selected_folder:
            self.script_folder_entry.delete(0, tk.END)
            self.script_folder_entry.insert(0, selected_folder)

    def clear_script_text(self):
        self.script_text_area.delete("1.0", tk.END)
        self.script_status_var.set("Text area cleared")

    def add_script_sample_text(self):
        sample = """# 1. Introduction to Python

**Script:**
Welcome to our Python tutorial series! Today, we'll explore the basics of Python programming.

# 2. Variables in Python

**Script:**
Let's dive into variables, the building blocks of any Python program.
"""
        self.script_text_area.insert("1.0", sample)

    def generate_script(self):
        folder_path = Path(self.script_folder_entry.get() or "content")
        content = self.script_text_area.get("1.0", tk.END).strip()
        
        if not content:
            messagebox.showerror("Error", "Text area is empty.")
            return

        # Ensure folder exists
        folder_path.mkdir(parents=True, exist_ok=True)

        # Extract question numbers
        pattern = r"(?m)^# (\d+)\.\s"
        question_numbers = re.findall(pattern, content)
        
        if not question_numbers:
            messagebox.showerror("Error", "No questions found in content.")
            return

        # Create filename based on question numbers
        filename = "_".join(question_numbers) + "_script.md"
        file_path = folder_path / filename

        try:
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)
            self.script_status_var.set(f"Generated script file '{filename}' in '{folder_path}'")
            messagebox.showinfo("Success", f"Script file '{filename}' generated in '{folder_path}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate script file: {str(e)}")

def main():
    root = tk.Tk()
    app = CombinedMarkdownApp(root)
    
    # Add keyboard shortcuts
    root.bind('<Control-o>', lambda e: app.load_markdown_file())
    root.bind('<Control-v>', lambda e: app.paste_from_clipboard())
    root.bind('<Control-s>', lambda e: app.save_html())
    root.bind('<F5>', lambda e: app.convert_to_html())
    
    root.mainloop()

if __name__ == "__main__":
    main()




    