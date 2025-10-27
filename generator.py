# expressive_from_csv_no_arcs.py
from PIL import Image, ImageDraw, ImageFilter
import pandas as pd, numpy as np
import hashlib, math, sys

# W, H = 15360, 8640
W, H = 1080, 720

class RowRNG:
    def __init__(self, seed_str: str):
        self.state = hashlib.sha256(seed_str.encode("utf-8")).digest(); self.idx = 0
    def _next_byte(self):
        if self.idx >= len(self.state):
            self.state = hashlib.sha256(self.state).digest(); self.idx = 0
        b = self.state[self.idx]; self.idx += 1; return b
    def uni(self, lo=0.0, hi=1.0): return lo + (hi-lo)*(self._next_byte()/255.0)
    def choice(self, seq): return seq[int(self.uni(0,1)*len(seq)) % len(seq)]

def sha_int(s: str) -> int: return int(hashlib.sha256(s.encode("utf-8")).hexdigest(), 16)

def hsl_to_rgb(h, s, l):
    c = (1-abs(2*l-1))*s; hp=h/60.0; x=c*(1-abs(hp%2-1))
    if   0<=hp<1: r1,g1,b1=c,x,0
    elif 1<=hp<2: r1,g1,b1=x,c,0
    elif 2<=hp<3: r1,g1,b1=0,c,x
    elif 3<=hp<4: r1,g1,b1=0,x,c
    elif 4<=hp<5: r1,g1,b1=x,0,c
    else:         r1,g1,b1=c,0,x
    m=l-c/2; return tuple(int(round((v+m)*255)) for v in (r1,g1,b1))

def build_palette(csv_text: str):
    base = sha_int(csv_text) % 360
    hues = [base,(base+20)%360,(base+160)%360,(base+200)%360,(base+300)%360]
    colors = [hsl_to_rgb(H,0.70,0.55) for H in hues]
    accents=[hsl_to_rgb((base+40)%360,0.55,0.70), hsl_to_rgb((base+220)%360,0.50,0.75)]
    return {"paint": colors+accents}

def extract_norm_params(row_vals, need=12):
    vals = [float(v) for v in row_vals if v is not None and str(v).strip()!='' and math.isfinite(float(v))]
    if not vals: vals=[0.0]
    lo,hi=min(vals),max(vals);  hi = hi if hi!=lo else lo+1.0
    norm=[(v-lo)/(hi-lo) for v in vals]
    if len(norm)<need:
        rng=RowRNG(str(vals)); norm += [rng.uni() for _ in range(need-len(norm))]
    return norm[:need]

def quad_bezier(p0,p1,p2,steps=80):
    pts=[]; 
    for i in range(steps+1):
        t=i/steps
        x=(1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t**2*p2[0]
        y=(1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t**2*p2[1]
        pts.append((x,y))
    return pts

def noisy_polyline(points, rng, jitter=2.0):
    return [(x+rng.uni(-1,1)*jitter, y+rng.uni(-1,1)*jitter) for x,y in points]

def draw_blob(layer, center, radius, color, rng):
    cx,cy=center; dl=ImageDraw.Draw(layer,"RGBA")
    rings=3+int(rng.uni(0,3))
    for r_i in range(rings):
        alpha=int(110+80*(1-r_i/(rings-1+1e-6)))
        n=20+int(rng.uni(0,25)); pts=[]
        for k in range(n):
            a=2*math.pi*k/n
            rr=radius*(0.6+0.5*rng.uni())*(0.9+0.15*math.sin(3*a+rng.uni()*2*math.pi))
            pts.append((cx+rr*math.cos(a), cy+rr*math.sin(a)))
        dl.polygon(pts, fill=color+(alpha,))

def draw_splatter(layer, origin, angle_deg, color, rng, count=80, spread=180):
    dl=ImageDraw.Draw(layer,"RGBA"); theta=math.radians(angle_deg)
    for i in range(count):
        t=(i+1)/count; dist=5+spread*(t**1.2)*rng.uni(0.5,1.0); phi=theta+rng.uni(-0.9,0.9)
        x=origin[0]+dist*math.cos(phi); y=origin[1]+dist*math.sin(phi)
        r=1+int(rng.uni(0.0,5.0)*(1.2-t)); alpha=int(80+140*(1-t))
        dl.ellipse([x-r,y-r,x+r,y+r], fill=color+(alpha,))

def render_expressive_from_csv(csv_path, out_path="abstract_expressive_no_arcs.png"):
    df = pd.read_csv(csv_path)
    with open(csv_path,"r",encoding="utf-8") as f: csv_text=f.read()
    pal = build_palette(csv_text)

    base = Image.new("RGBA",(W,H),(250,250,252,255))
    mask = Image.new("L",(W,H),0); md=ImageDraw.Draw(mask)
    cx,cy=W/2,H/2; rx,ry=W*0.46,H*0.40
    md.ellipse([cx-rx,cy-ry,cx+rx,cy+ry], fill=200)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=50))

    paint_layer = Image.new("RGBA",(W,H),(0,0,0,0))

    order = list(range(len(df)))
    if "z" in df.columns: order = list(np.argsort(df["z"].values))

    for idx in order:
        row = df.iloc[idx].to_dict()
        nums=[]
        for k,v in row.items():
            if k in ("shape","z"): continue
            try:
                fv=float(v); 
                if math.isfinite(fv): nums.append(fv)
            except: pass
        norm = extract_norm_params(nums, need=12)
        rng = RowRNG(str(row))

        px = W*0.2 + norm[0]*(W*0.6)
        py = H*0.2 + norm[1]*(H*0.6)
        size = 30 + norm[2]*220
        ang  = norm[3]*360
        width= 3 + int(norm[4]*20)
        vigor= norm[5]
        color = pal["paint"][ sha_int(str(row)) % len(pal["paint"]) ]

        shape = str(row.get("shape","")).strip().lower()
        # REMAP: supprimer arcs → remplacer par 'stroke'
        if shape not in ("blob","stroke","splatter"): 
            shape = "stroke"

        if shape == "blob":
            draw_blob(paint_layer,(px,py),size,color,rng)
        elif shape == "stroke":
            ctrl_dx=(norm[6]-0.5)*size*1.6; ctrl_dy=(norm[7]-0.5)*size*1.6
            theta=math.radians(ang)
            p0=(px-size*math.cos(theta), py-size*math.sin(theta))
            p2=(px+size*math.cos(theta), py+size*math.sin(theta))
            p1=(px+ctrl_dx, py+ctrl_dy)
            pts=noisy_polyline(quad_bezier(p0,p1,p2,steps=80), rng, jitter=2+vigor*3)
            dl=ImageDraw.Draw(paint_layer,"RGBA")
            dl.line(pts, fill=color+(220,), width=width)
            dl.line(pts, fill=color+(110,), width=max(1,int(width*0.5)))
        elif shape == "splatter":
            draw_splatter(paint_layer,(px,py),ang,color,rng,
                          count=60+int(vigor*80), spread=120+int(size))

    painted = Image.composite(paint_layer, Image.new("RGBA",(W,H),(0,0,0,0)), mask)
    out = Image.alpha_composite(base, painted)

    # (Optionnel) si tu veux aussi retirer les micro-splashes noirs de bord,
    # commente totalement la section "edge grime" de ta version précédente.

    out.save(out_path); return out_path

if __name__ == "__main__":
    import os
    if len(sys.argv)<2:
        print("Usage: python expressive_from_csv_no_arcs.py <input.csv> [output.png]")
        sys.exit(1)
    csv_in=sys.argv[1]; out=sys.argv[2] if len(sys.argv)>=3 else "abstract_expressive_no_arcs.png"
    print("Image écrite:", render_expressive_from_csv(csv_in, out))
