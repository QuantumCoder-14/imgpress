# imgpress

**Shrink images before you upload them to something with a size limit.** Dry run by default;
originals are never modified.

```
imgpress 1.0 - pics  (2 image(s))

  square.png                            6.7 KB  ->     3.0 KB  (55% smaller, 800x800)
  wide.png                              8.9 KB  ->     2.0 KB  (77% smaller, 800x533)

  15.6 KB -> 5.0 KB: saved 10.6 KB (68%).
  Written to pics/compressed. Originals untouched.
```

## Quick start

```bash
pip install pillow
python imgpress.py                              # dry run on ./images
python imgpress.py --path photos --apply
python imgpress.py --max-width 1600 --quality 80 --apply
python imgpress.py --format webp --apply
```

| Flag | What it does |
| --- | --- |
| `--path DIR` | Folder of images, default `./images` |
| `--apply` | Write the files; without it you get a dry run |
| `--max-width N` | Resize anything wider than this, keeping the aspect ratio |
| `--quality N` | JPEG/WebP quality, 1-95, default 82 |
| `--format` | Convert to `jpg`, `png` or `webp`; default keeps each file's format |

## Three guarantees

1. **Originals are untouched.** Output goes to `<path>/compressed/`, and a test asserts the
   source bytes are identical afterwards.
2. **No upscaling.** `--max-width 1600` leaves a 600px image alone instead of blurring it up.
3. **Dry run is the default.** You see the projected size per file before anything is written.

## Notes

- Converts to RGB only for JPEG and WebP, so PNG transparency survives.
- JPEG is written progressive and optimised, which is smaller for the same quality.
- WebP uses `method=6` — slower, noticeably smaller.
- Animated GIFs and multi-page TIFFs are not handled; they are skipped with a message rather
  than flattened into a single frame.

## Tests

```bash
python tests/test_imgpress.py      # 12 tests
```

Resize planning, aspect-ratio maths, no-upscale behaviour, format overrides, JPEG alias
handling, written size actually shrinking, originals unchanged, PNG to WebP, dry run writing
nothing, and the error paths.

## Licence

MIT with Commons Clause. Copyright (c) 2026 Siddhant Neekhra. See [LICENSE.md](LICENSE.md).
