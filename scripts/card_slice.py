#!/usr/bin/env python3
"""
Smart split for info card images.
- Only splits if height > min_total (default 1400px)
- Prefers natural break points (background / low-density rows) instead of hard-cutting
- Falls back to the lowest-density row near the target cut when no clean gap exists

Usage:
    python3 card_slice.py <image_path> [max_slice=1200] [min_total=1400]
"""

import os
import sys
from collections import Counter

import numpy as np
from PIL import Image


def compute_row_activity(img_array, bg_color, tolerance=15):
    """Return per-row activity scores.

    Lower scores mean the row is closer to the background and therefore a safer
    split point. This is more forgiving than requiring a perfectly clean row,
    which often fails once noise textures or compression are present.
    """
    if img_array.ndim == 3:
        bg = np.array(bg_color[:3]).astype(int)
        diff = np.abs(img_array[:, :, :3].astype(int) - bg)
        pixel_delta = np.max(diff, axis=2)
    else:
        pixel_delta = np.abs(img_array.astype(int) - int(bg_color[0]))

    ink_mask = pixel_delta > tolerance
    row_ink_ratio = ink_mask.mean(axis=1)
    row_delta = pixel_delta.mean(axis=1) / 255.0
    row_score = row_ink_ratio * 0.75 + row_delta * 0.25
    return row_ink_ratio, row_score


def find_gap_candidates(row_ink_ratio, max_ink_ratio=0.025, min_gap=8):
    """Find low-activity row runs that likely represent gaps between content."""
    gaps = []
    in_gap = False
    gap_start = 0

    for y, ink_ratio in enumerate(row_ink_ratio):
        if ink_ratio <= max_ink_ratio:
            if not in_gap:
                in_gap = True
                gap_start = y
        else:
            if in_gap:
                gap_len = y - gap_start
                if gap_len >= min_gap:
                    gaps.append((gap_start + gap_len // 2, gap_len))
                in_gap = False

    if in_gap:
        gap_len = len(row_ink_ratio) - gap_start
        if gap_len >= min_gap:
            gaps.append((gap_start + gap_len // 2, gap_len))

    return gaps


def find_best_fallback_break(row_score, last_break, height, max_slice, min_slice):
    """Pick the least busy row near the target cut when no clean gap exists."""
    min_break = last_break + min_slice
    reserve_tail = height - min_slice
    target = min(last_break + max_slice, reserve_tail)
    max_break = min(last_break + max_slice, reserve_tail)

    if max_break <= min_break:
        return min(last_break + max_slice, height - 1)

    search_window = max(80, min(220, max_slice // 4))
    start = max(min_break, target - search_window)
    end = min(max_break, target + search_window)

    if end <= start:
        return max(min_break, min(target, max_break))

    positions = np.arange(start, end + 1)
    scores = row_score[start:end + 1].copy()
    distance_penalty = np.abs(positions - target) / max(search_window, 1)
    scores += distance_penalty * 0.15

    return int(positions[int(np.argmin(scores))])


def find_break_points(img_array, bg_color, max_slice=1200, min_slice=600):
    """Find best split rows while avoiding text-heavy regions whenever possible."""
    height = img_array.shape[0]
    row_ink_ratio, row_score = compute_row_activity(img_array, bg_color)
    gaps = find_gap_candidates(row_ink_ratio)

    # Pick break points that keep slices between min_slice and max_slice
    break_points = []
    last_break = 0

    while height - last_break > max_slice:
        min_break = last_break + min_slice
        max_break = min(last_break + max_slice, height - min_slice)
        target = min(last_break + max_slice, max_break)

        candidates = [
            (abs(gap_y - target), -gap_len, gap_y)
            for gap_y, gap_len in gaps
            if min_break <= gap_y <= max_break
        ]

        if candidates:
            _, _, best = min(candidates)
        else:
            best = find_best_fallback_break(row_score, last_break, height, max_slice, min_slice)

        if best <= last_break:
            break

        break_points.append(best)
        last_break = best

    return break_points


def detect_bg_color(img):
    """Detect background color by sampling corners."""
    w, h = img.size
    pixels = [img.getpixel((x, y)) for x, y in [(5, 5), (w-5, 5), (5, h-5), (w-5, h-5)]]
    return Counter(pixels).most_common(1)[0][0]


def split_card(image_path, max_slice=1200, min_total=1400):
    img = Image.open(image_path)
    width, height = img.size

    if height <= min_total:
        print(f"No split needed ({height}px <= {min_total}px threshold)")
        return [image_path]

    base_dir = os.path.dirname(image_path)
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    if base_name.endswith(("-1", "-2", "-3", "-4", "-5")):
        base_name = base_name[:-2]

    bg_color = detect_bg_color(img)
    img_array = np.array(img)

    break_points = find_break_points(img_array, bg_color, max_slice=max_slice)

    if not break_points:
        print("No break points found, keeping as single image")
        return [image_path]

    cuts = [0] + break_points + [height]
    parts = []

    for i in range(len(cuts) - 1):
        top = cuts[i]
        bottom = cuts[i + 1]
        slice_h = bottom - top

        # Merge tiny trailing slices (< 200px) with previous
        if slice_h < 200 and i == len(cuts) - 2 and parts:
            prev_path = parts[-1]
            prev_top = cuts[i - 1]
            cropped = img.crop((0, prev_top, width, bottom))
            cropped.save(prev_path, "PNG")
            print(f"  Updated: {prev_path} ({bottom - prev_top}px, merged tiny tail)")
            continue

        cropped = img.crop((0, top, width, bottom))
        out_path = os.path.join(base_dir, f"{base_name}-{i+1}.png")
        cropped.save(out_path, "PNG")
        parts.append(out_path)
        print(f"  Saved: {out_path} ({slice_h}px)")

    return parts


def stitch_images(image_paths, output_path):
    """Vertically stitch multiple images into one long image.
    All images must have the same width. No gap between images.
    """
    images = [Image.open(p) for p in image_paths]

    if not images:
        print("No images to stitch", file=sys.stderr)
        sys.exit(1)

    width = images[0].size[0]
    for i, img in enumerate(images):
        if img.size[0] != width:
            print(f"Warning: {image_paths[i]} width {img.size[0]} != {width}, resizing", file=sys.stderr)
            img = img.resize((width, int(img.size[1] * width / img.size[0])), Image.LANCZOS)
            images[i] = img

    total_height = sum(img.size[1] for img in images)
    result = Image.new("RGB", (width, total_height))

    y = 0
    for img in images:
        result.paste(img, (0, y))
        y += img.size[1]

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or '.', exist_ok=True)
    result.save(output_path, "PNG")
    size_kb = os.path.getsize(output_path) / 1024
    print(f"Stitched {len(images)} images -> {output_path}")
    print(f"  Dimensions: {width}x{total_height}")
    print(f"  File size: {size_kb:.0f}KB")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  card_slice.py split <image_path> [max_slice=1200] [min_total=1400]")
        print("  card_slice.py stitch <output_path> <image1> <image2> [image3 ...]")
        print("  card_slice.py <image_path> [max_slice] [min_total]  (legacy split)")
        sys.exit(1)

    if sys.argv[1] == "stitch":
        if len(sys.argv) < 4:
            print("Usage: card_slice.py stitch <output_path> <image1> <image2> [...]")
            sys.exit(1)
        stitch_images(sys.argv[3:], sys.argv[2])
    elif sys.argv[1] == "split":
        path = sys.argv[2]
        max_s = int(sys.argv[3]) if len(sys.argv) > 3 else 1200
        min_t = int(sys.argv[4]) if len(sys.argv) > 4 else 1400
        result = split_card(path, max_s, min_t)
        print(f"\nResult: {len(result)} file(s)")
        for p in result:
            print(f"  {p}")
    else:
        # Legacy mode: positional args
        path = sys.argv[1]
        max_s = int(sys.argv[2]) if len(sys.argv) > 2 else 1200
        min_t = int(sys.argv[3]) if len(sys.argv) > 3 else 1400
        result = split_card(path, max_s, min_t)
        print(f"\nResult: {len(result)} file(s)")
        for p in result:
            print(f"  {p}")
