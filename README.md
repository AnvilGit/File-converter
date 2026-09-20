# Website Image Converter

A simple desktop image converter for preparing fast, high-quality website images. Convert PNG, JPEG, and WebP files to WebP, JPEG, PNG, or PDF while resizing images to practical website dimensions.

## Features

- Desktop GUI built with Python and Tkinter
- Convert PNG, JPEG, and WebP images
- Export to WebP, JPEG, PNG, or PDF
- Resize proportionally to a maximum width and height
- Never enlarges smaller images
- WebP and JPEG quality control from 1 to 100
- Website-focused size presets
- Optional recursive folder conversion from the command line
- Overwrite protection to prevent accidental file replacement
- Transparent images are placed on a white background for JPEG and PDF output

## Requirements

- Python 3.10 or newer
- Pillow
- Tkinter, included with standard Python installations on Windows and macOS

## Installation

Clone the repository, open the project folder, and install the dependency:

```powershell
python -m pip install -r requirements.txt
```

## Desktop GUI

Start the application without command-line arguments:

```powershell
python image_converter.py
```

### GUI workflow

1. Click **Browse...** next to **Source** and select a PNG, JPEG, or WebP image.
2. Select an **Output folder**.
3. Choose an output **Format**: WebP, JPEG, PNG, or PDF.
4. Choose a **Maximum size** preset or select **Custom size**.
5. Adjust quality for WebP or JPEG if needed.
6. Optionally enable overwrite protection settings.
7. Click **Convert images**.

The image keeps its original aspect ratio. For example, a 4000 x 2000 image with a 1920 x 1080 maximum becomes 1920 x 960, rather than being stretched or distorted.

## Website size presets

| Use case | Maximum size | Recommended format | Typical file size |
| --- | --- | --- | --- |
| Website main image | 1920 x 1080 | WebP or JPEG | 150-400 KB |
| Large / hero image | 2560 x 1440 | WebP | 250-600 KB |
| Thumbnail | 600 x 600 max | WebP | 20-80 KB |
| Mobile image | 1080 x 1080 max | WebP | 80-250 KB |

These file-size ranges are guidelines, not guarantees. Actual output size depends on image detail, colors, transparency, dimensions, and quality settings.

## Command-line usage

The command-line interface remains available for automation and batch conversion.

Convert one image to WebP:

```powershell
python image_converter.py photo.png --to webp
```

Convert an image to WebP with a chosen quality:

```powershell
python image_converter.py photo.png --to webp --output .\webp --quality 90
```

Convert every supported image in a folder:

```powershell
python image_converter.py .\images --to webp --output .\webp --recursive
```

Convert WebP back to another format:

```powershell
python image_converter.py photo.webp --to png
python image_converter.py photo.webp --to jpeg --quality 92
python image_converter.py photo.webp --to pdf
```

Run `python image_converter.py --help` to see all available options. Existing output files are protected by default; add `--overwrite` to replace them. The CLI supports optional `--quality`, `--recursive`, and `--overwrite` flags.

## Project files

| File | Purpose |
| --- | --- |
| `image_converter.py` | GUI, conversion engine, and command-line interface |
| `test_image_converter.py` | Automated conversion and resize tests |
| `requirements.txt` | Python dependency list |