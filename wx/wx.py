import traceback
import enum
import pygments, pygments.lexers, pygments.token
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
        self.SetSelectionMode(flags.MULTI_SELECTION)
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
        # style
        ctrl.StyleText()
    
    def OnSetMarkdownText(self, evt=None):
        # get HTML body
        htmlBody = self.GetHtmlBody()
        # populate raw HTML ctrl
        rawHtmlCtrl = self.GetCtrl(flags.RAW_HTML_CTRL)
        rawHtmlCtrl.SetValue(htmlBody)
        # style raw HTML ctrl
        rawHtmlCtrl.StyleText()
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
        # if single select, uncheck all other buttons
        if self._selectionMode == flags.SINGLE_SELECTION:
            if evt is not None:
                # if triggered by event, get triggering button
                thisBtn = evt.GetEventObject()
            else:
                # otherwise, get first button
                thisBtn = self.GetButton(flags.RAW_MARKDOWN_CTRL)
            
            for flag in (
                flags.RAW_MARKDOWN_CTRL,
                flags.RAW_HTML_CTRL,
                flags.RENDERED_HTML_CTRL,
            ):
                # get each button
                btn = self.GetButton(flag)
                # uncheck button if it's not the triggering button
                btn.SetValue(btn == thisBtn)
        # list of ctrls to show
        ctrls = []
        # check each button
        for flag in (
            flags.RAW_MARKDOWN_CTRL,
            flags.RAW_HTML_CTRL,
            flags.RENDERED_HTML_CTRL,
        ):
            # get button
            btn = self.GetButton(flag)
            # add ctrl to list if button is pressed
            if btn.GetValue():
                ctrls.append(flag)
        # add view toggle to list if shown 
        if self.GetCtrl(flags.VIEW_SWITCHER_CTRL).IsShown():
            ctrls.append(flags.VIEW_SWITCHER_CTRL)
        # set ctrls
        self.SetCtrls(ctrls)

    def GetHtml(self):
        # get html body
        htmlBody = self.GetHtmlBody()
        # get theme
        theme = self.GetCtrl(flags.RENDERED_HTML_CTRL).GetTheme()
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
        # store selection mode internally
        self._selectionMode = mode
        # set view to match any change
        self.OnViewSwitcherButtonClicked()
    
    def SetCtrls(self, ctrls):
        # figure out which ctrls are still in the panel
        children = []
        for i in range(3):
            try:
                ctrl = self.ctrlsPanel.GetWindow(i)
                children.append(ctrl)
            except:
                pass
        # remove them all
        for ctrl in children:
            self.ctrlsPanel.DetachWindow(ctrl)
        # add back in if indicated
        for flag in (flags.RAW_MARKDOWN_CTRL, flags.RAW_HTML_CTRL, flags.RENDERED_HTML_CTRL):
            # get ctrl and associated button
            ctrl = self.GetCtrl(flag)
            btn = self.GetButton(flag)

            if flag in ctrls:
                # if requested, add back in & set button value
                ctrl.Show()
                self.ctrlsPanel.AppendWindow(ctrl)
                btn.SetValue(True)
            else:
                # otherwise, hide & set button value
                ctrl.Hide()
                btn.SetValue(False)
        # layout panel
        self.ctrlsPanel.SizeWindows()
        # check for button ctrls flag
        self.GetCtrl(flags.VIEW_SWITCHER_CTRL).Show(flags.VIEW_SWITCHER_CTRL in ctrls)
    
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
                if hasattr(thisCtrl, "SetTheme"):
                    thisCtrl.SetTheme(theme)
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


class MarkdownCtrlFormatter:
    def __init__(self, theme):
        self.theme = theme
        self._baseFont = None
        self.styles = {}
    
    def GetBaseFont(self):
        if self._baseFont is None:
            # blank font object
            font = wx.Font()
            # set font and size
            font.SetPointSize(10)
            font.SetFamily(wx.FONTFAMILY_TELETYPE)
            # if we have a face name, set it
            if hasattr(self.theme, "font_family"):
                font.SetFaceName(self.theme.font_family)
            
            self._baseFont = font
        
        return self._baseFont
    
    def GetTokenStyle(self, token):
        if token not in self.styles:
            # get style for this token
            tokenStyle = self.theme.style_for_token(token)
            # get base font
            font = self.GetBaseFont()
            # apply style
            font.SetStyle(wx.FONTSTYLE_ITALIC if tokenStyle['italic'] else wx.FONTSTYLE_NORMAL)
            font.SetWeight(wx.FONTWEIGHT_BOLD if tokenStyle['bold'] else wx.FONTWEIGHT_NORMAL)
            font.SetUnderlined(tokenStyle['underline'])
            # create textattr from font & colour
            attr = wx.TextAttr(wx.Colour(f"#{tokenStyle['color']}"), font=font)
            # convert to rich text attribute
            style = wx.richtext.RichTextAttr(attr)
            # assign to styles dict
            self.styles[token] = style
        
        return self.styles[token]


class StyledTextCtrl(wx.richtext.RichTextCtrl):
    def __init__(self, parent, language, minSize=(256, 256), style=wx.richtext.RE_MULTILINE):
        # initialise
        wx.TextCtrl.__init__(self, parent, style=style)
        self.parent = parent
        # set minimum size
        self.SetMinSize(minSize)
        # setup lexer
        self.lexer = pygments.lexers.get_lexer_by_name(language)
        # setup formatter
        self.formatter = MarkdownCtrlFormatter(defaultEditorTheme)
        # bind style function
        self.Bind(wx.EVT_TEXT, self.StyleText)
        self.Bind(wx.EVT_KEY_UP, self.StyleText)
        self.Bind(wx.EVT_SHOW, self.OnShow)
    
    def SetTheme(self, theme):
        self.formatter = MarkdownCtrlFormatter(theme)
    
    def GetTheme(self):
        return self.formatter.theme
    
    def StyleText(self, evt=None):
        """
        Apply pyments.style to text contents
        """
        # don't restyle if ctrl is hidden
        if not self.IsShown():
            return
        # freeze while we style
        self.GetBuffer().BeginSuppressUndo()
        self.Freeze()

        # set base background colour
        self.SetBackgroundColour(wx.Colour(self.GetTheme().background_color))
        # set base style
        baseStyle = self.formatter.GetTokenStyle(pygments.token.Token)
        self.SetBasicStyle(baseStyle)
        # lex content to get tokens
        content = self.GetValue()
        tokens = pygments.lex(content, lexer=self.lexer)
        # set character style
        i = 0
        while content.startswith("\n"):
            content = content[1:]
            i += 1
        for token, text in tokens:
            charFormat = self.formatter.GetTokenStyle(token)
            # apply format object
            self.SetStyleEx(wx.richtext.RichTextRange(i, i+len(text)), charFormat)
            # move forward to next token
            i += len(text)
        
        # thaw once done
        self.GetBuffer().EndSuppressUndo()
        self.Thaw()
        self.Update()
        self.Refresh()

    def OnShow(self, evt):
        # style self
        self.StyleText(evt)
        # continue
        evt.Skip()


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
        if not self.IsShown():
            return
        # if not given a filename, use assets folder
        if filename is None:
            filename = Path(__file__).parent.parent / "assets" / "untitled.html"
        # enforce html extension
        filename = filename.parent / (filename.stem + ".html")
        # set html
        self.view.SetPage(content, str(filename))
    
    def GetTheme(self):
        return self.theme
    
    def SetTheme(self, theme):
        self.theme = theme
