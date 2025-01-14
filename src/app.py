"""
VHS Audio Auto Align Script

This script finds the closest Hz that will allow for seamless audio alignment without the need for hardware clock mods.

Dependencies:
- ffmpeg-python: For media file handling and probing.
- sox: For audio processing.
- mono: For executing .NET applications.
- dotenv: For loading environment variables.

Usage:
    python script.py <input_path> <tbc_json> <reference_video_path> --output_path <output_path> --hz <sample_rate> --channels <num_channels> --bits <bits_per_sample>
"""

from argparse import ArgumentParser
import subprocess
import ffmpeg  # Ensure you have the ffmpeg-python package installed
import math
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the executable path from the environment variable
VHS_DECODE_AUTO_AUDIO_ALIGN_EXE = os.getenv(
    'VHS_DECODE_AUTO_AUDIO_ALIGN_EXE', 'VhsDecodeAutoAudioAlign.exe')


def create_argument_parser() -> ArgumentParser:
    """
    Creates and returns an ArgumentParser object to handle command line arguments.

    Returns:
        ArgumentParser: The argument parser configured with required and optional arguments.
    """
    parser = ArgumentParser(description='VHS Audio Auto Align')

    # Required input path argument
    parser.add_argument(
        'input_path',
        type=str,
        help='Path to the input audio file (required)'
    )

    # Required TBC argument
    parser.add_argument(
        'tbc_json',
        type=str,
        help='Path to the TBC JSON file (required)'
    )

    # Required reference video path argument
    parser.add_argument(
        'reference_video_path',
        type=str,
        help='Path to the reference video file (required)'
    )

    # Optional output path argument with default
    parser.add_argument(
        '--output_path',
        type=str,
        default='linear-aligned.wav',
        help='Path to the output audio file (default: linear-aligned.wav)'
    )

    # Required sample rate argument
    parser.add_argument(
        '--hz',
        type=int,
        required=True,
        help='Sample rate in Hz (required)'
    )

    # Required channels argument
    parser.add_argument(
        '--channels',
        type=int,
        required=True,
        help='Number of audio channels (required)'
    )

    # Required bits argument
    parser.add_argument(
        '--bits',
        type=int,
        required=True,
        help='Bits per sample (required)'
    )

    return parser


def get_media_duration(path: str) -> float:
    """
    Retrieves the duration of a media file.

    Args:
        path (str): The path to the media file.

    Returns:
        float: The duration of the media file in seconds.
    """
    probe = ffmpeg.probe(path)
    return float(probe['format']['duration'])


def process_audio(input: str, tbc_path: str, output: str, rate_hz: int, channels: int, bits_per_sample: int) -> float:
    """
    Processes the audio to align it with the reference video using SoX and the VhsDecodeAutoAudioAlign executable.

    Args:
        input (str): Path to the input audio file.
        tbc_path (str): Path to the TBC JSON file.
        output (str): Path to the output audio file.
        rate_hz (int): Sample rate in Hz.
        channels (int): Number of audio channels.
        bits_per_sample (int): Bits per sample.

    Returns:
        float: The duration of the processed audio in seconds.
    """
    print(f"Processing audio at {rate_hz} Hz")
    sample_size_bytes = (bits_per_sample // 8) * channels

    try:
        # First command: sox processing to convert input audio to raw format
        sox_cmd_1 = [
            'sox', '-D',
            input,
            '-t', 'raw',
            '-b', str(bits_per_sample),
            '-c', str(channels),
            '-L',
            '-e', 'unsigned-integer',
            '-'
        ]
        sox_process = subprocess.Popen(sox_cmd_1, stdout=subprocess.PIPE)

        # Second command: aligning audio using mono and the VhsDecodeAutoAudioAlign executable
        mono_cmd = [
            'mono', VHS_DECODE_AUTO_AUDIO_ALIGN_EXE,
            'stream-align',
            # Sample size in bytes for the alignment process
            '--sample-size-bytes', str(sample_size_bytes),
            # Sample rate in Hz for the alignment process
            '--stream-sample-rate-hz', str(rate_hz),
            '--json', tbc_path
        ]
        mono_process = subprocess.Popen(
            mono_cmd, stdin=sox_process.stdout, stdout=subprocess.PIPE)
        # Allow sox_process to receive a SIGPIPE if mono_process exits
        sox_process.stdout.close()

        # Third command: final sox processing to output the aligned audio
        sox_cmd_2 = [
            'sox', '-D',
            '-t', 'raw',
            '-r', str(rate_hz),
            '-b', str(bits_per_sample),
            '-c', str(channels),
            '-L',
            '-e', 'unsigned-integer',
            '-',
            output
        ]
        subprocess.run(sox_cmd_2, stdin=mono_process.stdout)
        mono_process.stdout.close()  # Allow mono_process to receive a SIGPIPE if sox exits

        # Use FFmpeg to probe the output file and get the duration
        return get_media_duration(output)

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing the command: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def search(input_path: str,
           reference_video_path: str,
           tbc: str,
           output_path: str,
           hz: int,
           channels: int,
           bits: int) -> int:
    """
    Searches for the optimal sample rate to align the audio with the reference video.

    Args:
        input_path (str): Path to the input audio file.
        reference_video_path (str): Path to the reference video file.
        tbc (str): Path to the TBC JSON file.
        output_path (str): Path to the output audio file.
        hz (int): Initial sample rate in Hz.
        channels (int): Number of audio channels.
        bits (int): Bits per sample.

    Returns:
        tuple: A tuple containing the closest sample rate and the distance from the reference duration.
    """
    ref_duration = get_media_duration(reference_video_path)
    base_duration = process_audio(
        input_path, tbc, output_path, hz, channels, bits)

    # Calculate the adjusted sample rate based on the reference duration
    actual_hz = int(ref_duration * hz / base_duration)

    actual_duration = process_audio(
        input_path, tbc, output_path, actual_hz, channels, bits)

    return actual_hz, abs(ref_duration - actual_duration)


def main():
    """
    Main function to execute the script. Parses arguments, processes audio, and finds the optimal sample rate.
    """
    args = create_argument_parser().parse_args()

    # Access the arguments
    input_path = args.input_path
    tbc = args.tbc_json
    reference_video_path = args.reference_video_path
    output_path = args.output_path
    hz = args.hz
    channels = args.channels
    bits = args.bits

    t0 = time.time()
    actual_hz, actual_duration = search(
        input_path, reference_video_path, tbc, output_path, hz, channels, bits)
    
    t1 = time.time()

    print(f"Found a solution in {t1-t0} seconds: {actual_hz} Hz with a {actual_duration} second(s) shift")


if __name__ == "__main__":
    main()
