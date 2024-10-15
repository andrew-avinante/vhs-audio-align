# VHS Audio Auto Align

## Motivation
This script assists in aligning linear audio with TBC data, specifically addressing challenges encountered with [namazso's clockgen mod](https://github.com/namazso/cxadc-clockgen-mod). The original method of using a clock generator modification proved to be tedious and difficult for someone not well versed in hardware. Specifically, the provided documentation was lacking for the DomesdayDuplicator, and attempts to implement the modification were unsuccessful. To overcome these limitations, this script offers a software-based solution.

## Functionality
This script employs a binary search algorithm to determine the optimal sample rate for aligning audio with a reference video. It leverages `VhsDecodeAutoAudioAlign` and operates as follows:
- The script starts by running `VhsDecodeAutoAudioAlign` at an initial sample rate provided as input.
- It compares the duration of the processed audio to the duration of the reference video.
- Based on this comparison, the script adjusts the sample rate, increasing it if the audio is longer than the video and decreasing it if it's shorter.
- The process repeats, narrowing the search range until the closest matching sample rate is found.

## Requirements
- **ffmpeg-python**: This package is used to interact with FFmpeg within the Python script.
- **sox**: SoX is a command-line audio processing tool.
- **mono**: Mono is required for executing .NET applications, specifically `VhsDecodeAutoAudioAlign.exe`.
- **dotenv**: This package is used for loading environment variables.

## Running the Script

### 1. Environment Setup
- Ensure that all the necessary dependencies are installed.
    - `pip install -r requirements.txt`
- Set the path to `VhsDecodeAutoAudioAlign.exe` in the `.env` file using the variable `VHS_DECODE_AUTO_AUDIO_ALIGN_EXE`. `VhsDecodeAutoAudioAlign.exe` can be found [here](https://gitlab.com/wolfre/vhs-decode-auto-audio-align/-/releases).

### 2. Execution
Use the following command to run the script:

```bash
python script.py --output_path --hz --channels --bits 
```

### Arguments:
- **input_path** (required): Path to the input audio file.
- **tbc_json** (required): Path to the TBC JSON file.
- **reference_video_path** (required): Path to the audioless reference video file.
- **output_path** (optional): Path to the output audio file (default: `linear-aligned.wav`).
- **hz** (required): Initial sample rate in Hz.
- **channels** (required): Number of audio channels.
- **bits** (required): Bits per sample.

### Example:
```bash
python script.py input.wav tbc.json reference.mp4 --output_path aligned.wav --hz 48000 --channels 2 --bits 16
```