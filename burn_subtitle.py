from faster_whisper import WhisperModel

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}".replace('.', ':')

model = WhisperModel("medium", device="cpu", compute_type="int8")

segments, info = model.transcribe("C:/Users/dhruv/Videos/sample_audio_2.wav", beam_size=5, word_timestamps=True)

ass_path = "C:/Users/dhruv/Videos/output.ass"

with open(ass_path, "w", encoding="utf-8") as f:
    # Header
    f.write("[Script Info]\n")
    f.write("Title: Whisper Transcript\n")
    f.write("ScriptType: v4.00+\n\n")

    f.write("[V4+ Styles]\n")
    f.write("Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, "
            "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
    f.write("Style: Default,Arial,26,&H00FFFF00,&H00000000,-1,0,1,1,0,2,10,10,10,1\n\n")

    f.write("[Events]\n")
    f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

    for segment in segments:
        start = format_time(segment.start)
        end = format_time(segment.end)
        text = segment.text.strip().replace('\n', ' ')
        f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

print(f"✅ ASS subtitle saved at: {ass_path}")





# [Script Info]
# Title: Bold Rounded Highlight Subtitle
# ScriptType: v4.00+
# PlayResX: 1920
# PlayResY: 1080
# Timer: 100.0000
# ScaledBorderAndShadow: yes ; Recommended for consistent appearance across renderers

# [V4+ Styles]
# Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
# Style: FullScreen,Montserrat,60,&H00FFFFFF&,&H000000FF&,&H00000000&,&H33000000&,-1,0,0,0,100,100,0,0,3,3,1,2,50,50,50,1

# [Events]
# Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text


# ffmpeg -i "C:/Users/dhruv/Videos/2025-07-03 22-36-41.mp4" -vf "ass=C\\:/Users/dhruv/Videos/output.ass" -c:a copy "C:/Users/dhruv/Videos/output_burned.mp4"




