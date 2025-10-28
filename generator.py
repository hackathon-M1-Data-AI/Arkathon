from PIL import Image, ImageDraw, ImageFilter
import pandas as pd, numpy as np
import hashlib, math, sys

W, H = 1080, 720
class RowRNG:
    def __init__(self, seed_str: str):
        self.state = hashlib.sha256(seed_str.encode("utf-8")).digest()
        self.idx = 0

    def _next_byte(self):
        if self.idx >= len(self.state):
            self.state = hashlib.sha256(self.state).digest()
            self.idx = 0
        b = self.state[self.idx]
        self.idx += 1
        return b

    def uni(self, lo=0.0, hi=1.0):
        return lo + (hi - lo) * (self._next_byte() / 255.0)

    def choice(self, seq):
        return seq[int(self.uni(0, 1) * len(seq)) % len(seq)]


def sha_int(s: str) -> int:
    """
    The function `sha_int` takes a string input, encodes it using UTF-8, computes its SHA-256 hash,
    converts it to an integer, and returns the result.
    """
    return int(hashlib.sha256(s.encode("utf-8")).hexdigest(), 16)


def hsl_to_rgb(h, s, l):
    """
    The function `hsl_to_rgb` converts HSL (Hue, Saturation, Lightness) color values to RGB (Red, Green,
    Blue) color values.
    """
    c = (1 - abs(2 * l - 1)) * s
    hp = h / 60.0
    x = c * (1 - abs(hp % 2 - 1))
    if 0 <= hp <1 :
        r1, g1, b1 = c, x, 0
    elif 1 <= hp < 2:
        r1, g1, b1 = x, c, 0
    elif 2 <= hp < 3:
        r1, g1, b1 = 0, c, x
    elif 3 <= hp < 4:
        r1, g1, b1 = 0, x, c
    elif 4 <= hp < 5:
        r1, g1, b1 = x, 0, c
    else:
        r1, g1, b1 = c, 0, x
    m = l - c / 2
    return tuple(int(round((v + m) * 255)) for v in (r1, g1, b1))


def build_palette(csv_text: str):
    """
    This Python function generates a color palette based on a given CSV text input.
    """
    base = sha_int(csv_text) % 360
    hues = [
        base,
        (base + 30) % 360,
        (base + 280) % 360,
        (base + 340) % 360,
        (base + 300) % 360,
    ]
    colors = [hsl_to_rgb(H, 3.0, 0.5) for H in hues]
    accents = [
        hsl_to_rgb((base + 60) % 360, 5.0, 0.6),
        hsl_to_rgb((base + 210) % 360, 5.0, 0.5),
    ]
    return {"paint": colors + accents}


def extract_norm_params(row_vals, need=12):
    """
    The function `extract_norm_params` takes a list of row values, normalizes them, and ensures a
    specified length of normalized values is returned.
    """
    vals = [
        float(v)
        for v in row_vals
        if v is not None and str(v).strip() != "" and math.isfinite(float(v))
    ]
    if not vals:
        vals = [0.0]
    lo, hi = min(vals), max(vals)
    hi = hi if hi != lo else lo + 1.0
    norm = [(v - lo) / (hi - lo) for v in vals]
    if len(norm) < need:
        rng = RowRNG(str(vals))
        norm += [rng.uni() for _ in range(need - len(norm))]
    return norm[:need]


def quad_bezier(p0, p1, p2, steps=80):
    """
    The function `quad_bezier` calculates points along a quadratic Bezier curve defined by three control
    points.
    """
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
        pts.append((x, y))
    return pts


def noisy_polyline(points, rng, jitter=2.0):
    """
    The `noisy_polyline` function adds random noise to a given set of points to create a noisy polyline.
    """
    return [
        (x + rng.uni(-1, 1) * jitter, y + rng.uni(-1, 1) * jitter) for x, y in points
    ]


def draw_blob(layer, center, radius, color, rng):
    """
    The `draw_blob` function generates a blob-like shape with multiple rings of varying opacity and
    random points within each ring.
    """
    cx, cy = center
    dl = ImageDraw.Draw(layer, "RGBA")
    rings = 3 + int(rng.uni(0, 3))
    for r_i in range(rings):
        alpha = int(110 + 80 * (1 - r_i / (rings - 1 + 1e-6)))
        n = 20 + int(rng.uni(0, 25))
        pts = []
        for k in range(n):
            a = 2 * math.pi * k / n
            rr = (
                radius
                * (0.6 + 0.5 * rng.uni())
                * (0.9 + 0.15 * math.sin(3 * a + rng.uni() * 2 * math.pi))
            )
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        dl.polygon(pts, fill=color + (alpha,))


def draw_splatter(layer, origin, angle_deg, color, rng, count=80, spread=180):
    """
    The function `draw_splatter` draws a splatter effect on an image layer with specified parameters
    such as origin, angle, color, randomness, count, and spread.
    """
    dl = ImageDraw.Draw(layer, "RGBA")
    theta = math.radians(angle_deg)
    for i in range(count):
        t = (i + 1) / count
        dist = 5 + spread * (t**1.2) * rng.uni(0.5, 1.0)
        phi = theta + rng.uni(-0.9, 0.9)
        x = origin[0] + dist * math.cos(phi)
        y = origin[1] + dist * math.sin(phi)
        r = 1 + int(rng.uni(0.0, 5.0) * (1.2 - t))
        alpha = int(80 + 140 * (1 - t))
        dl.ellipse([x - r, y - r, x + r, y + r], fill=color + (alpha,))


def draw_spiral(layer, center, size, color, rng, turns=3):
    """
    Dessine une spirale organique avec variations de rayon.
    """
    dl = ImageDraw.Draw(layer, "RGBA")
    cx, cy = center
    points = []
    steps = 120
    
    for i in range(steps):
        t = i / steps
        angle = turns * 2 * math.pi * t
        radius = size * t * (0.8 + 0.4 * rng.uni())
        
        # Ajouter variation organique
        radius *= (1 + 0.2 * math.sin(8 * angle + rng.uni() * 2 * math.pi))
        
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))
    
    # Dessiner la spirale avec épaisseur variable
    for i in range(len(points) - 1):
        t = i / len(points)
        alpha = int(150 + 100 * (1 - t))
        width = max(1, int(8 * (1 - t * 0.7)))
        dl.line([points[i], points[i + 1]], fill=color + (alpha,), width=width)


def draw_wave(layer, center, size, color, rng):
    """
    Dessine des motifs d'ondes fluides et organiques.
    """
    dl = ImageDraw.Draw(layer, "RGBA")
    cx, cy = center
    
    wave_count = 3 + int(rng.uni(0, 5))
    
    for wave in range(wave_count):
        points = []
        steps = 60
        
        start_angle = rng.uni(0, 2 * math.pi)
        frequency = 2 + rng.uni(0, 4)
        amplitude = size * (0.2 + 0.3 * rng.uni())
        
        for i in range(steps):
            t = i / steps
            angle = start_angle + 2 * math.pi * t
            base_radius = size * (0.3 + 0.4 * t)
            
            wave_offset = amplitude * math.sin(frequency * angle)
            radius = base_radius + wave_offset
            
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            points.append((x, y))
        
        # Connecter au début pour fermer la forme
        points.append(points[0])
        
        alpha = int(60 + 80 * (1 - wave / wave_count))
        width = 2 + int(rng.uni(0, 4))
        
        for i in range(len(points) - 1):
            dl.line([points[i], points[i + 1]], fill=color + (alpha,), width=width)


def draw_cloud(layer, center, size, color, rng):
    """
    Dessine un nuage de particules avec distribution organique.
    """
    dl = ImageDraw.Draw(layer, "RGBA")
    cx, cy = center
    
    particle_count = 40 + int(rng.uni(0, 80))
    
    for i in range(particle_count):
        # Utiliser distribution gaussienne pour clustering naturel
        distance = size * abs(rng.uni(-1, 1) + rng.uni(-1, 1)) * 0.5
        angle = rng.uni(0, 2 * math.pi)
        
        x = cx + distance * math.cos(angle)
        y = cy + distance * math.sin(angle)
        
        particle_size = 1 + int(rng.uni(0, 8) * (1 - distance / size))
        alpha = int(60 + 120 * (1 - distance / size))
        
        dl.ellipse([x - particle_size, y - particle_size, 
                   x + particle_size, y + particle_size], 
                  fill=color + (alpha,))


def render_expressive_from_csv(csv_path, out_path="abstract_expressive_no_arcs.png"):
    """
    The function `render_expressive_from_csv` reads data from a CSV file, processes it to render
    abstract expressive shapes, and saves the output as an image.
    """
    df = pd.read_csv(csv_path)
    with open(csv_path, "r", encoding="utf-8") as f:
        csv_text = f.read()
    pal = build_palette(csv_text)

    base = Image.new("RGBA", (W, H), (250, 250, 252, 255))
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    cx, cy = W / 2, H / 2
    rx, ry = W * 0.46, H * 0.40
    md.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=200)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=50))

    paint_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    order = list(range(len(df)))
    if "z" in df.columns:
        order = list(np.argsort(df["z"].values))

    for idx in order:
        row = df.iloc[idx].to_dict()
        nums = []
        for k, v in row.items():
            if k in ("shape", "z"):
                continue
            try:
                fv = float(v)
                if math.isfinite(fv):
                    nums.append(fv)
            except:
                pass
        norm = extract_norm_params(nums, need=12)
        rng = RowRNG(str(row))

        px = W * 0.2 + norm[0] * (W * 0.6)
        py = H * 0.2 + norm[1] * (H * 0.6)
        size = 30 + norm[2] * 220
        ang = norm[3] * 360
        width = 3 + int(norm[4] * 20)
        vigor = norm[5]
        color = pal["paint"][sha_int(str(row)) % len(pal["paint"])]

        shape = str(row.get("shape", "")).strip().lower()
        # Support des nouvelles formes d'art abstrait
        if shape not in ("blob", "stroke", "splatter", "spiral", "wave", "cloud"):
            shape = "stroke"

        if shape == "blob":
            draw_blob(paint_layer, (px, py), size, color, rng)
        elif shape == "stroke":
            ctrl_dx = (norm[6] - 0.5) * size * 1.6
            ctrl_dy = (norm[7] - 0.5) * size * 1.6
            theta = math.radians(ang)
            p0 = (px - size * math.cos(theta), py - size * math.sin(theta))
            p2 = (px + size * math.cos(theta), py + size * math.sin(theta))
            p1 = (px + ctrl_dx, py + ctrl_dy)
            pts = noisy_polyline(
                quad_bezier(p0, p1, p2, steps=80), rng, jitter=2 + vigor * 3
            )
            dl = ImageDraw.Draw(paint_layer, "RGBA")
            dl.line(pts, fill=color + (220,), width=width)
            dl.line(pts, fill=color + (110,), width=max(1, int(width * 0.5)))
        elif shape == "splatter":
            draw_splatter(
                paint_layer,
                (px, py),
                ang,
                color,
                rng,
                count=60 + int(vigor * 80),
                spread=120 + int(size),
            )
        elif shape == "spiral":
            turns = 2 + int(norm[8] * 4)  # 2-6 tours
            draw_spiral(paint_layer, (px, py), size, color, rng, turns=turns)
        elif shape == "wave":
            draw_wave(paint_layer, (px, py), size, color, rng)
        elif shape == "cloud":
            draw_cloud(paint_layer, (px, py), size, color, rng)

    painted = Image.composite(
        paint_layer, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask
    )
    out = Image.alpha_composite(base, painted)

    # (Optionnel) si tu veux aussi retirer les micro-splashes noirs de bord,
    # commente totalement la section "edge grime" de ta version précédente.

    out.save(out_path)
    return out_path


if __name__ == "__main__":
    import os

    if len(sys.argv) < 2:
        print("Usage: python expressive_from_csv_no_arcs.py <input.csv> [output.png]")
        sys.exit(1)
    csv_in = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) >= 3 else "abstract_expressive_no_arcs.png"
    print("Image écrite:", render_expressive_from_csv(csv_in, out))
