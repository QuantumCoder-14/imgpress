#!/usr/bin/env python3
"""
imgpress - shrink images before you upload them somewhere with a size limit.

Usage:
    python imgpress.py                      dry run on ./images, shows what it would save
    python imgpress.py --path photos --apply
    python imgpress.py --max-width 1600 --quality 80 --apply
    python imgpress.py --format webp --apply

Originals are never modified. Output goes to <path>/compressed/.

Requires Pillow:  pip install pillow
"""

import argparse
import os
import sys
from pathlib import Path

APP = "imgpress"
VERSION = "1.0"
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


def human(size):
    size = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def find_images(root):
    root = Path(root)
    return sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() in EXTS)


def plan(image_path, max_width=None, quality=82, target_format=None):
    """
    Work out the output path and the size the result should have.
    Returns (out_path, (new_width, new_height)).
    """
    path = Path(image_path)
    with Image.open(path) as img:
        width, height = img.size
    if max_width and width > max_width:
        scale = max_width / width
        size = (max_width, max(1, round(height * scale)))
    else:
        size = (width, height)

    fmt = (target_format or path.suffix.lstrip(".")).lower()
    if fmt == "jpeg":
        fmt = "jpg"
    return path.parent / "compressed" / f"{path.stem}.{fmt}", size


def process(image_path, out_path, size, quality=82):
    """Write the compressed copy. Returns the new file size in bytes."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as img:
        img = img.convert("RGB") if out_path.suffix.lower() in (".jpg", ".webp") else img
        if tuple(img.size) != tuple(size):
            img = img.resize(size, Image.LANCZOS)
        fmt = out_path.suffix.lstrip(".").lower()
        if fmt == "jpg":
            img.save(out_path, "JPEG", quality=quality, optimize=True, progressive=True)
        elif fmt == "webp":
            img.save(out_path, "WEBP", quality=quality, method=6)
        elif fmt == "png":
            img.save(out_path, "PNG", optimize=True)
        else:
            img.save(out_path, fmt.upper(), quality=quality)
    return out_path.stat().st_size


def main(argv=None):
    p = argparse.ArgumentParser(prog=APP, description="Shrink images into a compressed/ folder.")
    p.add_argument("--path", default="images", help="folder of images (default: ./images)")
    p.add_argument("--apply", action="store_true", help="write the files (default is a dry run)")
    p.add_argument("--max-width", type=int, default=None, help="resize anything wider than this")
    p.add_argument("--quality", type=int, default=82, help="JPEG/WebP quality 1-95 (default 82)")
    p.add_argument("--format", default=None, choices=["jpg", "jpeg", "png", "webp"],
                   help="convert to this format (default: keep each file's format)")
    p.add_argument("--version", action="version", version=f"{APP} {VERSION}")
    args = p.parse_args(argv)

    if Image is None:
        print(f"{APP}: Pillow is required.  pip install pillow", file=sys.stderr)
        return 2
    if not 1 <= args.quality <= 95:
        print(f"{APP}: --quality must be between 1 and 95", file=sys.stderr)
        return 2

    root = Path(os.path.expanduser(args.path))
    if not root.is_dir():
        print(f"{APP}: no such folder: {root}", file=sys.stderr)
        return 2

    images = find_images(root)
    print(f"\n  {APP} {VERSION} - {root}  ({len(images)} image(s))"
          f"{'' if args.apply else '  DRY RUN, nothing will be written'}\n")
    if not images:
        print("  Nothing to do.\n")
        return 0

    before = after = 0
    rows = []
    for image_path in images:
        try:
            out_path, size = plan(image_path, args.max_width, args.quality, args.format)
            original = image_path.stat().st_size
            before += original
            if args.apply:
                written = process(image_path, out_path, size, args.quality)
                after += written
                rows.append((image_path.name, original, written, size))
            else:
                rows.append((image_path.name, original, None, size))
        except Exception as exc:
            print(f"  skipped {image_path.name}: {exc}")

    for name, original, written, size in rows:
        dims = f"{size[0]}x{size[1]}"
        if written is None:
            print(f"  {name:34} {human(original):>9}  ->  {dims}")
        else:
            saved = original - written
            pct = (saved / original * 100) if original else 0
            print(f"  {name:34} {human(original):>9}  ->  {human(written):>9}  "
                  f"({pct:.0f}% smaller, {dims})")

    if args.apply:
        saved = before - after
        pct = (saved / before * 100) if before else 0
        print(f"\n  {human(before)} -> {human(after)}: saved {human(saved)} ({pct:.0f}%).")
        print(f"  Written to {root / 'compressed'}. Originals untouched.\n")
    else:
        print(f"\n  {human(before)} of images. Add --apply to write the compressed copies.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
