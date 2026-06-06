# Nook

A minimal todo list that lives on your screen. Press a hotkey and it appears. Press it again and it's gone.

I built this for myself — I wanted something to keep track of my tasks without opening another app, switching tabs, or dealing with features I'd never use. If you want the same thing, here's how to get it.

---

## What it does

- Press `Ctrl+Shift+Space` to show or hide Nook
- Create named categories and add tasks under them
- Check off tasks, clear completed ones, edit inline
- Customize accent and background color
- Sits in your system tray when hidden
- Saves everything locally to a JSON file — no accounts, no cloud

---

## Install

### Windows

Download `Nook.exe` from the [latest release](https://github.com/virajapalleti/Nook-personal-productivity-hideout/releases) and run it. Nothing else needed.

To have it start automatically, press `Win+R`, type `shell:startup`, and drop `Nook.exe` in that folder.

---

### Linux / Run from source (Windows or Linux)

You'll need Python 3.10 or higher.

**1. Clone the repo**

```bash
git clone https://github.com/virajapalleti/Nook-personal-productivity-hideout
cd Nook-personal-productivity-hideout
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Run**

```bash
python main.py
```

On Linux, the `keyboard` library needs elevated permissions for global hotkeys. Either run with `sudo`, or add yourself to the `input` group (recommended):

```bash
sudo usermod -aG input $USER
```

Then log out and back in.

---

### Build a binary on Linux (optional)

If you want a standalone executable on Linux instead of running from source:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name Nook main.py
```

The binary will be at `dist/Nook`.

---

## Requirements

```
PyQt6
keyboard
```

---

## What's next

I'm switching to Linux soon, so proper native Linux support with a packaged binary is on the list.

Also want to add a small pixel art creature that sits on the edge of Nook and blinks at you. No purpose. Just company :)
