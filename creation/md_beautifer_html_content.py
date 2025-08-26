import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import os
import webbrowser
from pathlib import Path
import tempfile

class MarkdownToHTMLConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Markdown to HTML Converter with Mermaid Support")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.current_file = None
        self.output_html = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Markdown to HTML Converter", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Left panel - Input
        input_frame = ttk.LabelFrame(main_frame, text="Markdown Input", padding="5")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(1, weight=1)
        
        # Input buttons
        input_buttons = ttk.Frame(input_frame)
        input_buttons.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(input_buttons, text="Load MD File", 
                  command=self.load_markdown_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(input_buttons, text="Clear", 
                  command=self.clear_input).pack(side=tk.LEFT, padx=(0, 5))
        
        # Input text area
        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, 
                                                   width=50, height=25,
                                                   font=('Consolas', 10))
        self.input_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Right panel - Preview/Output
        output_frame = ttk.LabelFrame(main_frame, text="HTML Preview", padding="5")
        output_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1)
        
        # Output buttons
        output_buttons = ttk.Frame(output_frame)
        output_buttons.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(output_buttons, text="Convert to HTML", 
                  command=self.convert_to_html).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(output_buttons, text="Save HTML", 
                  command=self.save_html).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(output_buttons, text="Preview in Browser", 
                  command=self.preview_in_browser).pack(side=tk.LEFT, padx=(0, 5))
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, 
                                                    width=50, height=25,
                                                    font=('Consolas', 9))
        self.output_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Add sample text
        self.add_sample_text()
        
    def add_sample_text(self):
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

3. **Other Tag Uses**

   * Validation libraries use tags for rules.
   * Example: `validate:"required"` ensures field is not empty.
   * Tags make code cleaner and reusable.
   *Visual placeholder:*

   ```mermaid
   graph LR
   Field --> "Validation Rules" --> "Library Checks"
   ```

   *(On-screen text: "Struct tags for validation")*

**Conclusion:**
Struct tags are small but powerful. They help libraries understand your data. Start adding tags today to simplify serialization and validation.

---

# Question 17: What are Go interfaces?

**Introduction:**
Go interfaces are one of the most powerful features in the language. They define behavior without specifying implementation.

**Key Points:**

1. **Interface Definition**

   * An interface specifies method signatures
   * Example: `type Writer interface { Write([]byte) (int, error) }`
   * Any type implementing these methods satisfies the interface

2. **Implicit Implementation**

   * No explicit "implements" keyword needed
   * If a type has the required methods, it implements the interface
   * This enables duck typing: "If it walks like a duck..."

**Conclusion:**
Interfaces make Go code flexible and testable. They're the key to writing modular, maintainable programs.
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
                    self.current_file = file_path
                    self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
                
    def clear_input(self):
        self.input_text.delete("1.0", tk.END)
        self.status_var.set("Input cleared")
        
    def convert_to_html(self):
        markdown_content = self.input_text.get("1.0", tk.END)
        
        if not markdown_content.strip():
            messagebox.showwarning("Warning", "Please enter some markdown content first.")
            return
            
        try:
            html_content = self.markdown_to_html(markdown_content)
            self.output_html = html_content
            
            # Show preview in output text area
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", html_content)
            
            self.status_var.set("Conversion completed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
            
    def markdown_to_html(self, markdown_content):
        """Convert markdown content to HTML with Mermaid support"""
        
        # Basic HTML template
        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Converted Markdown Document</title>
    
    <!-- Load Mermaid from CDN -->
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
        // Initialize Mermaid with proper configuration
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

        # Convert markdown to HTML
        html_content = self.process_markdown(markdown_content)
        
        return html_template.format(content=html_content)
        
    def process_markdown(self, text):
        """Convert markdown syntax to HTML"""
        
        # Preserve line breaks in original text
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Handle mermaid code blocks first (more flexible pattern)
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
        
        # Handle horizontal rules
        text = re.sub(r'^---+\s*$', '<hr>', text, flags=re.MULTILINE)
        
        # Handle special video content patterns
        text = re.sub(r'\*\*Introduction:\*\*\s*(.*?)(?=\n\s*\*\*[A-Z]|\n\s*\d+\.|\n\s*$)', 
                     r'<div class="introduction"><strong>Introduction:</strong>\1</div>', text, flags=re.DOTALL)
        text = re.sub(r'\*\*Conclusion:\*\*\s*(.*?)(?=\n\s*\*\*[A-Z]|\n\s*---|\n\s*$)', 
                     r'<div class="conclusion"><strong>Conclusion:</strong>\1</div>', text, flags=re.DOTALL)
        text = re.sub(r'\*\*Key Points:\*\*', r'<div class="key-points"><strong>Key Points:</strong>', text)
        
        # Handle on-screen cues with more flexible patterns
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
        
        # Handle inline code with backticks (be more careful)
        text = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', text)
        
        # Convert remaining text to paragraphs, but be smarter about it
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
                    # Only wrap non-HTML content in paragraphs
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
                self.status_var.set(f"Saved: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"HTML file saved successfully!\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                
    def preview_in_browser(self):
        if not self.output_html:
            messagebox.showwarning("Warning", "Please convert markdown to HTML first.")
            return
            
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, "markdown_preview.html")
            
            with open(temp_file, 'w', encoding='utf-8') as file:
                file.write(self.output_html)
                
            # Open in browser
            webbrowser.open('file://' + os.path.abspath(temp_file))
            self.status_var.set("Preview opened in browser")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open preview: {str(e)}")

def main():
    root = tk.Tk()
    app = MarkdownToHTMLConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()