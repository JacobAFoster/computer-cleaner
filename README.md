# Duplicate File Finder

A small, offline desktop app for finding files that share a name across a
folder tree, comparing their sizes and contents, and moving the copies you
choose into a recoverable trash folder.

Built with Python and Tkinter; no third-party packages, no network access,
nothing leaves your machine.

---

## Features

- **Name-based grouping** — files with the same name (case-insensitive) are
  grouped together, so you see every copy at once.
- **Size comparison per group** — the group header shows the copy count and
  the min–max size range, and individual rows are labelled `largest` /
  `smallest` when they differ.
- **Per-file metadata** — every copy shows its relative path, exact size, and
  modified date.
- **Content verification** — one click hashes each file with SHA-256 and
  labels groups as *identical content* (green), *different content* (red), or
  *partial* (some files over the hash size limit or unreadable).
- **Selective removal** — tick the copies you want gone (click the checkbox
  column or press `Space` on a selected row), then move them to a trash
  folder in one step. Everything is recoverable.
- **Batch helpers** — right-click a group to *Keep newest / oldest / largest /
  smallest and check the rest*, or to check/uncheck the whole group.
- **Adjustable columns** — drag column separators to resize; widths are
  remembered. Double-click a header to auto-fit it to the widest cell.
- **Safe deletion** — files are moved, not deleted; a warning fires if you're
  about to empty an entire group; selected-but-not-deleted files trigger a
  confirm prompt on quit.

---

## Requirements

- Python 3.8 or newer
- Tkinter (bundled with the official installers on Windows and macOS; on
  Linux you may need `python3-tk`)

No third-party packages.

---

## Running

```bash
python main.py
