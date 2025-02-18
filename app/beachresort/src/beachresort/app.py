"""
translate a vtt file in a source language to target language and brung subtitles to given video
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import subprocess
import asyncio
import os

# Import the translation model libraries
from transformers import MarianMTModel, MarianTokenizer

class BeachResort(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title=self.formal_name)
        
        # UI Elements for file selection
        self.mp4_file_label = toga.Label("MP4 File: None", style=Pack(padding=5))
        self.vtt_file_label = toga.Label("VTT File: None", style=Pack(padding=5))
        
        # Buttons for file selection (using asynchronous callbacks)
        self.select_mp4_button = toga.Button("Select MP4", on_press=self.select_mp4, style=Pack(padding=5))
        self.select_vtt_button = toga.Button("Select VTT", on_press=self.select_vtt, style=Pack(padding=5))
        
        self.run_button = toga.Button("Translate & Burn Subtitles", on_press=self.async_run_process, style=Pack(padding=5))
        
        self.log_output = toga.MultilineTextInput(readonly=True, style=Pack(flex=1, padding=5))
        
        file_box = toga.Box(
            children=[
                toga.Box(children=[self.mp4_file_label, self.select_mp4_button], style=Pack(direction=ROW, padding=5)),
                toga.Box(children=[self.vtt_file_label, self.select_vtt_button], style=Pack(direction=ROW, padding=5))
            ],
            style=Pack(direction=COLUMN, padding=10)
        )
        
        main_box = toga.Box(
            children=[file_box, self.run_button, self.log_output],
            style=Pack(direction=COLUMN, padding=10)
        )
        
        self.main_window.content = main_box
        self.main_window.show()

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

    # --- File Dialog Methods using async ---
    async def async_select_mp4(self, widget):
        try:
            file_dialog = toga.OpenFileDialog(
                title="Select MP4 File",
                file_types=["mp4"]
            )
            # Use dialog.show() to present the dialog and await the result.
            file_path = await self.dialog(file_dialog)
            if file_path:
                self.mp4_file = file_path
                self.mp4_file_label.text = f"MP4 File: {os.path.basename(file_path)}"
                self.log(f"Selected MP4: {file_path}")
        except ValueError:
            self.label.text = "Open file (app) dialog was canceled"

    def select_mp4(self, widget):
        # Schedule the asynchronous file dialog method.
        asyncio.create_task(self.async_select_mp4(widget))

    async def async_select_vtt(self, widget):
        try: 
            file_dialog = toga.OpenFileDialog(
                title="Select VTT File",
                file_types=["vtt"]
            )
            file_path = await self.dialog(file_dialog)
            if file_path:
                self.vtt_file = file_path
                self.vtt_file_label.text = f"VTT File: {os.path.basename(file_path)}"
                self.log(f"Selected VTT: {file_path}")
        except ValueError:
            self.label.text = "Open file (app) dialog was canceled"

    def select_vtt(self, widget):
        asyncio.create_task(self.async_select_vtt(widget))

    async def async_run_process(self, widget):
        try:
            # First, prompt the user to choose an output file location using a save file dialog.
            save_dialog = toga.SaveFileDialog(
                title="Select Output File Location",
                file_types=["mp4"],
                suggested_filename=os.path.splitext(self.mp4_file)[0] + "-subtitled.mp4"
            )
            output_file = await self.dialog(save_dialog)
            if not output_file:
                self.log("Output file not selected; process canceled.")
                return
            self.output_file = output_file
            self.log(f"Selected output file: {self.output_file}")
        except ValueError:
            self.label.text = "Open file (app) dialog was canceled"

        # Determine SRT file name from the chosen output file.
        srt_file = os.path.splitext(self.output_file)[0] + "-translated.srt"
        
        # Ensure that both the input MP4 and VTT files have been selected.
        if not self.mp4_file or not self.vtt_file:
            self.log("Please select both an MP4 file and a VTT file.")
            return

        self.log("Starting the translation and burning process...")

        try:
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
            self.burn_subtitles(self.mp4_file, srt_file, self.output_file)
            self.log(f"Subtitled video saved as: {self.output_file}")
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

    def burn_subtitles(video_file, srt_file, output_file):
        # Determine the path to the bundled FFmpeg binary.
        # Assuming this file is in your source folder, the FFmpeg binary will be in:
        # ../Resources/ffmpeg_bin/ffmpeg
        current_dir = os.path.dirname(__file__)
        resources_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "Resources"))
        ffmpeg_path = os.path.join(resources_dir, "ffmpeg_bin", "ffmpeg")

        # Optional: Verify that the file exists and is executable.
        if not (os.path.exists(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK)):
            raise RuntimeError(f"Bundled FFmpeg binary not found or not executable: {ffmpeg_path}")

        # Build and run the FFmpeg command using the bundled binary.
        cmd = [
            ffmpeg_path,
            "-i", video_file,
            "-vf", f"subtitles={srt_file}",
            "-c:a", "copy",
            output_file
        ]
        print("Running FFmpeg command:", " ".join(cmd))
        subprocess.run(cmd, check=True)

def main():
    return BeachResort("BeachResort", "org.beeware.beachresort")

