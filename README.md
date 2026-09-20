# Website Image Converter

A small Python command-line tool for converting JPEG, PNG, and WebP images. It is designed for website assets: WebP output defaults to high quality while keeping files smaller than many PNG/JPEG originals, and transparent images are composited onto white when converting to JPEG or PDF.

## Setup

```powershell
python -m pip install -r requirements.txt
```

## GUI

Launch the desktop converter with no arguments:

```powershell
python image_converter.py
```

The GUI includes these website-focused maximum-size presets:

| Use | Maximum size | Recommended format | Typical file size |
| --- | --- | --- | --- |
| Website main image | 1920 x 1080 | WebP/JPEG | 150-400 KB |
| Large / hero image | 2560 x 1440 | WebP | 250-600 KB |
| Thumbnail | 600 x 600 max | WebP | 20-80 KB |
| Mobile image | 1080 x 1080 max | WebP | 80-250 KB |

Images are scaled down proportionally and are never enlarged. File-size ranges are typical targets, not guarantees: the final size depends on image detail, colors, transparency, and quality setting.

## Command line usage

Convert one image to WebP:

```powershell
python image_converter.py photo.png --to webp
```

Convert an entire folder:

```powershell
python image_converter.py .\images --to webp --output .\webp --recursive
```

Convert WebP back to another format:

```powershell
python image_converter.py photo.webp --to png
python image_converter.py photo.webp --to jpeg --quality 92
python image_converter.py photo.webp --to pdf
```

The supported targets are `webp`, `png`, `jpeg`, and `pdf`. Existing output files are protected by default; add `--overwrite` to replace them. For WebP and JPEG, `--quality` accepts values from 1 to 100 and defaults to 90.