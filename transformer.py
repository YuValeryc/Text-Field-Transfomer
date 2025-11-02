from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import showInfo, tooltip
from anki.notes import Note


def transform_text(text, option, custom_func):
    """Perform text transformation based on the selected option."""
    if option == "lower":
        return text.lower()
    elif option == "upper":
        return text.upper()
    elif option == "capitalize":
        return text.capitalize()
    elif option == "strip":
        return text.strip()
    elif option == "title":
        return text.title()
    elif option == "replace":
        # custom_func ở đây là tuple (find_text, replace_text)
        find_text, replace_text = custom_func if isinstance(custom_func, tuple) else ("", "")
        if not find_text:
            return text  # không thay gì nếu chưa nhập
        return text.replace(find_text, replace_text)
    elif option == "custom" and custom_func:
        try:
            func = eval(custom_func, {"__builtins__": {}})
            return func(text)
        except Exception as e:
            showInfo(f"Error in custom function:\n{e}")
            print(f"[Error] Custom function failed: {e}")
            return text
    else:
        return text


class TransformerDialog(QDialog):
    def __init__(self, parent_mw, nids_to_transform=None):
        super().__init__(parent_mw)
        self.mw = parent_mw
        self.nids_to_transform = nids_to_transform or []

        self.setWindowTitle("Text Field Transformer")
        self.resize(450, 350)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # --- Title ---
        title_label = QLabel("<h2>Transform Text Fields</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addSpacing(10)

        # --- Field selection ---
        layout.addWidget(QLabel("<b>Select Field:</b>"))
        self.fieldBox = QComboBox()
        self.fieldBox.setEditable(False)
        self.fieldBox.setMinimumHeight(30)
        layout.addWidget(self.fieldBox)

        # --- Option selection ---
        layout.addWidget(QLabel("<b>Transformation Type:</b>"))
        self.optionBox = QComboBox()
        self.optionBox.addItems([
            "lower (all lowercase)",
            "upper (ALL UPPERCASE)",
            "capitalize (First letter capitalized)",
            "title (Each Word Capitalized)",
            "strip (Remove whitespace)",
            "replace (find → replace)",
            "custom (Python lambda)"
        ])
        self.optionBox.setMinimumHeight(30)
        for i, key in enumerate(["lower", "upper", "capitalize", "title", "strip", "replace", "custom"]):
            self.optionBox.setItemData(i, key)
        layout.addWidget(self.optionBox)

        # --- Custom lambda input ---
        layout.addWidget(QLabel("<b>Custom function (e.g., <code>lambda x: x[::-1]</code>):</b>"))
        self.customEdit = QLineEdit()
        self.customEdit.setPlaceholderText("Enter a lambda function, e.g. lambda x: x.replace('a','b')")
        self.customEdit.setMinimumHeight(30)
        self.customEdit.setEnabled(False)
        layout.addWidget(self.customEdit)
        self.optionBox.currentIndexChanged.connect(self._update_custom_field_state)

        # --- Replace inputs ---
        replaceLayout = QGridLayout()
        replaceLayout.addWidget(QLabel("<b>Find text:</b>"), 0, 0)
        self.findEdit = QLineEdit()
        self.findEdit.setPlaceholderText("Text to find")
        self.findEdit.setMinimumHeight(30)
        replaceLayout.addWidget(self.findEdit, 0, 1)

        replaceLayout.addWidget(QLabel("<b>Replace with:</b>"), 1, 0)
        self.replaceEdit = QLineEdit()
        self.replaceEdit.setPlaceholderText("Replace with...")
        self.replaceEdit.setMinimumHeight(30)
        replaceLayout.addWidget(self.replaceEdit, 1, 1)

        layout.addLayout(replaceLayout)

        # Mặc định ẩn
        self.findEdit.setEnabled(False)
        self.replaceEdit.setEnabled(False)

        # --- In-place or clone ---
        self.inplaceCheck = QCheckBox("Apply in-place (overwrite selected field)")
        self.inplaceCheck.setChecked(True)
        layout.addWidget(self.inplaceCheck)
        layout.addSpacing(15)

        # --- Buttons ---
        btnLayout = QHBoxLayout()
        self.applyBtn = QPushButton("Apply Transformation")
        self.applyBtn.setMinimumHeight(35)
        self.applyBtn.setStyleSheet("background-color:#4CAF50;color:white;font-weight:bold;")
        self.cancelBtn = QPushButton("Cancel")
        self.cancelBtn.setMinimumHeight(35)
        btnLayout.addWidget(self.applyBtn)
        btnLayout.addWidget(self.cancelBtn)
        layout.addLayout(btnLayout)

        self.applyBtn.clicked.connect(self.apply)
        self.cancelBtn.clicked.connect(self.reject)

        self.load_fields()

    def _update_custom_field_state(self):
        selected_option = self.optionBox.currentData()
        self.customEdit.setEnabled(selected_option == "custom")
        if selected_option != "custom":
            self.customEdit.clear()

        is_replace = selected_option == "replace"
        self.findEdit.setEnabled(is_replace)
        self.replaceEdit.setEnabled(is_replace)
        if not is_replace:
            self.findEdit.clear()
            self.replaceEdit.clear()

    def load_fields(self):
        if self.nids_to_transform:
            sample_nid = self.nids_to_transform[0]
        else:
            all_nids = self.mw.col.find_notes("")
            if not all_nids:
                showInfo("No notes found in your collection.")
                self.reject()
                return
            sample_nid = all_nids[0]

        note = self.mw.col.get_note(sample_nid)
        fields = note.keys()
        if not fields:
            showInfo("This note type has no fields.")
            self.reject()
            return

        self.fieldBox.clear()
        self.fieldBox.addItems(fields)

    def apply(self):
        field = self.fieldBox.currentText()
        option = self.optionBox.currentData()
        inplace = self.inplaceCheck.isChecked()

        # ✅ Lấy đúng custom_func theo loại
        if option == "replace":
            find_text = self.findEdit.text()
            replace_text = self.replaceEdit.text()
            custom_func = (find_text, replace_text)
        else:
            custom_func = self.customEdit.text().strip()

        # Lấy danh sách note
        if self.nids_to_transform:
            nids = self.nids_to_transform
        else:
            nids = self.mw.col.find_notes("")

        if not nids:
            showInfo("No notes selected or found for transformation.")
            return

        count = 0
        self.mw.checkpoint("Text Field Transformation")

        try:
            for nid in nids:
                note = self.mw.col.get_note(nid)
                if not note or field not in note:
                    continue

                original = note[field]
                new_text = transform_text(original, option, custom_func)

                if new_text != original:
                    if inplace:
                        note[field] = new_text
                        note.flush()
                    else:
                        new_note = Note(self.mw.col, note.mid)
                        for k, v in note.items():
                            new_note[k] = new_text if k == field else v
                        self.mw.col.add_note(new_note)
                    count += 1

            self.mw.reset()
            showInfo(f"✅ Applied transformation to {count} note(s).")
            self.accept()

        except Exception as e:
            showInfo(f"⚠ Error during transformation:\n{e}")
            print(f"[Error] Transformation failed: {e}")
            raise


def open_transformer_from_browser(browser):
    selected_nids = browser.selected_notes()
    if not selected_nids:
        tooltip("Please select at least one note to transform.")
        return
    dlg = TransformerDialog(mw, nids_to_transform=selected_nids)
    dlg.setWindowModality(Qt.WindowModality.NonModal)
    dlg.setWindowFlags(Qt.WindowType.Dialog)
    dlg.show()


def add_browser_menu_action(browser, menu):
    action = QAction("Transform Field...", browser)
    action.triggered.connect(lambda: open_transformer_from_browser(browser))
    menu.addAction(action)


def safe_add_menu(*args):
    try:
        if len(args) == 1:
            browser = args[0]
            menu = getattr(browser, "menu", None)
        elif len(args) == 2:
            browser, menu = args
        else:
            return

        if menu is None:
            return

        add_browser_menu_action(browser, menu)
    except Exception as e:
        print(f"[Warning] Text Field Transformer menu hook error: {e}")


gui_hooks.browser_menus_did_init.append(safe_add_menu)
