import sys
import os
import subprocess
from transformers import MarianMTModel, MarianTokenizer

def parse_vtt_blocks(vtt_file):
    """
    Reads a VTT file and returns a list of subtitle blocks.
    Each block is a dict with keys: "start", "end", and "text".
    The timestamps are converted from VTT (with '.') to SRT (with ',').
    """
    with open(vtt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip header, NOTE blocks, or empty lines
        if line == "" or line.startswith("WEBVTT") or line.startswith("NOTE"):
            i += 1
            continue

        # Look for the timestamp line
        if "-->" in line:
            # Replace dot with comma for milliseconds (SRT requires comma)
            timestamp_line = line.replace('.', ',')
            # Split start and end times (expected format: "00:00:01,000 --> 00:00:04,000")
            parts = timestamp_line.split("-->")
            if len(parts) != 2:
                i += 1
                continue
            start = parts[0].strip()
            end = parts[1].strip()
            i += 1

            # Collect subtitle text lines until an empty line
            text_lines = []
            while i < len(lines) and lines[i].strip() != "":
                text_lines.append(lines[i].strip())
                i += 1
            block = {"start": start, "end": end, "text": "\n".join(text_lines)}
            blocks.append(block)
        else:
            i += 1

    return blocks

def translate_subtitle_blocks(blocks, tokenizer, model):
    """
    Translates the text in each subtitle block from Spanish to English.
    """
    for block in blocks:
        original_text = block["text"]
        # Tokenize and translate. For long texts you might consider splitting into smaller chunks.
        inputs = tokenizer([original_text], return_tensors="pt", padding=True, truncation=True)
        translated_tokens = model.generate(**inputs)
        translation = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
        block["text"] = translation
    return blocks

def write_srt(blocks, srt_file):
    """
    Writes out a list of subtitle blocks to an SRT file.
    """
    with open(srt_file, 'w', encoding='utf-8') as f:
        for i, block in enumerate(blocks, start=1):
            f.write(f"{i}\n")
            f.write(f"{block['start']} --> {block['end']}\n")
            f.write(f"{block['text']}\n\n")

def burn_subtitles(video_file, srt_file, output_file):
    """
    Uses FFmpeg to burn subtitles (SRT) into the video.
    """
    # FFmpeg command: input video, burn subtitles filter, copy audio, and output new video.
    cmd = [
        "ffmpeg",
        "-i", video_file,
        "-vf", f"subtitles={srt_file}",
        "-c:a", "copy",
        output_file
    ]
    print("Running FFmpeg command:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

def main():
    if len(sys.argv) != 3:
        print("Usage: python translate_and_burn.py video.mp4 subtitles.vtt")
        sys.exit(1)

    video_file = sys.argv[1]
    vtt_file = sys.argv[2]

    # Create filenames for the output SRT and video file.
    base_vtt, _ = os.path.splitext(vtt_file)
    srt_file = f"{base_vtt}-translated.srt"
    base_video, _ = os.path.splitext(video_file)
    output_video = f"{base_video}_subtitled.mp4"

    print("Parsing VTT file...")
    blocks = parse_vtt_blocks(vtt_file)
    if not blocks:
        print("No subtitle blocks found in the VTT file.")
        sys.exit(1)

    print("Loading translation model (this may take a while)...")
    model_name = "Helsinki-NLP/opus-mt-es-en"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)

    print("Translating subtitle blocks from Spanish to English...")
    translated_blocks = translate_subtitle_blocks(blocks, tokenizer, model)

    print("Writing translated subtitles to SRT file...")
    write_srt(translated_blocks, srt_file)
    print(f"SRT file created: {srt_file}")

    print("Burning subtitles into video...")
    burn_subtitles(video_file, srt_file, output_video)
    print(f"Subtitled video saved as: {output_video}")

if __name__ == "__main__":
    main()

