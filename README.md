PyCleaner

A cross-platform duplicate file finder and Windows maintenance toolkit.

PyCleaner is a safety-focused computer cleaning utility built with Python and Tkinter. It helps you identify duplicate files, remove unnecessary clutter, manage startup applications, and inspect Windows maintenance items.

Unlike traditional PC cleaners, PyCleaner uses a quarantine-first approach: files are moved to a recoverable location instead of being permanently deleted.

16 cleaners. Zero silent deletes. Every quarantined file can be restored.

Features
Feature	Platform	Description
Duplicate Files	Cross-platform	Find duplicates using file size and SHA-256 hashing
Empty Folders	Cross-platform	Find empty directories, including nested folders
Empty Files	Cross-platform	Find zero-byte files
Junk Files	Cross-platform	Identify temporary files and common junk
Old Files	Cross-platform	Find files based on modification age
Large Files	Cross-platform	Locate files above a configurable size
Temp & Cache	Cross-platform	Find temporary files and cache data
Downloads Triage	Cross-platform	Organise downloads by file type and age
Similar Images	Cross-platform	Find visually similar images using perceptual hashing
Startup Apps	Windows	View and manage startup applications
Installed Programs	Windows	Browse installed applications and launch uninstallers
Scheduled Tasks	Windows	View scheduled tasks
Services	Windows	View Windows services
Microsoft Store Apps	Windows	Manage selected AppX packages
Broken Shortcuts	Windows	Find shortcuts pointing to missing files
Recycle Bin	Windows	View and empty the Windows Recycle Bin

Total: 16 cleaners — 9 cross-platform and 7 Windows-only.

Safety First

PyCleaner is designed to minimise accidental data loss.

1. Quarantine instead of permanent deletion

Files are moved into a dedicated quarantine directory:

Windows: %APPDATA%\PyCleaner\trash
Linux/macOS: ~/.config/PyCleaner/trash

Each quarantine session receives its own folder containing a JSON manifest.

The manifest records:

Original file location.
Quarantined filename.
File size.
File or directory type.
Cleaner responsible for the action.

Files can be restored through the Trash tab.

2. Protected system locations

PyCleaner prevents cleaners from modifying important system directories, including:

C:\Windows
C:\Program Files
C:\Program Files (x86)
C:\ProgramData\Microsoft
C:\Users\Default
C:\$Recycle.Bin

The application also protects its own configuration and quarantine directories.

3. Dry-run mode

Each cleaner supports a dry-run option.

Dry-run mode allows you to:

Scan files.
Review selected items.
View confirmation dialogs.
Preview the actions that would be performed.

No files are modified during a dry run.

4. Action logging

Actions are recorded in:

%APPDATA%\PyCleaner\actions.log

This provides an audit trail of quarantine, restore, purge, and other supported operations.

Requirements
Python 3.10 or newer.
Tkinter.
Windows for Windows-specific cleaners.
PowerShell 3.0 or newer for Windows maintenance features.

Tkinter is included with most standard Python installations.

On Debian/Ubuntu, install it with:

bash
sudo apt install python3-tk

Optional dependencies

Some cleaners require additional packages.

Package	Feature
Pillow	Similar Images
imagehash	Similar Images
winshell	Windows Recycle Bin

Install them with:

bash
pip install Pillow imagehash winshell

Installation
1. Clone the repository
bash
git clone https://github.com/JacobAFoster/computer-cleaner.git
cd computer-cleaner

2. Create a virtual environment (recommended)

Windows:

powershell
python -m venv .venv
.venv\Scripts\activate


Linux/macOS:

bash
python3 -m venv .venv
source .venv/bin/activate

3. Install optional dependencies
bash
pip install Pillow imagehash winshell

4. Run PyCleaner
bash
python main.py

Quick Start
Launch PyCleaner using python main.py.
Select the cleaner you want to use.
Choose a folder to scan, where applicable.
Configure the cleaner's options.
Click Scan.
Review the results and select the items you want to process.
Click the appropriate action button.
Confirm the operation.

Files processed by the quarantine-enabled cleaners are moved into quarantine rather than permanently deleted.

You can restore quarantined files from the Trash tab.

Tip: Start by scanning your Downloads folder or another directory containing files you recognise.

The Interface

PyCleaner uses a tabbed Tkinter interface.

Available sections include:

Cleaner tabs for individual maintenance operations.
Trash for restoring or purging quarantined files.
Settings for configuring cleaner behaviour.

Additional interface features include:

Background scanning.
Progress reporting.
Scan cancellation.
File selection and bulk selection.
Configurable columns.
Right-click actions for duplicate groups.
Image previews for similar images.
Dry-run mode.

Column widths are saved individually for each cleaner.

Cleaner Details
Duplicate Files

Finds files with identical contents using file size and SHA-256 hashing.

Two scan modes are available:

Mode	Description
Content	Compares file sizes and SHA-256 hashes
Name	Groups files by matching filename

Content mode is recommended for identifying genuine duplicates.

Empty Folders

Finds empty directories, including nested empty directories.

Empty Files

Identifies files with a size of zero bytes.

Common placeholder files, such as .gitkeep and .nomedia, are excluded.

Junk Files

Identifies files matching configurable patterns, including:

Thumbs.db
desktop.ini
.DS_Store
*.tmp
*.bak
*.crdownload
*.partial
Old Files

Finds files based on their last modification date.

The default threshold is 365 days.

Large Files

Finds files exceeding a configurable size threshold.

The default threshold is 500 MB.

Temp & Cache

Scans common temporary and cache directories.

Windows:

%TEMP%
%LOCALAPPDATA%\Temp

Linux/macOS:

System temporary directory.
~/.cache
Downloads Triage

Groups files in your Downloads directory by category:

Installers
Archives
Documents
Images
Media
Code
Other

This cleaner is designed for reviewing downloads rather than automatically selecting files for removal.

Similar Images

Uses perceptual hashing to identify visually similar images.

Supported detection includes:

Resized images.
Re-encoded images.
Watermarked images.
Similar image variations.

Uses Difference Hashing (dHash) and BK-tree clustering.

Requires:

bash
pip install Pillow imagehash

Startup Apps

Windows-only.

Displays applications configured to launch during startup.

Supports enabling and disabling startup entries using Windows' StartupApproved mechanism.

Installed Programs

Windows-only.

Lists installed applications and allows you to launch their registered uninstallers.

PyCleaner launches the vendor's uninstall interface rather than silently uninstalling applications.

Scheduled Tasks

Windows-only.

Provides a read-only overview of scheduled Windows tasks.

Services

Windows-only.

Displays Windows services, including their status and startup type.

This cleaner is read-only.

Microsoft Store Apps

Windows-only.

Displays selected Microsoft Store applications using a curated allowlist.

Packages are categorised by risk level.

Some removal operations require administrator privileges.

Broken Shortcuts

Windows-only.

Identifies .lnk shortcuts whose target files no longer exist.

Recycle Bin

Windows-only.

Displays Recycle Bin contents and provides an option to empty the bin.

Requires:

bash
pip install winshell

Quarantine & Restore

PyCleaner's quarantine system stores processed files separately from the original directories.

Default locations:

Windows

text
%APPDATA%\PyCleaner\trash


Linux/macOS

text
~/.config/PyCleaner/trash


Each quarantine session contains:

A timestamped directory.
A manifest.json file.
The quarantined files.
Restoring files
Open the Trash tab.
Select the quarantine session.
Click Restore.
Files are moved back to their original locations.

If a file already exists at its original location, PyCleaner reports the conflict and leaves the quarantined copy untouched.

Retention

The default quarantine retention period is 30 days.

You can manually purge older quarantine sessions through the Trash tab.

Purging is separate from restoring and permanently removes quarantined data.

Configuration

PyCleaner stores its configuration in:

Windows

text
%APPDATA%\PyCleaner


Linux/macOS

text
~/.config/PyCleaner


Configuration files include:

File	Purpose
settings.json	Application and cleaner settings
columns.json	Legacy column configuration
columns_<id>.json	Individual cleaner column widths
appx_allowlist.json	Optional Store app allowlist
actions.log	Action history
trash/	Quarantined files and manifests
Command-Line Usage

PyCleaner also provides a headless command-line interface for scanning and testing cleaners without opening the graphical interface.

List available cleaners:

bash
python main.py --list


Scan a directory for duplicates:

bash
python main.py --scan ./Downloads --cleaner dedupe


Scan for junk files:

bash
python main.py --scan ./Downloads --cleaner junk --json


Scan for large files:

bash
python main.py --scan ./Downloads --cleaner large


Scan for similar images:

bash
python main.py --scan ./Pictures --cleaner similar_images --json


Important: CLI scan operations are read-only. They do not delete files or modify the quarantine manifest.

The --json option outputs structured results for scripting and automated testing.

Architecture

PyCleaner is built around a plugin-based cleaner architecture.

The main components are:

Component	Responsibility
Cleaner	Base class for individual cleaners
Item	Shared data structure for scan results
CleanerTab	Generic Tkinter interface for cleaners
CleanerApp	Main application and tab management
Quarantine	File quarantine, restoration, and purging
Settings	Configuration loading and saving

New cleaners can be added by extending the Cleaner base class and registering the new cleaner.

The generic interface handles scanning, progress reporting, selection, confirmation dialogs, and quarantine integration.

Development

Contributions and new cleaner ideas are welcome.

When adding a cleaner, aim to:

Follow the existing cleaner architecture.
Respect protected system paths.
Support cancellation during scanning.
Avoid permanent deletion wherever possible.
Provide clear descriptions of detected items.
Include appropriate error handling.
Test against fixture directories before using real data.
Project structure

The repository currently contains:

text
computer-cleaner/
├── main.py
├── column_widths.json
└── README.md

Known Limitations
Some cleaners are Windows-only.
Windows-specific functionality depends on PowerShell.
Similar image detection requires optional dependencies.
Network-drive scanning may be slower than local scanning.
macOS and Linux support has not been tested as extensively as Windows.
PyCleaner's quarantine is separate from the native operating system Trash.
Emptying the Windows Recycle Bin is a bulk operation.
Features intentionally excluded

PyCleaner deliberately avoids:

Registry cleaners.
RAM optimisers.
Fake performance-boosting features.
Silent application uninstalls.
Automatic modification of Windows services.
Unnecessary background processes.

The focus is on useful maintenance tools rather than misleading performance claims.

Troubleshooting

Missing cleaner tabs

Install the optional dependencies required by the cleaner.

bash
pip install Pillow imagehash winshell


PowerShell not found

Install or enable a supported version of PowerShell. Windows-specific cleaners that depend on PowerShell will not work without it.

Files cannot be moved

Some files may be locked by running applications. Close the application using the file and try again.

Quarantine is taking up disk space

Open the Trash tab and manually purge quarantine sessions you no longer need.

Scanning takes too long

Try scanning smaller directories instead of scanning an entire drive.

License

This project is licensed under the MIT License.

You are free to use, modify, and distribute the software in accordance with the license.

Disclaimer: PyCleaner is provided without warranty. Always review selected files before performing maintenance operations. Although quarantine and dry-run functionality help reduce accidental data loss, no cleaning utility can guarantee that every operation is risk-free.

Acknowledgements
Pillow and imagehash for image processing and perceptual hashing.
The Python community for the libraries and tools that make this project possible.
The open-source community for inspiration behind the quarantine-first approach.

Developed by JacobAFoster
