# Audio Converter Instructions

## Requirements
This application mainly relies on **FFmpeg** to perform audio conversions (e.g., MP3, OGG, FLAC). 

**IMPORTANT**: FFmpeg is NOT bundled with this executable by default to keep the file size small and avoid licensing issues.

### How to get FFmpeg working:
1.  **Download FFmpeg**:
    - Go to https://ffmpeg.org/download.html
    - Download a Windows build (e.g., from gyan.dev or BtbN).
    - Extract the zip file.
2.  **Locate ffmpeg.exe**:
    - Inside the extracted folder, look for the `bin` folder.
    - You should see `ffmpeg.exe` (and `ffprobe.exe`).
3.  **Place it next to the App**:
    - Copy `ffmpeg.exe` and `ffprobe.exe`.
    - Paste them into the SAME folder where you have `AudioConverter.exe`.

Once `ffmpeg.exe` is in the same folder as the application, the converter will work successfully.
