# PyCleaner

> A cross-platform duplicate finder and Windows maintenance toolkit — with a
> quarantine-first safety model, a plugin architecture for adding new cleaners,
> and a headless CLI for testing every cleaner without touching a real system.

**16 cleaners. Zero silent deletes. Every destructive action reversible from
the Trash tab.**

---

## Table of contents

- [Why another cleaner?](#why-another-cleaner)
- [Safety model](#safety-model)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [The interface](#the-interface)
- [Cleaners reference](#cleaners-reference)
  - [Duplicate files](#duplicate-files)
  - [Empty folders](#empty-folders)
  - [Empty files](#empty-files)
  - [Junk by name](#junk-by-name)
  - [Old files](#old-files)
  - [Large files](#large-files)
  - [Temp & cache](#temp--cache)
  - [Downloads triage](#downloads-triage)
  - [Similar images](#similar-images)
  - [Startup apps](#startup-apps)
  - [Programs](#programs)
  - [Scheduled tasks](#scheduled-tasks)
  - [Services](#services)
  - [Store apps](#store-apps)
  - [Broken shortcuts](#broken-shortcuts)
  - [Recycle bin](#recycle-bin)
- [Command-line usage](#command-line-usage)
- [The trash / quarantine](#the-trash--quarantine)
- [Configuration files](#configuration-files)
- [Architecture](#architecture)
- [Extending PyCleaner](#extending-pycleaner)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Known limitations & non-goals](#known-limitations--non-goals)
- [Changelog](#changelog)
- [License](#license)

---

## Why another cleaner?

Because most "PC cleaners" are snake oil. They warn about "1,247 problems"
that turn out to be cached thumbnails, they delete things silently, and
their "optimise" buttons trade real stability for a placebo.

PyCleaner takes the opposite stance:

- **Nothing is deleted.** Files move to a real quarantine folder with a
  JSON manifest. Restore is one click. Auto-purge after 30 days (configurable).
- **Nothing is silent.** Every action shows a confirmation dialog with the
  count, total size, and destination.
- **Nothing is guessed.** The Windows modules use the same mechanisms
  Task Manager uses (`StartupApproved`), the same allowlist discipline
  Microsoft's own "Apps & Features" uses, and launch vendor uninstallers
  rather than calling silent `/S` flags.
- **Nothing is a black box.** Every cleaner is ~60–150 lines of Python.
  Read them, audit them, extend them.
- **Registry is off-limits.** No "registry cleaner." Ever.

If you want a "BOOST PC 400%" button, this isn't for you. If you want a tool
you can hand to your parents without losing data, it is.

---

## Safety model

Three layers, applied to every action:

### 1. Quarantine, not delete

C:\Users\you\Downloads\report.pdf
│
└──moved──> %APPDATA%\PyCleaner\trash\20240115-093217\report.pdf
text


Alongside each stamp folder, a `manifest.json` records the original absolute
path, size, kind (file/dir), and which cleaner touched it. The Trash tab
lists every stamp with **Restore**, **Purge**, and a configurable
**auto-purge older than N days**.

Restore moves files back to their original path; if the path is occupied,
the conflict is reported and the item stays in quarantine.

### 2. Protected paths

Every cleaner consults `is_protected(path, root)` before returning an item.
It refuses to touch:

- Anything under `C:\Windows`, `C:\Program Files`, `C:\Program Files (x86)`,
  `C:\ProgramData\Microsoft`, `C:\Users\Default`, `C:\$Recycle.Bin`
- Anything outside the selected scan root (when one is chosen)
- The app's own config and quarantine directories

A warning dialog lets you override the outside-root check, but never the
system-path check.

### 3. Dry run

A per-tab checkbox runs the entire workflow — confirmations, progress,
result dialog — without touching a single byte. The dialog text says
"(Dry run — nothing will be changed.)" and the summary reports
`Would apply: N item(s)`. Use this before any mass deletion.

### Plus

- **Per-tab threading.** Scans and hashes run on a worker thread with
  progress and a Cancel button. The UI never hangs.
- **Every action logged.** `%APPDATA%\PyCleaner\actions.log` — timestamp,
  cleaner id, path, result.
- **Curated allowlists.** Store apps and startup entries are gated on
  explicit lists, not regex guesses.

---

## Features

| | Feature | Platform | Requires |
|---|---|---|---|
| 🗂 | **Duplicate files** — content (size+SHA-256) or same-name matching | Any | — |
| 📁 | **Empty folders** — iterative nested-empty detection | Any | — |
| 📄 | **Empty files** — with skip-list for `.gitkeep`, `.nomedia` | Any | — |
| 🧹 | **Junk by name** — `Thumbs.db`, `.DS_Store`, `*.tmp`, Office locks | Any | — |
| ⏰ | **Old files** — by modification age | Any | — |
| 🐘 | **Large files** — by size threshold | Any | — |
| 🌡 | **Temp & cache** — OS temp + user cache | Any | — |
| 📥 | **Downloads triage** — group `~/Downloads` by type + age | Any | — |
| 🖼 | **Similar images** — perceptual hash (dHash) + BK-tree clustering | Any | `Pillow`, `imagehash` |
| 🚀 | **Startup apps** — reversible enable/disable via `StartupApproved` | Windows | — |
| 📦 | **Programs** — enumerate uninstallers, launch vendor GUI | Windows | — |
| 🗓 | **Scheduled tasks** — read-only viewer | Windows | — |
| ⚙ | **Services** — read-only viewer | Windows | — |
| 🏪 | **Store apps** — curated AppX removal + provisioned removal | Windows | Admin for deprovision |
| 🔗 | **Broken shortcuts** — `.lnk` files with missing targets | Windows | — |
| 🗑 | **Recycle bin** — view + empty | Windows | `winshell` |

Total: 16 cleaners. 9 cross-platform, 7 Windows-only.

---

## Requirements

- **Python 3.10+** (uses `X | Y` type unions, `pathlib.Path.is_relative_to`)
- **Tkinter** (ships with CPython on Windows and macOS; `sudo apt install
  python3-tk` on Debian/Ubuntu)
- **PowerShell 3+** for the Windows apps module (built into Windows 8+)

### Optional dependencies

Only required if you want the corresponding cleaner. Missing deps cause that
tab to be silently omitted — the Settings tab tells you what to install.

```bash
pip install Pillow imagehash   # Similar images
pip install winshell           # Recycle bin

Or all at once:
bash

pip install "PyCleaner[optional]"   # if published
# or
pip install Pillow imagehash winshell

Installation
From source (recommended)
bash

git clone https://github.com/you/pycleaner.git
cd pycleaner

# Optional: virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # macOS / Linux

# Optional dependencies
pip install Pillow imagehash winshell

python cleaner.py

As a single file

cleaner.py is self-contained. Copy it anywhere and run it. First launch
creates %APPDATA%\PyCleaner (Windows) or ~/.config/PyCleaner (POSIX).
As a frozen executable (Windows)
bash

pip install pyinstaller
pyinstaller --onefile --windowed --name PyCleaner cleaner.py

The resulting dist/PyCleaner.exe is admin-aware; the "Relaunch as admin"
button in the Store apps tab uses ShellExecuteW runas and works from a
frozen binary.
Quick start

    Launch. python cleaner.py — the notebook opens on Duplicate files.

    Pick a folder. Click Choose folder… and select the tree you want to
    examine. Start small — a Downloads or Pictures folder — not C:\.

    Scan. Click Scan. Progress shows in the status bar; Cancel stops
    cleanly (the worker thread returns early on the next file).

    Review. Groups are shown as parent rows with individual files nested
    beneath. Click the checkbox column (☐ / ☑) to toggle. Space toggles
    the selection. Right-click a parent row for Keep newest — check others
    and friends.

    Delete. Delete checked… confirms count, size, and destination. Files
    move to quarantine, not oblivion.

    Restore (if you need to). Switch to the Trash tab. Select the
    stamp, click Restore selected. Files return to their original paths.

The interface
text

┌───────────────────────────────────────────────────────────────┐
│ Duplicate files │ Empty folders │ Empty files │ Junk │ … │ Trash │ Settings │
├───────────────────────────────────────────────────────────────┤
│ [Choose folder…] C:\Users\you\Downloads                       │
│ ☑ Recursive  ☐ Follow symlinks  ☐ Include hidden  ☐ Dry run  [Scan] [Cancel] │
│ Scanning… 1,247 files                                         │
├───────────────────────────────────────────────────────────────┤
│          │ Name / Path                │ Size   │ Modified │ Note   │
│ 📁 2×     │ report.docx                │ 2 copies · 1.2 MB each      │
│   ☑      │ 2024/report.docx           │ 1.2 MB │ 2024-01-15 09:12 │   │
│   ☐      │ backup/report.docx         │ 1.2 MB │ 2024-01-14 22:01 │   │
│   (preview pane on the right when the cleaner supports it)        │
├───────────────────────────────────────────────────────────────┤
│ [Uncheck all] [Check all] [Delete checked…] [Reset columns]       │
│                          3 groups · 2 selected · 2.4 MB to free   │
└───────────────────────────────────────────────────────────────┘

Column resizing is persisted per cleaner in columns_<id>.json. Double-click
a column header to auto-fit. Reset columns restores defaults.

The #0 column is the checkbox — clicking anywhere else on the row does
nothing (avoids accidental toggles when selecting text).

Right-click menu (dedupe only): Keep newest / oldest / largest / smallest
— check others, plus Uncheck group and Check whole group.

Preview pane (Similar images): appears on the right when the cleaner
provides one. Select a row to load a thumbnail; images over 50 MB show
(image too large to preview) instead of stalling.
Cleaners reference
Duplicate files

id dedupe · platform any · default mode content

Finds files with identical bytes. Two modes:
Mode	What it does	When to use
content (default)	Bucket by size, then SHA-256 within each bucket	Catches same-bytes/different-name duplicates; the common case
name	Group by filename (case-insensitive), no hashing	Fast, when you trust the naming

Content mode is fast because different-sized files can't be identical — most
files are eliminated before the first byte is read.

Files larger than Max file size to hash (MB) (default 200) are grouped
under unverified:<size> with a too large to hash note. Raise the limit in
Settings, or use the name mode.

Verify content re-hashes files whose mtime changed since the last hash.
Normal scans already hash everything, so this is mostly a no-op — use it
when you've scanned with a low limit and later want to verify large files.

Settings: dedupe_mode, hash_limit_mb.
Empty folders

id empty_folders · platform any · auto-checks

Directories with no files or subdirectories, after iteratively removing
nested empties. Detects chains like a/b/c/d where d is empty — all four
are reported.

Exclusions: .dedupe_trash, protected system paths, hidden directories
(unless Include hidden is on).

Restore: mkdir -p on the original path. Fails safely if the parent
doesn't exist yet (restore in reverse depth order; the manifest is FIFO so
restoring a whole stamp works correctly).
Empty files

id empty_files · platform any · auto-checks

Files with size == 0. Skips .gitkeep, .nomedia, .keep, .placeholder,
.gitignore, and *.lock.
Junk by name

id junk · platform any · auto-checks

Files matching a pattern list:
text

Thumbs.db  desktop.ini  .DS_Store  .Spotlight-V100  ehthumbs.db
~$*  *.tmp  *.bak  *.crdownload  *.part  *.partial  *.download

Editable in Settings → Junk patterns. Empty text area = use the defaults.
Any non-empty list replaces them.
Old files

id old · platform any

Files whose mtime is older than N days (default 365). Sorted by size
descending so the biggest wins appear first. Each row shows its age in days.

Option: min_days.
Large files

id large · platform any

Files over N MB (default 500). Sorted by size descending. A flat list —
no grouping, no duplicate detection.

Option: min_mb.
Temp & cache

id temp · platform any

Files in:

    Windows: %TEMP% and %LOCALAPPDATA%\Temp

    POSIX: tempfile.gettempdir() (usually /tmp) and ~/.cache

In-use files will fail to move (Windows lock) or disappear from under the
scan (POSIX unlink); each is reported individually rather than aborting the
run. This is expected — close apps before scanning if you want a clean result.
Downloads triage

id downloads · platform any

Groups ~/Downloads (non-recursively by default) into:
Category	Extensions
Installer	.exe .msi .dmg .pkg .deb .rpm .appimage
Archive	.zip .rar .7z .tar .gz .bz2 .xz .tgz
Document	.pdf .doc .docx .xls .xlsx .ppt .pptx .txt .md .rtf .odt
Image	.jpg .jpeg .png .gif .bmp .webp .tif .tiff .heic .svg
Media	.mp3 .mp4 .mov .avi .mkv .wav .flac .m4a .m4v .webm
Code	.py .js .ts .html .css .json .xml .yaml .yml .sh .bat .ps1 .rs .go
Other	everything else

Sorted by category then age. Nothing is auto-checked — this is a
review tool, not a bulk-delete tool.

Option: include_hidden.
Similar images

id similar_images · platform any · deps Pillow, imagehash

Finds images that look alike but aren't byte-identical (resized, re-encoded,
watermarked, or cropped). Uses dHash (64-bit perceptual hash) with a configurable
Hamming-distance threshold (default 8, ~87 % visual similarity).

Images are clustered with a BK-tree: each new image joins the first existing
cluster within threshold. This produces small, tight groups — good for visual
review — rather than mathematically ideal connected components.

A preview pane on the right shows a thumbnail of the selected image.
Select multiple rows or use Check all — but review each one visually. This
is the one cleaner where blind bulk deletion is genuinely dangerous.

Options: threshold (0–20; lower = stricter), min_kb (skip tiny images).
Startup apps

id startup · platform Windows

Enumerates four sources:

    HKCU\Software\Microsoft\Windows\CurrentVersion\Run

    HKLM\Software\Microsoft\Windows\CurrentVersion\Run (64-bit view)

    HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run (32-bit)

    Startup folders: %APPDATA%\…\Startup and %ProgramData%\…\Startup

Actions: Disable checked / Enable checked.

The mechanism is the same one Task Manager uses: writes a 12-byte REG_BINARY
under HKCU\…\Explorer\StartupApproved\{Run|Run32|StartupFolder}. Byte 0 of
0x02 = enabled, 0x03 = disabled. The Run value is never deleted — you
can always toggle it back. No admin required, even for HKLM entries, because
StartupApproved is per-user.

NOT a delete operation. After applying, rows stay in the tree with the
updated state. Click Scan to refresh if you want.
Programs

id programs · platform Windows

Enumerates installed programs from:

    HKLM\…\Uninstall (64-bit)

    HKLM\WOW6432Node\…\Uninstall (32-bit)

    HKCU\…\Uninstall (per-user)

Filters out entries with SystemComponent=1 (OS components) or ParentKeyName
(updates/patches), and entries without a DisplayName.

Action: Uninstall checked launches the vendor's registered
UninstallString via Popen. The vendor's own UI runs. We never call
QuietUninstallString or add /S. Silent uninstalls are how people lose
data.

The tree is not refreshed automatically — click Scan after the uninstaller
finishes. This is intentional: waiting synchronously would hang the app for
minutes, and refreshing mid-uninstall would show stale data.
Scheduled tasks

id tasks · platform Windows · read-only

Lists scheduled tasks via PowerShell Get-ScheduledTask. Filters out
\Microsoft\Windows\* by default; toggle Show Microsoft tasks to include
them.

Viewer only. Disabling services and tasks is a support nightmare and out
of scope. Use taskschd.msc or services.msc for that.
Services

id services · platform Windows · read-only

Lists services via PowerShell Get-Service. Shows name, status, start type,
and display name.

Viewer only. Use services.msc to change service state.
Store apps

id appx · platform Windows · admin recommended (required for deprovision)

Removes AppX packages (Store apps). Gated on a curated allowlist — a
package that isn't in the list never appears in the tree.

The default allowlist is risk-tiered:

    low (auto-checked) — Bing apps, Solitaire, Zune, Skype, Feedback Hub,
    Candy Crush, Disney apps, Spotify, etc.

    medium (amber text) — Calculator, Photos, Camera, Xbox app, Snip &
    Sketch, Edge.

    high (red text) — Store itself, DesktopAppInstaller (winget), HEIF /
    VP9 / WebP codecs. The confirmation dialog counts them and warns.

Two actions, two scopes:
Action	PowerShell	Admin?	Reversible?
Remove checked	Remove-AppxPackage -Package …	No	Yes — reinstall from Store
Remove provisioned	Remove-AppxProvisionedPackage -Online	Yes	No — reinstalls for new users only via reinstall

Removing a package for your account works without admin. Deprovisioning (so
new users don't get it pre-installed) requires admin. The banner appears
automatically; click Relaunch as admin to restart elevated.

Customizing the allowlist: copy APPX_ALLOWLIST_DEFAULT from the source
into %APPDATA%\PyCleaner\appx_allowlist.json and edit. Format:
json

[
  {"pattern": "Microsoft.BingNews", "risk": "low", "label": "Bing News"},
  {"pattern": "king.com.*", "risk": "low", "label": "King games"},
  {"pattern": "Microsoft.WindowsStore", "risk": "high", "label": "Store"}
]

Patterns match against Name or PackageFamilyName via fnmatch.

Never remove framework packages (Microsoft.VCLibs, Microsoft.NET.Native.*,
Microsoft.WindowsAppRuntime.*) or shell dependencies. They're not in the
allowlist, and adding them will break Windows in confusing ways.
Broken shortcuts

id broken_shortcuts · platform Windows

Finds .lnk files whose target no longer exists. Resolves targets via
PowerShell WScript.Shell — one batch call for the whole scan (a temp file
lists the shortcuts, PowerShell writes path\ttarget back).

Filters out:

    URL shortcuts (http:, https:, steam://, uplay://)

    Settings links (ms-, shell:)

    MSI-advertised targets ({GUID} form)

Expands environment variables before checking. Reports missing targets in the
Note column.
Recycle bin

id recycle · platform Windows · deps winshell

Lists the contents of the Windows Recycle Bin (original path, size, deletion
time).

Action: Empty Recycle Bin… — a single bulk action that empties the
entire bin. Windows' recycle-bin API doesn't support per-item deletion from
third-party code, so this is all-or-nothing.

Individual restore stays in Explorer (right-click → Restore). The in-app
Trash tab handles PyCleaner's own quarantine, not the Windows Recycle
Bin — they're different folders.
Command-line usage

The GUI is the primary interface, but every cleaner is headless-testable. This
is how you validate a cleaner on a fixture directory before running it against
your real system.
bash

# List all cleaners with availability and platform
python cleaner.py --list

# Scan without deleting (always the safe option)
python cleaner.py --scan C:\Users\you\Downloads --cleaner dedupe
python cleaner.py --scan C:\Users\you\Downloads --cleaner junk --json
python cleaner.py --scan C:\Users\you\Desktop   --cleaner broken_shortcuts
python cleaner.py --scan .                       --cleaner recycle
python cleaner.py --scan .                       --cleaner downloads
python cleaner.py --scan ~/Pictures              --cleaner similar_images --json

--scan never deletes, never touches the quarantine manifest, never opens
a window. --json produces structured output (includes data with the
cleaner-specific payload) suitable for jq / pytest assertions.
Example: JSON output
json

[
  {
    "key": "C:\\Users\\you\\Downloads\\Thumbs.db",
    "label": "Thumbs.db",
    "path": "C:\\Users\\you\\Downloads\\Thumbs.db",
    "size": 10240,
    "note": "matches Thumbs.db",
    "data": {}
  }
]

Fixture-based testing
text

tests/
├── fixtures/
│   ├── dedupe/
│   │   ├── a.txt            # content "hello"
│   │   ├── b.txt            # content "hello"  → duplicate of a.txt
│   │   ├── c.txt            # content "world"
│   │   └── nested/a.txt     # content "hello"  → duplicate of a.txt
│   ├── junk/
│   │   ├── Thumbs.db
│   │   └── keep.txt
│   └── empty/
│       └── a/b/c/           # nested empties
└── test_cleaners.py

python

def test_dedupe_finds_expected_duplicates():
    result = subprocess.run(
        ["python", "cleaner.py", "--scan", "tests/fixtures/dedupe",
         "--cleaner", "dedupe", "--json"],
        capture_output=True, text=True,
    )
    items = json.loads(result.stdout)
    paths = sorted(Path(it["path"]).name for it in items)
    assert paths == ["a.txt", "a.txt", "b.txt"]

The trash / quarantine

Location: %APPDATA%\PyCleaner\trash (Windows) or ~/.config/PyCleaner/trash
(POSIX). App-wide, not per-scan-root — one trash folder regardless of how
many different folders you scanned.
Structure
text

trash/
└── 20240115-093217/           # stamp: YYYYMMDD-HHMMSS
    ├── manifest.json
    ├── report.pdf
    └── Thumbs-1.db            # "Thumbs.db" already existed in this stamp

Manifest
json

{
  "created": 1704100000.123,
  "items": [
    {
      "original": "C:/Users/you/Downloads/report.pdf",
      "trashed": "report.pdf",
      "size": 1048576,
      "kind": "file",
      "cleaner": "dedupe"
    },
    {
      "original": "C:/Users/you/Downloads/empty-dir",
      "trashed": "",
      "size": 0,
      "kind": "dir",
      "cleaner": "empty_folders"
    }
  ]
}

Restoring

Select one or more stamps in the Trash tab, click Restore selected.

    Each file is moved back to original. If it exists, that item is reported
    as a conflict and stays in quarantine — nothing is overwritten.

    Directories are recreated with mkdir -p.

    If the stamp folder is empty afterward, it's deleted.

Retention

The default retention is 30 days. Purge older than Nd in the Trash tab
runs purge_older_than(days) on demand. There's no background task —
you must click the button. If you want automatic purging, add a startup hook
that calls Quarantine().purge_older_than(settings["trash_retention_days"]).
Manual inspection

Open folder opens the trash directory in Explorer / Finder / xdg-open.
You can inspect files, copy them out, or delete them yourself — the app
tolerates orphaned folders (it just skips them on the next stamps() call if
manifest.json is missing).
Configuration files

All in %APPDATA%\PyCleaner (Windows) or ~/.config/PyCleaner (POSIX).
File	Purpose
settings.json	Dedupe mode, hash limit, retention days, junk patterns
columns.json	Legacy column widths (fallback for dedupe)
columns_<id>.json	Per-cleaner column widths
appx_allowlist.json	Optional override for the AppX allowlist
actions.log	Append-only action audit trail
trash/	Quarantine with per-stamp manifests
settings.json
json

{
  "hash_limit_mb": 200,
  "dedupe_mode": "content",
  "trash_retention_days": 30,
  "junk_patterns": null
}

junk_patterns: null means "use cleaner defaults". Any non-empty list
replaces the defaults.
actions.log
text

2024-01-15 09:32:17 stash C:\Users\you\Downloads\report.pdf -> ...\report.pdf (dedupe)
2024-01-15 09:32:18 appx remove Microsoft.BingNews_4.51.1291.0_x64__8wekyb3d8bbwe
2024-01-15 09:32:19 uninstall-launch Foo App: "C:\Program Files\Foo\uninstall.exe" /gui
2024-01-15 09:33:05 restore 20240115-093217\report.pdf -> C:\Users\you\Downloads\report.pdf
2024-01-15 09:34:12 purge 20240115-093217

Useful for debugging "did I delete this?" and for auditing bulk operations
across a long-running session.
Architecture

Single file, ~3,000 lines, organized into clearly-commented sections. Splitting
into modules is a mechanical change — the sections already don't cross-import.
text

cleaner.py
├── 1.  Config & constants
├── 2.  Helpers (files, paths, registry, PowerShell)
├── 3.  Data model (Item, Cleaner)
├── 4.  File cleaners (dedupe, empty*, junk, old, large, temp)
├── 5.  Windows cleaners (startup, programs, tasks, services, appx)
├── 6.  Phase-5 cleaners (downloads, similar_images, shortcuts, recycle)
├── 7.  Cleaner registry (dict of id → class)
├── 8.  Quarantine
├── 9.  Settings (load/save)
├── 10. CleanerTab (the generic Tk tab)
├── 11. CleanerApp (the notebook)
└── 12. main() — argparse + headless CLI

The plugin contract

Every cleaner subclasses Cleaner and either overrides _scan_impl (returning
a list of Item) or sets readonly = True and lists items some other way.
Actions dispatch through apply_action(item, action, quarantine); bulk
actions (empty recycle bin) go through apply_bulk(action, items, quarantine).

Item is the only shared data type between the cleaner and the tab:
python

@dataclass
class Item:
    key: str                    # grouping key or unique identifier
    label: str                  # user-visible name
    path: Path | None           # file/folder, or None for registry/package items
    size: int = 0
    mtime: float | None = None
    note: str = ""              # free-form column text
    checked: bool = False
    iid: str | None = None      # set by the tab on insert
    data: dict = field(default_factory=dict)  # cleaner-specific payload

The data dict is where per-cleaner state lives — hash values, publisher,
uninstall strings, package names, enabled flags. The tab never inspects it;
only the cleaner's own render and apply methods do.
The generic tab

CleanerTab is instantiated once per cleaner class. It handles:

    Folder picker (if requires_root = True)

    Options rendering (from option_specs)

    Threaded scan with progress and cancel

    Tree rendering (flat or grouped by group_by)

    Checkbox toggling, Check/Uncheck all, keep-by, right-click menu

    Column width persistence (per-cleaner)

    Preview pane (if preview_pane() returns a class)

    Action dispatch (_run_action → apply_action or apply_bulk)

    Result dialogs

Adding a new cleaner means writing the subclass; zero changes to the tab.
Threading model

Scans run on a worker thread communicating via queue.Queue. The Tk main
thread polls the queue every 80 ms (self.after(80, poll)) — no
update_idletasks() hacks, no blocking calls on the UI thread. Cancel is a
threading.Event the worker checks between files.

Actions (apply, restore, purge) run synchronously on the UI thread. They
touch few files and are fast; a threaded apply loop would be over-engineering
and would complicate the result dialog. If a future action becomes slow, wrap
it in _run_thread.
Extending PyCleaner

Adding a cleaner is a 3-step process. Here's a complete example — stale
lockfiles (files named *.lock older than 7 days):
python

class StaleLockfilesCleaner(Cleaner):
    id = "stale_locks"
    name = "Stale lockfiles"
    description = "*.lock files not modified in 7 days."
    group_by = "none"
    option_specs = [
        {"key": "min_days", "label": "Older than (days)",
         "kind": "int", "default": 7, "min": 1, "max": 365},
    ]

    def _scan_impl(self, root, opts, progress_cb, cancel):
        days = int(opts.get("min_days", 7))
        cutoff = time.time() - days * 86400
        results = []
        for p, size, mtime in self._walk(root, opts, self._errors):
            if cancel.is_set():
                break
            if p.suffix.lower() == ".lock" and mtime < cutoff:
                age = int((time.time() - mtime) / 86400)
                results.append(Item(
                    key=str(p), label=p.name, path=p, size=size,
                    mtime=mtime, note=f"{age}d old"))
        return results

Then register it:
python

CLEANERS: dict[str, type[Cleaner]] = {
    c.id: c for c in (
        DedupeCleaner, EmptyFoldersCleaner, EmptyFilesCleaner,
        JunkByNameCleaner, OldFilesCleaner, LargeFilesCleaner,
        TempCacheCleaner, DownloadsCleaner,
        StartupCleaner, ProgramsCleaner, ScheduledTasksCleaner,
        ServicesCleaner, AppxCleaner,
        SimilarImagesCleaner, BrokenShortcutsCleaner, RecycleBinCleaner,
        StaleLockfilesCleaner,   # <── add here
    )
}

That's it. The tab, folder picker, threading, column persistence, delete
flow, trash integration, CLI --scan, and --list all work for free.
Overriding defaults
Attribute	Default	Override when
requires_root	True	Cleaner scans fixed paths (temp dir, recycle bin)
readonly	False	Viewer only (no checkboxes, no action buttons)
auto_check	False	Everything should start selected (safe bulk cleaners)
group_by	"key"	Flat list — set to "none"
apply_removes_items	True	Rows should stay after applying (startup, programs)
delete_verb / delete_noun	Delete / file(s)	Different language ("Remove", "folder(s)")
platforms	None (any)	Windows-only: ("win32",)
optional_deps	()	Requires pip packages: ("PIL", "imagehash")
needs_admin	False	Tab won't work at all without admin
admin_recommended	False	Some actions work better with admin (yellow banner)
columns / column_headers	("path","size","modified","info")	Different column schema
option_specs	[]	Per-tab options (spinbox, checkbox, entry)
has_verify	False	Show "Verify content" button (dedupe only)
has_keep_by	False	Right-click "Keep newest" menu
preview_pane()	None	Return a class: _ImagePreview style
Custom actions

For cleaners with non-delete actions (startup, programs, appx, recycle):
python

def action_buttons(self):
    return [
        {"label": "Disable checked", "action": "disable"},
        {"label": "Enable checked",  "action": "enable"},
        {"label": "Empty all",       "action": "empty_all", "bulk": True},
    ]

def apply_action(self, item, action, quarantine):
    if action == "disable":
        return self._set_enabled(item, False)
    if action == "enable":
        return self._set_enabled(item, True)
    return super().apply_action(item, action, quarantine)

def apply_bulk(self, action, items, quarantine):
    if action == "empty_all":
        # bulk operation
        return count, errors
    return super().apply_bulk(action, items, quarantine)

confirm_title(action) and confirm_text(action, items) let you customize
the confirmation dialog per action.
Troubleshooting

"Some optional cleaners are missing."
Install the deps listed on the Settings tab: pip install Pillow imagehash winshell. Or ignore it — those tabs simply won't appear.

"PowerShell not found" (Windows).
PowerShell 3+ is built into Windows 8+. If you're on Windows 7 or a stripped
down install, install PowerShell from Microsoft. The AppX, tasks, services,
and shortcut cleaners depend on it; the file cleaners don't.

The app hangs on scan of a huge folder.
Cancel is available; use it. For multi-TB scans, run several targeted scans
rather than one root. The dedupe content mode is much faster than the name
mode for large trees because it only hashes files that share a size.

"Cannot scan <path> (protected system path)."
is_protected() refuses paths under C:\Windows, C:\Program Files,
C:\ProgramData\Microsoft, etc. This is intentional. If you genuinely need
to clean those paths, use Windows' own cleanmgr or a system-level tool.
PyCleaner is a user-data cleaner, not a system cleaner.

A file failed to move ("in use").
Windows locks open files; POSIX unlinks them (the app sees them gone from the
next scan, but the process holding the handle keeps reading from the inode).
Close the app that has the file open and re-scan, or use the Windows
Resource Monitor to find the lock holder.

Trash is growing, disk is full.
Settings → trash_retention_days doesn't auto-purge; click Purge older than
Nd in the Trash tab. Or click Purge selected on a specific stamp. Or open
the folder and delete it manually — the app tolerates missing manifests.

Store app removal said "not found".
The PackageFullName may have changed since the scan (Windows auto-updates
apps). Re-scan and try again. Deprovisioning matches on PackageName (without
the version suffix), which is more stable, but reinstalls can still move things.

The UI is tiny/huge on a high-DPI screen.
Tkinter doesn't scale automatically on Windows. Set the DPI awareness in
main() before creating CleanerApp():
python

if os.name == "nt":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

FAQ

Why is there no registry cleaner?
Registry "cleaners" produce no measurable performance gain and are one of the
top causes of Windows boot failures. The state-of-the-art answer from every
serious systems engineer is "don't." PyCleaner won't.

Why can't I disable services?
Because services have dependencies, sc config changes are sticky, and
disabling the wrong one requires Safe Mode to recover from. Use services.msc
with a guide — it's safer and more educational.

Why does the dedupe name mode exist if content mode is better?
Because content mode hashes files, which is slow on huge trees, and name mode
is ~50× faster on cold cache. Name mode is the right tool for "I copied my
whole photo library twice and want to see the pairs before I delete the
backup."

Can I run PyCleaner on a network share?
File cleaners yes, but slow (network round-trips for every stat). Windows
registry-based cleaners are local-machine only. The trash folder is local; the
files it stashes will be moved over the network to %APPDATA%, which may be
slow or fail on read-only shares.

Does removing a Store app break Windows?
For apps in the low risk tier, no — they're end-user apps with no shell
dependencies. For medium, you might notice a "missing" shortcut or two
that a user actively relied on. For high, yes — removing the Store itself,
winget's backend, or media codecs will break features. The confirmation dialog
warns you. Removing Store apps is not a decision to make on someone else's
machine without asking.

Can I script the app?
Not the GUI — it's Tkinter. But every cleaner's scan is scriptable via --scan --json, and apply/apply_bulk are public methods you can call from Python:
python

from cleaner import DedupeCleaner, Quarantine
c = DedupeCleaner()
items = c.scan(Path("/data"), {"recursive": True}, print, threading.Event())
q = Quarantine()
for it in items[:5]:
    ok, msg = c.apply(it, q)
    print(ok, msg)

How do I uninstall PyCleaner?
Delete cleaner.py. Delete %APPDATA%\PyCleaner (this also deletes the
quarantine — restore first if you want to keep anything). Nothing is written
to the registry, no services are installed, no PATH entries.
Known limitations & non-goals
Not implemented

    Disk-usage treemap — needs a canvas renderer and drill-down navigation.
    Would be a whole tab, not a cleaner. Different interaction model.

    Near-duplicate videos — perceptual hashing for video is genuinely hard
    (temporal alignment, resolution changes). Out of scope.

    Broken registry uninstall entries — safe to flag, dangerous to delete.
    Better as a "report" than a cleaner.

    Scheduled task / service modification — read-only by design.

Won't implement

    Registry cleaner — no measurable gain, brick risk.

    RAM optimiser — Windows manages memory fine.

    "Boost PC" buttons — same.

    Silent uninstalls — data loss waiting to happen.

    Cloud sync — this is a local tool.

Platform notes

    Windows-only cleaners are: startup, programs, tasks, services, appx,
    broken_shortcuts, recycle. The file-based cleaners work on macOS and Linux
    but haven't been as heavily tested there.

    macOS quarantine doesn't integrate with Finder's Trash — PyCleaner's
    quarantine is a separate folder. Use it, then Cmd+Delete from Finder if
    you want the real trash.

    Linux — _is_hidden uses dot-prefix, which is the correct convention.

Changelog
Phase 5 (current)

    Similar images cleaner with BK-tree clustering and a preview pane.

    Broken shortcuts cleaner — .lnk resolution via PowerShell, no COM dep.

    Recycle bin cleaner — read-only view + empty-all bulk action.

    Downloads triage — ~/Downloads grouped by extension category.

    Optional deps infrastructure — optional_deps attribute + --list output.

    Preview pane hook — preview_pane() on Cleaner, wired into CleanerTab.

    Bulk actions — apply_bulk() + "bulk": True button spec.

    group_sort_key() — cleaner-defined group ordering.

Phase 4

    Store apps cleaner with risk-tiered curated allowlist.

    admin_recommended flag (vs needs_admin) for softened banner.

    row_tag() hook — per-row colouring (risk tiers).

    confirm_text(action, items) signature (was n, size) for risk-counting.

    apply_bulk() groundwork for recycle bin.

Phase 3

    Startup apps cleaner — reversible via StartupApproved.

    Programs cleaner — launches vendor uninstallers.

    Scheduled tasks / Services — read-only viewers.

    Elevation infrastructure — is_admin(), relaunch_as_admin().

    action_buttons(), apply_action(), render_row() hooks.

    Per-action confirm_title / confirm_text.

Phase 2

    Empty folders, Empty files, Junk by name, Old files,
    Large files, Temp & cache cleaners.

    Generic CleanerTab — folder picker, options, threading, action dispatch.

    Per-cleaner column layouts (columns_<id>.json).

    option_specs for per-tab options.

    _walk() extracted as shared file-walking primitive.

    Headless CLI — --scan, --cleaner, --json.

Phase 1

    Plugin architecture (Cleaner, Item, CleanerTab).

    Quarantine with manifest, restore, purge, retention.

    Protected paths guard.

    Dry run mode.

    Threading for scan and hash with progress + cancel.

    %APPDATA% config (was: next to the script).

    Dedupe rebuilt on size→hash bucketing (was: name-only).

    actions.log audit trail.

    Trash tab. Settings tab.

License

MIT. Do whatever you want. No warranty — this tool deletes files
(well, moves them to quarantine). If you point it at C:\ and click "check
all" then "delete", the outcome is on you. The safety model exists to make
that unlikely; it doesn't make it impossible.
Acknowledgments

    The StartupApproved mechanism is undocumented but well-known; references
    in this README come from observing Task Manager and the autoruns tool.

    The AppX allowlist draws from years of community lists (W4RH4WK, builtbybel,
    Sycnex) — curated and reduced, not copied.

    The BK-tree implementation is textbook; anyone who's taken a CS algorithms
    course will recognise it.

    The "quarantine-first, dry-run always" philosophy is borrowed from
    trash-cli, bleachbit, and every sysadmin who's ever been burned by an
    rm -rf with a bad variable.
