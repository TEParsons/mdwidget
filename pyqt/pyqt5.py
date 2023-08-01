import traceback
import enum
import pygments, pygments.lexers
import PyQt5.QtCore as util
import PyQt5.QtWidgets as qt
import PyQt5.QtGui as gui
import PyQt5.QtWebEngineWidgets as html

from pathlib import Path

from .. import flags
from ..assets import folder as assetsFolder
from ..themes.editor.default import DefaultStyle as defaultEditorTheme
from ..themes.viewer.default import DefaultStyle as defaultViewerTheme


class MarkdownCtrl(qt.QWidget, flags.FlagAtrributeMixin):
    def __init__(
            self, parent, interpreter=None, 
            minCtrlSize=(256, 256)
        ):
        # initialise
        qt.QWidget.__init__(self, parent)
        self.parent = parent

        # setup sizer
        self.sizer = qt.QVBoxLayout(self)

        # setup interpreter
        if interpreter is None:
            import markdown
            interpreter = markdown.Markdown()
        self.interpreter = interpreter

        # setup ctrls panel
        ctrlsPanel = qt.QSplitter(self)
        ctrlsPanel.setChildrenCollapsible(False)
        self.sizer.addWidget(ctrlsPanel, stretch=1)
        self._ctrls = {}

        # add view toggle ctrl
        viewSwitcherCtrl = self._ctrls[flags.ViewSwitcherCtrl] = qt.QWidget()
        viewSwitcherCtrl.sizer = qt.QHBoxLayout(viewSwitcherCtrl)
        self.sizer.addWidget(viewSwitcherCtrl)
        self._btns = qt.QButtonGroup(self)
        
        # add raw markdown ctrl
        rawMarkdownCtrl = self._ctrls[flags.RawMarkdownCtrl] = StyledTextCtrl(self, language="markdown", minSize=minCtrlSize)
        rawMarkdownCtrl.textChanged.connect(self.onSetMarkdownText)
        ctrlsPanel.addWidget(rawMarkdownCtrl)
        # add view toggle button
        rawMarkdownBtn = ViewToggleButton(viewSwitcherCtrl, iconName="view_md", label="Markdown code")
        rawMarkdownBtn.clicked.connect(self.onViewSwitcherButtonClicked)
        viewSwitcherCtrl.sizer.addWidget(rawMarkdownBtn)
        self._btns.addButton(rawMarkdownBtn, id=flags.RawMarkdownCtrl)

        # add raw html ctrl
        rawHtmlCtrl = self._ctrls[flags.RawHtmlCtrl] = StyledTextCtrl(self, language="html", minSize=minCtrlSize)
        rawHtmlCtrl.setReadOnly(True)
        ctrlsPanel.addWidget(rawHtmlCtrl)
        # add view toggle button
        rawHtmlBtn = ViewToggleButton(viewSwitcherCtrl, iconName="view_html", label="HTML code")
        rawHtmlBtn.clicked.connect(self.onViewSwitcherButtonClicked)
        viewSwitcherCtrl.sizer.addWidget(rawHtmlBtn)
        self._btns.addButton(rawHtmlBtn, id=flags.RawHtmlCtrl)

        # add rendered HTML ctrl
        renderedHtmlCtrl = self._ctrls[flags.RenderedHtmlCtrl] = HTMLPreviewCtrl(self, minSize=minCtrlSize)
        ctrlsPanel.addWidget(renderedHtmlCtrl)
        # add view toggle button
        renderedHtmlBtn = ViewToggleButton(viewSwitcherCtrl, iconName="view_preview", label="HTML preview")
        renderedHtmlBtn.clicked.connect(self.onViewSwitcherButtonClicked)
        viewSwitcherCtrl.sizer.addWidget(renderedHtmlBtn)
        self._btns.addButton(renderedHtmlBtn, id=flags.RenderedHtmlCtrl)

        # set default style
        self.setSelectionMode(flags.MultiSelection)
        self.setView(flags.AllCtrls)
    
    def getMarkdownText(self):
        # get markdown ctrl
        ctrl = self.getCtrl(flags.RawMarkdownCtrl)
        # get content
        return ctrl.toPlainText()

    def setMarkdownText(self, value):
        # get markdown ctrl
        ctrl = self.getCtrl(flags.RawMarkdownCtrl)
        # set content
        ctrl.setPlainText(value)
    
    def onSetMarkdownText(self, evt=None):
        # get HTML body
        htmlBody = self.getHtmlBody()
        # populate raw HTML ctrl
        rawHtmlCtrl = self.getCtrl(flags.RawHtmlCtrl)
        rawHtmlCtrl.setPlainText(htmlBody)
        # get full HTML
        htmlFull = self.getHtml()
        # populate rendered HTML ctrl
        renderedHtmlCtrl = self.getCtrl(flags.RenderedHtmlCtrl)
        renderedHtmlCtrl.setHtml(htmlFull)
    
    def getHtmlBody(self):
        # get markdown
        mdContent = self.getMarkdownText()
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

    def onViewSwitcherButtonClicked(self, evt=None):
        for flag in (
            flags.RawMarkdownCtrl,
            flags.RawHtmlCtrl,
            flags.RenderedHtmlCtrl,
        ):
            # get ctrl and button
            ctrl = self.getCtrl(flag)
            btn = self.getButton(flag)
            # align ctrl to button state
            if btn.isChecked():
                ctrl.show()
            else:
                ctrl.hide()

    def getHtml(self):
        # get html body
        htmlBody = self.getHtmlBody()
        # get theme
        theme = self.getCtrl(flags.RenderedHtmlCtrl).theme
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
    
    def getCtrl(self, flag):
        """
        """
        if flag in self._ctrls:
            return self._ctrls[flag]
    
    def getButton(self, flag):
        """
        """
        return self._btns.button(flag)
    
    def setSelectionMode(self, mode):
        """
        """
        if mode == flags.SingleSelection:
            self._btns.setExclusive(True)
        if mode == flags.MultiSelection:
            self._btns.setExclusive(False)
        # set view to match any change
        self.onViewSwitcherButtonClicked()
    
    def setCtrls(self, ctrls):
        # check flags
        for flag in [
            flags.RawMarkdownCtrl,
            flags.RawHtmlCtrl,
            flags.RenderedHtmlCtrl,
            flags.ViewSwitcherCtrl,
        ]:
            # get ctrl and associated button
            ctrl = self.getCtrl(flag)
            btn = self.getButton(flag)

            if flag in ctrls:
                # if visibility is True, show corresponding component
                ctrl.show()
                if btn is not None:
                    btn.setChecked(True)
            else:
                # if False, hide the corresponding component
                ctrl.hide()
                if btn is not None:
                    btn.setChecked(False)
    
    def setButtons(self, buttons):
        """
        """
        # check flags
        for flag in [
            flags.RawMarkdownCtrl,
            flags.RawHtmlCtrl,
            flags.RenderedHtmlCtrl,
        ]:
            # get corresponding button
            btn = self.getButton(flag)

            if flag in buttons:
                # if visibility is True, show corresponding button
                btn.show()
            else:
                # if False, hide the corresponding button
                btn.hide()
                btn.setChecked(False)
    
    def setView(self, ctrls):
        """
        """
        # check flags
        for flag in [
            flags.RawMarkdownCtrl,
            flags.RawHtmlCtrl,
            flags.RenderedHtmlCtrl,
        ]:
            # get corresponding button
            btn = self.getButton(flag)
            # check/unecheck button as requested
            btn.setChecked(flag in ctrls)
        # refresh ctrls view
        self.onViewSwitcherButtonClicked()
    
    def setTheme(self, theme, ctrl):
        """
        """
        # check ctrl flags
        for flag in [
            flags.RawMarkdownCtrl,
            flags.RawHtmlCtrl,
            flags.RenderedHtmlCtrl,
        ]:
            if flag in ctrl:
                # get ctrl
                thisCtrl = self.getCtrl(flag)
                # set theme
                if hasattr(thisCtrl, "setTheme"):
                    thisCtrl.setTheme(theme)
                # restyle
                if isinstance(ctrl, StyledTextCtrl):
                    thisCtrl.styleText()
                if isinstance(ctrl, HTMLPreviewCtrl):
                    thisCtrl.setHtml(self.getHtml())
    
    def setButtonStyle(self, style, buttons=flags.AllCtrls):
        """
        """
        # check flags
        for flag in [
            flags.RawMarkdownCtrl,
            flags.RawHtmlCtrl,
            flags.RenderedHtmlCtrl,
        ]:
            if flag in buttons:
                # get corresponding button
                btn = self.getButton(flag)
                # apply style
                if flags.ButtonIconOnly in style:
                    btn.setIcon(btn._icon)
                    btn.setText("")
                elif flags.ButtonTextOnly in style:
                    btn.setIcon(gui.QIcon())
                    btn.setText(btn._label)
                elif flags.ButtonTextOnly in style:
                    btn.setIcon(btn._icon)
                    btn.setText(btn._label)
    
    def setButtonIcon(self, icon, buttons=flags.AllCtrls):
        """
        """
        # check flags
        for flag in [
            flags.RawMarkdownCtrl,
            flags.RawHtmlCtrl,
            flags.RenderedHtmlCtrl,
        ]:
            if flag in buttons:
                # get button
                btn = self.getButton(flag)
                # if icon is a string or Path, load from file
                if isinstance(icon, (str, Path)):
                    icon = gui.QIcon(str(icon))
                # set icon
                btn._icon = icon
                btn.setIcon(btn._icon)
    
    def setButtonsLayout(self, flag):
        """
        """
        viewSwitcherCtrl = self.getCtrl(flags.ViewSwitcherCtrl)
        # set position
        for thisFlag, sizerDir, btnSizerDir in [
            (flags.LeftButtonsArea, self.sizer.Direction.RightToLeft, self.sizer.Direction.TopToBottom),
            (flags.RightButtonsArea, self.sizer.Direction.LeftToRight, self.sizer.Direction.TopToBottom),
            (flags.TopButtonsArea, self.sizer.Direction.BottomToTop, self.sizer.Direction.LeftToRight),
            (flags.BottomButtonsArea, self.sizer.Direction.TopToBottom, self.sizer.Direction.LeftToRight),
        ]:
            if flag | thisFlag == flag:
                # if flag is present, use sizer directions to move buttons to the corresponding area
                self.sizer.setDirection(sizerDir)
                viewSwitcherCtrl.sizer.setDirection(btnSizerDir)
        # set alignment
        for thisFlag, sizerFlag in [
            (flags.AlignButtonsLeading, util.Qt.AlignLeading),
            (flags.AlignButtonsCenter, util.Qt.AlignCenter),
            (flags.AlignButtonsTrailing, util.Qt.AlignTrailing),
        ]:
            if flag | thisFlag == flag:
                # if flag is present, apply corresponding alignment to button sizer
                viewSwitcherCtrl.sizer.setAlignment(sizerFlag)


class ViewToggleButton(qt.QPushButton):           
    def __init__(self, parent, iconName=None, label=""):
        # initialise
        qt.QPushButton.__init__(self, parent)
        self.parent = parent
        self.setCheckable(True)
        # set label
        self.setText(label)
        self._label = label
        # set icon
        if iconName is not None:
            iconPath = assetsFolder / "icons" / f"{iconName}.svg"
            icon = gui.QIcon(str(iconPath))
        else:
            icon = gui.QIcon()
        self.setIcon(icon)
        self._icon = icon


class MarkdownCtrlFormatter:
    def __init__(self, theme):
        self.theme = theme
        self.styles = {}
    
    def GetBaseFont(self):
        # create format object
        charFormat = gui.QTextCharFormat()
        charFormat.setFontFamily("monospace")
        if hasattr(self.theme, "font_family"):
            charFormat.setFontFamily(self.theme.font_family)
        charFormat.setFontPointSize(10)
        
        return charFormat
    
    def GetTokenFont(self, token):
        if token not in self.styles:
            # get style for this token
            tokenStyle = self.theme.style_for_token(token)
            # get base font
            charFormat = self.GetBaseFont()
            # apply style
            charFormat.setFontItalic(tokenStyle['italic'])
            if tokenStyle['bold']:
                charFormat.setFontWeight(600)
            charFormat.setFontUnderline(tokenStyle['underline'])
            charFormat.setForeground(gui.QColor(f"#{tokenStyle['color']}"))
            # assign to styles dict
            self.styles[token] = charFormat
        
        return self.styles[token]


class StyledTextCtrl(qt.QTextEdit):
    def __init__(self, parent, language, minSize=(256, 256)):
        # initialise
        qt.QTextEdit.__init__(self)
        self.parent = parent
        # disable rich text - we don't want any non-markdown styling
        self.setAcceptRichText(False)
        # set minimum size
        self.setMinimumSize(*minSize)
        # setup lexer
        self.lexer = pygments.lexers.get_lexer_by_name(language)
        # setup formatter
        self.formatter = MarkdownCtrlFormatter(defaultEditorTheme)
        # bind style function
        self.textChanged.connect(self.styleText)
    
    def setTheme(self, theme):
        self.formatter = MarkdownCtrlFormatter(theme)
    
    def getTheme(self):
        return self.formatter.theme
    
    def styleText(self):
        """
        Apply pyments.style to text contents
        """
        # don't restyle if ctrl is hidden
        if not self.isVisible():
            return
        # don't trigger any events while this method executes
        self.blockSignals(True)
        self.setUpdatesEnabled(False)

        # get cursor handle
        cursor = gui.QTextCursor(self.document())
        # set base style
        self.setStyleSheet(
            f"background-color: {self.getTheme().background_color};"
        )
        # lex content to get tokens
        content = self.toPlainText()
        tokens = pygments.lex(content, lexer=self.lexer)
        # re-add characters with styling
        i = 0
        while content.startswith("\n"):
            content = content[1:]
            i += 1
        for token, text in tokens:
            charFormat = self.formatter.GetTokenFont(token)
            # select corresponding chars
            cursor.setPosition(i)
            cursor.movePosition(cursor.Right, n=len(text), mode=cursor.KeepAnchor)
            # format selection
            cursor.setCharFormat(charFormat)
            # move forward to next token
            i += len(text)

        # allow signals to trigger again
        self.blockSignals(False)
        self.setUpdatesEnabled(True)


class HTMLPreviewCtrl(html.QWebEngineView):
    theme = defaultViewerTheme

    def __init__(self, parent, minSize=(256, 256)):
        # initalise
        html.QWebEngineView.__init__(self)
        self.parent = parent
        # set minimum size
        self.setMinimumSize(*minSize)
    
    def setTheme(self, theme):
        self.theme = theme
    
    def getTheme(self):
        return self.theme
    
    def setHtml(self, content, filename=None):
        if not self.isVisible():
            return
        # if not given a filename, use assets folder
        if filename is None:
            filename = Path(__file__).parent.parent / "assets" / "untitled.html"
        # enforce html extension
        filename = filename.parent / (filename.stem + ".html")
        # get base url
        base_url = util.QUrl.fromLocalFile(str(filename))
        # set HTML
        html.QWebEngineView.setHtml(self, content, base_url)
