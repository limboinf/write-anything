#!/usr/bin/env python3
"""
Playwright-based screenshot for info card HTML files.
Uses local fonts — no network dependency.

Usage:
    python3 screenshot.py card.html card.png
    python3 screenshot.py card.html card.png --width 540 --scale 2 --wait 2000
    python3 screenshot.py batch ./cards/
    python3 screenshot.py batch ./cards/ --output-dir ./output/
"""

import argparse
import os
import sys


def screenshot(html_path, output_path, width=540, scale=2, wait_ms=2000):
    """Take a full-page screenshot of an HTML file using Playwright."""
    from playwright.sync_api import sync_playwright

    html_path = os.path.abspath(html_path)
    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found", file=sys.stderr)
        sys.exit(1)

    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": width, "height": 1},
            device_scale_factor=scale,
        )
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(wait_ms)  # font rendering settle
        page.screenshot(path=output_path, full_page=True)
        browser.close()

    size_kb = os.path.getsize(output_path) / 1024
    try:
        from PIL import Image
        img = Image.open(output_path)
        print(f"OK: {output_path}")
        print(f"  Dimensions: {img.size[0]}x{img.size[1]}")
        print(f"  File size: {size_kb:.0f}KB")
    except ImportError:
        print(f"OK: {output_path} ({size_kb:.0f}KB)")


def batch_screenshot(html_dir, output_dir=None, width=540, scale=2, wait_ms=2000):
    """Batch screenshot all card-*.html files in a directory.

    Expects files named: card-cover.html, card-1.html, card-2.html, ...
    Outputs: card-cover.png, card-1.png, card-2.png, ...
    """
    import glob

    html_dir = os.path.abspath(html_dir)
    if output_dir is None:
        output_dir = html_dir
    os.makedirs(output_dir, exist_ok=True)

    pattern = os.path.join(html_dir, "card-*.html")
    html_files = sorted(glob.glob(pattern))

    if not html_files:
        print(f"No card-*.html files found in {html_dir}", file=sys.stderr)
        sys.exit(1)

    results = []
    for html_path in html_files:
        base = os.path.splitext(os.path.basename(html_path))[0]
        out_path = os.path.join(output_dir, f"{base}.png")
        print(f"Screenshotting {os.path.basename(html_path)}...")
        screenshot(html_path, out_path, width=width, scale=scale, wait_ms=wait_ms)
        results.append(out_path)

    print(f"\nBatch complete: {len(results)} screenshots")
    return results


def main():
    # Legacy mode: python3 screenshot.py file.html out.png [--width ...]
    if len(sys.argv) >= 3 and sys.argv[1] not in ("batch", "single") and not sys.argv[1].startswith("-"):
        parser = argparse.ArgumentParser(description="Screenshot an info card HTML")
        parser.add_argument("html", help="Path to HTML file")
        parser.add_argument("output", help="Output PNG path")
        parser.add_argument("--width", type=int, default=540)
        parser.add_argument("--scale", type=int, default=2)
        parser.add_argument("--wait", type=int, default=2000)
        args = parser.parse_args()
        screenshot(args.html, args.output, args.width, args.scale, args.wait)
        return

    parser = argparse.ArgumentParser(description="Screenshot info card HTML files")
    subparsers = parser.add_subparsers(dest="command")

    single = subparsers.add_parser("single", help="Screenshot a single HTML file")
    single.add_argument("html", help="Path to HTML file")
    single.add_argument("output", help="Output PNG path")
    single.add_argument("--width", type=int, default=540)
    single.add_argument("--scale", type=int, default=2)
    single.add_argument("--wait", type=int, default=2000)

    batch = subparsers.add_parser("batch", help="Screenshot all card-*.html in a directory")
    batch.add_argument("dir", help="Directory containing card-*.html files")
    batch.add_argument("--output-dir", help="Output directory (default: same as input)")
    batch.add_argument("--width", type=int, default=540)
    batch.add_argument("--scale", type=int, default=2)
    batch.add_argument("--wait", type=int, default=2000)

    args = parser.parse_args()
    if args.command == "batch":
        batch_screenshot(args.dir, args.output_dir, args.width, args.scale, args.wait)
    elif args.command == "single":
        screenshot(args.html, args.output, args.width, args.scale, args.wait)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
