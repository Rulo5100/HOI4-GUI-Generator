"""Clickable state maps cut out of the mod's map/provinces.bmp.

`StateMap` finds the provinces of each state (history/states), crops the region around them, scales
it to `width` pixels and produces:

* a backdrop sprite (sea, foreign land, brass frame),
* for every layer, one sprite per state whose frames are the layer's colours (frame 1 = first colour),
* for every layer, a legend swatch strip.

Each state sprite carries its pixel offset on the backdrop (`offset(sprite_name)`), so the GUI can
place the pieces exactly. Wire a frame variable per state (see frames.Thresholds / frames.Flags) to
colour them in game.

Requires numpy.
"""
import glob
import os
import re

from PIL import Image, ImageDraw, ImageFilter

from .sprites import Sprite, Swatches

Image.MAX_IMAGE_PIXELS = None


class _MapPiece(Sprite):
    def __init__(self, name, texture, frames, draw):
        super().__init__(name, texture, frames)
        self._draw = draw

    def render(self, t):
        return self._draw(t)


class StateMap:
    def __init__(self, fs, states, sprite_prefix, file_prefix, png_dir, layers, width=270, pad=18,
                 bg_name="map_bg", key_size=14):
        """layers: list of (layer_name, [colours]) e.g. [("map", TIER_COL), ("pmap", PLAN_COL)].

        Sprites are named f"{sprite_prefix}{layer}_{state}" with textures f"{png_dir}/{file_prefix}{layer}_{state}.png".
        """
        self.fs, self.states = fs, list(states)
        self.sprite_prefix, self.file_prefix, self.png_dir = sprite_prefix, file_prefix, png_dir.rstrip("/")
        self.layers = layers
        self.width, self.pad, self.bg_name, self.key_size = width, pad, bg_name, key_size
        self._d = None
        self.offs, self.centre = {}, {}

    # ------------------------------------------------------------------ data
    def state_provinces(self, sid):
        files = [x for x in glob.glob(os.path.join(self.fs.root, "history/states/*.txt")) if re.match(rf"{sid}\s*-", os.path.basename(x))]
        if not files:
            raise FileNotFoundError(f"no history/states file for state {sid}")
        with open(files[0], encoding="utf-8-sig", errors="ignore") as f:
            t = f.read()
        return [int(x) for x in re.search(r"provinces\s*=\s*\{([^}]*)\}", t).group(1).split()]

    def data(self):
        if self._d:
            return self._d
        import numpy as np
        root = self.fs.root
        im = np.array(Image.open(os.path.join(root, "map/provinces.bmp")).convert("RGB"))
        key = (im[:, :, 0].astype(np.int32) << 16) | (im[:, :, 1].astype(np.int32) << 8) | im[:, :, 2]
        col, typ = {}, {}
        with open(os.path.join(root, "map/definition.csv"), encoding="utf-8", errors="ignore") as f:
            for line in f:
                p = line.strip().split(";")
                if len(p) >= 5 and p[0].isdigit():
                    col[int(p[0])] = (int(p[1]) << 16) | (int(p[2]) << 8) | int(p[3])
                    typ[int(p[0])] = p[4]
        masks = {s: np.isin(key, np.array([col[p] for p in self.state_provinces(s)])) for s in self.states}
        allm = np.zeros_like(masks[self.states[0]])
        for s in self.states:
            allm |= masks[s]
        ys, xs = np.nonzero(allm)
        pad = self.pad
        x0, x1, y0, y1 = max(xs.min() - pad, 0), xs.max() + pad, max(ys.min() - pad, 0), ys.max() + pad
        sea_keys = np.array([c for i, c in col.items() if typ[i] in ("sea", "lake")])
        crop = key[y0:y1, x0:x1]
        sea = np.isin(crop, sea_keys)
        sc = self.width / (x1 - x0)
        self._d = dict(masks={s: m[y0:y1, x0:x1] for s, m in masks.items()}, sea=sea, sc=sc,
                       size=(int((x1 - x0) * sc), int((y1 - y0) * sc)))
        return self._d

    @property
    def size(self):
        return self.data()["size"]

    @staticmethod
    def _down(mask, size):
        import numpy as np
        return Image.fromarray((mask * 255).astype(np.uint8)).resize(size, Image.LANCZOS)

    # ------------------------------------------------------------------ sprites
    def sprite_name(self, layer, sid):
        return f"{self.sprite_prefix}{layer}_{sid}"

    @property
    def bg_sprite(self):
        return f"{self.sprite_prefix}{self.bg_name}"

    def key_sprite(self, layer):
        return f"{self.sprite_prefix}{layer}_key"

    def offset(self, sprite_name):
        return self.offs[sprite_name]

    def sprites(self):
        """All map sprites in .gfx order: backdrop, per state each layer, then the legend keys."""
        D = self.data()
        W, H = D["size"]
        out = []

        def draw_bg(t):
            land = self._down(~D["sea"], (W, H))
            bg = Image.new("RGBA", (W, H), t.map_sea)
            bg.paste(Image.new("RGBA", (W, H), t.map_land), (0, 0), land)
            frame = Image.new("RGBA", (W + 6, H + 6), (0, 0, 0, 0))
            ImageDraw.Draw(frame).rounded_rectangle([0, 0, W + 5, H + 5], 6, fill=t.outline)
            frame.paste(bg, (3, 3))
            return frame
        out.append(_MapPiece(self.bg_sprite, f"{self.png_dir}/{self.file_prefix}{self.bg_name}.png", 1, draw_bg))
        import numpy as np
        for s in self.states:
            m = self._down(D["masks"][s], (W, H))
            a = np.array(m)
            ys, xs = np.nonzero(a > 40)
            bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
            mc = m.crop((bx0, by0, bx1, by1))
            ring = mc.filter(ImageFilter.MaxFilter(3))
            for layer, cols in self.layers:
                def draw(t, mc=mc, ring=ring, cols=cols):
                    w, h = mc.size
                    strip = Image.new("RGBA", (w * len(cols), h), (0, 0, 0, 0))
                    for f, c in enumerate(cols):
                        fill = Image.new("RGBA", (w, h), t.colour(c) + (255,))
                        outline = Image.new("RGBA", (w, h), t.dark_line)
                        cell = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                        cell.paste(outline, (0, 0), ring)
                        cell.paste(fill, (0, 0), mc.point(lambda v: 255 if v > 150 else 0))
                        strip.paste(cell, (f * w, 0))
                    return strip
                name = self.sprite_name(layer, s)
                out.append(_MapPiece(name, f"{self.png_dir}/{self.file_prefix}{layer}_{s}.png", len(cols), draw))
                self.offs[name] = (int(bx0) + 3, int(by0) + 3)
            cy, cx = np.nonzero(a > 150)
            self.centre[s] = (int(cx.mean()) + 3, int(cy.mean()) + 3)
        for layer, cols in self.layers:
            out.append(Swatches(self.key_sprite(layer), f"{self.png_dir}/{self.file_prefix}{layer}_key.png", cols, self.key_size))
        return out
