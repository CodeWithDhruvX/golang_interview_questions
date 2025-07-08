from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ✅ Use correct model ID
model_id = "ai4bharat/indictrans2"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

def translate(text, src_lang="hi", tgt_lang="en"):
    prefix = f"{src_lang}2{tgt_lang}: "
    input_text = prefix + text
    batch = tokenizer([input_text], return_tensors="pt")
    generated_ids = model.generate(**batch, max_length=256)
    output = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
    return output[0]

# Test it
hindi_text = "आप कैसे हैं?"
hinglish_translation = translate(hindi_text)
print("🗣️ Hinglish:", hinglish_translation)
