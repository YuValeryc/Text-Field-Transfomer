from anki.hooks import addHook

# Import the function from transformer.py
from .transformer import open_transformer_from_browser


def add_transformer_to_browser_edit_menu(browser):
    """
    Add the 'Transform Field...' action to the Edit menu in the Anki Browser.
    """
    print("[Info] Adding 'Transform Field...' to the Browser Edit menu...")

    # Get the Edit menu from the browser window
    menu = browser.form.menuEdit

    # Add a separator for better visual grouping
    menu.addSeparator()

    # Create a new action in the Edit menu
    action = menu.addAction("Transform Field...")

    # Connect the action to open the Transformer dialog
    # Lambda ensures the current 'browser' instance is passed correctly
    action.triggered.connect(lambda _, b=browser: open_transformer_from_browser(b))

    print("[Success] 'Transform Field...' added to Browser Edit menu.")


# ========== ACTIVATE HOOK ==========
addHook("browser.setupMenus", add_transformer_to_browser_edit_menu)
print("[Hook Registered] 'browser.setupMenus' -> add_transformer_to_browser_edit_menu")
