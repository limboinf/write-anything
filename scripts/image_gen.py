#!/usr/bin/env python3
"""
AI image generation module for write-anything.

Supports multiple providers via a simple abstraction:
  - ark (Volcengine Ark / doubao-seedream) — default, good for Chinese prompts
  - gemini (Google Gemini Imagen) — multimodal image generation
  - Custom providers via ImageProvider base class

API key loading:
  - All API keys are loaded from environment variables
  - Supported env names:
      ARK_API_KEY
      GEMINI_API_KEY

Usage as CLI:

Single image:
    python3 image_gen.py single --prompt "描述" --output cover.png
    python3 image_gen.py single --prompt "描述" --output cover.png --size cover
    python3 image_gen.py single --prompt "描述" --output cover.png --provider gemini

Grouped images:
    python3 image_gen.py group --group-name 封面 --prompt "未来感 AI 插画" --output-dir out/
    python3 image_gen.py group --group-name 配图 --prompt "极简科技风" --output-dir out/ --count 4

Legacy CLI compatibility:
    python3 image_gen.py --prompt "描述" --output cover.png
    python3 image_gen.py --prompt "描述" --output cover.png --provider gemini

Usage as module:
    from image_gen import generate_image, generate_image_group
    path = generate_image("prompt text", "output.png", size="cover")
    paths = generate_image_group("prompt text", "封面", "out", count=4, size="cover")
"""

import abc
import argparse
import base64
import json
import os
import sys
from pathlib import Path

import requests  # type: ignore[import-not-found]
import yaml  # type: ignore[import-not-found]

# --- Config ---

CONFIG_PATHS = [
    Path.cwd() / "config.yaml",
    Path(__file__).parent.parent / "config.yaml",  # skill root
    Path(__file__).parent / "config.yaml",  # toolkit dir
    Path.home() / ".config" / "write-anything" / "config.yaml",
]


def _load_config() -> dict:
    for p in CONFIG_PATHS:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


# --- Size presets ---

# Cover: 2.35:1 横版封面（微信公众号）
# Article: 16:9 横版（头条封面 / 通用内文配图）
# Vertical: 9:16 竖版（小红书封面 / 竖版配图）
SIZE_PRESETS = {
    "cover": {"ark": "2952x1256", "gemini": "1792x1024"},
    "article": {"ark": "2560x1440", "gemini": "1792x1024"},
    "vertical": {"ark": "1088x2560", "gemini": "1024x1792"},
    "square": {"ark": "2048x2048", "gemini": "1024x1024"},
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _compress_image(raw_bytes: bytes, max_size: int) -> bytes:
    """Compress image to fit under max_size by reducing JPEG quality."""
    from io import BytesIO

    from PIL import Image  # type: ignore[import-not-found]

    img = Image.open(BytesIO(raw_bytes))
    if img.mode == "RGBA":
        img = img.convert("RGB")

    last_result = raw_bytes
    for quality in (90, 80, 70, 60, 50):
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        last_result = buf.getvalue()
        if buf.tell() <= max_size:
            return last_result

    return last_result


# --- Provider abstraction ---


class ImageProvider(abc.ABC):
    """Base class for image generation providers."""

    @abc.abstractmethod
    def generate(self, prompt: str, size: str) -> bytes:
        """Generate an image and return raw bytes.

        Args:
            prompt: Image description (Chinese or English).
            size: Resolved size string (e.g. "1792x1024").

        Returns:
            Raw image bytes.
        """
        ...

    def resolve_size(self, preset: str) -> str:
        """Resolve a size preset to a concrete size string for this provider."""
        provider_key = self.provider_key()
        if preset in SIZE_PRESETS:
            return SIZE_PRESETS[preset].get(
                provider_key, list(SIZE_PRESETS[preset].values())[0]
            )
        return preset  # assume explicit WxH

    @classmethod
    @abc.abstractmethod
    def provider_key(cls) -> str:
        """Short identifier used for size preset lookup."""
        ...


class ArkProvider(ImageProvider):
    """Image generation via Volcengine Ark API."""

    @classmethod
    def provider_key(cls) -> str:
        return "ark"

    def __init__(
        self,
        api_key: str,
        model: str = "doubao-seedream-5-0-260128",
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url

    def generate(self, prompt: str, size: str) -> bytes:
        body = {
            "model": self._model,
            "prompt": prompt,
            "response_format": "url",
            "size": size,
            "stream": False,
            "watermark": False,
        }

        resp = requests.post(
            f"{self._base_url}/images/generations",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            json=body,
            timeout=120,
        )

        data = resp.json()
        if resp.status_code != 200:
            error = data.get("error", {})
            msg = error.get("message", json.dumps(data, ensure_ascii=False))
            raise ValueError(f"Ark API error ({resp.status_code}): {msg}")

        image_data = data.get("data", [])
        if not image_data:
            raise ValueError(
                f"No image returned: {json.dumps(data, ensure_ascii=False)}"
            )

        image_url = image_data[0].get("url")
        if not image_url:
            raise ValueError(
                f"No image URL in response: {json.dumps(data, ensure_ascii=False)}"
            )

        img_resp = requests.get(image_url, timeout=60)
        img_resp.raise_for_status()
        return img_resp.content


class GeminiProvider(ImageProvider):
    """Google Gemini Imagen provider."""

    @classmethod
    def provider_key(cls) -> str:
        return "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.1-flash-image-preview",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url

    def generate(self, prompt: str, size: str) -> bytes:
        # Append size instruction to prompt (Gemini doesn't have a native size param)
        if "x" in size:
            w, h = size.split("x", 1)
            prompt = f"{prompt}\n\nGenerate this image at {w}x{h} resolution."

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }
        resp = requests.post(
            f"{self._base_url}/models/{self._model}:generateContent",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            json=body,
            timeout=120,
        )
        if resp.status_code != 200:
            try:
                error = resp.json().get("error", {})
                msg = error.get("message", resp.text[:200])
            except (ValueError, KeyError):
                msg = resp.text[:200]
            raise ValueError(f"Gemini API error ({resp.status_code}): {msg}")
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("No candidates in Gemini response")
        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            inline_data = part.get("inlineData")
            if inline_data and inline_data.get("mimeType", "").startswith("image/"):
                return base64.b64decode(inline_data["data"])
        raise ValueError("No image found in Gemini response parts")


# --- Provider registry ---

SUPPORTED_PROVIDERS = ("ark", "gemini")

PROVIDERS = {
    "ark": ArkProvider,
    "gemini": GeminiProvider,
}

PROVIDER_API_KEY_ENVS = {
    "ark": "ARK_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def _resolve_api_key(provider_name: str) -> str | None:
    """Resolve API key from environment variables."""
    env_name = PROVIDER_API_KEY_ENVS.get(provider_name)
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    return None


def _detect_extension(raw_bytes: bytes) -> str:
    """Detect image extension from bytes."""
    if raw_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if raw_bytes.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if raw_bytes.startswith(b"GIF87a") or raw_bytes.startswith(b"GIF89a"):
        return ".gif"
    if raw_bytes.startswith(b"RIFF") and raw_bytes[8:12] == b"WEBP":
        return ".webp"
    if raw_bytes.startswith(b"BM"):
        return ".bmp"
    return ".png"


def _normalize_output_path(output_path: str, raw_bytes: bytes) -> Path:
    """Append detected extension when output path has no suffix."""
    output = Path(output_path)
    if output.suffix:
        return output
    return output.with_suffix(_detect_extension(raw_bytes))


def _build_provider(config: dict) -> ImageProvider:
    """Build an ImageProvider from config.yaml's image section."""
    img_cfg = config.get("image", {})
    provider_name = img_cfg.get("provider", "ark")

    if provider_name == "doubao":
        raise ValueError(
            "Provider 'doubao' has been removed. Please change it to 'ark'."
        )

    provider_cls = PROVIDERS.get(provider_name)
    if not provider_cls:
        raise ValueError(
            f"Unknown image provider: '{provider_name}'. "
            f"Available: {', '.join(SUPPORTED_PROVIDERS)}"
        )

    api_key = _resolve_api_key(provider_name)
    if not api_key:
        provider_env = PROVIDER_API_KEY_ENVS.get(provider_name)
        raise ValueError(
            f"Image API key not found in environment variables. Set {provider_env}."
        )

    kwargs = {"api_key": api_key}
    if img_cfg.get("model"):
        kwargs["model"] = img_cfg["model"]
    if img_cfg.get("base_url"):
        kwargs["base_url"] = img_cfg["base_url"]

    return provider_cls(**kwargs)


# --- Public API ---


def generate_image(
    prompt: str,
    output_path: str,
    size: str = "cover",
    config: dict | None = None,
) -> str:
    """
    Generate a single image using the configured provider.

    Args:
        prompt: Image generation prompt (Chinese or English).
        output_path: Where to save the image.
        size: Size preset ("cover", "article", "vertical", "square") or explicit "WxH".
        config: Optional config dict. If None, loads from config.yaml.

    Returns:
        The output file path.
    """
    if config is None:
        config = _load_config()

    provider = _build_provider(config)
    resolved_size = provider.resolve_size(size)

    raw_bytes = provider.generate(prompt, resolved_size)

    # Compress if over 5MB (WeChat upload limit)
    if len(raw_bytes) > MAX_FILE_SIZE:
        raw_bytes = _compress_image(raw_bytes, MAX_FILE_SIZE)

    output = _normalize_output_path(output_path, raw_bytes)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw_bytes)
    return str(output)


def generate_image_group(
    prompt: str,
    group_name: str,
    output_dir: str,
    count: int = 4,
    size: str = "cover",
    config: dict | None = None,
) -> list[str]:
    """
    Generate a group of images using one prompt.

    Args:
        prompt: Group image generation prompt.
        group_name: Prefix used in output filenames, e.g. "组名" -> 组名1, 组名2...
        output_dir: Directory to save generated images.
        count: Number of images to generate in the group.
        size: Size preset ("cover", "article", "vertical", "square") or explicit "WxH".
        config: Optional config dict. If None, loads from config.yaml.

    Returns:
        A list of output file paths.
    """
    if count < 1:
        raise ValueError("count must be >= 1")

    if config is None:
        config = _load_config()

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    paths = []
    for index in range(1, count + 1):
        output_path = output_root / f"{group_name}{index}"
        paths.append(generate_image(prompt, str(output_path), size=size, config=config))
    return paths


def main():
    legacy_mode = len(sys.argv) > 1 and sys.argv[1] not in {
        "single",
        "group",
        "-h",
        "--help",
    }

    parser = argparse.ArgumentParser(
        description="Generate images using AI (Volcengine Ark / Gemini)"
    )

    if legacy_mode:
        parser.add_argument("--prompt", required=True, help="Image generation prompt")
        parser.add_argument("--output", required=True, help="Output file path")
        parser.add_argument(
            "--size",
            default="cover",
            help="Size: cover, article, vertical, square, or WxH",
        )
        parser.add_argument(
            "--provider",
            default=None,
            choices=SUPPORTED_PROVIDERS,
            help="Override provider (ark, gemini). Default: from config.yaml",
        )
        args = parser.parse_args()
        args.command = "single"
    else:
        subparsers = parser.add_subparsers(dest="command", required=True)

        single_parser = subparsers.add_parser("single", help="Generate a single image")
        single_parser.add_argument(
            "--prompt", required=True, help="Image generation prompt"
        )
        single_parser.add_argument("--output", required=True, help="Output file path")
        single_parser.add_argument(
            "--size",
            default="cover",
            help="Size: cover, article, vertical, square, or WxH",
        )
        single_parser.add_argument(
            "--provider",
            default=None,
            choices=SUPPORTED_PROVIDERS,
            help="Override provider (ark, gemini). Default: from config.yaml",
        )

        group_parser = subparsers.add_parser("group", help="Generate a group of images")
        group_parser.add_argument(
            "--prompt", required=True, help="Group image generation prompt"
        )
        group_parser.add_argument(
            "--group-name", required=True, help="Group output prefix"
        )
        group_parser.add_argument(
            "--output-dir", required=True, help="Output directory"
        )
        group_parser.add_argument(
            "--count",
            type=int,
            default=4,
            help="Number of images to generate in this group",
        )
        group_parser.add_argument(
            "--size",
            default="cover",
            help="Size: cover, article, vertical, square, or WxH",
        )
        group_parser.add_argument(
            "--provider",
            default=None,
            choices=SUPPORTED_PROVIDERS,
            help="Override provider (ark, gemini). Default: from config.yaml",
        )

        args = parser.parse_args()

    try:
        config = _load_config()
        if args.provider:
            config.setdefault("image", {})["provider"] = args.provider

        if args.command == "single":
            path = generate_image(
                args.prompt, args.output, size=args.size, config=config
            )
            print(f"Image saved: {path}")
        elif args.command == "group":
            paths = generate_image_group(
                args.prompt,
                args.group_name,
                args.output_dir,
                count=args.count,
                size=args.size,
                config=config,
            )
            print("Images saved:")
            for path in paths:
                print(path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
