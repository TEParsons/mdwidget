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


class MarkdownCtrlFlag(enum.Flag):
    # identifiers for controls
    RawMarkdownCtrl = enum.auto()
    RawHtmlCtrl = enum.auto()
    RenderedHtmlCtrl = enum.auto()
    AllCtrls = RawMarkdownCtrl | RawHtmlCtrl | RenderedHtmlCtrl
    # identifiers for toggle buttons
    RawMarkdownCtrlButton = enum.auto()
    RawHtmlCtrlButton = enum.auto()
    RenderedHtmlCtrlButton = enum.auto()
    AllCtrlButtons = RawMarkdownCtrlButton | RawHtmlCtrlButton | RenderedHtmlCtrlButton
    # button position options
    LeftButtonsArea = enum.auto()
    RightButtonsArea = enum.auto()
    TopButtonsArea = enum.auto()
    BottomButtonsArea = enum.auto()
    # button alignment options
    AlignButtonsLeading = enum.auto()
    AlignButtonsCenter = enum.auto()
    AlignButtonsTrailing = enum.auto()
    # button style options
    ButtonIconOnly = enum.auto()
    ButtonTextOnly = enum.auto()
    ButtonTextBesideIcon = enum.auto()

    # default style
    Default = (
        RawMarkdownCtrl | RenderedHtmlCtrl | 
        RawMarkdownCtrlButton | RenderedHtmlCtrlButton | 
        BottomButtonsArea | AlignButtonsCenter | ButtonIconOnly
    )


class MarkdownCtrl(qt.QWidget):
    MarkdownCtrlFlag = MarkdownCtrlFlag
    def __init__(
            self, parent, interpreter=None, minCtrlSize=(256, 256), 
            flags=MarkdownCtrlFlag.Default
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

        # setup panel
        self.ctrls = qt.QSplitter(self)
        self.ctrls.setChildrenCollapsible(False)
        self.sizer.addWidget(self.ctrls, stretch=1)
        
        # add raw markdown ctrl
        self.rawMarkdownCtrl = StyledTextCtrl(self, language="markdown", minSize=minCtrlSize)
        self.ctrls.addWidget(self.rawMarkdownCtrl)

        # add raw html ctrl
        self.rawHTMLCtrl = StyledTextCtrl(self, language="html", minSize=minCtrlSize)
        self.rawHTMLCtrl.setReadOnly(True)
        self.ctrls.addWidget(self.rawHTMLCtrl)

        # add rendered HTML ctrl
        self.renderedHTMLCtrl = HTMLPreviewCtrl(self, minSize=minCtrlSize)
        self.ctrls.addWidget(self.renderedHTMLCtrl)

        # add view toggle
        self.viewToggleCtrl = ViewToggleCtrl(self)
        self.rawMarkdownCtrlToggle = self.viewToggleCtrl.addButton(ctrl=self.rawMarkdownCtrl, iconName="view_md", label="Markdown code")
        self.rawHtmlCtrlToggle = self.viewToggleCtrl.addButton(ctrl=self.rawHTMLCtrl, iconName="view_html", label="HTML code")
        self.renderedHtmlCtrlToggle = self.viewToggleCtrl.addButton(ctrl=self.renderedHTMLCtrl, iconName="view_preview", label="HTML preview")
        self.sizer.addWidget(self.viewToggleCtrl)

        # bind to render function
        self.rawMarkdownCtrl.textChanged.connect(self.renderHTML)

        # set flags
        self.setWindowFlags(flags)
    
    def renderHTML(self, event=None):
        # get markdown
        mdContent = self.rawMarkdownCtrl.toPlainText()
        # parse to HTML
        try:
            htmlContent = self.interpreter.convert(mdContent)
        except Exception as err:
            tb = "\n".join(traceback.format_exception(err))
            htmlContent = (
                f"<h1>Error</h1>\n"
                f"<p>Could not parse Markdown. Error from Python:</p>\n"
                f"<pre><code>{tb}</code></pre>\n"
                )
        # apply to HTML ctrl
        self.rawHTMLCtrl.setPlainText(htmlContent)
        # apply to HTML viewer
        self.renderedHTMLCtrl.setBody(htmlContent)
    
    def getCtrl(self, flag):
        """
        """
        for thisFlag, ctrl in [
            (MarkdownCtrlFlag.RawMarkdownCtrl, self.rawMarkdownCtrl),
            (MarkdownCtrlFlag.RawHtmlCtrl, self.rawHTMLCtrl),
            (MarkdownCtrlFlag.RenderedHtmlCtrl, self.renderedHTMLCtrl),
            # if given a button, return its ctrl
            (MarkdownCtrlFlag.RawMarkdownCtrlButton, self.rawMarkdownCtrl),
            (MarkdownCtrlFlag.RawHtmlCtrlButton, self.rawHTMLCtrl),
            (MarkdownCtrlFlag.RenderedHtmlCtrlButton, self.renderedHTMLCtrl),
        ]:
            if thisFlag == flag:
                return ctrl
    
    def getButton(self, flag):
        """
        """
        for thisFlag, btn in [
            (MarkdownCtrlFlag.RawMarkdownCtrlButton, self.rawMarkdownCtrlToggle),
            (MarkdownCtrlFlag.RawHtmlCtrlButton, self.rawHtmlCtrlToggle),
            (MarkdownCtrlFlag.RenderedHtmlCtrlButton, self.renderedHtmlCtrlToggle),
            # if given a ctrl, return its button
            (MarkdownCtrlFlag.RawMarkdownCtrl, self.rawMarkdownCtrlToggle),
            (MarkdownCtrlFlag.RawHtmlCtrl, self.rawHtmlCtrlToggle),
            (MarkdownCtrlFlag.RenderedHtmlCtrl, self.renderedHtmlCtrlToggle),
        ]:
            if thisFlag == flag:
                return btn
    
    def _getFlags(self, objs):
        """
        """
        flag = self._getFlag(objs[0])
        for obj in objs:
            flag |= self._getFlag(obj)
        
        return flag
    
    def _getFlag(self, obj):
        """
        """
        flagMap = {
            # controls
            self.rawMarkdownCtrl: MarkdownCtrlFlag.RawMarkdownCtrl,
            self.rawHTMLCtrl: MarkdownCtrlFlag.RawHtmlCtrl,
            self.renderedHTMLCtrl: MarkdownCtrlFlag.RenderedHtmlCtrl,
            # buttons
            self.rawMarkdownCtrlToggle: MarkdownCtrlFlag.RawMarkdownCtrlButton,
            self.rawHtmlCtrlToggle: MarkdownCtrlFlag.RawHtmlCtrlButton,
            self.renderedHtmlCtrlToggle: MarkdownCtrlFlag.RenderedHtmlCtrlButton
        }

        return flagMap[obj]        
    
    def setWindowFlags(self, flags):
        """
        """
        # set ctrl visibility
        self.setCtrlVisibility(False)
        self.setCtrlVisibility(True, ctrls=flags)
        # set button visibility
        self.setButtonVisibility(False)
        self.setButtonVisibility(True, buttons=flags)
        # set button style
        self.setButtonStyle(flags, buttons=MarkdownCtrlFlag.AllCtrlButtons)
        # set buttons position
        self.setButtonsPosition(flags)        
        # set button alignment
        self.setButtonsAlignment(flags)
        # remove all bespoke flags
        for attr in dir(MarkdownCtrlFlag):
            flag = getattr(MarkdownCtrlFlag, attr)
            if isinstance(flag, enum.Flag):
                flags &= flag
    
    def setCtrlVisibility(self, visibility, ctrls=MarkdownCtrlFlag.AllCtrls):
        """
        """
        # if given object handle(s), get flags
        if isinstance(ctrls, (list, tuple)):
            ctrls = self._getFlags(ctrls)
        if isinstance(ctrls, (qt.QWidget, qt.QPushButton)):
            ctrls = self._getFlag(ctrls)
        # check flags
        for flag in [
            MarkdownCtrlFlag.RawMarkdownCtrl,
            MarkdownCtrlFlag.RawHtmlCtrl,
            MarkdownCtrlFlag.RenderedHtmlCtrl,
        ]:
            if flag in ctrls and visibility:
                # if flag is present, show the corresponding ctrl (setting its button to True)
                self.getCtrl(flag).show()
                self.getButton(flag).setChecked(True)
            elif flag in ctrls:
                # otherwise, hide the corresponding ctrl (setting its button to False)
                self.getCtrl(flag).hide()
                self.getButton(flag).setChecked(False)
    
    def setButtonVisibility(self, visibility, buttons=MarkdownCtrlFlag.AllCtrlButtons):
        """
        """
        # if given object handle(s), get flags
        if isinstance(buttons, (list, tuple)):
            buttons = self._getFlags(buttons)
        if isinstance(buttons, (qt.QWidget, qt.QPushButton)):
            buttons = self._getFlag(buttons)
        # check flags
        for flag in [
            MarkdownCtrlFlag.RawMarkdownCtrlButton,
            MarkdownCtrlFlag.RawHtmlCtrlButton,
            MarkdownCtrlFlag.RenderedHtmlCtrlButton,
        ]:
            if flag in buttons and visibility:
                # if visibility is True, show corresponding component
                self.getButton(flag).show()
            elif flag in buttons:
                # if False, hide the corresponding button
                self.getButton(flag).hide()

    
    def setButtonStyle(self, style, buttons=MarkdownCtrlFlag.AllCtrlButtons):
        """
        """
        # if given object handle(s), get flags
        if isinstance(buttons, (list, tuple)):
            buttons = self._getFlags(buttons)
        if isinstance(buttons, (qt.QWidget, qt.QPushButton)):
            buttons = self._getFlag(buttons)
        # check flags
        for flag in [
            MarkdownCtrlFlag.RawMarkdownCtrlButton, MarkdownCtrlFlag.RawMarkdownCtrl,
            MarkdownCtrlFlag.RawHtmlCtrlButton, MarkdownCtrlFlag.RawHtmlCtrl,
            MarkdownCtrlFlag.RenderedHtmlCtrlButton, MarkdownCtrlFlag.RenderedHtmlCtrl,
        ]:
            if flag in buttons:
                # if visibility is True, style corresponding button
                self.getButton(flag).setStyle(style)
    
    def setButtonsPosition(self, pos):
        """
        """
        for flag, sizerDir, btnSizerDir in [
            (MarkdownCtrlFlag.LeftButtonsArea, self.sizer.Direction.RightToLeft, self.sizer.Direction.TopToBottom),
            (MarkdownCtrlFlag.RightButtonsArea, self.sizer.Direction.LeftToRight, self.sizer.Direction.TopToBottom),
            (MarkdownCtrlFlag.TopButtonsArea, self.sizer.Direction.BottomToTop, self.sizer.Direction.LeftToRight),
            (MarkdownCtrlFlag.BottomButtonsArea, self.sizer.Direction.TopToBottom, self.sizer.Direction.LeftToRight),
        ]:
            if pos | flag == pos:
                # if flag is present, use sizer directions to move buttons to the corresponding area
                self.sizer.setDirection(sizerDir)
                self.viewToggleCtrl.sizer.setDirection(btnSizerDir)
    
    def setButtonsAlignment(self, align):
        """
        """
        for flag, sizerFlag in [
            (MarkdownCtrlFlag.AlignButtonsLeading, util.Qt.AlignLeading),
            (MarkdownCtrlFlag.AlignButtonsCenter, util.Qt.AlignCenter),
            (MarkdownCtrlFlag.AlignButtonsTrailing, util.Qt.AlignTrailing),
        ]:
            if align | flag == align:
                # if flag is present, apply corresponding alignment to button sizer
                self.viewToggleCtrl.sizer.setAlignment(sizerFlag)


class ViewToggleCtrl(qt.QWidget):  
    class ViewToggleButton(qt.QPushButton):
        def __init__(self, parent, ctrl, iconName=None, label=""):
            # initialise
            qt.QPushButton.__init__(self, parent)
            self.parent = parent
            # make checkable
            self.setCheckable(True)
            # connect function
            self.ctrl = ctrl
            self.clicked.connect(self.onClick)
            # set icon
            if iconName is not None:
                iconPath = assetsFolder / "icons" / f"{iconName}.svg"
                self._icon = gui.QIcon(str(iconPath))
            else:
                self._icon = gui.QIcon()
            self.setIcon(self._icon)
            # set label
            self._label = label
            self.setText(label)
        
        def setStyle(self, style):
            for flag, icon, text in [
                (MarkdownCtrlFlag.ButtonIconOnly, self._icon, ""),
                (MarkdownCtrlFlag.ButtonTextOnly, gui.QIcon(), self._label),
                (MarkdownCtrlFlag.ButtonTextBesideIcon, self._icon, self._label),
            ]:
                if flag in style:
                    self.setIcon(icon)
                    self.setText(text)
        
        def onClick(self, evt=None):
            if self.isChecked():
                self.ctrl.show()
            else:
                self.ctrl.hide()
           
    def __init__(self, parent):
        # initialise
        qt.QWidget.__init__(self, parent)
        self.parent = parent
        # setup layout
        self.sizer = qt.QBoxLayout(qt.QBoxLayout.LeftToRight, self)
        self.sizer.setAlignment(util.Qt.AlignCenter)
        # array for buttons
        self.btns = []
    
    def addButton(self, ctrl, iconName=None, label=""):
        # make button
        btn = self.ViewToggleButton(self, ctrl, iconName=iconName, label=label)
        # store button handle
        self.btns.append(btn)
        # add to sizer
        self.sizer.addWidget(btn)

        return btn
    
    def setValues(self, values):
        # if given a single bool, make iterable
        if isinstance(values, bool):
            values = (values,)
        # if single length iterable, fit to length
        if len(values) == 1:
            values = values * len(self.btns)
        assert len(values) == len(self.btns), "When setting values for ViewToggle, there must be the same number of values as there are buttons."
        # set each button in order
        for btn, val in zip(self.btns, values):
            btn.setChecked(val)
            btn.onClick()
    
    def setVisibility(self, visible):
        # if given a single bool, make iterable
        if isinstance(visible, bool):
            visible = (visible,)
        # if single length iterable, fit to length
        if len(visible) == 1:
            visible = visible * len(self.btns)
        assert len(visible) == len(self.btns), "When setting visibility for ViewToggle, there must be the same number of values as there are buttons."
        # set visibility for each button
        for btn, val in zip(self.btns, visible):
            if val:
                btn.show()
            else:
                btn.hide()
        # if entirely hidden, hide panel
        if any(visible):
            self.show()
        else:
            self.hide()
    
    def setStyle(self, style):
        self._style = style
        for btn in self.btns:
                btn.setStyle(style)


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
        # start off with no content
        self._body = ""
    
    def refresh(self, event=None):
        self.setBody(self.getBody())

    def setBody(self, content:str, filename:Path=None):
        # store just body
        self._body = content
        # construct full HTML
        content_html = (
            f"<head>\n"
            f"<style>\n"
            f"{viewerTheme}\n"
            f"</style>\n"
            f"</head>\n"
            f"<body>\n"
            f"{content}\n"
            f"</body>"
        )
        # if not given a filename, use assets folder
        if filename is None:
            filename = Path(__file__).parent.parent / "assets" / "untitled.html"
        # enforce html extension
            filename = filename.parent / (filename.stem + ".html")
        # get base url
        base_url = util.QUrl.fromLocalFile(str(filename))
        # set HTML
        self.setHtml(content_html, base_url)
    
    def getBody(self):
        return self._body
    
    def showEvent(self, event):
        self.refresh()
        return html.QWebEngineView.showEvent(self, event)
    
    def hideEvent(self, event):
        return html.QWebEngineView.hideEvent(self, event)
