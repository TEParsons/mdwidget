import enum
import case_changer as cc
from types import SimpleNamespace

__all__ = ["FlagAtrributeMixin"]


class FlagAtrributeMixin:
    """
    Adds enum flags and their aliases as class attributes for consistency with e.g. 
    pyqt5's method of organising flags.
    """
    def __init_subclass__(cls):
        # define more granular groups to split flags into
        flag_groups = {
            'CtrlId': ("raw_markdown_ctrl", "raw_html_ctrl", "rendered_html_ctrl", "all_ctrls", "view_switcher_ctrl"),
            'SelectionModeFlag': ("single_selection", "multi_selection"),
            'ButtonStyleFlag': ("button_icon_only", "button_text_only", "button_text_beside_icon"),
            'ButtonLayoutFlag': ("left_buttons_area", "right_buttons_area", "top_buttons_area", "bottom_buttons_area", "align_buttons_leading", "align_buttons_center", "align_buttons_trailing")
        }
        # iterate through groups
        for group_name, flag_names in flag_groups.items():
            # create a simple namespace to store flag refs
            group = SimpleNamespace()
            # iterate through flags
            for flag_name in flag_names:
                # get flag
                for flag_cls in (MarkdownCtrlFlag, CtrlId):
                    if hasattr(flag_cls, flag_name):
                        flag = getattr(flag_cls, flag_name)
                # assign flag to group
                setattr(group, flag_name, flag)
                # alias PascalCase
                pascal = cc.pascal_case(flag_name)
                setattr(group, pascal, flag)
                # alias CONSTANT_CASE
                constant = cc.constant_case(flag_name)
                setattr(group, constant, flag)
            # assign namespace to class
            setattr(cls, group_name, group)


def create_global_aliases(cls):
    for attr in dir(cls):
        # get flag handle
        flag = getattr(cls, attr)
        # skip protected attributes
        if not isinstance(flag, cls):
            continue
        # globalise
        globals()[attr] = flag
        __all__.append(attr)
        # alias PascalCase
        pascal = cc.pascal_case(attr)
        globals()[pascal] = flag
        __all__.append(pascal)
        # alias CONSTANT_CASE
        constant = cc.constant_case(attr)
        globals()[constant] = flag
        __all__.append(constant)


class MarkdownCtrlFlag(enum.Flag):
    # selection options
    single_selection = enum.auto()
    multi_selection = enum.auto()
    # button style options
    button_icon_only = enum.auto()
    button_text_only = enum.auto()
    button_text_beside_icon = enum.auto()
    # button position options
    left_buttons_area = enum.auto()
    right_buttons_area = enum.auto()
    top_buttons_area = enum.auto()
    bottom_buttons_area = enum.auto()
    # button alignment options
    align_buttons_leading = enum.auto()
    align_buttons_center = enum.auto()
    align_buttons_trailing = enum.auto()


create_global_aliases(MarkdownCtrlFlag)


class CtrlId(enum.IntFlag):
    # identifiers for controls
    raw_markdown_ctrl = enum.auto()
    raw_html_ctrl = enum.auto()
    rendered_html_ctrl = enum.auto()
    all_ctrls = raw_markdown_ctrl | raw_html_ctrl | rendered_html_ctrl
    # identifier for button area
    view_switcher_ctrl = enum.auto()


create_global_aliases(CtrlId)
