from pygments.token import Token
from pygments.styles.default import DefaultStyle


class TorillicStyle(DefaultStyle):
    _palette = {
        'white': "#FFFFFF",
        'offwhite': "#fcf5e5",
        'green': "#e0e5c1",
        'yellow': "#c9ad6a",
        'red': "#822000",
        'purple': "#704cd9",
        'black': "#000000"
    }

    font_family = "Source Code Pro"
    background_color = _palette['offwhite']
    highlight_color = _palette['green']
    line_number_color = _palette['white']
    line_number_background_color = _palette['red']
    line_number_special_color = _palette['black']
    line_number_special_background_color = _palette['yellow']

    # define token styles
    styles = DefaultStyle.styles.copy()
    styles = {
        Token: "{black}".format(**_palette),
        Token.Whitespace: "{yellow}".format(**_palette),
        Token.Comment: "{green}".format(**_palette),
        Token.Keyword:                   "bold {red}".format(**_palette),
        Token.Operator:                  "bold {red}".format(**_palette),
        Token.Name:                  "{red}".format(**_palette),
        Token.Name.Decorator:            "{purple}".format(**_palette),
        Token.String:                    "{yellow} bg:{green}".format(**_palette),
        Token.Generic.Heading: "bold {red}".format(**_palette),
        Token.Generic.Subheading: "bold underline {red}".format(**_palette),
        Token.Generic.Emph:              "italic".format(**_palette),
        Token.Generic.Strong:            "bold".format(**_palette),
        Token.Error:                     "{red}".format(**_palette)
    }