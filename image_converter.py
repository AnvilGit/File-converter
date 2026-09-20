"""Convert common website image formats with Pillow.

Examples:
    python image_converter.py photo.png --to webp
    python image_converter.py input_folder --to webp --output output_folder
    python image_converter.py image.webp --to pdf
"""

from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path
from typing import Iterable
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, UnidentifiedImageError


SUPPORTED_INPUTS = {".jpeg", ".jpg", ".png", ".webp"}
OUTPUT_EXTENSIONS = {"webp": ".webp", "png": ".png", "jpeg": ".jpg", "pdf": ".pdf"}
SIZE_PRESETS = {
    "Website main image | 1920 x 1080 | 150-400 KB": (1920, 1080),
    "Large / hero image | 2560 x 1440 | 250-600 KB": (2560, 1440),
    "Thumbnail | 600 x 600 max | 20-80 KB": (600, 600),
    "Mobile image | 1080 x 1080 max | 80-250 KB": (1080, 1080),
    "Custom size": None,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert JPEG, PNG, and WebP images, including PDF export."
    )
    parser.add_argument("source", type=Path, help="An image file or a folder of images.")
    parser.add_argument(
        "--to",
        choices=sorted(OUTPUT_EXTENSIONS),
        required=True,
        help="Target format: webp, png, jpeg, or pdf.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for one source, or output folder for a folder source.",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=90,
        help="WebP/JPEG quality from 1 to 100 (default: 90).",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search subfolders when the source is a folder.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace files that already exist.",
    )
    return parser


def validate_quality(quality: int) -> None:
    if not 1 <= quality <= 100:
        raise ValueError("quality must be between 1 and 100")


def find_sources(source: Path, recursive: bool) -> Iterable[Path]:
    if source.is_file():
        if source.suffix.lower() not in SUPPORTED_INPUTS:
            raise ValueError("source must be a JPEG, PNG, or WebP image")
        return [source]
    if source.is_dir():
        pattern = "**/*" if recursive else "*"
        return sorted(
            path
            for path in source.glob(pattern)
            if path.is_file() and path.suffix.lower() in SUPPORTED_INPUTS
        )
    raise FileNotFoundError(f"source does not exist: {source}")


def output_path(source: Path, target: str, destination: Path | None, multiple: bool) -> Path:
    extension = OUTPUT_EXTENSIONS[target]
    if not multiple and destination is not None and destination.suffix:
        return destination
    folder = destination if destination is not None else source.parent
    return folder / f"{source.stem}{extension}"


def resize_to_fit(image: Image.Image, max_width: int | None, max_height: int | None) -> Image.Image:
    if max_width is None and max_height is None:
        return image
    if (max_width is not None and max_width < 1) or (max_height is not None and max_height < 1):
        raise ValueError("maximum width and height must be positive")
    resized = image.copy()
    resized.thumbnail((max_width or image.width, max_height or image.height), Image.Resampling.LANCZOS)
    return resized


def prepare_for_format(image: Image.Image, target: str) -> Image.Image:
    if target in {"jpeg", "pdf"}:
        if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
            background = Image.new("RGB", image.size, "white")
            alpha = image.convert("RGBA").getchannel("A")
            background.paste(image.convert("RGBA"), mask=alpha)
            return background
        return image.convert("RGB")
    if target == "png":
        return image.copy()
    return image.convert("RGBA") if image.mode in {"P", "LA"} else image


def convert_image(
    source: Path,
    destination: Path,
    target: str,
    quality: int,
    max_width: int | None = None,
    max_height: int | None = None,
) -> None:
    try:
        with Image.open(source) as image:
            resized = resize_to_fit(image, max_width, max_height)
            converted = prepare_for_format(resized, target)
            destination.parent.mkdir(parents=True, exist_ok=True)
            save_kwargs: dict[str, object] = {}
            if target == "webp":
                save_kwargs = {"format": "WEBP", "quality": quality, "method": 6}
            elif target == "jpeg":
                save_kwargs = {"format": "JPEG", "quality": quality, "optimize": True}
            elif target == "png":
                save_kwargs = {"format": "PNG", "optimize": True}
            else:
                save_kwargs = {"format": "PDF", "resolution": 150.0}
            converted.save(destination, **save_kwargs)
            if converted is not resized:
                converted.close()
            if resized is not image:
                resized.close()
    except UnidentifiedImageError as error:
        raise ValueError(f"could not read image: {source}") from error


def convert(
    source: Path,
    target: str,
    destination: Path | None,
    quality: int,
    recursive: bool,
    overwrite: bool,
    max_width: int | None = None,
    max_height: int | None = None,
) -> list[Path]:
    validate_quality(quality)
    sources = list(find_sources(source, recursive))
    if not sources:
        raise ValueError(f"no supported images found in: {source}")

    multiple = len(sources) > 1
    results: list[Path] = []
    for source_path in sources:
        target_path = output_path(source_path, target, destination, multiple)
        if target_path.exists() and not overwrite:
            raise FileExistsError(f"output exists (use --overwrite): {target_path}")
        convert_image(source_path, target_path, target, quality, max_width, max_height)
        results.append(target_path)
    return results


class ConverterWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Web Image Converter")
        self.root.geometry("760x650")
        self.root.minsize(680, 570)
        self.root.configure(bg="#f4f1ea")
        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.format_var = tk.StringVar(value="webp")
        self.preset_var = tk.StringVar(value=next(iter(SIZE_PRESETS)))
        self.width_var = tk.StringVar(value="1920")
        self.height_var = tk.StringVar(value="1080")
        self.quality_var = tk.IntVar(value=90)
        self.recursive_var = tk.BooleanVar(value=False)
        self.overwrite_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="Choose an image or folder to begin.")
        self._build()
        self._update_preset()

    def _build(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f1ea")
        style.configure("Card.TFrame", background="#fffdf8")
        style.configure("TLabel", background="#f4f1ea", foreground="#263238", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#f4f1ea", foreground="#173f43", font=("Segoe UI", 26, "bold"))
        style.configure("Subtitle.TLabel", background="#f4f1ea", foreground="#607276", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background="#fffdf8", foreground="#263238", font=("Segoe UI", 10))
        style.configure("Section.TLabel", background="#fffdf8", foreground="#173f43", font=("Segoe UI", 12, "bold"))
        style.configure("Accent.TButton", background="#e06b45", foreground="white", font=("Segoe UI", 11, "bold"), padding=(18, 10))
        style.map("Accent.TButton", background=[("active", "#c95432")])
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=5)

        outer = ttk.Frame(self.root, padding=(30, 24, 30, 20))
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Web Image Converter", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Shrink website images without giving up the detail that matters.", style="Subtitle.TLabel").pack(anchor="w", pady=(2, 18))

        card = ttk.Frame(outer, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True)
        self._source_row(card, "Source", self.source_var, self.choose_source)
        self._source_row(card, "Output folder", self.output_var, self.choose_output)

        ttk.Label(card, text="Conversion", style="Section.TLabel").grid(row=2, column=0, columnspan=3, sticky="w", pady=(20, 10))
        ttk.Label(card, text="Format", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=5)
        format_box = ttk.Combobox(card, textvariable=self.format_var, values=("webp", "jpeg", "png", "pdf"), state="readonly", width=18)
        format_box.grid(row=3, column=1, sticky="w", pady=5)
        format_box.bind("<<ComboboxSelected>>", lambda _event: self._update_quality_state())
        ttk.Label(card, text="Quality", style="Card.TLabel").grid(row=3, column=2, sticky="e", padx=(20, 8))
        self.quality_scale = ttk.Scale(card, from_=1, to=100, variable=self.quality_var, orient="horizontal", length=130)
        self.quality_scale.grid(row=3, column=3, sticky="ew", pady=5)
        self.quality_label = ttk.Label(card, text="90", style="Card.TLabel", width=4)
        self.quality_label.grid(row=3, column=4, sticky="w")
        self.quality_scale.configure(command=lambda value: self.quality_label.configure(text=str(round(float(value)))))

        ttk.Label(card, text="Maximum size", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=5)
        preset_box = ttk.Combobox(card, textvariable=self.preset_var, values=list(SIZE_PRESETS), state="readonly", width=43)
        preset_box.grid(row=4, column=1, columnspan=4, sticky="ew", pady=5)
        preset_box.bind("<<ComboboxSelected>>", lambda _event: self._update_preset())
        ttk.Label(card, text="Width", style="Card.TLabel").grid(row=5, column=0, sticky="w", pady=5)
        self.width_entry = ttk.Entry(card, textvariable=self.width_var, width=10)
        self.width_entry.grid(row=5, column=1, sticky="w", pady=5)
        ttk.Label(card, text="Height", style="Card.TLabel").grid(row=5, column=2, sticky="e", padx=(20, 8), pady=5)
        self.height_entry = ttk.Entry(card, textvariable=self.height_var, width=10)
        self.height_entry.grid(row=5, column=3, sticky="w", pady=5)
        ttk.Label(card, text="Images are scaled down proportionally; small images are not enlarged.", style="Card.TLabel").grid(row=6, column=1, columnspan=4, sticky="w", pady=(0, 8))

        ttk.Label(card, text="Typical output size", style="Section.TLabel").grid(row=7, column=0, columnspan=5, sticky="w", pady=(18, 6))
        ttk.Label(card, text="Website main image: 150-400 KB  |  Hero: 250-600 KB  |  Thumbnail: 20-80 KB  |  Mobile: 80-250 KB", style="Card.TLabel", wraplength=650).grid(row=8, column=0, columnspan=5, sticky="w")

        options = ttk.Frame(card, style="Card.TFrame")
        options.grid(row=9, column=0, columnspan=5, sticky="w", pady=(18, 8))
        ttk.Checkbutton(options, text="Include subfolders", variable=self.recursive_var).pack(side="left", padx=(0, 18))
        ttk.Checkbutton(options, text="Overwrite existing files", variable=self.overwrite_var).pack(side="left")
        self.convert_button = ttk.Button(card, text="Convert images", style="Accent.TButton", command=self.start_conversion)
        self.convert_button.grid(row=10, column=0, columnspan=5, sticky="ew", pady=(15, 8))
        ttk.Label(card, textvariable=self.status_var, style="Card.TLabel", wraplength=650).grid(row=11, column=0, columnspan=5, sticky="w")
        card.columnconfigure(1, weight=1)
        card.columnconfigure(3, weight=1)

    def _source_row(self, parent: ttk.Frame, label: str, variable: tk.StringVar, command: object) -> None:
        row = 0 if label == "Source" else 1
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, columnspan=3, sticky="ew", pady=5, padx=(0, 10))
        ttk.Button(parent, text="Browse...", command=command).grid(row=row, column=4, sticky="e", pady=5)

    def choose_source(self) -> None:
        selected = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")])
        if selected:
            self.source_var.set(selected)
            if not self.output_var.get():
                self.output_var.set(str(Path(selected).parent))

    def choose_output(self) -> None:
        selected = filedialog.askdirectory()
        if selected:
            self.output_var.set(selected)

    def _update_preset(self) -> None:
        size = SIZE_PRESETS.get(self.preset_var.get())
        if size:
            self.width_var.set(str(size[0]))
            self.height_var.set(str(size[1]))
        self.width_entry.configure(state="normal" if size is None else "disabled")
        self.height_entry.configure(state="normal" if size is None else "disabled")

    def _update_quality_state(self) -> None:
        state = "disabled" if self.format_var.get() in {"png", "pdf"} else "normal"
        self.quality_scale.configure(state=state)

    def start_conversion(self) -> None:
        try:
            source = Path(self.source_var.get().strip())
            output = Path(self.output_var.get().strip()) if self.output_var.get().strip() else None
            max_width = int(self.width_var.get()) if self.width_var.get().strip() else None
            max_height = int(self.height_var.get()) if self.height_var.get().strip() else None
            if max_width is None or max_height is None:
                raise ValueError("enter both a maximum width and height")
            validate_quality(int(self.quality_var.get()))
        except ValueError as error:
            messagebox.showerror("Check the settings", str(error))
            return
        self.convert_button.configure(state="disabled")
        self.status_var.set("Converting... your images are being prepared.")
        threading.Thread(target=self._convert_in_background, args=(source, output, max_width, max_height), daemon=True).start()

    def _convert_in_background(self, source: Path, output: Path | None, max_width: int, max_height: int) -> None:
        try:
            results = convert(source, self.format_var.get(), output, int(self.quality_var.get()), self.recursive_var.get(), self.overwrite_var.get(), max_width, max_height)
            self.root.after(0, lambda: self._conversion_finished(results))
        except (FileExistsError, FileNotFoundError, ValueError) as error:
            self.root.after(0, lambda: self._conversion_failed(str(error)))

    def _conversion_finished(self, results: list[Path]) -> None:
        self.convert_button.configure(state="normal")
        self.status_var.set(f"Done. Created {len(results)} file(s) in {results[0].parent}.")
        messagebox.showinfo("Conversion complete", f"Created {len(results)} file(s).")

    def _conversion_failed(self, error: str) -> None:
        self.convert_button.configure(state="normal")
        self.status_var.set("Conversion stopped. Check the source and output settings.")
        messagebox.showerror("Conversion failed", error)


def launch_gui() -> None:
    root = tk.Tk()
    ConverterWindow(root)
    root.mainloop()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        results = convert(
            args.source,
            args.to,
            args.output,
            args.quality,
            args.recursive,
            args.overwrite,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        parser.error(str(error))
    for result in results:
        print(f"Created: {result}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 1:
        launch_gui()
    else:
        raise SystemExit(main())