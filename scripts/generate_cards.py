import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

SOURCE_DIR = r"c:\Users\emman\Documents\GitHub\emmanuel-gbra\public\images\projects"
OUT_DIR = r"c:\Users\emman\Documents\GitHub\Losahfirst\assets"

FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"


def make_rounded_mask(size, radius):
    """High-res supersampled rounded rectangle mask for crisp anti-aliased corners."""
    scale = 4
    w, h = size
    mask = Image.new("L", (w * scale, h * scale), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        [(0, 0), (w * scale - 1, h * scale - 1)],
        radius=radius * scale,
        fill=255,
    )
    return mask.resize(size, Image.Resampling.LANCZOS)


def create_card(
    out_name,
    img_path,
    title,
    subtitle,
    right_top,
    right_bottom,
    width=880,
    height=500,
    footer_height=118,
    radius=24,
    is_compact=False,
    crop_anchor=(0.5, 0.3),
):
    card = Image.new("RGBA", (width, height), (14, 14, 14, 255))
    img_h = height - footer_height

    # Load and fit project screenshot cleanly into top area
    src = Image.open(img_path).convert("RGBA")
    fitted = ImageOps.fit(
        src,
        (width, img_h),
        method=Image.Resampling.LANCZOS,
        centering=crop_anchor,
    )
    card.paste(fitted, (0, 0))

    draw = ImageDraw.Draw(card)

    # Subtle separator line between screenshot and dark footer
    draw.rectangle([(0, img_h), (width, height)], fill=(15, 15, 15, 255))
    draw.line([(0, img_h), (width, img_h)], fill=(38, 38, 38, 255), width=2)

    # Typography
    if is_compact:
        f_title = ImageFont.truetype(FONT_BOLD, 28)
        f_sub = ImageFont.truetype(FONT_REG, 19)
        f_rt = ImageFont.truetype(FONT_BOLD, 22)
        f_rb = ImageFont.truetype(FONT_REG, 17)
        pad_x = 24
        y_top = img_h + 18
        y_bot = img_h + 56
    else:
        f_title = ImageFont.truetype(FONT_BOLD, 34)
        f_sub = ImageFont.truetype(FONT_REG, 22)
        f_rt = ImageFont.truetype(FONT_BOLD, 28)
        f_rb = ImageFont.truetype(FONT_REG, 20)
        pad_x = 30
        y_top = img_h + 22
        y_bot = img_h + 68

    # Left texts
    draw.text((pad_x, y_top), title, font=f_title, fill=(248, 248, 248, 255))
    draw.text((pad_x, y_bot), subtitle, font=f_sub, fill=(148, 148, 148, 255))

    # Right texts (aligned right)
    if right_top:
        has_star = right_top.startswith("★ ")
        text_rt = right_top[2:] if has_star else right_top
        bbox = draw.textbbox((0, 0), text_rt, font=f_rt)
        tw = bbox[2] - bbox[0]
        tx = width - pad_x - tw
        ty = y_top + (3 if not is_compact else 2)
        draw.text((tx, ty), text_rt, font=f_rt, fill=(240, 240, 240, 255))
        if has_star:
            # Draw crisp 5-point star icon to the left of text_rt
            r_out = 10 if not is_compact else 8
            r_in = r_out * 0.42
            cx = tx - r_out - 9
            cy = ty + (bbox[3] - bbox[1]) / 2 + 4
            pts = []
            for i in range(10):
                ang = math.radians(-90 + i * 36)
                r = r_out if i % 2 == 0 else r_in
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
            draw.polygon(pts, fill=(240, 240, 240, 255))
    if right_bottom:
        bbox = draw.textbbox((0, 0), right_bottom, font=f_rb)
        tw = bbox[2] - bbox[0]
        draw.text(
            (width - pad_x - tw, y_bot + 1),
            right_bottom,
            font=f_rb,
            fill=(140, 140, 140, 255),
        )

    # Subtle outer border on rounded card
    border_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(border_layer)
    bdraw.rounded_rectangle(
        [(1, 1), (width - 2, height - 2)],
        radius=radius,
        outline=(46, 46, 46, 255),
        width=2,
    )

    # Apply rounded mask
    mask = make_rounded_mask((width, height), radius)
    out = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    out.paste(card, (0, 0), mask)
    out = Image.alpha_composite(out, border_layer)

    out_path = os.path.join(OUT_DIR, out_name)
    out.save(out_path, "PNG", optimize=True)
    print(f"Generated {out_path} ({width}x{height})")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Row 1: 2 Large Bento Cards (880 x 500)
    create_card(
        out_name="card-ciewele.png",
        img_path=os.path.join(SOURCE_DIR, "ciewele-dashboard.png"),
        title="CIE Wélé",
        subtitle="AI Chatbot & Real-Time Ops Dashboard",
        right_top="★ 87.5%",
        right_bottom="cie_wele_app",
        width=880,
        height=500,
        footer_height=118,
        radius=26,
        is_compact=False,
        crop_anchor=(0.5, 0.45),
    )

    create_card(
        out_name="card-bornofspirit.png",
        img_path=os.path.join(SOURCE_DIR, "bornofspirit-desktop.png"),
        title="Born of Spirit",
        subtitle="Audio Bible AI in African local languages",
        right_top="Voice AI",
        right_bottom="WhatsApp & TG",
        width=880,
        height=500,
        footer_height=118,
        radius=26,
        is_compact=False,
        crop_anchor=(0.5, 0.35),
    )

    # Row 2: 4 Compact Bento Cards (440 x 330)
    create_card(
        out_name="card-kanari.png",
        img_path=os.path.join(SOURCE_DIR, "kanari-africa.png"),
        title="Kanari Africa",
        subtitle="CMMS & Field Ops",
        right_top="SaaS",
        right_bottom="",
        width=440,
        height=330,
        footer_height=96,
        radius=20,
        is_compact=True,
        crop_anchor=(0.35, 0.25),
    )

    create_card(
        out_name="card-ecofier.png",
        img_path=os.path.join(SOURCE_DIR, "ecofier-landing.png"),
        title="Ecofier",
        subtitle="Weighbridge Suite",
        right_top="Win/Mac",
        right_bottom="",
        width=440,
        height=330,
        footer_height=96,
        radius=20,
        is_compact=True,
        crop_anchor=(0.5, 0.45),
    )

    create_card(
        out_name="card-techroot.png",
        img_path=os.path.join(SOURCE_DIR, "techroot.png"),
        title="TechRoot",
        subtitle="Hardware & Drones",
        right_top="IoT",
        right_bottom="",
        width=440,
        height=330,
        footer_height=96,
        radius=20,
        is_compact=True,
        crop_anchor=(0.5, 0.4),
    )

    create_card(
        out_name="card-ciprel.png",
        img_path=os.path.join(SOURCE_DIR, "motor-analytics.jpg"),
        title="CIPREL SCADA",
        subtitle="Turbine Analytics",
        right_top="HMI",
        right_bottom="",
        width=440,
        height=330,
        footer_height=96,
        radius=20,
        is_compact=True,
        crop_anchor=(0.5, 0.45),
    )


if __name__ == "__main__":
    main()
