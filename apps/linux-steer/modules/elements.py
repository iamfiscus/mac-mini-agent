"""Element ID system — matches macOS steer exactly.

Role prefixes: B=button, T=textField, S=staticText, I=image,
C=checkbox, L=link, M=menuItem, O=ocrElement.
Counter resets per snapshot.
"""

from dataclasses import dataclass, asdict

# AT-SPI2 role name → single-letter prefix
ROLE_PREFIX = {
    "push button": "B",
    "toggle button": "B",
    "text": "T",
    "password text": "T",
    "entry": "T",
    "label": "S",
    "static": "S",
    "image": "I",
    "icon": "I",
    "check box": "C",
    "link": "L",
    "menu item": "M",
    "menu": "M",
}


@dataclass
class Element:
    id: str
    role: str
    label: str
    x: int
    y: int
    width: int
    height: int

    def to_dict(self) -> dict:
        return asdict(self)


class ElementStore:
    """Accumulates elements and assigns sequential IDs."""

    def __init__(self):
        self._counters: dict[str, int] = {}
        self.elements: list[Element] = []

    def add(self, role: str, label: str, x: int, y: int, width: int, height: int) -> Element:
        prefix = ROLE_PREFIX.get(role.lower(), "E")
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        element = Element(
            id=f"{prefix}{self._counters[prefix]}",
            role=role,
            label=label,
            x=x, y=y, width=width, height=height,
        )
        self.elements.append(element)
        return element

    def add_ocr(self, text: str, x: int, y: int, width: int, height: int) -> Element:
        self._counters["O"] = self._counters.get("O", 0) + 1
        element = Element(
            id=f"O{self._counters['O']}",
            role="ocrElement",
            label=text,
            x=x, y=y, width=width, height=height,
        )
        self.elements.append(element)
        return element

    def to_list(self) -> list[dict]:
        return [e.to_dict() for e in self.elements]

    def find_by_text(self, text: str) -> Element | None:
        text_lower = text.lower()
        for e in self.elements:
            if text_lower in e.label.lower():
                return e
        return None

    def find_by_id(self, element_id: str) -> Element | None:
        for e in self.elements:
            if e.id == element_id:
                return e
        return None
