"""GUI element model and .gui emission.

Each element knows how to print itself as Paradox script. The key order and whitespace are fixed
(tabs, one attribute per line), so a rebuild is byte-identical and diffs stay readable.

Sizes (`w`, `h`) are kept on every element, even where the .gui file does not need them (icons,
buttons), so the layout helpers, the validator and the preview renderer can reason about extents.
"""


def num(v):
    """Paradox-friendly number: 10 not 10.0, 0.5 stays 0.5."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


class Element:
    kind = "element"

    def __init__(self, name, x, y, w=0, h=0, tooltip=None, extra=None):
        self.name, self.x, self.y = name, x, y
        self.w, self.h = w, h
        self.tooltip = tooltip
        self.extra = list((extra or {}).items()) if isinstance(extra, dict) else list(extra or [])
        self.board = None
        self.meta = {}             # free slot for widgets / preview hints

    def _extra(self, pad):
        out = ""
        for k, v in self.extra:
            out += f"{pad}{k} = {v}\n"
        return out

    def bbox(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def emit(self, level=2):
        raise NotImplementedError


class Text(Element):
    """instantTextBoxType. `fmt=None` leaves out the format line (engine default: left)."""
    kind = "text"

    def __init__(self, name, x, y, text, w, h=20, font="hoi_16mbs", fmt="left", tooltip=None, extra=None):
        super().__init__(name, x, y, w, h, tooltip, extra)
        self.text, self.font, self.fmt = text, font, fmt

    def emit(self, level=2):
        p, q = "\t" * level, "\t" * (level + 1)
        s = (f"{p}instantTextBoxType = {{\n{q}name = \"{self.name}\"\n{q}position = {{ x = {self.x} y = {self.y} }}\n"
             f"{q}font = \"{self.font}\"\n{q}text = \"{self.text}\"\n{q}maxWidth = {self.w}\n{q}maxHeight = {self.h}\n"
             f"{q}fixedsize = yes\n")
        if self.fmt:
            s += f"{q}format = {self.fmt}\n"
        if self.tooltip:
            s += f"{q}pdx_tooltip = \"{self.tooltip}\"\n"
        return s + self._extra(q) + f"{p}}}\n"


class Icon(Element):
    """iconType. `frame=None` leaves out the frame line (single-frame sprites)."""
    kind = "icon"

    def __init__(self, name, x, y, sprite, frame=1, scale=None, tooltip=None, w=0, h=0, extra=None):
        super().__init__(name, x, y, w, h, tooltip, extra)
        self.sprite, self.frame, self.scale = sprite, frame, scale

    def emit(self, level=2):
        p, q = "\t" * level, "\t" * (level + 1)
        s = f"{p}iconType = {{\n{q}name = \"{self.name}\"\n{q}position = {{ x = {self.x} y = {self.y} }}\n{q}spriteType = \"{self.sprite}\"\n"
        if self.frame is not None:
            s += f"{q}frame = {self.frame}\n"
        if self.scale is not None:
            s += f"{q}scale = {num(self.scale)}\n"
        if self.tooltip:
            s += f"{q}pdx_tooltip = \"{self.tooltip}\"\n"
        return s + self._extra(q) + f"{p}}}\n"


class Button(Element):
    kind = "button"

    def __init__(self, name, x, y, sprite, tooltip=None, text=None, font="hoi_16mbs", scale=None,
                 clicksound="click_default", w=0, h=0, extra=None):
        super().__init__(name, x, y, w, h, tooltip, extra)
        self.sprite, self.text, self.font, self.scale, self.clicksound = sprite, text, font, scale, clicksound

    def emit(self, level=2):
        p, q = "\t" * level, "\t" * (level + 1)
        s = f"{p}buttonType = {{\n{q}name = \"{self.name}\"\n{q}position = {{ x = {self.x} y = {self.y} }}\n{q}spriteType = \"{self.sprite}\"\n"
        if self.clicksound:
            s += f"{q}clicksound = {self.clicksound}\n"
        if self.tooltip:
            s += f"{q}pdx_tooltip = \"{self.tooltip}\"\n"
        if self.text:
            s += f"{q}buttonText = \"{self.text}\"\n{q}buttonFont = \"{self.font}\"\n"
        if self.scale is not None:
            s += f"{q}scale = {num(self.scale)}\n"
        return s + self._extra(q) + f"{p}}}\n"


class GridBox(Element):
    """gridboxType, the host element of a scripted GUI dynamic list."""
    kind = "gridbox"

    def __init__(self, name, x, y, w, h, slot_w, slot_h, fmt="UPPER_LEFT", max_slots_h=None, max_slots_v=None, extra=None):
        super().__init__(name, x, y, w, h, None, extra)
        self.slot_w, self.slot_h, self.fmt = slot_w, slot_h, fmt
        self.max_slots_h, self.max_slots_v = max_slots_h, max_slots_v

    def emit(self, level=2):
        p, q = "\t" * level, "\t" * (level + 1)
        s = (f"{p}gridboxType = {{\n{q}name = \"{self.name}\"\n{q}position = {{ x = {self.x} y = {self.y} }}\n"
             f"{q}size = {{ width = {self.w} height = {self.h} }}\n{q}slotsize = {{ width = {self.slot_w} height = {self.slot_h} }}\n"
             f"{q}format = \"{self.fmt}\"\n")
        if self.max_slots_h:
            s += f"{q}max_slots_horizontal = {self.max_slots_h}\n"
        if self.max_slots_v:
            s += f"{q}max_slots_vertical = {self.max_slots_v}\n"
        return s + self._extra(q) + f"{p}}}\n"


class Window(Element):
    """containerWindowType. `w` may be a number or a string such as "100%%" (the escaped percent HOI4 wants)."""
    kind = "window"

    def __init__(self, name, x=0, y=0, w="100%%", h=0, children=None, extra=None):
        super().__init__(name, x, y, w, h, None, extra)
        self.children = list(children or [])

    def add(self, el):
        self.children.append(el)
        return el

    def emit(self, level=1):
        p, q = "\t" * level, "\t" * (level + 1)
        body = "".join(c.emit(level + 1) for c in self.children)
        return (f"{p}containerWindowType = {{\n{q}name = \"{self.name}\"\n{q}position = {{ x = {self.x} y = {self.y} }}\n"
                f"{q}size = {{ width = {self.w} height = {self.h} }}\n" + self._extra(q) + f"{body}{p}}}\n")

    def walk(self):
        for c in self.children:
            yield c
            if isinstance(c, Window):
                yield from c.walk()
