import tempfile
import unittest
from pathlib import Path

from PIL import Image

from image_converter import convert


class ImageConverterTests(unittest.TestCase):
    def test_round_trip_supports_all_requested_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            source = folder / "sample.png"
            Image.new("RGBA", (32, 24), (20, 120, 220, 255)).save(source)

            webp = convert(source, "webp", None, 90, False, False)[0]
            output_folder = folder / "converted"
            png = convert(webp, "png", output_folder, 90, False, False)[0]
            jpeg = convert(webp, "jpeg", output_folder, 90, False, False)[0]
            pdf = convert(webp, "pdf", output_folder, 90, False, False)[0]

            with Image.open(webp) as image:
                self.assertEqual(image.format, "WEBP")
            with Image.open(png) as image:
                self.assertEqual(image.format, "PNG")
            with Image.open(jpeg) as image:
                self.assertEqual(image.format, "JPEG")
            self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))

    def test_folder_conversion_uses_output_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            source_folder = folder / "source"
            output_folder = folder / "output"
            source_folder.mkdir()
            Image.new("RGB", (8, 8), "red").save(source_folder / "one.jpg")
            Image.new("RGB", (8, 8), "blue").save(source_folder / "two.png")

            results = convert(source_folder, "webp", output_folder, 90, False, False)

            self.assertEqual({path.name for path in results}, {"one.webp", "two.webp"})
            self.assertTrue(all(path.exists() for path in results))

    def test_maximum_size_preserves_aspect_ratio(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            source = folder / "wide.png"
            Image.new("RGB", (4000, 2000), "green").save(source)

            result = convert(source, "webp", folder / "output", 90, False, False, 1920, 1080)[0]

            with Image.open(result) as image:
                self.assertEqual(image.size, (1920, 960))


if __name__ == "__main__":
    unittest.main()