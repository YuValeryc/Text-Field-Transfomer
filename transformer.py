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
            "custom (Python lambda)"
        ])
        self.optionBox.setMinimumHeight(30)
        # Store true option key
        for i, key in enumerate(["lower", "upper", "capitalize", "title", "strip", "custom"]):
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
        """Enable or disable the custom function field based on selection."""
        selected_option = self.optionBox.currentData()
        self.customEdit.setEnabled(selected_option == "custom")
        if selected_option != "custom":
            self.customEdit.clear()

    def load_fields(self):
        """Load the list of fields from the first available note."""
        print("[Info] Loading note fields...")

        if self.nids_to_transform:
            sample_nid = self.nids_to_transform[0]
        else:
            all_nids = self.mw.col.find_notes("")
            if not all_nids:
                showInfo("No notes found in your collection.")
                print("[Warning] No notes found.")
                self.reject()
                return
            sample_nid = all_nids[0]

        try:
            note = self.mw.col.get_note(sample_nid)
        except Exception as e:
            showInfo("Failed to load note data.")
            print(f"[Error] Could not load note data: {e}")
            self.reject()
            return

        fields = note.keys()
        if not fields:
            showInfo("This note type has no fields.")
            print("[Warning] Note type has no fields.")
            self.reject()
            return

        self.fieldBox.clear()
        self.fieldBox.addItems(fields)
        print(f"[Info] Loaded fields: {fields}")

    def apply(self):
        """Apply the selected transformation to the chosen field(s)."""
        field = self.fieldBox.currentText()
        option = self.optionBox.currentData()
        custom = self.customEdit.text().strip()
        inplace = self.inplaceCheck.isChecked()

        print(f"[Info] Applying transformation: field='{field}', option='{option}', inplace={inplace}")

        # Retrieve note IDs safely
        if self.nids_to_transform:
            nids = self.nids_to_transform
        elif hasattr(self.mw, "browser") and getattr(self.mw, "browser", None):
            try:
                nids = self.mw.browser.selected_notes()
            except Exception:
                nids = []
            if not nids:
                nids = self.mw.col.find_notes("")
        else:
            nids = self.mw.col.find_notes("")

        if not nids:
            showInfo("No notes selected or found for transformation.")
            print("[Warning] No notes selected or found.")
            return

        count = 0
        self.mw.checkpoint("Text Field Transformation")  # safer than deprecated undo_group_*
        try:
            for nid in nids:
                note = self.mw.col.get_note(nid)
                if not note:
                    continue

                if field not in note:
                    continue

                original = note[field]
                new_text = transform_text(original, option, custom)

                if new_text != original:
                    if inplace:
                        note[field] = new_text
                        note.flush()
                        count += 1
                    else:
                        new_note = Note(self.mw.col, note.mid)
                        for k, v in note.items():
                            new_note[k] = new_text if k == field else v
                        self.mw.col.add_note(new_note)
                        count += 1

            self.mw.reset()
            showInfo(f"✅ Applied transformation to {count} note(s).")
            print(f"[Success] Transformation applied to {count} note(s).")
            self.accept()

        except Exception as e:
            showInfo(f"⚠ Error during transformation:\n{e}")
            print(f"[Error] Transformation failed: {e}")
            raise


def open_transformer_from_tools_menu():
    """Open the transformer dialog from the Tools menu."""
    print("[Action] Opened transformer from Tools menu.")
    dlg = TransformerDialog(mw)
    dlg.exec()


def open_transformer_from_browser(browser):
    """Open the transformer dialog from the Browser context menu."""
    selected_nids = browser.selected_notes()
    if not selected_nids:
        tooltip("Please select at least one note to transform.")
        print("[Warning] No notes selected in browser.")
        return
    print(f"[Action] Opening transformer for {len(selected_nids)} selected notes.")
    dlg = TransformerDialog(mw, nids_to_transform=selected_nids)
    dlg.exec()


def add_browser_menu_action(browser, menu):
    """Add 'Transform Field...' option to the browser context menu."""
    action = QAction("Transform Field...", browser)
    action.triggered.connect(lambda: open_transformer_from_browser(browser))
    menu.addAction(action)
    print("[Info] Added 'Transform Field...' to browser menu.")


#  Register hooks
gui_hooks.browser_menus_did_init.append(add_browser_menu_action)

#  Add to Tools menu
action = QAction("Transform Fields (All Notes)", mw)
action.triggered.connect(open_transformer_from_tools_menu)
mw.form.menuTools.addAction(action)
print("[Info] 'Transform Fields (All Notes)' added to Tools menu.")
