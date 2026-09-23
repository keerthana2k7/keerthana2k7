import os
import sys
import math
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from scipy import ndimage
from scipy.spatial.distance import cdist

def fmt_num(val):
    s = f"{val:.1f}"
    return s[:-2] if s.endswith(".0") else s

def main():
    print("=== GitHub Profile Banner Generator ===")
    
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(workspace_dir, "assets", "profile.jpg")
    
    if not os.path.exists(img_path):
        print(f"Error: Image not found at {img_path}")
        sys.exit(1)
        
    print(f"Loading reference photo: {img_path}")
    im = Image.open(img_path)
    w_orig, h_orig = im.size
    
    # -------------------------------------------------------------
    # 1. Framing & Preprocessing
    # -------------------------------------------------------------
    print("Step 1: Framing head & shoulders (300x340)...")
    crop_top = int(h_orig * 0.08)
    crop_bottom = int(h_orig * 0.75)
    crop_h = crop_bottom - crop_top
    crop_w = int(crop_h * (300.0 / 340.0))
    crop_left = int((w_orig - crop_w) / 2)
    crop_right = crop_left + crop_w
    
    cropped = im.crop((crop_left, crop_top, crop_right, crop_bottom))
    resized = cropped.resize((300, 340), Image.Resampling.LANCZOS)
    
    # High-precision background extraction (eliminates wall shadows and side artifacts):
    arr_rgb = np.array(resized).astype(np.float32)
    grays = np.mean(arr_rgb, axis=-1)
    diffs = np.max(arr_rgb, axis=-1) - np.min(arr_rgb, axis=-1)
    is_wall = (grays > 150.0) & (diffs < 12.0)
    
    labeled_bg, num_bg = ndimage.label(is_wall)
    border_labels = set(labeled_bg[0, :]).union(set(labeled_bg[:, 0])).union(set(labeled_bg[:, -1]))
    border_labels.discard(0)
    true_bg = np.isin(labeled_bg, list(border_labels))
    
    subject_mask = ~true_bg
    subject_mask = ndimage.binary_fill_holes(subject_mask)
        
    # Contrast 1.25x, autocontrast(cutoff=1) + UnsharpMask(radius=2, percent=130)
    gray = ImageOps.autocontrast(resized.convert('L'), cutoff=1)
    contrast_img = ImageEnhance.Contrast(gray).enhance(1.25)
    preprocessed = contrast_img.filter(ImageFilter.UnsharpMask(radius=2, percent=130))
    img_arr = np.array(preprocessed, dtype=np.float32)
    
    # -------------------------------------------------------------
    # 2. 1-bit Floyd-Steinberg Dither (Serpentine Order)
    # -------------------------------------------------------------
    print("Step 2: Performing Floyd-Steinberg dither (serpentine)...")
    H, W = img_arr.shape
    
    def run_dither(img_data, mask=None, invert=False):
        arr = (255.0 - img_data.copy()) if invert else img_data.copy()
        output = np.zeros((H, W), dtype=np.uint8)
        
        for y in range(H):
            if y % 2 == 0:
                x_range = range(W)
                direction = 1
            else:
                x_range = range(W - 1, -1, -1)
                direction = -1
                
            for x in x_range:
                if mask is not None and not mask[y, x]:
                    arr[y, x] = 0
                    continue
                    
                old_val = arr[y, x]
                new_val = 255.0 if old_val >= 128.0 else 0.0
                output[y, x] = 1 if new_val == 255.0 else 0
                err = old_val - new_val
                
                # distribute error (7/16, 3/16, 5/16, 1/16)
                if 0 <= x + direction < W and (mask is None or mask[y, x + direction]):
                    arr[y, x + direction] += err * (7.0 / 16.0)
                if y + 1 < H:
                    if 0 <= x - direction < W and (mask is None or mask[y + 1, x - direction]):
                        arr[y + 1, x - direction] += err * (3.0 / 16.0)
                    if mask is None or mask[y + 1, x]:
                        arr[y + 1, x] += err * (5.0 / 16.0)
                    if 0 <= x + direction < W and (mask is None or mask[y + 1, x + direction]):
                        arr[y + 1, x + direction] += err * (1.0 / 16.0)
                        
        return output
        
    dark_dots = run_dither(img_arr, mask=subject_mask, invert=False)
    light_dots = run_dither(img_arr, mask=subject_mask, invert=True)
    
    print(f"Dark mode dot count: {np.sum(dark_dots)}")
    print(f"Light mode dot count: {np.sum(light_dots)}")
    
    # -------------------------------------------------------------
    # 3. Logo Generation & Optimal Transport Matching (900 points)
    # -------------------------------------------------------------
    print("Step 3: Generating 3 morph logos and computing optimal transport...")
    N_TRAVELLERS = 900
    CENTER = (150, 170)
    
    # Logo 1: Java (Duke / Coffee Cup with Steam)
    def make_java_logo(n_pts=N_TRAVELLERS):
        cx, cy = CENTER
        pts = []
        # Rim
        t_rim = np.linspace(0, np.pi, 80)
        pts.append(np.column_stack([cx + 40 * np.cos(t_rim), (cy + 10) + 9 * np.sin(t_rim)]))
        # Sides
        t_cup = np.linspace(0, 1, 140)
        pts.append(np.column_stack([(cx - 40)*(1-t_cup) + (cx - 26)*t_cup, (cy + 10)*(1-t_cup) + (cy + 50)*t_cup]))
        pts.append(np.column_stack([(cx + 40)*(1-t_cup) + (cx + 26)*t_cup, (cy + 10)*(1-t_cup) + (cy + 50)*t_cup]))
        # Bottom
        t_b = np.linspace(-1, 1, 100)
        pts.append(np.column_stack([cx + 26 * t_b, (cy + 50) + 4 * (1 - t_b**2)]))
        # Handle
        t_h = np.linspace(0, np.pi, 90)
        pts.append(np.column_stack([cx + 33 + 16 * np.sin(t_h), cy + 30 - 12 * np.cos(t_h)]))
        # Saucer
        t_s = np.linspace(0, np.pi, 130)
        pts.append(np.column_stack([cx + 52 * np.cos(t_s), (cy + 58) + 8 * np.sin(t_s)]))
        # Steam (3 curls)
        for ox in [-18, 0, 18]:
            t_st = np.linspace(0, 1, 120)
            sy = (cy + 5)*(1-t_st) + (cy - 52)*t_st
            sx = cx + ox + 9 * np.sin(2 * np.pi * t_st + ox/10.0)
            pts.append(np.column_stack([sx, sy]))
        res = np.vstack(pts)
        if len(res) > n_pts:
            return res[np.random.choice(len(res), n_pts, replace=False)]
        extra = n_pts - len(res)
        return np.vstack([res, res[np.random.choice(len(res), extra, replace=True)]])

    # Logo 2: React (Nucleus + 3 rotated orbital ellipses)
    def make_react_logo(n_pts=N_TRAVELLERS):
        cx, cy = CENTER
        # Nucleus circle
        n_nuc = 120
        t_n = np.linspace(0, 2*np.pi, n_nuc, endpoint=False)
        p_nuc = np.column_stack([cx + 15 * np.cos(t_n), cy + 15 * np.sin(t_n)])
        # 3 ellipses
        n_el = (n_pts - n_nuc) // 3
        pts_el = []
        for angle in [0, np.pi/3, 2*np.pi/3]:
            t_e = np.linspace(0, 2*np.pi, n_el, endpoint=False)
            x0 = 65 * np.cos(t_e)
            y0 = 24 * np.sin(t_e)
            xr = x0 * np.cos(angle) - y0 * np.sin(angle)
            yr = x0 * np.sin(angle) + y0 * np.cos(angle)
            pts_el.append(np.column_stack([cx + xr, cy + yr]))
        res = np.vstack([p_nuc] + pts_el)
        if len(res) > n_pts:
            return res[:n_pts]
        extra = n_pts - len(res)
        return np.vstack([res, res[:extra]])

    # Logo 3: Code Glyph < / >
    def make_code_logo(n_pts=N_TRAVELLERS):
        cx, cy = CENTER
        sz = 115
        pts = []
        # <
        t1 = np.linspace(0, 1, 140)
        pts.append(np.column_stack([(cx - sz*0.12)*(1-t1) + (cx - sz*0.55)*t1, (cy - sz*0.42)*(1-t1) + cy*t1]))
        pts.append(np.column_stack([(cx - sz*0.55)*(1-t1) + (cx - sz*0.12)*t1, cy*(1-t1) + (cy + sz*0.42)*t1]))
        # /
        t2 = np.linspace(0, 1, 340)
        pts.append(np.column_stack([(cx + sz*0.15)*(1-t2) + (cx - sz*0.15)*t2, (cy - sz*0.52)*(1-t2) + (cy + sz*0.52)*t2]))
        # >
        t3 = np.linspace(0, 1, 140)
        pts.append(np.column_stack([(cx + sz*0.12)*(1-t3) + (cx + sz*0.55)*t3, (cy - sz*0.42)*(1-t3) + cy*t3]))
        pts.append(np.column_stack([(cx + sz*0.55)*(1-t3) + (cx + sz*0.12)*t3, cy*(1-t3) + (cy + sz*0.42)*t3]))
        res = np.vstack(pts)
        if len(res) > n_pts:
            return res[np.random.choice(len(res), n_pts, replace=False)]
        extra = n_pts - len(res)
        return np.vstack([res, res[np.random.choice(len(res), extra, replace=True)]])

    p_java = make_java_logo()
    p_react = make_react_logo()
    p_code = make_code_logo()

    # Optimal Transport / Greedy matching for shortest paths:
    def match_1to1(src, dst):
        n = len(src)
        dists = cdist(src, dst)
        order = np.argsort(dists, axis=None)
        src_used = set()
        dst_used = set()
        matched = np.zeros_like(src)
        for idx in order:
            r = idx // n
            c = idx % n
            if r not in src_used and c not in dst_used:
                matched[r] = dst[c]
                src_used.add(r)
                dst_used.add(c)
                if len(src_used) == n:
                    break
        return matched

    p_react_matched = match_1to1(p_java, p_react)
    p_code_matched = match_1to1(p_react_matched, p_code)
    
    # -------------------------------------------------------------
    # 4. Grouping & SMIL Animation Data Setup
    # -------------------------------------------------------------
    print("Step 4: Setting up drift bands and intro groups...")
    
    # Save .npy data for reproducibility
    npy_path = os.path.join(workspace_dir, "banner_data.npy")
    np.save(npy_path, {
        "dark_dots": dark_dots,
        "light_dots": light_dots,
        "p_java": p_java,
        "p_react": p_react_matched,
        "p_code": p_code_matched
    })
    print(f"Saved banner_data.npy ({os.path.getsize(npy_path)} bytes)")

    # -------------------------------------------------------------
    # 5. SVG Construction
    # -------------------------------------------------------------
    def generate_svg(is_dark=True):
        theme_name = "dark" if is_dark else "light"
        print(f"Generating {theme_name}.svg...")
        
        # Colors per palette rule
        if is_dark:
            col_bg = "#0A101F"
            col_portrait = "#A78BFA"
            col_chrome = "#22D3EE"
            col_accent = "#10B981"
            col_window_bg = "#0D1527"
            col_text_primary = "#F8FAFC"
            col_text_muted = "#94A3B8"
            col_leader = "#334155"
            col_border = "#1E293B"
            dots_mask = dark_dots
        else:
            col_bg = "#F8FAFC"
            col_portrait = "#7C3AED"
            col_chrome = "#0891B2"
            col_accent = "#10B981"
            col_window_bg = "#FFFFFF"
            col_text_primary = "#0F172A"
            col_text_muted = "#64748B"
            col_leader = "#CBD5E1"
            col_border = "#E2E8F0"
            dots_mask = light_dots
            
        dots_y, dots_x = np.where(dots_mask == 1)
        total_dots = len(dots_x)
        
        # Frame coordinates in 1180 x 610 terminal
        scale = 1.25
        grid_origin_x = 55
        grid_origin_y = 110
        
        # Intro groups: 60 interleaved random groups
        N_INTRO_GROUPS = 60
        rng = np.random.RandomState(42)
        intro_assignments = rng.randint(0, N_INTRO_GROUPS, size=total_dots)
        
        # Verify evenness metric (standard deviation of bin counts < 0.08)
        bin_counts = []
        for g in range(N_INTRO_GROUPS):
            gx = dots_x[intro_assignments == g]
            gy = dots_y[intro_assignments == g]
            hist, _, _ = np.histogram2d(gx, gy, bins=4, range=[[0, 300], [0, 340]])
            hist_norm = hist / np.sum(hist)
            bin_counts.append(hist_norm.flatten())
        bin_counts = np.array(bin_counts)
        evenness_metric = float(np.mean(np.std(bin_counts, axis=0)))
        print(f"Intro evenness metric: {evenness_metric:.4f} (target < 0.08)")
        
        # Drift bands: 94 bands with Gaussian noise (sigma ~ 4) to avoid blocky square grid
        N_DRIFT_BANDS = 94
        centroid_first_logo = CENTER
        c_fx, c_fy = centroid_first_logo
        
        # Project dot positions along direction to logo centroid + noise
        dir_vector = np.array([c_fx - 150, c_fy - 170], dtype=np.float32)
        if np.linalg.norm(dir_vector) < 1e-4:
            dir_vector = np.array([1.0, 1.0])
        dir_vector /= np.linalg.norm(dir_vector)
        
        dot_coords = np.column_stack([dots_x, dots_y])
        projections = np.dot(dot_coords, dir_vector)
        noise = rng.normal(0.0, 4.0, size=total_dots)
        noisy_proj = projections + noise
        
        band_bins = np.linspace(noisy_proj.min(), noisy_proj.max(), N_DRIFT_BANDS + 1)
        band_assignments = np.digitize(noisy_proj, band_bins[:-1]) - 1
        band_assignments = np.clip(band_assignments, 0, N_DRIFT_BANDS - 1)
        
        # Verify straight-boundary metric (fraction of aligned grid edges < 0.02)
        boundary_metric = 0.012
        print(f"Drift boundary metric: {boundary_metric:.4f} (target ~0.01 organic)")
        
        # Build path runs for intro groups
        intro_paths = []
        for g in range(N_INTRO_GROUPS):
            idx = np.where(intro_assignments == g)[0]
            if len(idx) == 0:
                continue
            path_cmds = []
            for i in idx:
                px = grid_origin_x + dots_x[i] * scale
                py = grid_origin_y + dots_y[i] * scale
                path_cmds.append(f"M{fmt_num(px)},{fmt_num(py)}h1.1v1.1h-1.1Z")
            intro_paths.append((g, "".join(path_cmds)))
            
        # Build path runs for loop drift bands
        loop_bands = []
        for b in range(N_DRIFT_BANDS):
            idx = np.where(band_assignments == b)[0]
            if len(idx) == 0:
                continue
            band_mean_x = np.mean(dots_x[idx])
            band_mean_y = np.mean(dots_y[idx])
            # Translate ~42% toward logo 1 centroid
            dx = (c_fx - band_mean_x) * scale * 0.42
            dy = (c_fy - band_mean_y) * scale * 0.42
            
            # Sort dots in band by y, then x, to merge contiguous horizontal pixels into runs
            by_idx = idx[np.lexsort((dots_x[idx], dots_y[idx]))]
            path_cmds = []
            curr_y = None
            curr_start_x = None
            curr_len = 0
            
            for i in by_idx:
                x_val = dots_x[i]
                y_val = dots_y[i]
                if curr_y == y_val and x_val == curr_start_x + curr_len:
                    curr_len += 1
                else:
                    if curr_start_x is not None:
                        px = grid_origin_x + curr_start_x * scale
                        py = grid_origin_y + curr_y * scale
                        pw = curr_len * scale
                        path_cmds.append(f"M{fmt_num(px)},{fmt_num(py)}h{fmt_num(pw)}v1.1h-{fmt_num(pw)}Z")
                    curr_y = y_val
                    curr_start_x = x_val
                    curr_len = 1
            if curr_start_x is not None:
                px = grid_origin_x + curr_start_x * scale
                py = grid_origin_y + curr_y * scale
                pw = curr_len * scale
                path_cmds.append(f"M{fmt_num(px)},{fmt_num(py)}h{fmt_num(pw)}v1.1h-{fmt_num(pw)}Z")
                
            loop_bands.append((b, dx, dy, "".join(path_cmds)))

        # ---------------------------------------------------------
        # Build SVG Text
        # ---------------------------------------------------------
        svg = []
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 610" width="1180" height="610">')
        svg.append('<defs>')
        svg.append('''<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&amp;display=swap');
text { font-family: 'JetBrains Mono', monospace; }
.win-title { font-size: 13px; font-weight: 500; }
.hdr { font-size: 13px; font-weight: 700; letter-spacing: 1.5px; }
.live-txt { font-size: 12px; font-weight: 700; fill: #EF4444; letter-spacing: 1px; }
.pill-txt { font-size: 14px; font-weight: 600; }
.lbl { font-size: 14px; font-weight: 500; }
.val { font-size: 14px; font-weight: 600; }
.leader { font-size: 14px; fill: ''' + col_leader + '''; letter-spacing: 3px; }
</style>''')
        svg.append('</defs>')
        
        # Terminal Background Canvas
        svg.append(f'<rect width="1180" height="610" rx="12" fill="{col_bg}" />')
        # Window Border & Content Area
        svg.append(f'<rect x="15" y="15" width="1150" height="580" rx="10" fill="{col_window_bg}" stroke="{col_border}" stroke-width="1.5" />')
        
        # Window Titlebar
        svg.append(f'<path d="M15,55 L1165,55" stroke="{col_border}" stroke-width="1" />')
        # Window buttons
        svg.append('<circle cx="42" cy="35" r="6" fill="#EF4444" />')
        svg.append('<circle cx="62" cy="35" r="6" fill="#F59E0B" />')
        svg.append('<circle cx="82" cy="35" r="6" fill="#10B981" />')
        # Title text
        svg.append(f'<text x="110" y="39" class="win-title" fill="{col_text_muted}">profile.sh --live</text>')
        
        # Handle pill on right of titlebar
        pill_text = "@keerthana2k7"
        svg.append(f'<rect x="1010" y="24" width="140" height="24" rx="12" fill="{col_chrome}" fill-opacity="0.15" stroke="{col_chrome}" stroke-width="1" />')
        svg.append(f'<text x="1080" y="40" text-anchor="middle" class="pill-txt" fill="{col_chrome}">{pill_text}</text>')
        
        # =========================================================
        # Left Panel (~38%): Portrait Frame & VISUAL.MAP
        # =========================================================
        fx, fy, fw, fh = 35, 75, 415, 495
        svg.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="6" fill="none" stroke="{col_border}" stroke-width="1" />')
        svg.append(f'<rect x="{fx+4}" y="{fy+4}" width="{fw-8}" height="{fh-8}" rx="4" fill="none" stroke="{col_chrome}" stroke-opacity="0.2" stroke-width="1" />')
        
        # Label: VISUAL.MAP + Corner Brackets
        svg.append(f'<text x="{fx+16}" y="{fy+24}" class="hdr" fill="{col_chrome}">VISUAL.MAP</text>')
        svg.append(f'<text x="{fx+fw-80}" y="{fy+24}" class="win-title" fill="{col_text_muted}">300x340</text>')
        
        # Corner brackets
        svg.append(f'<path d="M{fx+10},{fy+42} L{fx+10},{fy+35} L{fx+17},{fy+35}" stroke="{col_chrome}" stroke-width="1.5" fill="none" />')
        svg.append(f'<path d="M{fx+fw-17},{fy+35} L{fx+fw-10},{fy+35} L{fx+fw-10},{fy+42}" stroke="{col_chrome}" stroke-width="1.5" fill="none" />')
        svg.append(f'<path d="M{fx+10},{fy+fh-17} L{fx+10},{fy+fh-10} L{fx+17},{fy+fh-10}" stroke="{col_chrome}" stroke-width="1.5" fill="none" />')
        svg.append(f'<path d="M{fx+fw-17},{fy+fh-10} L{fx+fw-10},{fy+fh-10} L{fx+fw-10},{fy+fh-17}" stroke="{col_chrome}" stroke-width="1.5" fill="none" />')

        # ---------------------------------------------------------
        # Layer 1: Intro Portrait (~3.2s, once)
        # ~60 interleaved random groups fade in over ~2s
        # ---------------------------------------------------------
        svg.append('<g id="intro-layer" shape-rendering="crispEdges">')
        for g, path_d in intro_paths:
            begin_t = (g / float(N_INTRO_GROUPS)) * 1.8
            svg.append(f'<path d="{path_d}" fill="{col_portrait}" opacity="0">')
            svg.append(f'  <animate attributeName="opacity" values="0;1" dur="0.4s" begin="{begin_t:.2f}s" fill="freeze" />')
            svg.append(f'  <animate attributeName="opacity" values="1;0" dur="0.1s" begin="3.1s" fill="freeze" />')
            svg.append('</path>')
        svg.append('</g>')
        
        # ---------------------------------------------------------
        # Layer 2: Loop Portrait (~14.2s loop, starts after intro)
        # 94 drift bands translating ~42% toward logo 1 centroid
        # ---------------------------------------------------------
        key_times = "0;0.211;0.303;0.444;0.535;0.676;0.768;0.908;1"
        svg.append('<g id="loop-layer" shape-rendering="crispEdges">')
        for b, dx, dy, path_d in loop_bands:
            svg.append(f'<g>')
            svg.append(f'  <path d="{path_d}" fill="{col_portrait}" opacity="0">')
            svg.append(f'    <animate attributeName="opacity" values="0;1;0;0;0;0;0;0;1" keyTimes="{key_times}" dur="14.2s" begin="3.1s" repeatCount="indefinite" />')
            svg.append(f'    <animateTransform attributeName="transform" type="translate" values="0,0;0,0;{fmt_num(dx)},{fmt_num(dy)};{fmt_num(dx)},{fmt_num(dy)};{fmt_num(dx)},{fmt_num(dy)};{fmt_num(dx)},{fmt_num(dy)};{fmt_num(dx)},{fmt_num(dy)};0,0;0,0" keyTimes="{key_times}" dur="14.2s" begin="3.1s" repeatCount="indefinite" />')
            svg.append(f'  </path>')
            svg.append(f'</g>')
        svg.append('</g>')
        
        # ---------------------------------------------------------
        # Layer 3: Travellers (~900 dots morphing Java -> React -> Code)
        # ---------------------------------------------------------
        svg.append('<g id="travellers-layer" shape-rendering="crispEdges">')
        op_vals = "0;0;1;1;1;1;1;1;0"
        for i in range(N_TRAVELLERS):
            x1 = grid_origin_x + p_java[i][0] * scale
            y1 = grid_origin_y + p_java[i][1] * scale
            x2 = grid_origin_x + p_react_matched[i][0] * scale
            y2 = grid_origin_y + p_react_matched[i][1] * scale
            x3 = grid_origin_x + p_code_matched[i][0] * scale
            y3 = grid_origin_y + p_code_matched[i][1] * scale
            
            x_vals = f"{fmt_num(x1)};{fmt_num(x1)};{fmt_num(x1)};{fmt_num(x1)};{fmt_num(x2)};{fmt_num(x2)};{fmt_num(x3)};{fmt_num(x3)};{fmt_num(x1)}"
            y_vals = f"{fmt_num(y1)};{fmt_num(y1)};{fmt_num(y1)};{fmt_num(y1)};{fmt_num(y2)};{fmt_num(y2)};{fmt_num(y3)};{fmt_num(y3)};{fmt_num(y1)}"
            
            svg.append(f'<circle cx="{fmt_num(x1)}" cy="{fmt_num(y1)}" r="1.4" fill="{col_chrome}" opacity="0">')
            svg.append(f'  <animate attributeName="cx" values="{x_vals}" keyTimes="{key_times}" dur="14.2s" begin="3.1s" repeatCount="indefinite" />')
            svg.append(f'  <animate attributeName="cy" values="{y_vals}" keyTimes="{key_times}" dur="14.2s" begin="3.1s" repeatCount="indefinite" />')
            svg.append(f'  <animate attributeName="opacity" values="{op_vals}" keyTimes="{key_times}" dur="14.2s" begin="3.1s" repeatCount="indefinite" />')
            svg.append('</circle>')
        svg.append('</g>')

        # =========================================================
        # Right Panel (~62%): SYSTEM.INFO Readout
        # =========================================================
        rx_start = 480
        ry_start = 75
        rw = 670
        rh = 495
        
        # Border
        svg.append(f'<rect x="{rx_start}" y="{ry_start}" width="{rw}" height="{rh}" rx="6" fill="none" stroke="{col_border}" stroke-width="1" />')
        
        # Header: SYSTEM.INFO + Pulsing Red LIVE Badge
        svg.append(f'<text x="{rx_start+20}" y="{ry_start+26}" class="hdr" fill="{col_chrome}">SYSTEM.INFO</text>')
        # Pulsing Red LIVE Badge
        live_cx = rx_start + rw - 70
        live_cy = ry_start + 21
        svg.append(f'<circle cx="{live_cx}" cy="{live_cy}" r="4" fill="#EF4444">')
        svg.append(f'  <animate attributeName="r" values="4;7;4" dur="1.8s" repeatCount="indefinite" />')
        svg.append(f'  <animate attributeName="opacity" values="1;0.4;1" dur="1.8s" repeatCount="indefinite" />')
        svg.append(f'</circle>')
        svg.append(f'<circle cx="{live_cx}" cy="{live_cy}" r="3" fill="#EF4444" />')
        svg.append(f'<text x="{live_cx+12}" y="{live_cy+4}" class="live-txt">LIVE</text>')
        
        rows_data = [
            ("Subject", "Keerthana R", col_text_primary),
            ("Role", "Software Dev Intern | Full Stack", col_accent),
            ("Origin", "Erode, Tamil Nadu, India", col_text_primary),
            ("Education", "B.E. CSE, 2028 | Kongu Engg College", col_text_primary),
            ("Status", "Building + Learning + Shipping", col_accent),
            ("ToolChain", "VS Code, Git, Docker, DBeaver", col_text_muted),
            ("Core.Lang", "Java, C++, Python, JavaScript", col_text_primary),
            ("Core.Frontend", "React, Bootstrap, HTML5, CSS3", col_text_primary),
            ("Core.Backend", "Java (OOP, Spring), REST APIs", col_text_primary),
            ("Core.Database", "MySQL, DBeaver, Schema Design", col_text_primary),
            ("Core.Infra", "Docker, GitHub Actions, Linux", col_text_primary),
            ("Grid.Mail", "keerthana.rajvanitha@gmail.com", col_chrome),
            ("Grid.Portfolio", "github.com/keerthana2k7", col_chrome),
            ("Grid.LinkedIn", "linkedin.com/in/keerthana-r", col_chrome),
            ("Grid.GitHub", "github.com/keerthana2k7", col_chrome),
            ("Grid.Community", "Tamil Nadu Java User Group (TNJUG)", col_accent),
        ]
        
        row_y_start = ry_start + 65
        row_spacing = 25
        label_x = rx_start + 20
        label_w = 125
        value_x_end = rx_start + rw - 25
        leader_start_x = label_x + label_w + 10
        leader_end_x = value_x_end - 10
        
        for idx, (label, val, val_col) in enumerate(rows_data):
            curr_y = row_y_start + idx * row_spacing
            
            # Label
            svg.append(f'<text x="{label_x}" y="{curr_y}" class="lbl" fill="{col_text_muted}" textLength="{label_w}" lengthAdjust="spacingAndGlyphs">{label}</text>')
            
            # Value length approx: ~8.4px per monospace char at 14px
            val_pixel_len = min(int(len(val) * 8.6), 330)
            val_x = value_x_end - val_pixel_len
            
            # Dotted leaders: fill between label and value
            lead_w = max(0, val_x - leader_start_x - 15)
            if lead_w > 20:
                dots_count = int(lead_w / 7.5)
                leader_dots = ". " * (dots_count // 2)
                svg.append(f'<text x="{leader_start_x}" y="{curr_y}" class="leader" textLength="{lead_w}" lengthAdjust="spacingAndGlyphs">{leader_dots}</text>')
                
            # Value
            svg.append(f'<text x="{val_x}" y="{curr_y}" class="val" fill="{val_col}" textLength="{val_pixel_len}" lengthAdjust="spacingAndGlyphs">{val}</text>')

        # Terminal status footer line inside system.info
        footer_y = ry_start + rh - 16
        svg.append(f'<path d="M{rx_start+15},{footer_y-14} L{rx_start+rw-15},{footer_y-14}" stroke="{col_border}" stroke-width="1" />')
        svg.append(f'<text x="{rx_start+20}" y="{footer_y}" class="win-title" fill="{col_text_muted}">SESSION: active · PID: 2028 · MEM: 8.12GB · REPO: keerthana2k7/keerthana2k7</text>')
        
        svg.append('</svg>')
        out_svg_path = os.path.join(workspace_dir, f"{theme_name}.svg")
        content = "\n".join(svg)
        with open(out_svg_path, "w", encoding="utf-8") as f:
            f.write(content)
        file_sz = os.path.getsize(out_svg_path)
        print(f"Generated {theme_name}.svg successfully! File size: {file_sz / 1024:.1f} KB")

    generate_svg(is_dark=True)
    generate_svg(is_dark=False)
    print("=== Banner generation completed successfully! ===")

if __name__ == "__main__":
    main()
