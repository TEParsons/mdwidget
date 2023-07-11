import traceback
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
    def __init__(
            self, parent, interpreter=None, 
            minCtrlSize=(256, 256), alignment=()
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
        self.viewToggleCtrl.addButton(ctrl=self.rawMarkdownCtrl, iconName="view_md", label="Markdown code")
        self.viewToggleCtrl.addButton(ctrl=self.rawHTMLCtrl, iconName="view_html", label="HTML code")
        self.viewToggleCtrl.addButton(ctrl=self.renderedHTMLCtrl, iconName="view_preview", label="HTML preview")
        self.setButtonValues((True, False, True))
        self.setButtonVisibility((True, True, True))
        self.sizer.addWidget(self.viewToggleCtrl)

        # bind to render function
        self.rawMarkdownCtrl.textChanged.connect(self.renderHTML)
    
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
    
    def setButtonValues(self, values):
        self.viewToggleCtrl.setValues(values)
    
    def setButtonVisibility(self, visible):
        self.viewToggleCtrl.setVisibility(visible)
    
    def setButtonStyle(self, style):
        """
        Set the style for view toggle buttons.

        Parameters
        ----------
        ori : PyQt5.QtCore.Qt.ToolButtonStyle
            How should the buttons look? Default is ToolButtonIconOnly.
            - ToolButtonIconOnly : Only show icons, no label
            - ToolButtonTextOnly : Only show label, no icon
            - ToolButtonTextBesideIcon : Show icon and label
        """
        self.viewToggleCtrl.setStyle(style)
    
    def setButtonAlignment(self, align):
        """
        Set the alignment of view toggle buttons within their panel.

        Parameters
        ----------
        align : PyQt5.QtCore.Qt.AlignmentFlag
            One or more (combined via the | operator) AlignmentFlag.

            Horizontal flags (ignored when orientation is vertical):
            - AlignLeft : Align to the left of the panel
            - AlignHCenter : Align to the center of the panel
            - AlignRight : Align to the right of the panel

            Vertical flags (ignored when orientation is horizontal):
            - AlignTop : Align to the top of the panel
            - AlignVCenter : Align to the center of the panel
            - AlignBottom : Align to the bottom of the panel

            Bidirectional flags (always used):
            - AlignLeading : Align to the start of the panel
            - AlignCenter : Align to the center of the panel
            - AlignTrailing : Align to the end of the panel
        
            Default is AlignCenter.
        """
        self.viewToggleCtrl.sizer.setAlignment(align)
    
    def setButtonPosition(self, pos):
        """
        Set the position of the toggle buttons panel within this control.

        Parameters
        ----------
        pos : PyQt5.QtCore.Qt.ToolBarArea
            Where should the buttons panel be relative to the text controls? Default is BottomToolBarArea.
            - LeftToolBarArea : Buttons will be to the left of text controls
            - RightToolBarArea : Buttons will be to the right of text controls
            - TopToolBarArea : Buttons will be above text controls
            - BottomToolBarArea : Buttons will be below text controls
        """
        # set to left position
        if pos | util.Qt.LeftToolBarArea == pos:
            self.sizer.setDirection(self.sizer.Direction.RightToLeft)
            self.viewToggleCtrl.sizer.setDirection(self.sizer.Direction.TopToBottom)
        # set to right position
        if pos | util.Qt.RightToolBarArea == pos:
            self.sizer.setDirection(self.sizer.Direction.LeftToRight)
            self.viewToggleCtrl.sizer.setDirection(self.sizer.Direction.TopToBottom)
        # set to top position
        if pos | util.Qt.TopToolBarArea == pos:
            self.sizer.setDirection(self.sizer.Direction.BottomToTop)
            self.viewToggleCtrl.sizer.setDirection(self.sizer.Direction.LeftToRight)
        # set to right position
        if pos | util.Qt.BottomToolBarArea == pos:
            self.sizer.setDirection(self.sizer.Direction.TopToBottom)
            self.viewToggleCtrl.sizer.setDirection(self.sizer.Direction.LeftToRight)


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
            if style | util.Qt.ToolButtonIconOnly == style:
                self.setIcon(self._icon)
                self.setText("")
            if style | util.Qt.ToolButtonTextOnly == style:
                self.setIcon(gui.QIcon())
                self.setText(self._label)
            if style | util.Qt.ToolButtonTextBesideIcon == style:
                self.setIcon(self._icon)
                self.setText(self._label)
        
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
        # set default style
        self.setStyle(util.Qt.ToolButtonIconOnly)
    
    def addButton(self, ctrl, iconName=None, label=""):
        # make button
        btn = self.ViewToggleButton(self, ctrl, iconName=iconName, label=label)
        # apply own style
        btn.setStyle(self._style)
        # store button handle
        self.btns.append(btn)
        # add to sizer
        self.sizer.addWidget(btn)
    
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
