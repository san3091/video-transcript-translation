"""
translate a vtt file in a source language to target language and brung subtitles to given video
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import subprocess
import os

# Import the translation model libraries
from transformers import MarianMTModel, MarianTokenizer

class BeachResort(toga.App):
    def startup(self):
        # Create the main window.
        self.main_window = toga.MainWindow(title=self.formal_name)
        
        # UI Elements for file selection
        self.mp4_file_label = toga.Label("MP4 File: None", style=Pack(padding=5))
        self.vtt_file_label = toga.Label("VTT File: None", style=Pack(padding=5))
        
        self.select_mp4_button = toga.Button("Select MP4", on_press=self.select_mp4, style=Pack(padding=5))
        self.select_vtt_button = toga.Button("Select VTT", on_press=self.select_vtt, style=Pack(padding=5))
        
        # Button to trigger the translation and burning process
        self.run_button = toga.Button("Translate & Burn Subtitles", on_press=self.run_process, style=Pack(padding=5))
        
        # Multiline text area for output/logs
        self.log_output = toga.MultilineTextInput(readonly=True, style=Pack(flex=1, padding=5))
        
        # Layout: arrange file selection in a box
        file_box = toga.Box(
            children=[
                toga.Box(children=[self.mp4_file_label, self.select_mp4_button], style=Pack(direction=ROW, padding=5)),
                toga.Box(children=[self.vtt_file_label, self.select_vtt_button], style=Pack(direction=ROW, padding=5))
            ],
            style=Pack(direction=COLUMN, padding=10)
        )
        
        # Main box layout
        main_box = toga.Box(
            children=[file_box, self.run_button, self.log_output],
            style=Pack(direction=COLUMN, padding=10)
        )
        
        self.main_window.content = main_box
        self.main_window.show()

        # Initialize file paths
        self.mp4_file = None
        self.vtt_file = None

        # Load the translation model (this may take some time)
        self.log("Loading translation model...")
        self.model_name = "Helsinki-NLP/opus-mt-es-en"
        self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
        self.model = MarianMTModel.from_pretrained(self.model_name)
        self.log("Translation model loaded.")

    def log(self, message):
        """Append a message to the log output."""
        self.log_output.value += message + "\n"

    def select_mp4(self, widget):
        """Opens a file dialog to select an MP4 file."""
        try:
            file_path = toga.FileDialog.open_file(
                title="Select MP4 File",
                file_types=["mp4"]
            )
            if file_path:
                self.mp4_file = file_path
                self.mp4_file_label.text = f"MP4 File: {os.path.basename(file_path)}"
                self.log(f"Selected MP4: {file_path}")
        except Exception as e:
            self.log(f"Error selecting MP4 file: {e}")

    def select_vtt(self, widget):
        """Opens a file dialog to select a VTT file."""
        try:
            file_path = toga.FileDialog.open_file(
                title="Select VTT File",
                file_types=["vtt"]
            )
            if file_path:
                self.vtt_file = file_path
                self.vtt_file_label.text = f"VTT File: {os.path.basename(file_path)}"
                self.log(f"Selected VTT: {file_path}")
        except Exception as e:
            self.log(f"Error selecting VTT file: {e}")

    def run_process(self, widget):
        """Runs the full process: parse, translate, write SRT, and burn subtitles."""
        if not self.mp4_file or not self.vtt_file:
            self.log("Please select both an MP4 file and a VTT file.")
            return

        self.log("Starting the translation and burning process...")

        try:
            # Determine output filenames
            srt_file = os.path.splitext(self.vtt_file)[0] + "-translated.srt"
            output_video = os.path.splitext(self.mp4_file)[0] + "_subtitled.mp4"
            
            # Parse the VTT file into subtitle blocks.
            blocks = self.parse_vtt_blocks(self.vtt_file)
            self.log("Parsed VTT file.")
            
            # Translate the subtitle blocks from Spanish to English.
            translated_blocks = self.translate_subtitle_blocks(blocks)
            self.log("Translated subtitle blocks.")
            
            # Write out the translated subtitles to an SRT file.
            self.write_srt(translated_blocks, srt_file)
            self.log(f"Wrote SRT file: {srt_file}")
            
            # Burn the subtitles into the video using FFmpeg.
            self.burn_subtitles(self.mp4_file, srt_file, output_video)
            self.log(f"Subtitled video saved as: {output_video}")
        except Exception as e:
            self.log(f"Error during process: {e}")

    def parse_vtt_blocks(self, vtt_file):
        """
        Reads a VTT file and returns a list of subtitle blocks.
        Each block is a dictionary with 'start', 'end', and 'text' keys.
        """
        with open(vtt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        blocks = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Skip headers or empty lines
            if line == "" or line.startswith("WEBVTT") or line.startswith("NOTE"):
                i += 1
                continue

            # Look for the timestamp line
            if "-->" in line:
                # Convert timestamp dots to commas (SRT requires commas)
                timestamp_line = line.replace('.', ',')
                parts = timestamp_line.split("-->")
                if len(parts) != 2:
                    i += 1
                    continue
                start = parts[0].strip()
                end = parts[1].strip()
                i += 1

                # Collect subtitle text lines until an empty line is encountered.
                text_lines = []
                while i < len(lines) and lines[i].strip() != "":
                    text_lines.append(lines[i].strip())
                    i += 1

                blocks.append({"start": start, "end": end, "text": "\n".join(text_lines)})
            else:
                i += 1

        return blocks

    def translate_subtitle_blocks(self, blocks):
        """
        Translates the text in each subtitle block from Spanish to English.
        """
        for block in blocks:
            original_text = block["text"]
            # Tokenize and translate the subtitle text.
            inputs = self.tokenizer([original_text], return_tensors="pt", padding=True, truncation=True)
            translated_tokens = self.model.generate(**inputs)
            translation = self.tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
            block["text"] = translation
        return blocks

    def write_srt(self, blocks, srt_file):
        """
        Writes a list of subtitle blocks to an SRT file.
        """
        with open(srt_file, 'w', encoding='utf-8') as f:
            for i, block in enumerate(blocks, start=1):
                f.write(f"{i}\n")
                f.write(f"{block['start']} --> {block['end']}\n")
                f.write(f"{block['text']}\n\n")

    def burn_subtitles(self, video_file, srt_file, output_file):
        """
        Calls FFmpeg to burn the SRT subtitles into the video.
        """
        cmd = [
            "ffmpeg",
            "-i", video_file,
            "-vf", f"subtitles={srt_file}",
            "-c:a", "copy",
            output_file
        ]
        self.log("Running FFmpeg to burn subtitles...")
        subprocess.run(cmd, check=True)

def main():
    return BeachResort("BeachResort", "org.beeware.beachresort")

