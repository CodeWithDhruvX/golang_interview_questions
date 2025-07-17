import whisper_timestamped as whisper
from datetime import timedelta

# Step 1: Load Whisper model
model = whisper.load_model("base")

# Step 2: Transcribe Hinglish audio
result = whisper.transcribe(model, "audio.mp3")

# Step 3: Load your custom transcript
with open("transcript.txt", "r", encoding="utf-8") as f:
    custom_lines = [line.strip() for line in f if line.strip()]

# Step 4: Align custom lines to Whisper segments
output_lines = []
for i, segment in enumerate(result["segments"]):
    if i >= len(custom_lines):
        break

    start = str(timedelta(seconds=int(segment["start"])))
    end = str(timedelta(seconds=int(segment["end"])))
    text = custom_lines[i]
    output_lines.append(f"[{start} --> {end}] {text}")

# Step 5: Save to timestamped text file
with open("output.txt", "w", encoding="utf-8") as out:
    out.write("\n".join(output_lines))

print("✅ Timestamped transcript saved to output.txt")
