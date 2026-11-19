import math
import os
from xml.sax.saxutils import escape

OUT_SVG = r"c:\Users\emman\Documents\GitHub\Losahfirst\assets\terminal.svg"

# High-resolution 2D mask of Africa (normalized x in [-1, 1], y in [-1, 1])
# Defined as a crisp polygon of Africa + Madagascar
AFRICA_POLY = [
    (-0.42, -0.92), (-0.15, -0.96), (0.10, -0.88), (0.28, -0.82),
    (0.45, -0.78), (0.56, -0.52), (0.72, -0.30), (0.86, -0.22),
    (0.76, -0.02), (0.60, 0.14), (0.50, 0.34), (0.44, 0.56),
    (0.32, 0.78), (0.16, 0.94), (0.04, 0.92), (-0.06, 0.74),
    (-0.14, 0.46), (-0.18, 0.18), (-0.28, 0.02), (-0.54, -0.02),
    (-0.76, -0.10), (-0.88, -0.26), (-0.86, -0.48), (-0.72, -0.72),
    (-0.56, -0.86),
]

MADAGASCAR_POLY = [
    (0.68, 0.40), (0.78, 0.36), (0.76, 0.62), (0.66, 0.74), (0.60, 0.64),
]

SHADE_CHARS = ".,-~:;=!*#$@"


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def in_africa(x, y):
    return point_in_poly(x, y, AFRICA_POLY) or point_in_poly(x, y, MADAGASCAR_POLY)


def build_3d_points():
    """Sample a 3D extruded Africa model with front face, back face, and side walls."""
    points = []  # (x, y, z, nx, ny, nz)
    thickness = 0.28
    half_t = thickness / 2.0

    # Sample grid for front & back faces + detect boundary for side extrusion
    step = 0.042
    xs = [round(-0.95 + i * step, 4) for i in range(int(1.90 / step) + 1)]
    ys = [round(-1.00 + i * step, 4) for i in range(int(2.00 / step) + 1)]

    grid = {}
    for ix, x in enumerate(xs):
        for iy, y in enumerate(ys):
            grid[(ix, iy)] = in_africa(x, y)

    for ix, x in enumerate(xs):
        for iy, y in enumerate(ys):
            if not grid[(ix, iy)]:
                continue
            # Slight pillowed dome normal on front/back for rich specular shading
            dome_nx = x * 0.22
            dome_ny = y * 0.22
            nlen = math.sqrt(dome_nx * dome_nx + dome_ny * dome_ny + 1.0)
            # Front face (+z)
            points.append((x, y, half_t, dome_nx / nlen, dome_ny / nlen, 1.0 / nlen))
            # Back face (-z)
            points.append((x, y, -half_t, dome_nx / nlen, dome_ny / nlen, -1.0 / nlen))

            # Check if boundary pixel to extrude side walls
            nx_edge, ny_edge = 0.0, 0.0
            is_edge = False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if not grid.get((ix + dx, iy + dy), False):
                    is_edge = True
                    nx_edge += dx
                    ny_edge += dy
            if is_edge:
                elen = math.sqrt(nx_edge * nx_edge + ny_edge * ny_edge) or 1.0
                nx_edge /= elen
                ny_edge /= elen
                for iz in range(1, 7):
                    z = -half_t + thickness * (iz / 7.0)
                    points.append((x, y, z, nx_edge, ny_edge, 0.0))

    return points


def render_frame(points, angle_y, tilt_x=0.22, cols=30, rows=16):
    zbuf = [[-1e9] * cols for _ in range(rows)]
    cbuf = [[" "] * cols for _ in range(rows)]

    cos_y, sin_y = math.cos(angle_y), math.sin(angle_y)
    cos_x, sin_x = math.cos(tilt_x), math.sin(tilt_x)

    # Light direction (front-top-right)
    lx, ly, lz = 0.45, -0.45, 0.77
    llen = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / llen, ly / llen, lz / llen

    cam_dist = 3.2
    scale_x = 18.5
    scale_y = 9.6

    for x, y, z, nx, ny, nz in points:
        # Rotate around Y
        x1 = x * cos_y + z * sin_y
        z1 = -x * sin_y + z * cos_y
        y1 = y

        # Slight tilt around X for 3D depth
        y2 = y1 * cos_x - z1 * sin_x
        z2 = y1 * sin_x + z1 * cos_x
        x2 = x1

        # Rotate normal
        nx1 = nx * cos_y + nz * sin_y
        nz1 = -nx * sin_y + nz * cos_y
        ny1 = ny

        ny2 = ny1 * cos_x - nz1 * sin_x
        nz2 = ny1 * sin_x + nz1 * cos_x
        nx2 = nx1

        ooz = 1.0 / (cam_dist - z2)
        px = int(cols / 2 + x2 * scale_x * ooz * 2.1)
        py = int(rows / 2 + y2 * scale_y * ooz * 2.1)

        if 0 <= px < cols and 0 <= py < rows:
            if z2 > zbuf[py][px]:
                zbuf[py][px] = z2
                lum = nx2 * lx + ny2 * ly + nz2 * lz
                # Ambient + diffuse so back/shadowed edges still show crisp ASCII
                intensity = max(0.08, min(1.0, 0.25 + 0.85 * max(0.0, lum)))
                idx = int(intensity * (len(SHADE_CHARS) - 1))
                cbuf[py][px] = SHADE_CHARS[idx]

    return ["".join(row) for row in cbuf]


def generate_svg():
    points = build_3d_points()
    num_frames = 30
    duration = 3.6  # seconds per full 360° rotation
    step_pct = 100.0 / num_frames
    step_sec = duration / num_frames

    frame_groups = []
    for i in range(num_frames):
        angle = (2.0 * math.pi * i) / num_frames
        lines = render_frame(points, angle)
        delay = -((duration - i * step_sec) % duration)
        text_elems = []
        for r_idx, line in enumerate(lines):
            y_pos = r_idx * 13
            text_elems.append(f'      <text x="0" y="{y_pos}" xml:space="preserve">{escape(line)}</text>')
        group = (
            f'    <g class="ascii-frame" style="animation-delay: {delay:.3f}s;">\n'
            + "\n".join(text_elems)
            + "\n    </g>"
        )
        frame_groups.append(group)

    frames_markup = "\n".join(frame_groups)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 470" width="900" height="470" role="img" aria-label="Emmanuel GBRA — GitHub Profile Terminal">
  <defs>
    <style>
      .mono {{ font-family: 'JetBrains Mono', 'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; }}
      .title-bar-text {{ fill: #737373; font-size: 13px; }}
      .box-legend {{ fill: #8a8a8a; font-size: 13px; }}
      .name-text {{ fill: #f5f5f5; font-size: 16px; font-weight: 700; }}
      .ascii {{ fill: #e8e8e8; font-size: 11px; font-weight: 700; white-space: pre; }}
      .loc-text {{ fill: #737373; font-size: 12.5px; }}
      .sec-head {{ fill: #f5f5f5; font-size: 13.5px; font-weight: 700; }}
      .sec-body {{ fill: #b8b8b8; font-size: 13px; }}
      .prompt-caret {{ fill: #e5e5e5; font-size: 14px; font-weight: 700; }}
      .prompt-hint {{ fill: #6e6e6e; font-size: 13.5px; }}
      .shortcut-hint {{ fill: #555555; font-size: 12px; }}

      @keyframes blink {{
        0%, 49% {{ opacity: 1; }}
        50%, 100% {{ opacity: 0; }}
      }}
      .cursor {{
        fill: #f5f5f5;
        animation: blink 1.1s step-end infinite;
      }}

      @keyframes frameCycle {{
        0% {{ opacity: 1; }}
        {step_pct:.4f}% {{ opacity: 0; }}
        100% {{ opacity: 0; }}
      }}
      .ascii-frame {{
        opacity: 0;
        animation: frameCycle {duration:.2f}s steps(1, end) infinite;
      }}
    </style>
  </defs>

  <!-- Outer macOS Terminal Window -->
  <rect x="2" y="2" width="896" height="466" rx="14" ry="14" fill="#0c0c0c" stroke="#282828" stroke-width="1.5"/>

  <!-- Top Title Bar -->
  <path d="M 16 2 H 884 A 14 14 0 0 1 898 16 V 38 H 2 V 16 A 14 14 0 0 1 16 2 Z" fill="#181818"/>
  <line x1="2" y1="38" x2="898" y2="38" stroke="#242424" stroke-width="1"/>

  <!-- macOS Traffic Light Dots -->
  <circle cx="24" cy="20" r="6" fill="#3a3a3a"/>
  <circle cx="44" cy="20" r="6" fill="#3a3a3a"/>
  <circle cx="64" cy="20" r="6" fill="#3a3a3a"/>

  <!-- Window Title -->
  <text x="450" y="24" text-anchor="middle" class="mono title-bar-text">~/Losahfirst</text>

  <!-- Inner TUI Frame -->
  <rect x="24" y="60" width="852" height="306" rx="8" ry="8" fill="none" stroke="#2a2a2a" stroke-width="1.2"/>
  <rect x="38" y="51" width="94" height="18" fill="#0c0c0c"/>
  <text x="46" y="64" class="mono box-legend">Losahfirst</text>

  <!-- Center Vertical Divider -->
  <line x1="354" y1="84" x2="354" y2="344" stroke="#222222" stroke-width="1"/>

  <!-- LEFT COLUMN: Name + 3D Rotating Africa ASCII Art + Location -->
  <text x="189" y="96" text-anchor="middle" class="mono name-text">Emmanuel GBRA</text>

  <g transform="translate(89, 120)" class="mono ascii">
{frames_markup}
  </g>

  <text x="189" y="340" text-anchor="middle" class="mono loc-text">Abidjan, Côte d'Ivoire</text>

  <!-- RIGHT COLUMN: About, Stack, Elsewhere -->
  <text x="386" y="102" class="mono sec-head">About</text>
  <text x="386" y="128" class="mono sec-body">AI &amp; Data Systems Architect · R&amp;D &amp; Continuous Improvement.</text>
  <text x="386" y="150" class="mono sec-body">Electronics, client-server software &amp; machine data on the field.</text>
  <text x="386" y="172" class="mono sec-body">Building African autonomous LiDAR/radar &amp; wave energy.</text>

  <!-- Horizontal Divider -->
  <line x1="386" y1="196" x2="844" y2="196" stroke="#222222" stroke-width="1"/>

  <text x="386" y="226" class="mono sec-head">Stack</text>
  <text x="386" y="252" class="mono sec-body">Python · C/C++ · Vue.js · RAG/AI · Predictive ML · IoT · SCADA</text>

  <text x="386" y="294" class="mono sec-head">Elsewhere</text>
  <text x="386" y="320" class="mono sec-body">emmanuelgbra.com · linkedin.com/in/korekou-emmanuel-gbra</text>

  <!-- Bottom Interactive Prompt Bar -->
  <rect x="24" y="384" width="852" height="44" rx="7" ry="7" fill="#0f0f0f" stroke="#2e2e2e" stroke-width="1.2"/>
  <text x="42" y="411" class="mono prompt-caret">&gt;</text>
  <rect x="62" y="397" width="9" height="18" class="cursor"/>
  <text x="76" y="411" class="mono prompt-hint">Try "make machine data speak to solve real field problems"</text>

  <!-- Bottom Shortcuts Hint -->
  <text x="42" y="451" class="mono shortcut-hint">? for shortcuts</text>
</svg>
'''

    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg)
    size_kb = os.path.getsize(OUT_SVG) / 1024.0
    print(f"Generated animated {OUT_SVG} ({num_frames} frames, {size_kb:.1f} KB)")

    # Print sample frames 0, 5, 10 to stdout to verify silhouette & 3D rotation
    for idx in [0, 5, 10]:
        print(f"\n--- Frame {idx} ---")
        for l in render_frame(points, (2.0 * math.pi * idx) / num_frames):
            print(l)


if __name__ == "__main__":
    generate_svg()
