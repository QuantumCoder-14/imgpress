#!/usr/bin/env python3
import sys, unittest, io, tempfile, shutil
from contextlib import redirect_stdout
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import imgpress
from PIL import Image

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="imgpress-"))
        self.images = self.tmp / "images"
        self.images.mkdir()
    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
    def make(self, name, size=(1200, 800), colour=(120, 30, 200)):
        p = self.images / name
        Image.new("RGB", size, colour).save(p)
        return p

class TestPlan(Base):
    def test_resize_plan(self):
        p = self.make("wide.png")
        out, size = imgpress.plan(p, max_width=600)
        self.assertEqual(size[0], 600)
        self.assertEqual(size[1], 400)
        self.assertEqual(out.parent.name, "compressed")

    def test_no_upscale(self):
        p = self.make("small.png", size=(300, 200))
        _, size = imgpress.plan(p, max_width=1600)
        self.assertEqual(size, (300, 200))

    def test_format_override(self):
        p = self.make("a.png")
        out, _ = imgpress.plan(p, target_format="webp")
        self.assertEqual(out.suffix, ".webp")

    def test_jpeg_alias(self):
        p = self.make("a.png")
        out, _ = imgpress.plan(p, target_format="jpeg")
        self.assertEqual(out.suffix, ".jpg")

class TestProcess(Base):
    def test_writes_smaller_file(self):
        p = self.make("a.png", size=(1400, 900))
        out, size = imgpress.plan(p, max_width=500, target_format="jpg")
        written = imgpress.process(p, out, size, quality=70)
        self.assertTrue(out.exists())
        self.assertLess(written, p.stat().st_size)
        with Image.open(out) as img:
            self.assertEqual(img.size, (500, 321))

    def test_original_untouched(self):
        p = self.make("a.png", size=(900, 900))
        before = p.read_bytes()
        out, size = imgpress.plan(p, max_width=300, target_format="jpg")
        imgpress.process(p, out, size)
        self.assertEqual(p.read_bytes(), before)

    def test_png_to_webp(self):
        p = self.make("a.png")
        out, size = imgpress.plan(p, max_width=400, target_format="webp")
        imgpress.process(p, out, size)
        with Image.open(out) as img:
            self.assertEqual(img.format, "WEBP")

class TestCli(Base):
    def test_dry_run_writes_nothing(self):
        self.make("a.png")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = imgpress.main(["--path", str(self.images)])
        self.assertEqual(code, 0)
        self.assertFalse((self.images / "compressed").exists())
        self.assertIn("DRY RUN", buf.getvalue())

    def test_apply_writes(self):
        self.make("a.png")
        with redirect_stdout(io.StringIO()):
            code = imgpress.main(["--path", str(self.images), "--apply", "--max-width", "400"])
        self.assertEqual(code, 0)
        self.assertTrue((self.images / "compressed").exists())

    def test_bad_quality(self):
        self.make("a.png")
        self.assertEqual(imgpress.main(["--path", str(self.images), "--quality", "500"]), 2)

    def test_missing_folder(self):
        self.assertEqual(imgpress.main(["--path", str(self.tmp / "nope")]), 2)

    def test_no_images(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(imgpress.main(["--path", str(self.images)]), 0)
        self.assertIn("Nothing to do", buf.getvalue())

if __name__ == "__main__":
    unittest.main(verbosity=1)
