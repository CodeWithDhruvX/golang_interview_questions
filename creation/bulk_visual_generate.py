import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

# Function to browse folder
def browse_folder():
    selected_folder = filedialog.askdirectory()
    if selected_folder:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, selected_folder)

# Function to clear text
def clear_text():
    text_area.delete("1.0", tk.END)

# Function to generate markdown files
def generate_files():
    folder_path = folder_entry.get() or "content"
    content = text_area.get("1.0", tk.END).strip()
    
    if not content:
        messagebox.showerror("Error", "Text area is empty.")
        return

    # Ensure folder exists
    os.makedirs(folder_path, exist_ok=True)

    # Split content into questions
    # Matches lines like "# Question 16:"
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

        file_path = os.path.join(folder_path, f"question{question_number}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(question_content)

    messagebox.showinfo("Success", f"Generated {len(matches)} files in '{folder_path}'.")

# Create main window
root = tk.Tk()
root.title("Markdown File Generator")

# Folder selection
tk.Label(root, text="Folder:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
folder_entry = tk.Entry(root, width=50)
folder_entry.grid(row=0, column=1, padx=5, pady=5)
folder_entry.insert(0, "content")
tk.Button(root, text="Browse", command=browse_folder).grid(row=0, column=2, padx=5, pady=5)

# Text area
text_area = tk.Text(root, width=100, height=35)
text_area.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

# Buttons
tk.Button(root, text="Clear Text", command=clear_text, bg="lightcoral").grid(row=2, column=0, padx=5, pady=10)
tk.Button(root, text="Generate", command=generate_files, bg="lightgreen").grid(row=2, column=2, padx=5, pady=10)

root.mainloop()
