# expressive_from_csv_no_arcs.py
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
    
    :param s: The parameter `s` is a string that will be converted to its SHA-256 hash value and then
    converted to an integer
    :type s: str
    :return: The function `sha_int` takes a string `s`, encodes it using UTF-8, computes the SHA-256
    hash of the encoded string, converts the hash to a hexadecimal representation, and then converts the
    hexadecimal representation to an integer. The function returns this integer value.
    """
    return int(hashlib.sha256(s.encode("utf-8")).hexdigest(), 16)


def hsl_to_rgb(h, s, l):
    """
    The function `hsl_to_rgb` converts HSL (Hue, Saturation, Lightness) color values to RGB (Red, Green,
    Blue) color values.
    
    :param h: The `h` parameter in the `hsl_to_rgb` function represents the hue value in the HSL (Hue,
    Saturation, Lightness) color model. Hue is the attribute of a color by virtue of which it is
    discernible as red, green, blue, or any intermediate
    :param s: The parameter `s` in the `hsl_to_rgb` function stands for saturation. It represents the
    intensity or purity of the color. A saturation value of 0 results in a grayscale color (no color),
    while a saturation value of 1 represents a fully saturated color
    :param l: The parameter `l` in the `hsl_to_rgb` function represents the lightness value in the HSL
    (Hue, Saturation, Lightness) color model. It determines how light or dark the color is. The value of
    `l` ranges from 0 to 1,
    :return: The function `hsl_to_rgb` returns a tuple containing the RGB values converted from the
    given HSL values (hue, saturation, lightness).
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
    
    :param csv_text: The `build_palette` function takes a CSV text as input and generates a color
    palette based on the content of the text. The function calculates a base hue value from the SHA-1
    hash of the input text and then generates a set of hues and corresponding colors based on this base
    hue
    :type csv_text: str
    :return: The function `build_palette` returns a dictionary with the key "paint" containing a list of
    colors and accents generated based on the input `csv_text`. The colors are generated using the HSL
    to RGB conversion with specific hue values calculated from the input text. The accents are also
    generated based on the hue values with slight variations in saturation and lightness.
    """
    base = sha_int(csv_text) % 360
    hues = [
        base,
        (base + 20) % 360,
        (base + 160) % 360,
        (base + 200) % 360,
        (base + 300) % 360,
    ]
    colors = [hsl_to_rgb(H, 0.70, 0.55) for H in hues]
    accents = [
        hsl_to_rgb((base + 40) % 360, 0.55, 0.70),
        hsl_to_rgb((base + 220) % 360, 0.50, 0.75),
    ]
    return {"paint": colors + accents}


def extract_norm_params(row_vals, need=12):
    """
    The function `extract_norm_params` takes a list of row values, normalizes them, and ensures a
    specified length of normalized values is returned.
    
    :param row_vals: The `extract_norm_params` function takes a list of values `row_vals` as input and
    returns a normalized version of these values. The function ensures that the input values are valid
    numbers and then normalizes them between 0 and 1
    :param need: The `need` parameter in the `extract_norm_params` function specifies the desired length
    of the output list `norm`. If the length of the normalized values `norm` is less than the specified
    `need`, additional values are generated using the `RowRNG` class to fill up to the required,
    defaults to 12 (optional)
    :return: The function `extract_norm_params` returns a list of normalized values extracted from the
    input `row_vals`. If the length of the normalized values is less than the specified `need`
    parameter, additional random values are generated to meet the required length. The function then
    returns the normalized values truncated to the length specified by the `need` parameter.
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
    
    :param p0: The `p0`, `p1`, and `p2` parameters in the `quad_bezier` function represent the control
    points of a quadratic Bezier curve
    :param p1: The `quad_bezier` function you provided calculates points along a quadratic Bezier curve
    given three control points `p0`, `p1`, and `p2`. The function uses the formula for a quadratic
    Bezier curve to calculate the intermediate points
    :param p2: The `p2` parameter in the `quad_bezier` function represents the control point that
    influences the curvature of the quadratic Bezier curve. It is a tuple containing the x and y
    coordinates of the control point. In the context of quadratic Bezier curves, `p0` is the starting
    :param steps: The `steps` parameter in the `quad_bezier` function determines the number of points to
    calculate along the quadratic Bezier curve. Increasing the number of steps will result in a smoother
    curve with more points, while decreasing the number of steps will create a more segmented curve with
    fewer points, defaults to 80 (optional)
    :return: The function `quad_bezier` returns a list of points that form a quadratic Bezier curve
    based on the input control points `p0`, `p1`, and `p2`.
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
    
    :param points: The `points` parameter in the `noisy_polyline` function is a list of tuples
    representing the coordinates of points in a polyline. Each tuple contains the x and y coordinates of
    a point on the polyline
    :param rng: The `rng` parameter is likely an object that provides random number generation
    functionality. In the context of the `noisy_polyline` function, it seems to be used to introduce
    random noise to the input points of a polyline. The function uses the `rng.uni(-1, 1)` method
    :param jitter: The `jitter` parameter in the `noisy_polyline` function represents the amount of
    random noise that will be added to each point in the polyline. This noise is generated by randomly
    perturbing the x and y coordinates of each point within a range defined by the `rng` parameter
    :return: The `noisy_polyline` function returns a list of tuples where each tuple contains the x and
    y coordinates of a point from the input `points` list with added noise. The noise is generated using
    random values from a uniform distribution within the range [-1, 1] multiplied by the `jitter`
    parameter.
    """
    return [
        (x + rng.uni(-1, 1) * jitter, y + rng.uni(-1, 1) * jitter) for x, y in points
    ]


def draw_blob(layer, center, radius, color, rng):
    """
    The `draw_blob` function generates a blob-like shape with multiple rings of varying opacity and
    random points within each ring.
    
    :param layer: The `layer` parameter is the image layer on which the blob will be drawn. It is
    typically an image or a canvas where you want to draw the blob
    :param center: The `center` parameter in the `draw_blob` function represents the coordinates of the
    center point of the blob you want to draw. It is a tuple containing the x and y coordinates of the
    center point on the image where the blob will be drawn
    :param radius: The `radius` parameter in the `draw_blob` function represents the distance from the
    center of the blob to its outer edge. It determines the overall size of the blob that will be drawn
    on the specified `layer`
    :param color: The `color` parameter in the `draw_blob` function represents the color of the blob
    that will be drawn. It is expected to be a tuple of RGBA values, where each value ranges from 0 to
    255. The tuple should have 4 values representing the red, green, blue,
    :param rng: The `rng` parameter in the `draw_blob` function seems to be an object that provides
    random number generation functionality. It is used to generate random values for determining the
    number of rings, the number of points in each ring, and various other factors that contribute to the
    shape and appearance of the blob
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
    
    :param layer: The `layer` parameter is the image layer on which you want to draw the splatter
    effect. It is typically an image or a canvas where you want to add the splatter design
    :param origin: The `origin` parameter in the `draw_splatter` function represents the starting point
    or center of the splatter effect on the image. It is a tuple containing the x and y coordinates of
    the origin point. The splatter effect will radiate outwards from this point based on the other
    :param angle_deg: The `angle_deg` parameter in the `draw_splatter` function represents the angle at
    which the splatter will be drawn, measured in degrees. This angle determines the direction in which
    the splatter will spread out from the origin point
    :param color: The `color` parameter in the `draw_splatter` function represents the color of the
    splatter that will be drawn on the image. It is expected to be a tuple representing the RGBA values
    of the color. For example, if you want to use a red color with full opacity, you
    :param rng: The `rng` parameter in the `draw_splatter` function seems to be an instance of a random
    number generator. It is used to generate random values within a specified range for various
    calculations within the function. The specific implementation of the random number generator is not
    provided in the code snippet you shared
    :param count: The `count` parameter in the `draw_splatter` function represents the number of
    splatter shapes to be drawn on the layer. It determines how many times the loop will iterate to
    create individual splatter shapes, defaults to 80 (optional)
    :param spread: The `spread` parameter in the `draw_splatter` function controls how wide the splatter
    effect will be. It determines how far the individual splatter points will be spread out from the
    origin point. Increasing the `spread` value will result in a wider distribution of splatter points
    around the, defaults to 180 (optional)
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


def render_expressive_from_csv(csv_path, out_path="abstract_expressive_no_arcs.png"):
    """
    The function `render_expressive_from_csv` reads data from a CSV file, processes it to render
    abstract expressive shapes, and saves the output as an image.
    
    :param csv_path: The `csv_path` parameter is the file path to the CSV file containing the data
    needed for rendering the expressive image. This CSV file likely contains information such as shapes,
    colors, sizes, angles, and other parameters that will be used to create the visual elements in the
    final image
    :param out_path: The `out_path` parameter in the `render_expressive_from_csv` function is a string
    that specifies the output file path where the generated image will be saved. By default, if no
    `out_path` is provided when calling the function, the image will be saved as
    "abstract_expressive_no, defaults to abstract_expressive_no_arcs.png (optional)
    :return: The function `render_expressive_from_csv` returns the file path where the output image
    `abstract_expressive_no_arcs.png` is saved after processing the CSV data and rendering the
    expressive elements on the image.
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
        # REMAP: supprimer arcs → remplacer par 'stroke'
        if shape not in ("blob", "stroke", "splatter"):
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
