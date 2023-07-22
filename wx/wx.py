import traceback
import enum
import pygments, pygments.lexers
import wx
import wx.lib.splitter
import wx.html2 as html
import wx.richtext


from pathlib import Path

from .. import flags
from ..assets import folder as assetsFolder
from ..themes.editor.default import DefaultStyle as defaultEditorTheme
from ..themes.viewer.default import DefaultStyle as defaultViewerTheme


class MarkdownCtrl(wx.Panel, flags.FlagAtrributeMixin):
    def __init__(
            self, parent, interpreter=None, 
            minCtrlSize=(256, 256)
        ):
        # initialise
        wx.Panel.__init__(self, parent)
        self.parent = parent

        # setup sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        # setup interpreter
        if interpreter is None:
            import markdown
            interpreter = markdown.Markdown()
        self.interpreter = interpreter

        # setup ctrls panel
        self.ctrlsPanel = ctrlsPanel = wx.lib.splitter.MultiSplitterWindow(self, id=wx.ID_ANY)
        self.ctrlsPanel.SetMinimumPaneSize(minCtrlSize[0])
        self.ctrlsPanel.SetMinSize(minCtrlSize)
        self.sizer.Add(ctrlsPanel, proportion=1, flag=wx.EXPAND)
        self._ctrls = {}

        # add view toggle ctrl
        viewSwitcherCtrl = self._ctrls[flags.VIEW_SWITCHER_CTRL] = wx.Panel(self)
        viewSwitcherCtrl.sizer = wx.BoxSizer(wx.HORIZONTAL)
        viewSwitcherCtrl.SetSizer(viewSwitcherCtrl.sizer)
        self.sizer.Add(viewSwitcherCtrl)
        self._btns = {}
        
        # add raw markdown ctrl
        rawMarkdownCtrl = self._ctrls[flags.RAW_MARKDOWN_CTRL] = StyledTextCtrl(ctrlsPanel, language="markdown", minSize=minCtrlSize, style=wx.richtext.RE_MULTILINE)
        ctrlsPanel.AppendWindow(rawMarkdownCtrl)
        rawMarkdownCtrl.Bind(wx.EVT_TEXT, self.OnSetMarkdownText)
        # add view toggle button
        rawMarkdownBtn = ViewToggleButton(viewSwitcherCtrl, iconName="view_md", label="Markdown code")
        rawMarkdownBtn.Bind(wx.EVT_TOGGLEBUTTON, self.OnViewSwitcherButtonClicked)
        viewSwitcherCtrl.sizer.Add(rawMarkdownBtn, border=3, flag=wx.ALL)
        self._btns[flags.RAW_MARKDOWN_CTRL] = rawMarkdownBtn

        # add raw html ctrl
        rawHtmlCtrl = self._ctrls[flags.RAW_HTML_CTRL] = StyledTextCtrl(ctrlsPanel, language="html", minSize=minCtrlSize, style=wx.richtext.RE_MULTILINE | wx.richtext.RE_READONLY)
        ctrlsPanel.AppendWindow(rawHtmlCtrl)
        # add view toggle button
        rawHtmlBtn = ViewToggleButton(viewSwitcherCtrl, iconName="view_html", label="HTML code")
        rawHtmlBtn.Bind(wx.EVT_TOGGLEBUTTON, self.OnViewSwitcherButtonClicked)
        viewSwitcherCtrl.sizer.Add(rawHtmlBtn, border=3, flag=wx.ALL)
        self._btns[flags.RAW_HTML_CTRL] = rawHtmlBtn

        # add rendered HTML ctrl
        renderedHtmlCtrl = self._ctrls[flags.RENDERED_HTML_CTRL] = HTMLPreviewCtrl(ctrlsPanel, minSize=minCtrlSize)
        ctrlsPanel.AppendWindow(renderedHtmlCtrl)
        # add view toggle button
        renderedHtmlBtn = ViewToggleButton(viewSwitcherCtrl, iconName="view_preview", label="HTML preview")
        renderedHtmlBtn.Bind(wx.EVT_TOGGLEBUTTON, self.OnViewSwitcherButtonClicked)
        viewSwitcherCtrl.sizer.Add(renderedHtmlBtn, border=3, flag=wx.ALL)
        self._btns[flags.RENDERED_HTML_CTRL] = renderedHtmlBtn


        # set default style
        # self.setSelectionMode(self.SelectionMode.MultiSelection)
        self.SetView(flags.ALL_CTRLS)
        self.SetButtonsLayout(flags.ALIGN_BUTTONS_CENTER | flags.BOTTOM_BUTTONS_AREA)
    
    def GetMarkdownText(self):
        # get markdown ctrl
        ctrl = self.GetCtrl(flags.RAW_MARKDOWN_CTRL)
        # get content
        return ctrl.GetValue()

    def SetMarkdownText(self, value):
        # get markdown ctrl
        ctrl = self.GetCtrl(flags.RAW_MARKDOWN_CTRL)
        # set content
        ctrl.SetValue(value)
    
    def OnSetMarkdownText(self, evt=None):
        # get HTML body
        htmlBody = self.GetHtmlBody()
        # populate raw HTML ctrl
        rawHtmlCtrl = self.GetCtrl(flags.RAW_HTML_CTRL)
        rawHtmlCtrl.SetValue(htmlBody)
        # get full HTML
        htmlFull = self.GetHtml()
        # populate rendered HTML ctrl
        renderedHtmlCtrl = self.GetCtrl(flags.RENDERED_HTML_CTRL)
        renderedHtmlCtrl.SetHtml(htmlFull)
    
    def GetHtmlBody(self):
        # get markdown
        mdContent = self.GetMarkdownText()
        # parse to HTML
        try:
            htmlContent = self.interpreter.convert(mdContent)
        except Exception as err:
            # on fail, return error as HTML
            tb = "\n".join(traceback.format_exception(err))
            htmlContent = (
                f"<h1>Error</h1>\n"
                f"<p>Could not parse Markdown. Error from Python:</p>\n"
                f"<pre><code>{tb}</code></pre>\n"
                )
        
        return htmlContent

    def OnViewSwitcherButtonClicked(self, evt=None):
        for flag in (
            flags.RAW_MARKDOWN_CTRL,
            flags.RAW_HTML_CTRL,
            flags.RENDERED_HTML_CTRL,
        ):
            # get ctrl and button
            ctrl = self.GetCtrl(flag)
            btn = self.GetButton(flag)
            # align ctrl to button state
            if btn.GetValue():
                ctrl.Show()
            else:
                ctrl.Hide()
        self.ctrlsPanel.SizeWindows()

    def GetHtml(self):
        # get html body
        htmlBody = self.GetHtmlBody()
        # get theme
        theme = self.GetCtrl(flags.RENDERED_HTML_CTRL).theme
        # construct full html
        htmlFull = (
            f"<head>\n"
            f"<style>\n"
            f"{theme}\n"
            f"</style>\n"
            f"</head>\n"
            f"<body>\n"
            f"<main>\n"
            f"{htmlBody}\n"
            f"</main>\n"
            f"</body>"
        )
        
        return htmlFull
    
    def GetCtrl(self, flag):
        """
        """
        if flag in self._ctrls:
            return self._ctrls[flag]
    
    def GetButton(self, flag):
        """
        """
        if flag in self._btns:
            return self._btns[flag]
    
    def SetSelectionMode(self, mode):
        """
        """
        if mode == flags.SINGLE_SELECTION:
            self._btns.setExclusive(True)
        if mode == flags.MULTI_SELECTION:
            self._btns.setExclusive(False)
        # set view to match any change
        self.OnViewSwitcherButtonClicked()
    
    def SetCtrls(self, ctrls):
        # check flags
        for flag in [
            flags.RAW_MARKDOWN_CTRL,
            flags.RAW_HTML_CTRL,
            flags.RENDERED_HTML_CTRL,
            flags.VIEW_SWITCHER_CTRL,
        ]:
            # get ctrl and associated button
            ctrl = self.GetCtrl(flag)
            btn = self.GetButton(flag)

            if flag in ctrls:
                # if visibility is True, show corresponding component
                ctrl.Show()
                if btn is not None:
                    btn.SetValue(True)
            else:
                # if False, hide the corresponding component
                ctrl.Hide()
                if btn is not None:
                    btn.SetValue(False)
    
    def SetButtons(self, buttons):
        """
        """
        # check flags
        for flag in [
            flags.RAW_MARKDOWN_CTRL,
            flags.RAW_HTML_CTRL,
            flags.RENDERED_HTML_CTRL,
        ]:
            # get corresponding button
            btn = self.GetButton(flag)

            if flag in buttons:
                # if visibility is True, show corresponding button
                btn.Show()
            else:
                # if False, hide the corresponding button
                btn.Hide()
                btn.SetValue(False)
    
    def SetView(self, ctrls):
        """
        """
        # check flags
        for flag in [
            flags.RAW_MARKDOWN_CTRL,
            flags.RAW_HTML_CTRL,
            flags.RENDERED_HTML_CTRL,
        ]:
            # get corresponding button
            btn = self.GetButton(flag)
            # check/unecheck button as requested
            btn.SetValue(flag in ctrls)
        # refresh ctrls view
        self.OnViewSwitcherButtonClicked()
    
    def SetTheme(self, theme, ctrl):
        """
        """
        # check ctrl flags
        for flag in [
            flags.RAW_MARKDOWN_CTRL,
            flags.RAW_HTML_CTRL,
            flags.RENDERED_HTML_CTRL,
        ]:
            if flag in ctrl:
                # get ctrl
                thisCtrl = self.GetCtrl(flag)
                # set theme
                thisCtrl.theme = theme
                # restyle
                if isinstance(ctrl, StyledTextCtrl):
                    thisCtrl.StyleText()
                if isinstance(ctrl, HTMLPreviewCtrl):
                    thisCtrl.SetHtml(self.GetHtml())
    
    def SetButtonStyle(self, style, buttons=flags.ALL_CTRLS):
        """
        """
        # check flags
        for flag in [
            flags.RAW_MARKDOWN_CTRL,
            flags.RAW_HTML_CTRL,
            flags.RENDERED_HTML_CTRL,
        ]:
            if flag in buttons:
                # get corresponding button
                btn = self.GetButton(flag)
                # apply style
                if flags.BUTTON_ICON_ONLY in style:
                    btn.SetBitmap(btn._icon)
                    btn.SetLabel("")
                elif flags.BUTTON_TEXT_ONLY in style:
                    btn.SetBitmap(wx.Bitmap())
                    btn.SetLabel(btn._label)
                elif flags.BUTTON_TEXT_ONLY in style:
                    btn.SetBitmap(btn._icon)
                    btn.SetLabel(btn._label)
    
    def SetButtonIcon(self, icon, buttons=flags.ALL_CTRLS):
        """
        """
        # check flags
        for flag in [
            flags.RAW_MARKDOWN_CTRL,
            flags.RAW_HTML_CTRL,
            flags.RENDERED_HTML_CTRL,
        ]:
            if flag in buttons:
                # get button
                btn = self.GetButton(flag)
                # if icon is a string or Path, load from file
                if isinstance(icon, (str, Path)):
                    icon = wx.Bitmap(str(icon))
                # set icon
                btn._icon = icon
                btn.SetIcon(btn._icon)
    
    def SetButtonsLayout(self, flag):
        """
        """
        viewSwitcherCtrl = self.GetCtrl(flags.VIEW_SWITCHER_CTRL)
        # set position
        for thisFlag, sizerDir, btnSizerDir, pos in [
            (flags.LEFT_BUTTONS_AREA, wx.HORIZONTAL, wx.VERTICAL, 0),
            (flags.RIGHT_BUTTONS_AREA, wx.HORIZONTAL, wx.VERTICAL, 1),
            (flags.TOP_BUTTONS_AREA, wx.VERTICAL, wx.HORIZONTAL, 0),
            (flags.BOTTOM_BUTTONS_AREA, wx.VERTICAL, wx.HORIZONTAL, 1),
        ]:
            if flag | thisFlag == flag:
                # if flag is present, use sizer directions to move buttons to the corresponding area
                self.sizer.SetOrientation(sizerDir)
                viewSwitcherCtrl.sizer.SetOrientation(btnSizerDir)
                # to change layout order, move buttons ctrl to start/end of sizer
                self.sizer.Detach(viewSwitcherCtrl)
                self.sizer.Insert(pos, viewSwitcherCtrl)
        
        # set alignment
        for thisFlag, sizerFlagH, sizerFlagV in [
            (flags.ALIGN_BUTTONS_LEADING, wx.ALIGN_LEFT, wx.ALIGN_TOP),
            (flags.ALIGN_BUTTONS_CENTER, wx.ALIGN_CENTER, wx.ALIGN_CENTER),
            (flags.ALIGN_BUTTONS_TRAILING, wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM),
        ]:
            if flag | thisFlag == flag:
                item = self.sizer.GetItem(viewSwitcherCtrl)
                # if flag is present, apply corresponding alignment to button sizer item
                if self.sizer.GetOrientation() == wx.HORIZONTAL:
                    item.SetFlag(sizerFlagV)
                else:
                    item.SetFlag(sizerFlagH)
        
        self.Layout()


class ViewToggleButton(wx.ToggleButton):           
    def __init__(self, parent, iconName=None, label=""):
        # initialise
        wx.ToggleButton.__init__(self, parent, style=wx.BU_EXACTFIT)
        self.parent = parent
        # set label
        self.SetLabel(label)
        self._label = label
        # set icon
        if iconName is not None:
            iconPath = assetsFolder / "icons" / f"{iconName}.png"
            icon = wx.Bitmap(str(iconPath))
        else:
            icon = wx.Bitmap()
        self.SetBitmap(icon)
        self._icon = icon


class StyledTextCtrl(wx.richtext.RichTextCtrl):
    theme = defaultEditorTheme

    def __init__(self, parent, language, minSize=(256, 256), style=wx.richtext.RE_MULTILINE):
        # initialise
        wx.TextCtrl.__init__(self, parent, style=style)
        self.parent = parent
        # set minimum size
        self.SetMinSize(minSize)
        # setup lexer
        self.lexer = pygments.lexers.get_lexer_by_name(language)
        # bind style function
        self.Bind(wx.EVT_TEXT, self.StyleText)
        self.Bind(wx.EVT_KEY_UP, self.StyleText)
    
    def StyleText(self, evt=None):
        """
        Apply pyments.style to text contents
        """
        # freeze while we style
        self.GetBuffer().BeginSuppressUndo()

        # set base font
        baseFont = wx.Font()
        baseFont.SetPointSize(10)
        baseFont.SetFamily(wx.FONTFAMILY_TELETYPE)
        if hasattr(self.theme, "font_family"):
            baseFont.SetFaceName(self.theme.font_family)
        # set base background colour
        self.SetBackgroundColour(wx.Colour(self.theme.background_color))
        # lex content to get tokens
        content = self.GetValue()
        tokens = pygments.lex(content, lexer=self.lexer)
        # set character style
        i = 0
        while content.startswith("\n"):
            content = content[1:]
            i += 1
        for token, text in tokens:
            # get style for this token
            token_style = self.theme.style_for_token(token)
            # create format object
            char_font = wx.Font(baseFont)
            char_font.SetStyle(wx.FONTSTYLE_ITALIC if token_style['italic'] else wx.FONTSTYLE_NORMAL)
            char_font.SetWeight(wx.FONTWEIGHT_BOLD if token_style['bold'] else wx.FONTWEIGHT_NORMAL)
            char_font.SetUnderlined(token_style['underline'])
            char_format = wx.richtext.RichTextAttr(wx.TextAttr(wx.Colour(f"#{token_style['color']}"), font=char_font))
            # apply format object
            self.SetStyleEx(wx.richtext.RichTextRange(i, i+len(text)), char_format)
            # move forward to next token
            i += len(text)
        
        # thaw once done
        self.GetBuffer().EndSuppressUndo()
        
        self.Update()
        self.Refresh()


class HTMLPreviewCtrl(wx.Panel):
    theme = defaultViewerTheme

    def __init__(self, parent, minSize=(256, 256)):
        # initalise
        wx.Panel.__init__(self, parent)
        self.parent = parent
        # setup sizer
        self.sizer = wx.BoxSizer()
        self.SetSizer(self.sizer)
        # add webview
        self.view = html.WebView.New(self)
        self.sizer.Add(self.view, proportion=1, flag=wx.EXPAND)
        
        # set minimum size
        self.SetMinSize(minSize)
    
    def SetHtml(self, content, filename=None):
        # if not given a filename, use assets folder
        if filename is None:
            filename = Path(__file__).parent.parent / "assets" / "untitled.html"
        # enforce html extension
        filename = filename.parent / (filename.stem + ".html")
        # set html
        self.view.SetPage(content, str(filename))
