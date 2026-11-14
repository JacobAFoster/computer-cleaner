import hashlib
import json
import os
import shutil
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, ttk

TRASH_DIR_NAME = ".dedupe_trash"
HASH_SIZE_LIMIT = 200 * 1024 * 1024   # skip hashing files above this size
HASH_CHUNK = 1 << 16                  # 64 KB read blocks

CHECKED = "\u2611"
UNCHECKED = "\u2610"

COLUMNS_FILE = Path(__file__).with_name("column_widths.json")

# Order matters: matches identify_column() indices (#0, #1, ...)
COL_ORDER = ["#0", "path", "size", "modified", "info"]

DEFAULT_WIDTHS = {
    "#0": 40,
    "path": 520,
    "size": 110,
    "modified": 150,
    "info": 200,
}
MIN_WIDTHS = {
    "#0": 30,
    "path": 200,
    "size": 70,
    "modified": 110,
    "info": 80,
}
ANCHORS = {
    "#0": "center",
    "path": "w",
    "size": "e",
    "modified": "w",
    "info": "w",
}


# ----------------------------------------------------------------- helpers
def human_size(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            if unit == "B":
                return f"{n:.0f} B"
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"  # unreachable


def file_hash(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(HASH_CHUNK), b""):
                h.update(block)
    except OSError:
        return None
    return h.hexdigest()


class DedupeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Duplicate File Finder")
        self.geometry("1100x680")
        self.minsize(820, 480)

        self.root_dir = None
        self.groups = {}          # name_lower -> list of file dicts
        self.tree_iids = {}       # child iid -> (name_lower, index)
        self.parent_iids = {}     # name_lower -> parent iid
        self.parent_key_by_iid = {}

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        top = tk.Frame(self, padx=8, pady=8)
        top.pack(fill="x")
        tk.Button(top, text="Choose folder\u2026",
                  command=self.choose_folder).pack(side="left")
        self.folder_var = tk.StringVar(value="(no folder selected)")
        tk.Label(top, textvariable=self.folder_var, anchor="w",
                 fg="gray30").pack(side="left", fill="x", expand=True, padx=(8, 0))

        opts = tk.Frame(self, padx=8)
        opts.pack(fill="x", pady=(0, 6))
        self.recursive_var = tk.BooleanVar(value=True)
        self.follow_var = tk.BooleanVar(value=False)
        self.hidden_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opts, text="Recursive",
                       variable=self.recursive_var).pack(side="left")
        tk.Checkbutton(opts, text="Follow symlinks",
                       variable=self.follow_var).pack(side="left", padx=(8, 0))
        tk.Checkbutton(opts, text="Include hidden files",
                       variable=self.hidden_var).pack(side="left", padx=(8, 0))
        self.scan_btn = tk.Button(opts, text="Scan", command=self.scan)
        self.scan_btn.pack(side="left", padx=(12, 0))

        tree_frame = tk.Frame(self, padx=8)
        tree_frame.pack(fill="both", expand=True)

        columns = ("path", "size", "modified", "info")
        self.tree = ttk.Treeview(tree_frame, columns=columns,
                                 show="tree headings", selectmode="extended")

        self.tree.heading("#0", text="")
        self.tree.heading("path", text="Name / Path")
        self.tree.heading("size", text="Size")
        self.tree.heading("modified", text="Modified")
        self.tree.heading("info", text="Note")

        self._apply_column_widths()

        self.tree.tag_configure("parent", font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("identical", foreground="#2e7d32")
        self.tree.tag_configure("different", foreground="#8a1c1c")

        vsb = tk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.config(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Button-1>", self.on_click)
        self.tree.bind("<space>", self.on_space)
        for seq in ("<Button-3>", "<Button-2>", "<Control-Button-1>"):
            self.tree.bind(seq, self.on_right_click)

        # Column-resize / auto-fit bindings.
        self.tree.bind("<ButtonRelease-1>", self._on_tree_release)
        self.tree.bind("<Double-1>", self._on_header_double_click)

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Keep newest \u2014 check others",
                              command=lambda: self.keep_by("newest"))
        self.menu.add_command(label="Keep oldest \u2014 check others",
                              command=lambda: self.keep_by("oldest"))
        self.menu.add_command(label="Keep largest \u2014 check others",
                              command=lambda: self.keep_by("largest"))
        self.menu.add_command(label="Keep smallest \u2014 check others",
                              command=lambda: self.keep_by("smallest"))
        self.menu.add_separator()
        self.menu.add_command(label="Uncheck group", command=self.uncheck_group)
        self.menu.add_command(label="Check whole group", command=self.check_group)

        bottom = tk.Frame(self, padx=8, pady=8)
        bottom.pack(fill="x")
        tk.Button(bottom, text="Uncheck all",
                  command=self.uncheck_all).pack(side="left")
        tk.Button(bottom, text="Verify identical content",
                  command=self.verify_content).pack(side="left", padx=(8, 0))
        tk.Button(bottom, text="Delete checked\u2026",
                  command=self.delete_checked).pack(side="left", padx=(8, 0))
        tk.Button(bottom, text="Reset columns",
                  command=self.reset_columns).pack(side="left", padx=(8, 0))
        self.summary = tk.Label(bottom, text="", anchor="e", fg="gray30")
        self.summary.pack(side="right")

    # ------------------------------------------------------ column widths
    def _apply_column_widths(self):
        saved = self._load_column_widths()
        for col, default in DEFAULT_WIDTHS.items():
            self.tree.column(
                col,
                width=saved.get(col, default),
                minwidth=MIN_WIDTHS[col],
                anchor=ANCHORS[col],
                stretch=(col == "path"),
            )

    def _load_column_widths(self):
        try:
            data = json.loads(COLUMNS_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {
            k: v for k, v in data.items()
            if k in DEFAULT_WIDTHS and isinstance(v, int) and v > 0
        }

    def _save_column_widths(self):
        widths = {c: int(self.tree.column(c, "width")) for c in DEFAULT_WIDTHS}
        try:
            COLUMNS_FILE.write_text(json.dumps(widths, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _on_tree_release(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region in ("heading", "separator"):
            self._save_column_widths()

    def _on_header_double_click(self, event):
        if self.tree.identify_region(event.x, event.y) != "heading":
            return
        self._autofit_column(self.tree.identify_column(event.x))
        self._save_column_widths()
        return "break"

    def _autofit_column(self, col_id):
        try:
            idx = int(col_id.lstrip("#"))
        except ValueError:
            return
        if idx >= len(COL_ORDER):
            return
        col = COL_ORDER[idx]
        if col == "#0":
            return

        font = tkfont.nametofont("TkDefaultFont")
        width = font.measure(self.tree.heading(col, "text") or "")
        for parent in self.tree.get_children(""):
            width = max(width, font.measure(str(self.tree.set(parent, col))))
            for child in self.tree.get_children(parent):
                width = max(width, font.measure(str(self.tree.set(child, col))))

        new_w = max(MIN_WIDTHS[col], min(width + 18, 900))
        self.tree.column(col, width=new_w)

    def reset_columns(self):
        for col, w in DEFAULT_WIDTHS.items():
            self.tree.column(col, width=w)
        self._save_column_widths()

    # ------------------------------------------------------------- scanning
    def choose_folder(self):
        path = filedialog.askdirectory(title="Choose folder to scan")
        if not path:
            return
        new_root = Path(path)
        if self.root_dir is not None and new_root != self.root_dir:
            self.groups.clear()
            self._populate_tree()
            self._update_summary()
        self.root_dir = new_root
        self.folder_var.set(str(self.root_dir))

    def scan(self):
        if not self.root_dir or not self.root_dir.is_dir():
            messagebox.showinfo("No folder", "Choose a folder first.", parent=self)
            return

        self.groups = {}
        self.scan_btn.config(state="disabled", text="Scanning\u2026")
        self.update_idletasks()

        try:
            files = self._collect_files()
            groups = {}
            for p, size, mtime in files:
                groups.setdefault(p.name.lower(), []).append({
                    "path": p, "size": size, "mtime": mtime,
                    "checked": False, "hash": None,
                })
            self.groups = {k: v for k, v in groups.items() if len(v) > 1}
        finally:
            self.scan_btn.config(state="normal", text="Scan")

        self._populate_tree()
        self._update_summary()

    def _collect_files(self):
        root = self.root_dir
        recursive = self.recursive_var.get()
        follow = self.follow_var.get()
        include_hidden = self.hidden_var.get()

        def on_error(_err):
            pass

        files = []
        if recursive:
            seen_dirs = set()
            for dirpath, dirnames, filenames in os.walk(
                root, followlinks=follow, onerror=on_error
            ):
                if follow:
                    real = os.path.realpath(dirpath)
                    if real in seen_dirs:
                        dirnames[:] = []
                        continue
                    seen_dirs.add(real)

                dirnames[:] = [d for d in dirnames if d != TRASH_DIR_NAME]
                if not include_hidden:
                    dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                for fn in filenames:
                    if not include_hidden and fn.startswith("."):
                        continue
                    p = Path(dirpath) / fn
                    try:
                        st = p.stat()
                    except OSError:
                        continue
                    files.append((p, st.st_size, st.st_mtime))
        else:
            try:
                for entry in root.iterdir():
                    if not include_hidden and entry.name.startswith("."):
                        continue
                    if entry.is_file():
                        try:
                            st = entry.stat()
                        except OSError:
                            continue
                        files.append((entry, st.st_size, st.st_mtime))
            except OSError:
                pass
        return files

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.tree_iids = {}
        self.parent_iids = {}
        self.parent_key_by_iid = {}

        for key in sorted(self.groups):
            files = self.groups[key]
            sizes = [f["size"] for f in files]
            mn, mx = min(sizes), max(sizes)
            n = len(files)
            if mn == mx:
                size_text = f"{n} copies \u00b7 {human_size(mn)} each"
            else:
                size_text = (f"{n} copies \u00b7 "
                             f"{human_size(mn)} \u2013 {human_size(mx)}")

            parent = self.tree.insert(
                "", "end", text="",
                values=(files[0]["path"].name, size_text, "", ""),
                tags=("parent",), open=True,
            )
            self.parent_iids[key] = parent
            self.parent_key_by_iid[parent] = key

            for i, f in enumerate(files):
                info = ""
                if mn != mx:
                    if f["size"] == mx:
                        info = "largest"
                    elif f["size"] == mn:
                        info = "smallest"
                child = self.tree.insert(
                    parent, "end",
                    text=CHECKED if f["checked"] else UNCHECKED,
                    values=(
                        self._relpath(f["path"]),
                        human_size(f["size"]),
                        time.strftime("%Y-%m-%d %H:%M",
                                      time.localtime(f["mtime"])),
                        info,
                    ),
                )
                self.tree_iids[child] = (key, i)

    def _relpath(self, p):
        try:
            return str(p.relative_to(self.root_dir))
        except ValueError:
            return str(p)

    # ------------------------------------------------------------ selection
    def on_click(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid or iid not in self.tree_iids:
            return
        if self.tree.identify_column(event.x) != "#0":
            return
        self._toggle(iid)
        return "break"

    def on_space(self, _event=None):
        toggled = False
        for iid in self.tree.selection():
            if iid in self.tree_iids:
                self._toggle(iid)
                toggled = True
        return "break" if toggled else None

    def _toggle(self, iid):
        key, idx = self.tree_iids[iid]
        files = self.groups[key]
        files[idx]["checked"] = not files[idx]["checked"]
        self.tree.item(iid,
                       text=CHECKED if files[idx]["checked"] else UNCHECKED)
        self._update_summary()

    def _refresh_checks(self):
        for iid, (key, idx) in self.tree_iids.items():
            checked = self.groups[key][idx]["checked"]
            self.tree.item(iid, text=CHECKED if checked else UNCHECKED)

    def uncheck_all(self):
        for files in self.groups.values():
            for f in files:
                f["checked"] = False
        self._refresh_checks()
        self._update_summary()

    def uncheck_group(self):
        for iid in self.tree.selection():
            key = self._group_for_iid(iid)
            if key is None:
                continue
            for f in self.groups[key]:
                f["checked"] = False
        self._refresh_checks()
        self._update_summary()

    def check_group(self):
        for iid in self.tree.selection():
            key = self._group_for_iid(iid)
            if key is None:
                continue
            for f in self.groups[key]:
                f["checked"] = True
        self._refresh_checks()
        self._update_summary()

    def _group_for_iid(self, iid):
        if iid in self.tree_iids:
            return self.tree_iids[iid][0]
        return self.parent_key_by_iid.get(iid)

    # -------------------------------------------------------------- keep by
    def on_right_click(self, event):
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        if iid not in self.tree.selection():
            self.tree.selection_set(iid)
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def keep_by(self, criterion):
        for iid in self.tree.selection():
            key = self._group_for_iid(iid)
            if key is None:
                continue
            files = self.groups[key]
            if not files:
                continue
            picker = {
                "newest":   lambda: max(range(len(files)),
                                        key=lambda i: files[i]["mtime"]),
                "oldest":   lambda: min(range(len(files)),
                                        key=lambda i: files[i]["mtime"]),
                "largest":  lambda: max(range(len(files)),
                                        key=lambda i: files[i]["size"]),
                "smallest": lambda: min(range(len(files)),
                                        key=lambda i: files[i]["size"]),
            }.get(criterion)
            if picker is None:
                continue
            keep = picker()
            for i, f in enumerate(files):
                f["checked"] = (i != keep)
        self._refresh_checks()
        self._update_summary()

    # -------------------------------------------------------------- hashing
    def verify_content(self):
        if not self.groups:
            messagebox.showinfo("Nothing to verify",
                                "Scan a folder first.", parent=self)
            return

        skipped = 0
        for files in self.groups.values():
            for f in files:
                if f["hash"] is not None:
                    continue
                if f["size"] > HASH_SIZE_LIMIT:
                    skipped += 1
                    continue
                f["hash"] = file_hash(f["path"])
            self.update_idletasks()

        for key, files in self.groups.items():
            parent = self.parent_iids.get(key)
            hashed = [f for f in files if f["hash"] is not None]
            all_hashed = len(hashed) == len(files)
            valid_hashes = {f["hash"] for f in hashed}

            if parent:
                if all_hashed and len(valid_hashes) == 1:
                    self.tree.set(parent, "info", "identical content")
                elif all_hashed:
                    self.tree.set(parent, "info", "different content")
                else:
                    self.tree.set(parent, "info",
                                  f"partial ({len(hashed)}/{len(files)} hashed)")

            sizes = [f["size"] for f in files]
            mn, mx = min(sizes), max(sizes)
            for iid, (k, i) in self.tree_iids.items():
                if k != key:
                    continue
                f = files[i]
                note_parts = []
                if mx != mn:
                    if f["size"] == mx:
                        note_parts.append("largest")
                    elif f["size"] == mn:
                        note_parts.append("smallest")
                if f["hash"] is not None:
                    matches = sum(1 for x in files if x["hash"] == f["hash"])
                    if matches > 1:
                        note_parts.append(f"matches {matches - 1} other(s)")
                self.tree.set(iid, "info", " \u00b7 ".join(note_parts))

                if all_hashed:
                    tag = "identical" if len(valid_hashes) == 1 else "different"
                    self.tree.item(iid, tags=(tag,))

        msg = "Content verification complete."
        if skipped:
            msg += (f"\n{skipped} file(s) were not hashed "
                    f"(larger than {human_size(HASH_SIZE_LIMIT)}).")
        messagebox.showinfo("Verify content", msg, parent=self)

    # --------------------------------------------------------------- summary
    def _update_summary(self):
        selected = 0
        bytes_freed = 0
        groups_touched = 0
        for files in self.groups.values():
            touched = False
            for f in files:
                if f["checked"]:
                    selected += 1
                    bytes_freed += f["size"]
                    touched = True
            if touched:
                groups_touched += 1
        self.summary.config(
            text=(f"{len(self.groups)} duplicate group(s) \u00b7 "
                  f"{selected} selected across {groups_touched} group(s) \u00b7 "
                  f"{human_size(bytes_freed)} to free")
        )

    # ---------------------------------------------------------------- delete
    def delete_checked(self):
        checked = [(key, f) for key, files in self.groups.items()
                   for f in files if f["checked"]]
        if not checked:
            messagebox.showinfo("Nothing selected",
                                "Check the files you want to remove.",
                                parent=self)
            return

        empties = [key for key, files in self.groups.items()
                   if files and all(f["checked"] for f in files)]
        if empties:
            names = ", ".join(sorted(empties)[:5])
            if len(empties) > 5:
                names += f", and {len(empties) - 5} more"
            if not messagebox.askyesno(
                "Whole groups selected",
                f"You've selected every file in {len(empties)} group(s):\n"
                f"{names}\n\nDelete them all anyway?",
                parent=self,
            ):
                return

        total = sum(f["size"] for _, f in checked)
        if not messagebox.askyesno(
            "Delete files",
            f"Move {len(checked)} file(s) ({human_size(total)}) to:\n"
            f"{self.root_dir / TRASH_DIR_NAME}\n\n"
            "They can be recovered from there.\n\nContinue?",
            parent=self,
        ):
            return

        stamp = time.strftime("%Y%m%d-%H%M%S")
        moved = 0
        errors = []
        trashed = set()
        for _key, f in checked:
            try:
                self._trash(f["path"], stamp)
                moved += 1
                trashed.add(f["path"])
            except OSError as e:
                errors.append(f"{f['path']}: {e}")

        new_groups = {}
        for key, files in self.groups.items():
            remaining = [f for f in files if f["path"] not in trashed]
            if len(remaining) >= 2:
                new_groups[key] = remaining
        self.groups = new_groups

        self._populate_tree()
        self._update_summary()

        msg = f"Moved {moved} file(s) to the trash folder."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                msg += f"\n\u2026and {len(errors) - 10} more."
        messagebox.showinfo("Done", msg, parent=self)

    def _trash(self, path, stamp):
        root, path = Path(self.root_dir), Path(path)
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = Path(path.name)
        dest = root / TRASH_DIR_NAME / stamp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            suffix = int(time.time() * 1000) % 100_000_000
            dest = dest.with_name(f"{dest.stem}-{suffix}{dest.suffix}")
        shutil.move(str(path), str(dest))
        return dest

    # ----------------------------------------------------------------- close
    def on_close(self):
        self._save_column_widths()
        if any(f["checked"] for files in self.groups.values() for f in files):
            if not messagebox.askyesno(
                "Quit?",
                "You have checked files that haven't been deleted. Quit anyway?",
                parent=self,
            ):
                return
        self.destroy()


if __name__ == "__main__":
    DedupeApp().mainloop()