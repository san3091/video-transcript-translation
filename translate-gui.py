import tkinter as tk
from tkinter import filedialog, messagebox
from transformers import MarianMTModel, MarianTokenizer
import os

class TranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spanish to English Translator")
        self.geometry("700x600")
        self.input_filepath = None  # to store the name of the opened file

        # Create the UI elements
        self.create_widgets()

        # Load the translation model (this may take a few seconds)
        self.load_model()

    def create_widgets(self):
        # Button to open a file
        self.open_button = tk.Button(self, text="Open File", command=self.open_file)
        self.open_button.pack(pady=10)

        # Label and text widget for input Spanish text
        self.input_label = tk.Label(self, text="Input Spanish Text:")
        self.input_label.pack()
        self.input_text = tk.Text(self, height=10, width=80)
        self.input_text.pack(pady=5)

        # Button to trigger translation
        self.translate_button = tk.Button(self, text="Translate", command=self.translate_text)
        self.translate_button.pack(pady=10)

        # Label and text widget for output English text
        self.output_label = tk.Label(self, text="Translated English Text:")
        self.output_label.pack()
        self.output_text = tk.Text(self, height=10, width=80)
        self.output_text.pack(pady=5)

        # Button to save the translated text
        self.save_button = tk.Button(self, text="Save Translation", command=self.save_translation)
        self.save_button.pack(pady=10)

    def load_model(self):
        try:
            self.model_name = "Helsinki-NLP/opus-mt-es-en"
            self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
            self.model = MarianMTModel.from_pretrained(self.model_name)
        except Exception as e:
            messagebox.showerror("Model Loading Error", f"Failed to load translation model: {e}")
            self.quit()

    def open_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    text = file.read()
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert(tk.END, text)
                self.input_filepath = filepath  # store for later use when saving
            except Exception as e:
                messagebox.showerror("File Error", f"Failed to open file: {e}")

    def translate_text(self):
        spanish_text = self.input_text.get("1.0", tk.END).strip()
        if not spanish_text:
            messagebox.showwarning("Input Error", "Please load a file or enter some text to translate.")
            return

        try:
            # Tokenize and translate the input text
            inputs = self.tokenizer([spanish_text], return_tensors="pt", padding=True, truncation=True)
            translated_tokens = self.model.generate(**inputs)
            english_text = self.tokenizer.decode(translated_tokens[0], skip_special_tokens=True)

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, english_text)
        except Exception as e:
            messagebox.showerror("Translation Error", f"Translation failed: {e}")

    def save_translation(self):
        english_text = self.output_text.get("1.0", tk.END).strip()
        if not english_text:
            messagebox.showwarning("Save Error", "There is no translated text to save.")
            return

        # Determine the output filename based on the input file if available
        if self.input_filepath:
            base, ext = os.path.splitext(self.input_filepath)
            output_filepath = f"{base}-translated{ext}"
        else:
            output_filepath = filedialog.asksaveasfilename(defaultextension=".txt",
                                                           filetypes=[("Text files", "*.txt")])
            if not output_filepath:
                return

        try:
            with open(output_filepath, 'w', encoding='utf-8') as file:
                file.write(english_text)
            messagebox.showinfo("Saved", f"Translation saved to:\n{output_filepath}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file: {e}")

if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()

