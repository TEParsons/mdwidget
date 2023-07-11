from pathlib import Path


LatteStyle = (
    Path(__file__).parent / "css" / "catppuccin" / "latte.css"
).read_text(encoding="utf-8")


FrappeStyle = (
    Path(__file__).parent / "css" / "catppuccin" / "frappe.css"
).read_text(encoding="utf-8")


MochaStyle = (
    Path(__file__).parent / "css" / "catppuccin" / "mocha.css"
).read_text(encoding="utf-8")


MacchiatoStyle = (
    Path(__file__).parent / "css" / "catppuccin" / "macchiato.css"
).read_text(encoding="utf-8")