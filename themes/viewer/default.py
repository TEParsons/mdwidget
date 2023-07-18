from pathlib import Path


DefaultStyle = (
    Path(__file__).parent / "css" / "default" / "default.css"
).read_text(encoding="utf-8")