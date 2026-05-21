from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from ..ui_tokens import UiTokens


class BackgroundLayer(ctk.CTkLabel):
    """Full-window underwater background.

    Phase 1 intentionally generates this in memory so the app does not depend on
    external art yet. If assets/background.png exists, it is used and darkened.
    """

    def __init__(self, master, *, tokens: UiTokens, assets_dir: Path):
        super().__init__(master, text="")
        self.tokens = tokens
        self.assets_dir = assets_dir
        self._image_ref: Optional[ctk.CTkImage] = None
        self._last_size: tuple[int, int] = (0, 0)
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, _event=None) -> None:
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        if width < 100 or height < 100:
            return
        if abs(width - self._last_size[0]) < 40 and abs(height - self._last_size[1]) < 40:
            return
        self._last_size = (width, height)
        self._render(width, height)

    def _render(self, width: int, height: int) -> None:
        asset = self.assets_dir / "background.png"
        if asset.is_file():
            image = _cover_image(Image.open(asset).convert("RGB"), width, height)
            image = ImageEnhance.Brightness(image).enhance(0.48)
            image = ImageEnhance.Contrast(image).enhance(1.08)
        else:
            image = _procedural_underwater(width, height)

        self._image_ref = ctk.CTkImage(light_image=image, dark_image=image, size=(width, height))
        self.configure(image=self._image_ref)


def _cover_image(image: Image.Image, width: int, height: int) -> Image.Image:
    src_ratio = image.width / image.height
    target_ratio = width / height
    if src_ratio > target_ratio:
        new_height = height
        new_width = int(height * src_ratio)
    else:
        new_width = width
        new_height = int(width / src_ratio)
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left = max(0, (new_width - width) // 2)
    top = max(0, (new_height - height) // 2)
    return resized.crop((left, top, left + width, top + height))


def _procedural_underwater(width: int, height: int) -> Image.Image:
    rng = random.Random(2701)
    image = Image.new("RGB", (width, height), "#06131A")
    draw = ImageDraw.Draw(image, "RGBA")

    for y in range(height):
        t = y / max(1, height - 1)
        r = int(3 + 8 * (1 - t) + 1 * t)
        g = int(31 + 62 * (1 - t) + 11 * t)
        b = int(47 + 92 * (1 - t) + 24 * t)
        draw.line((0, y, width, y), fill=(r, g, b, 255))

    # Diffuse surface light and center readability vignette.
    for i in range(11):
        alpha = max(12, 72 - i * 6)
        box = (
            int(width * (0.25 - i * 0.018)),
            int(height * (-0.10 - i * 0.018)),
            int(width * (0.75 + i * 0.018)),
            int(height * (0.45 + i * 0.018)),
        )
        draw.ellipse(box, fill=(45, 185, 215, alpha))

    # Distant terrain/coral silhouettes.
    for layer in range(4):
        y_base = int(height * (0.72 + layer * 0.055))
        points = [(-20, height + 30)]
        for x in range(-20, width + 80, max(40, width // 26)):
            wave = math.sin((x / width) * math.tau * (layer + 1.4)) * (20 + layer * 8)
            y = y_base + int(wave) + rng.randint(-22, 18)
            points.append((x, y))
        points.append((width + 50, height + 30))
        color = (3, 20 + layer * 8, 30 + layer * 9, 100 + layer * 22)
        draw.polygon(points, fill=color)

    # PDA-style hex mesh, deliberately subtle so it reads as texture, not noise.
    hex_size = max(26, min(44, width // 42))
    hex_h = int(hex_size * 0.86)
    mesh_color = (104, 224, 242, 15)
    for row, y in enumerate(range(-hex_h, height + hex_h, hex_h)):
        x_offset = -hex_size if row % 2 else -(hex_size // 2)
        for x in range(x_offset, width + hex_size, hex_size * 2):
            points = [
                (x + hex_size // 2, y),
                (x + hex_size + hex_size // 2, y),
                (x + hex_size * 2, y + hex_h // 2),
                (x + hex_size + hex_size // 2, y + hex_h),
                (x + hex_size // 2, y + hex_h),
                (x, y + hex_h // 2),
            ]
            draw.line(points + [points[0]], fill=mesh_color, width=1)

    # Coral glow clusters.
    for _ in range(42):
        x = rng.choice([rng.randint(0, int(width * 0.18)), rng.randint(int(width * 0.76), width)])
        y = rng.randint(int(height * 0.55), height)
        radius = rng.randint(2, 7)
        color = rng.choice([(86, 80, 235, 120), (255, 93, 180, 90), (56, 214, 214, 90)])
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    # Bubbles and plankton specks.
    for _ in range(230):
        x = rng.randint(0, width)
        y = rng.randint(0, height)
        r = rng.choice([1, 1, 1, 2])
        alpha = rng.randint(28, 105)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(100, 230, 255, alpha))

    # Soft dark vignette around edges and stronger dark center under the UI.
    vignette = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette, "RGBA")
    for i in range(30):
        alpha = int(i * 4.2)
        vdraw.rectangle(
            (i * 5, i * 4, width - i * 5, height - i * 4),
            outline=(0, 0, 0, max(0, 125 - alpha)),
            width=6,
        )
    vdraw.rounded_rectangle(
        (int(width * 0.045), int(height * 0.055), int(width * 0.955), int(height * 0.94)),
        radius=24,
        fill=(0, 8, 14, 58),
    )
    vdraw.rounded_rectangle(
        (int(width * 0.04), int(height * 0.05), int(width * 0.96), int(height * 0.945)),
        radius=28,
        outline=(122, 233, 250, 35),
        width=2,
    )
    image = Image.alpha_composite(image.convert("RGBA"), vignette)
    return image.filter(ImageFilter.SMOOTH_MORE).convert("RGB")
