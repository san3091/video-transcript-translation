import sys
import os
from transformers import MarianMTModel, MarianTokenizer

def main():
    # Check that an input file was provided
    if len(sys.argv) < 2:
        print("Usage: python translate.py input_file")
        sys.exit(1)

    input_file = sys.argv[1]

    # Read the Spanish text from the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            spanish_text = f.read()
    except Exception as e:
        print(f"Error reading file {input_file}: {e}")
        sys.exit(1)

    # Load the MarianMT model and tokenizer for Spanish -> English
    model_name = "Helsinki-NLP/opus-mt-es-en"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)

    # Tokenize the Spanish text
    inputs = tokenizer([spanish_text], return_tensors="pt", padding=True, truncation=True)
    
    # Translate the text
    translated_tokens = model.generate(**inputs)
    
    # Decode the tokens to get the English translation
    english_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)

    # Construct the output file name by appending "-spanish" before the file extension
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}-spanish{ext}"

    # Write the translated English text to the output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(english_text)
    except Exception as e:
        print(f"Error writing to file {output_file}: {e}")
        sys.exit(1)

    print(f"Translation complete. Output written to {output_file}")

if __name__ == "__main__":
    main()

