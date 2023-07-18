try:
    from catppuccin.extras.pygments import FrappeStyle
    from catppuccin.extras.pygments import LatteStyle
    from catppuccin.extras.pygments import MacchiatoStyle
    from catppuccin.extras.pygments import MochaStyle
except ModuleNotFoundError:
    raise ModuleNotFoundError("Please install `catppuccin` package in order to use catppuccin editor themes.")

__all__ = ["FrappeStyle", "LatteStyle", "MacchiatoStyle", "MochaStyle"]
