from pathlib import Path

TorillicStyle = (
    Path(__file__).parent / "css" / "torillic" / "torillic.css"
).read_text(encoding="utf-8")