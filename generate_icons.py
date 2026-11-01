"""Generate minimal PWA icons for BookEase using Pillow."""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "pillow"], check=True)
    from PIL import Image, ImageDraw, ImageFont

ICONS_DIR = Path(__file__).parent / "web" / "static" / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

# Brand colors
BG_COLOR     = (74, 23, 40)      # #4A1728
ACCENT_COLOR = (196, 98, 122)    # #C4627A
TEXT_COLOR   = (245, 230, 234)   # #F5E6EA

def make_icon(size: int, filename: str):
    """Create a square icon with rounded corners and the BookEase ✦ symbol."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle/rounded rect
    radius = size // 5
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG_COLOR)

    # Inner accent ring
    pad = size // 10
    draw.rounded_rectangle(
        [pad, pad, size - 1 - pad, size - 1 - pad],
        radius=radius - pad // 2,
        outline=ACCENT_COLOR,
        width=max(2, size // 48),
    )

    # Symbol "✦" or "B"
    symbol_size = int(size * 0.45)
    try:
        font = ImageFont.truetype("arial.ttf", symbol_size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", symbol_size)
        except Exception:
            font = ImageFont.load_default()

    symbol = "✦"
    try:
        bbox = draw.textbbox((0, 0), symbol, font=font)
    except Exception:
        bbox = (0, 0, symbol_size, symbol_size)

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = (size - th) // 2

    # Shadow
    draw.text((tx + 2, ty + 2), symbol, font=font, fill=(0, 0, 0, 120))
    # Main text
    draw.text((tx, ty), symbol, font=font, fill=ACCENT_COLOR)

    out_path = ICONS_DIR / filename
    img.save(out_path, "PNG")
    print(f"  Created: {out_path} ({size}x{size})")

def make_og_image():
    """Create a simple OG image (1200x630)."""
    w, h = 1200, 630
    img  = Image.new("RGB", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Gradient effect (manual bands)
    for y in range(h):
        ratio = y / h
        r = int(74  + (106 - 74)  * ratio)
        g = int(23  + (32  - 23)  * ratio)
        b = int(40  + (64  - 40)  * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Icon in top-left area
    symbol_size = 120
    try:
        font_big = ImageFont.truetype("arial.ttf", symbol_size)
        font_med = ImageFont.truetype("arial.ttf", 72)
        font_sm  = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font_big = font_med = font_sm = ImageFont.load_default()

    # Title
    draw.text((w // 2, h // 2 - 60), "✦ BookEase", font=font_med, fill=TEXT_COLOR, anchor="mm")
    draw.text((w // 2, h // 2 + 30), "Book your appointment online", font=font_sm, fill=ACCENT_COLOR, anchor="mm")

    out_path = ICONS_DIR / "og-image.png"
    img.save(out_path, "PNG")
    print(f"  Created: {out_path} (1200x630)")

def make_favicon(size: int, filename: str):
    """Create a small favicon."""
    img  = Image.new("RGBA", (size, size), BG_COLOR)
    draw = ImageDraw.Draw(img)
    # Simple dot
    pad = size // 6
    draw.ellipse([pad, pad, size - pad, size - pad], fill=ACCENT_COLOR)
    out_path = ICONS_DIR / filename
    img.save(out_path, "PNG")
    print(f"  Created: {out_path} ({size}x{size})")

if __name__ == "__main__":
    print("Generating BookEase PWA icons...")
    make_icon(192, "icon-192.png")
    make_icon(512, "icon-512.png")
    make_favicon(32, "favicon-32.png")
    make_favicon(16, "favicon-16.png")
    make_og_image()
    print("Done!")

