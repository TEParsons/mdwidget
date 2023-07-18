import traceback
import enum
import pygments, pygments.lexers
import PyQt5.QtCore as util
import PyQt5.QtWidgets as qt
import PyQt5.QtGui as gui
import PyQt5.QtWebEngineWidgets as html

from pathlib import Path

from ..themes.editor import current as editorTheme
from ..themes.viewer import current as viewerTheme
from ..assets import folder as assetsFolder


class MarkdownCtrl(qt.QWidget):
    class SelectionMode(enum.Flag):
        SingleSelection = enum.auto()
        MultiSelection = enum.auto()
    
    class IdentifierFlag(enum.IntFlag):
        # identifiers for controls
        RawMarkdownCtrl = enum.auto()
        RawHtmlCtrl = enum.auto()
        RenderedHtmlCtrl = enum.auto()
        AllCtrls = RawMarkdownCtrl | RawHtmlCtrl | RenderedHtmlCtrl
        # identifier for button area
        ViewSwitcherCtrl = enum.auto()
    
    class ButtonStyleFlag(enum.Flag):
        # button style options
        ButtonIconOnly = enum.auto()
        ButtonTextOnly = enum.auto()
        ButtonTextBesideIcon = enum.auto()
    
    class ButtonLayoutFlag(enum.Flag):
        # button position options
        LeftButtonsArea = enum.auto()
        RightButtonsArea = enum.auto()
        TopButtonsArea = enum.auto()
        BottomButtonsArea = enum.auto()
        # button alignment options
        AlignButtonsLeading = enum.auto()
        AlignButtonsCenter = enum.auto()
        AlignButtonsTrailing = enum.auto()

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
        viewSwitcherCtrl = self._ctrls[self.IdentifierFlag.ViewSwitcherCtrl] =qt.QWidget()
        viewSwitcherCtrl.sizer = qt.QHBoxLayout(viewSwitcherCtrl)
        self.sizer.addWidget(viewSwitcherCtrl)
        self._btns = qt.QButtonGroup(self)
        
        # add raw markdown ctrl
        rawMarkdownCtrl = self._ctrls[self.IdentifierFlag.RawMarkdownCtrl] = StyledTextCtrl(self, language="markdown", minSize=minCtrlSize)
        rawMarkdownCtrl.textChanged.connect(self.onSetMarkdownText)
        ctrlsPanel.addWidget(rawMarkdownCtrl)
        # add view toggle button
        rawMarkdownBtn = ViewToggleButton(viewSwitcherCtrl, iconName="view_md", label="Markdown code")
        rawMarkdownBtn.clicked.connect(self.onViewSwitcherButtonClicked)
        viewSwitcherCtrl.sizer.addWidget(rawMarkdownBtn)
        self._btns.addButton(rawMarkdownBtn, id=self.IdentifierFlag.RawMarkdownCtrl)

        # add raw html ctrl
        rawHtmlCtrl = self._ctrls[self.IdentifierFlag.RawHtmlCtrl] = StyledTextCtrl(self, language="html", minSize=minCtrlSize)
        rawHtmlCtrl.setReadOnly(True)
        ctrlsPanel.addWidget(rawHtmlCtrl)
        # add view toggle button
        rawHtmlBtn = ViewToggleButton(viewSwitcherCtrl, iconName="view_html", label="HTML code")
        rawHtmlBtn.clicked.connect(self.onViewSwitcherButtonClicked)
        viewSwitcherCtrl.sizer.addWidget(rawHtmlBtn)
        self._btns.addButton(rawHtmlBtn, id=self.IdentifierFlag.RawHtmlCtrl)

        # add rendered HTML ctrl
        renderedHtmlCtrl = self._ctrls[self.IdentifierFlag.RenderedHtmlCtrl] = HTMLPreviewCtrl(self, minSize=minCtrlSize)
        ctrlsPanel.addWidget(renderedHtmlCtrl)
        # add view toggle button
        renderedHtmlBtn = ViewToggleButton(viewSwitcherCtrl, iconName="view_preview", label="HTML preview")
        renderedHtmlBtn.clicked.connect(self.onViewSwitcherButtonClicked)
        viewSwitcherCtrl.sizer.addWidget(renderedHtmlBtn)
        self._btns.addButton(renderedHtmlBtn, id=self.IdentifierFlag.RenderedHtmlCtrl)

        # set default style
        self.setSelectionMode(self.SelectionMode.MultiSelection)
        self.setView(self.IdentifierFlag.AllCtrls)
    
    def getMarkdownText(self):
        # get markdown ctrl
        ctrl = self.getCtrl(self.IdentifierFlag.RawMarkdownCtrl)
        # get content
        return ctrl.toPlainText()

    def setMarkdownText(self):
        # get markdown ctrl
        ctrl = self.getCtrl(self.IdentifierFlag.RawMarkdownCtrl)
        # set content
        ctrl.setPlainText(ctrl)
    
    def onSetMarkdownText(self, evt=None):
        # get HTML body
        htmlBody = self.getHtmlBody()
        # populate raw HTML ctrl
        rawHtmlCtrl = self.getCtrl(self.IdentifierFlag.RawHtmlCtrl)
        rawHtmlCtrl.setPlainText(htmlBody)
        # get full HTML
        htmlFull = self.getHtml()
        # populate rendered HTML ctrl
        renderedHtmlCtrl = self.getCtrl(self.IdentifierFlag.RenderedHtmlCtrl)
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
            MarkdownCtrl.IdentifierFlag.RawMarkdownCtrl,
            MarkdownCtrl.IdentifierFlag.RawHtmlCtrl,
            MarkdownCtrl.IdentifierFlag.RenderedHtmlCtrl,
        ):
            # get ctrl and button
            ctrl = self.getCtrl(flag)
            btn = self.getButton(flag)
            # align ctrl to button state
            if btn.isVisible() and btn.isChecked():
                ctrl.show()
            else:
                ctrl.hide()

    def getHtml(self):
        # get html body
        htmlBody = self.getHtmlBody()
        # construct full html
        htmlFull = (
            f"<head>\n"
            f"<style>\n"
            f"{viewerTheme}\n"
            f"</style>\n"
            f"</head>\n"
            f"<body>\n"
            f"{htmlBody}\n"
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
        if mode == self.SelectionMode.SingleSelection:
            self._btns.setExclusive(True)
        if mode == self.SelectionMode.MultiSelection:
            self._btns.setExclusive(False)
        # set view to match any change
        self.onViewSwitcherButtonClicked()
    
    def setCtrls(self, ctrls):
        # check flags
        for flag in [
            MarkdownCtrl.IdentifierFlag.RawMarkdownCtrl,
            MarkdownCtrl.IdentifierFlag.RawHtmlCtrl,
            MarkdownCtrl.IdentifierFlag.RenderedHtmlCtrl,
            MarkdownCtrl.IdentifierFlag.ViewSwitcherCtrl,
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
            MarkdownCtrl.IdentifierFlag.RawMarkdownCtrl,
            MarkdownCtrl.IdentifierFlag.RawHtmlCtrl,
            MarkdownCtrl.IdentifierFlag.RenderedHtmlCtrl,
        ]:
            # get corresponding button
            btn = self.getButton(flag)

            if flag in buttons:
                # if visibility is True, show corresponding button
                btn.show()
            else:
                # if False, hide the corresponding button
                btn.hide()
    
    def setView(self, ctrls):
        """
        """
        # check flags
        for flag in [
            MarkdownCtrl.IdentifierFlag.RawMarkdownCtrl,
            MarkdownCtrl.IdentifierFlag.RawHtmlCtrl,
            MarkdownCtrl.IdentifierFlag.RenderedHtmlCtrl,
        ]:
            # get corresponding button
            btn = self.getButton(flag)
            # check/unecheck button as requested
            btn.setChecked(flag in ctrls)
        # refresh ctrls view
        self.onViewSwitcherButtonClicked()
    
    def setButtonStyle(self, style, buttons=IdentifierFlag.AllCtrls):
        """
        """
        # check flags
        for flag in [
            self.IdentifierFlag.RawMarkdownCtrl,
            self.IdentifierFlag.RawHtmlCtrl,
            self.IdentifierFlag.RenderedHtmlCtrl,
        ]:
            if flag in buttons:
                # get corresponding button
                btn = self.getButton(flag)
                # apply style
                if MarkdownCtrl.ButtonStyleFlag.ButtonIconOnly in style:
                    btn.setIcon(btn._icon)
                    btn.setText("")
                elif MarkdownCtrl.ButtonStyleFlag.ButtonTextOnly in style:
                    btn.setIcon(gui.QIcon())
                    btn.setText(btn._label)
                elif MarkdownCtrl.ButtonStyleFlag.ButtonTextOnly in style:
                    btn.setIcon(btn._icon)
                    btn.setText(btn._label)
    
    def setButtonIcon(self, icon, buttons=IdentifierFlag.AllCtrls):
        """
        """
        # check flags
        for flag in [
            self.IdentifierFlag.RawMarkdownCtrl,
            self.IdentifierFlag.RawHtmlCtrl,
            self.IdentifierFlag.RenderedHtmlCtrl,
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
        viewSwitcherCtrl = self.getCtrl(self.IdentifierFlag.ViewSwitcherCtrl)
        # set position
        for thisFlag, sizerDir, btnSizerDir in [
            (self.ButtonStyleFlag.LeftButtonsArea, self.sizer.Direction.RightToLeft, self.sizer.Direction.TopToBottom),
            (self.ButtonStyleFlag.RightButtonsArea, self.sizer.Direction.LeftToRight, self.sizer.Direction.TopToBottom),
            (self.ButtonStyleFlag.TopButtonsArea, self.sizer.Direction.BottomToTop, self.sizer.Direction.LeftToRight),
            (self.ButtonStyleFlag.BottomButtonsArea, self.sizer.Direction.TopToBottom, self.sizer.Direction.LeftToRight),
        ]:
            if flag | thisFlag == flag:
                # if flag is present, use sizer directions to move buttons to the corresponding area
                self.sizer.setDirection(sizerDir)
                viewSwitcherCtrl.sizer.setDirection(btnSizerDir)
        # set alignment
        for flag, sizerFlag in [
            (self.ButtonStyleFlag.AlignButtonsLeading, util.Qt.AlignLeading),
            (self.ButtonStyleFlag.AlignButtonsCenter, util.Qt.AlignCenter),
            (self.ButtonStyleFlag.AlignButtonsTrailing, util.Qt.AlignTrailing),
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
        # bind style function
        self.textChanged.connect(self.styleText)
    
    def styleText(self):
        """
        Apply pyments.style to text contents
        """
        # don't trigger any events while this method executes
        self.blockSignals(True)

        # get cursor handle
        cursor = gui.QTextCursor(self.document())
        # set base style
        self.setStyleSheet(
            f"background-color: {editorTheme.background_color};"
            f"font-family: JetBrains Mono, Noto Emoji;"
            f"font-size: 10pt;"
            f"border: 1px solid {editorTheme.line_number_background_color};"
        )
        # lex content to get tokens
        tokens = pygments.lex(self.toPlainText(), lexer=self.lexer)
        # re-add characters with styling
        i = 0
        for token, text in tokens:
            # get style for this token
            token_style = editorTheme.style_for_token(token)
            # create format object
            char_format = gui.QTextCharFormat()
            char_format.setFontFamily("JetBrains Mono")
            char_format.setFontItalic(token_style['italic'])
            if token_style['bold']:
                char_format.setFontWeight(600)
            char_format.setFontUnderline(token_style['underline'])
            char_format.setForeground(gui.QColor("#" + token_style['color']))
            # select corresponding chars
            cursor.setPosition(i)
            cursor.movePosition(cursor.Right, n=len(text), mode=cursor.KeepAnchor)
            # format selection
            cursor.setCharFormat(char_format)
            # move forward to next token
            i += len(text)

        # allow signals to trigger again
        self.blockSignals(False)


class HTMLPreviewCtrl(html.QWebEngineView):
    def __init__(self, parent, minSize=(256, 256)):
        # initalise
        html.QWebEngineView.__init__(self)
        self.parent = parent
        # set minimum size
        self.setMinimumSize(*minSize)
    
    def setHtml(self, content, filename=None):
        # if not given a filename, use assets folder
        if filename is None:
            filename = Path(__file__).parent.parent / "assets" / "untitled.html"
        # enforce html extension
        filename = filename.parent / (filename.stem + ".html")
        # get base url
        base_url = util.QUrl.fromLocalFile(str(filename))
        # set HTML
        html.QWebEngineView.setHtml(self, content, base_url)
