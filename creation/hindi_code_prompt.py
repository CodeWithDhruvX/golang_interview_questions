import tkinter as tk
from tkinter import ttk, messagebox
import json
from pygments.lexers import guess_lexer
from pygments.util import ClassNotFound

# --- Smart Language Detector ---
def detect_language(content):
    try:
        lexer = guess_lexer(content)
        language = lexer.name.lower()

        if "python" in language:
            return "python"
        elif "javascript" in language:
            return "javascript"
        elif "go" in language:
            return "go"
        elif "java" in language:
            return "java"
        elif "c++" in language or "cpp" in language:
            return "cpp"
        elif "c#" in language:
            return "csharp"
        elif "html" in language:
            return "html"
        elif "css" in language:
            return "css"
        elif "php" in language:
            return "php"
        elif "ruby" in language:
            return "ruby"
        else:
            return "plaintext"
    except ClassNotFound:
        return "plaintext"

# --- Core Engine ---
def generate_prompt(obj, selected_mode, add_best_mistakes):
    title = obj.get('title', 'Untitled')
    content = obj.get('content', '')
    slide_type = obj.get('slide_type', 'code')

    language = detect_language(content)

    output = f"### 📘 Title: {title}\n\n"
    output += "---\n\n"

    if selected_mode == "Code Creation Mode":
        output += f"### 🛠 Code Banayein\n"
        output += f"Iss idea par based code likhiye:\n\n"
        output += f"**Idea:** {content}\n\n"
        output += f"### 💻 Code ({language})\n"
        output += f"```{language}\n"
        output += f"// Yahan se code shuru hota hai...\n"
        output += f"```\n\n"
        output += "---\n\n"
        output += "### 🧠 Samjhaaiye:\n- Yeh code kya karta hai, detail mein batayein.\n\n"

        if add_best_mistakes:
            output += "### ✅ Best Practices:\n- Is code ke liye best practices kya hain.\n\n"
            output += "### ⚡ Galtiyaan:\n- Common mistakes aur unka solution.\n\n"

        return output

    # Normal explanation
    output += f"### 💻 Code ({language})\n"
    output += f"```{language}\n{content}\n```\n\n"
    output += "---\n\n"

    if selected_mode == "Simple Mode":
        output += "### 🧠 Asaan Explanation:\n- Code ka basic matlab samjhaayein.\n\n"
    elif selected_mode == "Detailed Mode":
        output += "### 🧠 Detail Explanation:\n- Line by line samjhaayein.\n- Agar ho sake to analogy dein.\n\n"
        output += "### ✅ Best Practices:\n- Code ke behtar tarike.\n\n"
        output += "### 🌍 Real Life Use:\n- Ye code kahaan use hota hai, batayein.\n\n"
        output += "### ⚡ Galtiyaan:\n- Log kya galti karte hain, aur kaise sudhaarein.\n\n"
    elif selected_mode == "Deep Dive Mode":
        output += "### 🧠 Deep Dive Explanation:\n- Line by line breakdown.\n- Memory aur performance ke aspects.\n- Internal working bhi samjhaayein.\n\n"
        output += "### ✅ Best Practices:\n- Large scale ke liye optimize karne ke tareeke.\n\n"
        output += "### 🌍 Real Use Cases:\n- Jaise banking, finance, data-heavy apps.\n\n"
        output += "### ⚡ Galtiyaan:\n- Overflow ya portability errors.\n\n"
    elif selected_mode == "Interview Mode":
        output += "### 🧠 Interview Style Explanation:\n- STAR method ka use karke samjhaayein.\n\n"
        output += "### 🎯 Interview Tip:\n- Type safety aur optimization pe focus karein.\n\n"
    elif selected_mode == "Mistake Hunt Mode":
        output += "### ⚡ Galtiyan (Mistake Hunt Mode):\n- Common errors aur unka fix.\n\n"
    elif selected_mode == "Pro Developer Mode":
        output += "### 🧠 Pro Tips:\n- Production-ready, scalable, readable aur clean code likhna.\n\n"
    elif selected_mode == "Architecture Mode":
        output += "### 🏛 Architecture Connect:\n- Yeh code system ya microservices mein kaise fit hota hai.\n\n"
    else:
        output += "### 🧠 General Explanation:\n- Code samjhaane ka normal tareeka.\n\n"

    return output

# --- GUI App ---
def generate_output():
    try:
        input_text = input_box.get("1.0", tk.END).strip()
        objs = json.loads(input_text)

        if not isinstance(objs, list):
            objs = [objs]

        selected_mode = mode_var.get()
        add_best_mistakes = add_best_mistakes_var.get()
        final_output = ""

        for obj in objs:
            prompt = generate_prompt(obj, selected_mode, add_best_mistakes)
            final_output += prompt + "\n\n"

        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, final_output)

    except Exception as e:
        messagebox.showerror("Error", f"Galat input format!\n\n{str(e)}")

def copy_output():
    root.clipboard_clear()
    root.clipboard_append(output_box.get("1.0", tk.END))
    messagebox.showinfo("Copied", "Output clipboard mein copy ho gaya!")

# --- Main Window ---
root = tk.Tk()
root.title("💡 Prompt Generator App (Hinglish Edition)")
root.geometry("1000x900")

# Input Frame
input_frame = tk.Frame(root)
input_frame.pack(pady=10)

tk.Label(input_frame, text="JSON Paste karo (Code idea ya content):").pack(anchor="w")
input_box = tk.Text(input_frame, width=120, height=10)
input_box.pack()

# Mode Selector
mode_frame = tk.Frame(root)
mode_frame.pack(pady=5)

tk.Label(mode_frame, text="Flavor Mode choose karo:").pack(side="left", padx=5)

mode_var = tk.StringVar()
mode_dropdown = ttk.Combobox(mode_frame, textvariable=mode_var, width=35)
mode_dropdown['values'] = (
    "Simple Mode",
    "Detailed Mode",
    "Deep Dive Mode",
    "Interview Mode",
    "Pro Developer Mode",
    "Mistake Hunt Mode",
    "Architecture Mode",
    "Code Creation Mode",
)
mode_dropdown.current(7)
mode_dropdown.pack(side="left", padx=5)

# Checkbox
add_best_mistakes_var = tk.BooleanVar()
add_best_mistakes_checkbox = tk.Checkbutton(root, text="Code Creation Mode mein Best Practices aur Mistakes bhi chahiye", variable=add_best_mistakes_var)
add_best_mistakes_checkbox.pack(pady=5)

# Buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=5)

tk.Button(button_frame, text="🚀 Output Banao", command=generate_output).pack(side="left", padx=10)
tk.Button(button_frame, text="📋 Copy Karo", command=copy_output).pack(side="left", padx=10)

# Output Frame
output_frame = tk.Frame(root)
output_frame.pack(pady=10)

tk.Label(output_frame, text="👉 Final Output Yahan Aayega:").pack(anchor="w")
output_box = tk.Text(output_frame, width=120, height=20)
output_box.pack()

# Plan Section
plan_frame = tk.LabelFrame(root, text="🧭 Mode ka Use Case Samjho", padx=10, pady=10)
plan_frame.pack(padx=10, pady=10, fill="both")

plan_info = (
    "Mode                    | Kya karta hai\n"
    "-------------------------|------------------------------------------------------\n"
    "Simple Mode             | Basic aur short explanation.\n"
    "Detailed Mode           | Full breakdown + analogies.\n"
    "Deep Dive Mode          | Memory, internals, aur performance.\n"
    "Interview Mode          | Interview-style STAR format se samjhao.\n"
    "Pro Developer Mode      | Clean, scalable, production-level code likhne ka tarika.\n"
    "Mistake Hunt Mode       | Log jo galti karte hain, woh highlight karo.\n"
    "Architecture Mode       | System architecture mein code ka role batayein.\n"
    "Code Creation Mode      | Sirf idea se naya code banao + explain karo.\n"
)

plan_text = tk.Text(plan_frame, height=12, width=100, wrap="none", bg="#f9f9f9")
plan_text.insert(tk.END, plan_info)
plan_text.config(state="disabled")
plan_text.pack()

root.mainloop()
