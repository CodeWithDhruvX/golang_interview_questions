import tkinter as tk
from tkinter import scrolledtext, messagebox
import json
import pyperclip

def generate_script():
    try:
        raw_json = input_text.get("1.0", tk.END).strip()
        slide = json.loads(raw_json)

        title = slide.get("title", "").strip()
        content = slide.get("content", "").strip()
        slide_type = slide.get("slide_type", "").strip().lower()

        if not (title and content and slide_type):
            raise ValueError("Slide must include title, content, and slide_type.")

        # Get video duration from entry (default to 5 if invalid)
        try:
            minute = int(duration_entry.get().strip())
            if minute <= 0:
                raise ValueError
        except:
            minute = 5

        output = f"""I’m creating a {minute} minute educational YouTube video about Topic, aimed at beginner programmers in India.

Here are the slides in JSON format:

   {{
      "title": "{title}",
      "content": "{content}",
      "slide_type": "{slide_type}"
    }}

[Repeat for all slides]

Based on these slides, create a script segment for my YouTube video. The tone should be **conversational, clear, and beginner-friendly**, crafted especially for an Indian audience who understands English.

✅ Tone and Style Guidelines:
- Use **spoken-style English**, like you're casually explaining something to a friend or junior developer.
- Keep the language simple, friendly, and natural.
- Use **relatable examples** (especially ones an Indian beginner would connect with, like classroom explanations, job interviews, or real coding tasks).
- Avoid complicated words or phrases that sound too formal or western.
- Don’t use any Hindi or Hinglish — keep it **100% English**, but **Indian-friendly**.
- Maintain a **teacher-like tone**, as if guiding someone new to programming.

🎯 Instructions:

Start with the first slide:
- Read the title and content and explain what it means.
- Use simple, real-life or beginner-level programming examples.
- Highlight **why this topic matters**, especially in real-world coding scenarios.

📘 For `code` slides:
- Explain the code line by line.
- Mention what each part does in a clear and practical way.
- Help beginners avoid common mistakes.

📊 For `table` slides:
- Walk through each row and column clearly.
- Compare values or concepts simply.
- Help the viewer understand how to use this information in actual development work.

⛔ Rules:
- No intro or outro.
- Do not explain multiple slides at once — only one slide per explanation.
- Assume the viewer is new to Topic and programming.
- when the slide_type text, then only explain the theory part. don't include any code"""

        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, output)

    except Exception as e:
        messagebox.showerror("Error", f"Could not generate script.\n\n{e}")

def copy_script():
    content = output_text.get("1.0", tk.END).strip()
    if content:
        pyperclip.copy(content)
        # messagebox.showinfo("Copied", "Script copied to clipboard!")
    # else:
    #     messagebox.showwarning("Warning", "There’s nothing to copy.")

# Setup GUI
root = tk.Tk()
root.title("Topic Slide Prompt Formatter")

tk.Label(root, text="Enter Single Slide JSON:").pack(anchor='w', padx=10, pady=(10, 0))
input_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10)
input_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

tk.Label(root, text="Video Duration (in minutes):").pack(anchor='w', padx=10, pady=(10, 0))
duration_entry = tk.Entry(root)
duration_entry.insert(0, "5")  # default value
duration_entry.pack(fill=tk.X, padx=10, pady=(0, 5))

tk.Button(root, text="Copy to Clipboard", command=copy_script).pack(pady=(0, 10))
tk.Button(root, text="Generate YouTube Prompt", command=generate_script).pack(pady=5)

tk.Label(root, text="Formatted Prompt Output:").pack(anchor='w', padx=10)
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=20)
output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)



root.mainloop()
