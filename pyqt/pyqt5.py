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
        NoSelection = enum.auto()
        SingleSelection = enum.auto()
        MultiSelection = enum.auto()
    
    class IdentifierFlag(enum.Flag):
        # identifiers for controls
        RawMarkdownCtrl = enum.auto()
        RawHtmlCtrl = enum.auto()
        RenderedHtmlCtrl = enum.auto()
        AllCtrls = RawMarkdownCtrl | RawHtmlCtrl | RenderedHtmlCtrl
        # identifiers for button area
        ViewSwitcherCtrl = enum.auto()
    
    class ButtonStyleFlag(enum.Flag):
        # button style options
        ButtonIconOnly = enum.auto()
        ButtonTextOnly = enum.auto()
        ButtonTextBesideIcon = enum.auto()
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
            minCtrlSize=(256, 256),
            showCtrls=IdentifierFlag.RawMarkdownCtrl | IdentifierFlag.RenderedHtmlCtrl | IdentifierFlag.ViewSwitcherCtrl,
            selectionMode=SelectionMode.MultiSelection,
            buttonStyle=ButtonStyleFlag.ButtonIconOnly | ButtonStyleFlag.BottomButtonsArea | ButtonStyleFlag.AlignButtonsCenter
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
        
        # add raw markdown ctrl
        rawMarkdownCtrl = self._ctrls[self.IdentifierFlag.RawMarkdownCtrl] = StyledTextCtrl(self, language="markdown", minSize=minCtrlSize)
        rawMarkdownCtrl.textChanged.connect(self.renderHTML)
        ctrlsPanel.addWidget(rawMarkdownCtrl)

        # add raw html ctrl
        rawHtmlCtrl = self._ctrls[self.IdentifierFlag.RawHtmlCtrl] = StyledTextCtrl(self, language="html", minSize=minCtrlSize)
        rawHtmlCtrl.setReadOnly(True)
        ctrlsPanel.addWidget(rawHtmlCtrl)

        # add rendered HTML ctrl
        renderedHtmlCtrl = self._ctrls[self.IdentifierFlag.RenderedHtmlCtrl] = HTMLPreviewCtrl(self, minSize=minCtrlSize)
        ctrlsPanel.addWidget(renderedHtmlCtrl)

        # add view toggle ctrl
        viewSwitcherCtrl = self._ctrls[self.IdentifierFlag.ViewSwitcherCtrl] = ViewToggleCtrl(self)
        self.sizer.addWidget(viewSwitcherCtrl)

        # add buttons
        self.rawMarkdownCtrlToggle = viewSwitcherCtrl.addButton(ctrl=rawMarkdownCtrl, iconName="view_md", label="Markdown code")
        self.rawHtmlCtrlToggle = viewSwitcherCtrl.addButton(ctrl=rawHtmlCtrl, iconName="view_html", label="HTML code")
        self.renderedHtmlCtrlToggle = viewSwitcherCtrl.addButton(ctrl=renderedHtmlCtrl, iconName="view_preview", label="HTML preview")

        # set ctrl visibility
        self.setCtrlVisibility(False)
        self.setCtrlVisibility(True, ctrls=showCtrls)
        # set button visibility
        self.setButtons(showCtrls)
        # set selection mode
        self.setSelectionMode(selectionMode)
        # set button style
        self.setButtonStyle(buttonStyle, buttons=self.IdentifierFlag.AllCtrls)
        self.setButtonsPosition(buttonStyle)        
        self.setButtonsAlignment(buttonStyle)
    
    def renderHTML(self, event=None):
        # get markdown
        mdContent = self.getCtrl(self.IdentifierFlag.RawMarkdownCtrl).toPlainText()
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
        if flag in self._ctrls:
            return self._ctrls[flag]
    
    def getButton(self, flag):
        """
        """
        for thisFlag, btn in [
            (self.IdentifierFlag.RawMarkdownCtrl, self.rawMarkdownCtrlToggle),
            (self.IdentifierFlag.RawHtmlCtrl, self.rawHtmlCtrlToggle),
            (self.IdentifierFlag.RenderedHtmlCtrl, self.renderedHtmlCtrlToggle),
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
        for flag, thisObj in self._ctrls.items():
            if thisObj == flag:
                return flag    
    
    def setSelectionMode(self, mode=True):
        """
        """
        viewSwitcherCtrl = self.getCtrl(self.IdentifierFlag.ViewSwitcherCtrl)
        viewSwitcherCtrl.setSelectionMode(mode)
    
    def setCtrls(self, ctrls):
        # check flags
        for flag in [
            MarkdownCtrl.IdentifierFlag.RawMarkdownCtrl,
            MarkdownCtrl.IdentifierFlag.RawHtmlCtrl,
            MarkdownCtrl.IdentifierFlag.RenderedHtmlCtrl,
            MarkdownCtrl.IdentifierFlag.ViewSwitcherCtrl,
        ]:
            if flag in ctrls:
                # if visibility is True, show corresponding component
                self.getCtrl(flag).show()
                self.getButton(flag).setChecked(True)
            else:
                # if False, hide the corresponding button
                self.getCtrl(flag).hide()
                self.getButton(flag).setChecked(False)
    
    def setCtrlVisibility(self, visibility, ctrls=IdentifierFlag.AllCtrls):
        """
        """
        # if given object handle(s), get flags
        if isinstance(ctrls, (list, tuple)):
            ctrls = self._getFlags(ctrls)
        if isinstance(ctrls, (qt.QWidget, qt.QPushButton)):
            ctrls = self._getFlag(ctrls)
        # check flags
        for flag in [
            self.IdentifierFlag.RawMarkdownCtrl,
            self.IdentifierFlag.RawHtmlCtrl,
            self.IdentifierFlag.RenderedHtmlCtrl,
        ]:
            if flag in ctrls and visibility:
                # if flag is present, show the corresponding ctrl (setting its button to True)
                self.getCtrl(flag).show()
                self.getButton(flag).setChecked(True)
            elif flag in ctrls:
                # otherwise, hide the corresponding ctrl (setting its button to False)
                self.getCtrl(flag).hide()
                self.getButton(flag).setChecked(False)
    
    def setButtons(self, buttons):
        """
        """
        # if given object handle(s), get flags
        if isinstance(buttons, (list, tuple)):
            buttons = self._getFlags(buttons)
        if isinstance(buttons, (qt.QWidget, qt.QPushButton)):
            buttons = self._getFlag(buttons)
        # check flags
        for flag in [
            MarkdownCtrl.IdentifierFlag.RawMarkdownCtrl,
            MarkdownCtrl.IdentifierFlag.RawHtmlCtrl,
            MarkdownCtrl.IdentifierFlag.RenderedHtmlCtrl,
        ]:
            if flag in buttons:
                # if visibility is True, show corresponding component
                self.getButton(flag).show()
            else:
                # if False, hide the corresponding button
                self.getButton(flag).hide()
    
    def setButtonStyle(self, style, buttons=IdentifierFlag.AllCtrls):
        """
        """
        # if given object handle(s), get flags
        if isinstance(buttons, (list, tuple)):
            buttons = self._getFlags(buttons)
        if isinstance(buttons, (qt.QWidget, qt.QPushButton)):
            buttons = self._getFlag(buttons)
        # check flags
        for flag in [
            self.IdentifierFlag.RawMarkdownCtrl,
            self.IdentifierFlag.RawHtmlCtrl,
            self.IdentifierFlag.RenderedHtmlCtrl,
        ]:
            if flag in buttons:
                # if visibility is True, style corresponding button
                self.getButton(flag).setStyle(style)
    
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
    
    def setButtonsPosition(self, pos):
        """
        """
        viewSwitcherCtrl = self.getCtrl(self.IdentifierFlag.ViewSwitcherCtrl)
        for flag, sizerDir, btnSizerDir in [
            (self.ButtonStyleFlag.LeftButtonsArea, self.sizer.Direction.RightToLeft, self.sizer.Direction.TopToBottom),
            (self.ButtonStyleFlag.RightButtonsArea, self.sizer.Direction.LeftToRight, self.sizer.Direction.TopToBottom),
            (self.ButtonStyleFlag.TopButtonsArea, self.sizer.Direction.BottomToTop, self.sizer.Direction.LeftToRight),
            (self.ButtonStyleFlag.BottomButtonsArea, self.sizer.Direction.TopToBottom, self.sizer.Direction.LeftToRight),
        ]:
            if pos | flag == pos:
                # if flag is present, use sizer directions to move buttons to the corresponding area
                self.sizer.setDirection(sizerDir)
                viewSwitcherCtrl.sizer.setDirection(btnSizerDir)
    
    def setButtonsAlignment(self, align):
        """
        """
        viewSwitcherCtrl = self.getCtrl(self.IdentifierFlag.ViewSwitcherCtrl)
        for flag, sizerFlag in [
            (self.ButtonStyleFlag.AlignButtonsLeading, util.Qt.AlignLeading),
            (self.ButtonStyleFlag.AlignButtonsCenter, util.Qt.AlignCenter),
            (self.ButtonStyleFlag.AlignButtonsTrailing, util.Qt.AlignTrailing),
        ]:
            if align | flag == align:
                # if flag is present, apply corresponding alignment to button sizer
                viewSwitcherCtrl.sizer.setAlignment(sizerFlag)


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
                (MarkdownCtrl.ButtonStyleFlag.ButtonIconOnly, self._icon, ""),
                (MarkdownCtrl.ButtonStyleFlag.ButtonTextOnly, gui.QIcon(), self._label),
                (MarkdownCtrl.ButtonStyleFlag.ButtonTextBesideIcon, self._icon, self._label),
            ]:
                if flag in style:
                    self.setIcon(icon)
                    self.setText(text)
        
        def onClick(self, evt=None, recursive=True):
            if self.parent.multipleSelection:
                # if parent allows multiselect, do simple show/hide
                if self.isChecked():
                    self.ctrl.show()
                else:
                    self.ctrl.hide()
            elif self.isChecked():
                # get index
                i = self.parent.btns.index(self)
                # create values array
                values = [False] * len(self.parent.btns)
                values[i] = True
                # set from parent
                self.parent.setValues(values)
            else:
                # if deselecting in single select mode, reselect
                self.setChecked(True)        
           
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

    def setSelectionMode(self, mode):
        # convert to boolean if using flags
        if not isinstance(mode, bool) and MarkdownCtrl.SelectionMode.MultiSelection in mode:
            mode = True
        if not isinstance(mode, bool) and MarkdownCtrl.SelectionMode.SingleSelection in mode:
            mode = False 
        # set
        self.multipleSelection = mode
        # set values again (so limiting happens)
        self.setValues(self.getValues())
    
    def setValues(self, values):
        # if given a single bool, make iterable
        if isinstance(values, bool):
            values = (values,)
        # if single length iterable, fit to length
        if len(values) == 1:
            values = values * len(self.btns)
        assert len(values) == len(self.btns), "When setting values for ViewToggle, there must be the same number of values as there are buttons."
        # if multiple selection is disabled, only take first button
        if not self.multipleSelection and True in values:
            i = values.index(True)
            values = [False] * len(self.btns)
            values[i] = True
        # set each button in order
        for btn, val in zip(self.btns, values):
            btn.setChecked(val)
            # show/hide ctrl as appropriate
            if btn.isChecked():
                btn.ctrl.show()
            else:
                btn.ctrl.hide()
    
    def getValues(self):
        values = []
        for btn in self.btns:
            values.append(btn.isChecked())
        
        return values
    
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
