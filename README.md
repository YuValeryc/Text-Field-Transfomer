# 🧩 Text Field Transformer for Anki

Transform your Anki note fields easily — lowercase, uppercase, title case, trim, or even custom Python lambdas.

## 🚀 Features
- Apply transformations to selected notes or all notes  
- Built-in types: `lower`, `upper`, `capitalize`, `title`, `strip`, `custom`  
- Custom Python lambda support (e.g. `lambda x: x[::-1]`)  
- Integrated in:
  - **Browser → Edit → Transform Field...**
  - **Tools → Transform Fields (All Notes)**  

## 🧠 Usage
1. Open Anki Browser and select notes  
2. Go to **Edit → Transform Field...**  
3. Choose field + transformation type  
4. (Optional) Add custom lambda  
5. Click **Apply Transformation**

## 🧰 Debug
View logs in Anki console (`Ctrl + Shift + ;`):
[Info] Loading note fields...
[Success] Transformation applied to 5 note(s).
[Error] Custom function failed: ...

## ⚠️ Notes
- Always back up your collection before bulk edits  
- Test custom lambdas carefully  