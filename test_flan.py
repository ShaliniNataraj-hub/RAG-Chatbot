import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "google/flan-t5-large"

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name)

print("Loading model on CPU...")
model = AutoModelForSeq2SeqLM.from_pretrained(
    model_name
)

model.eval()

question = """
Explain what a Support Vector Machine is in simple terms.
"""

inputs = tokenizer(
    question,
    return_tensors="pt"
)

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=150
    )

answer = tokenizer.decode(
    outputs[0],
    skip_special_tokens=True
)

print("\nAnswer:")
print(answer)