# Viewing Diagrams in Cursor

Since Cursor is based on VS Code, you have several options to view the Mermaid diagrams.

## Option 1: HTML Viewer (Recommended - Easiest!)

**No setup needed!**

1. In Cursor, open the file: `ARCHITECTURE_DIAGRAMS_VIEWER.html`
2. Right-click on the file → **"Open With"** → **"Open in Browser"**
   - Or press `Cmd/Ctrl + Shift + P` → type "Open in Browser"
3. All diagrams will render automatically in your default browser

**This is the fastest way - no extensions needed!**

---

## Option 2: Cursor/VS Code Extension

### Install Mermaid Preview Extension:

1. **Open Extensions in Cursor:**
   - Press `Cmd/Ctrl + Shift + X`
   - Or click the Extensions icon in the sidebar

2. **Search and Install:**
   - Search for: `"Markdown Preview Mermaid Support"`
   - Author: **bierner** (Matt Bierner)
   - Click **Install**

3. **View Diagrams:**
   - Open `ARCHITECTURE_DIAGRAMS.md`
   - Press `Cmd/Ctrl + Shift + V` to open Markdown preview
   - Or right-click → **"Open Preview"**
   - Diagrams will render in the preview pane

### Alternative Extension:

- **Mermaid Editor** by tomoyukim
  - Provides a dedicated Mermaid editor with live preview
  - Search: `"Mermaid Editor"`

---

## Option 3: Use Cursor's Built-in Preview

1. Open `ARCHITECTURE_DIAGRAMS.md`
2. Press `Cmd/Ctrl + Shift + V` (or `Cmd/Ctrl + K V` for side-by-side)
3. If Mermaid extension is installed, diagrams will render
4. If not, install the extension from Option 2

---

## Option 4: Command Palette Shortcuts

### Quick Commands:

1. `Cmd/Ctrl + Shift + P` (Open Command Palette)
2. Type one of these:
   - `Markdown: Open Preview` - View markdown with diagrams
   - `Markdown: Open Preview to the Side` - Side-by-side view

---

## Recommended Workflow

### For Quick Viewing:
1. **Use the HTML file** (`ARCHITECTURE_DIAGRAMS_VIEWER.html`)
   - Right-click → Open in Browser
   - Best visual experience, no setup

### For Editing/Development:
1. **Install Mermaid extension** (Option 2)
2. **Open the markdown file** in Cursor
3. **Use preview** (`Cmd/Ctrl + Shift + V`)
4. Edit and see changes in real-time

---

## Troubleshooting

### Extension not working?
- Make sure you installed: `bierner.markdown-mermaid`
- Reload Cursor: `Cmd/Ctrl + Shift + P` → "Developer: Reload Window"
- Check if extension is enabled in Extensions panel

### Diagrams not rendering?
- Verify the extension is installed and enabled
- Try the HTML viewer instead (always works)
- Check that the Mermaid syntax is correct in the markdown file

### Preview not showing?
- Make sure you're in a `.md` file
- Try `Cmd/Ctrl + K V` for side-by-side preview
- Check Cursor's Markdown preview settings

---

## Quick Test

To verify everything works:

1. **Test HTML Viewer:**
   - Open `ARCHITECTURE_DIAGRAMS_VIEWER.html`
   - Right-click → Open in Browser
   - You should see all diagrams rendered

2. **Test Extension:**
   - Install Mermaid extension
   - Open `ARCHITECTURE_DIAGRAMS.md`
   - Press `Cmd/Ctrl + Shift + V`
   - You should see diagrams in the preview

---

## Pro Tips

- **Split View:** Use `Cmd/Ctrl + \` to split editor, then preview in second pane
- **Live Editing:** With extension, edit markdown and see diagram updates in real-time
- **Export:** Use the HTML viewer, then use browser's print/save feature to export as PDF

---

**TL;DR:** Start with the HTML file (right-click → Open in Browser). It's the easiest and works immediately!

