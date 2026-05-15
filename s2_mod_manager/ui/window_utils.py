from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk


@dataclass(frozen=True)
class WindowPlacement:
    width: int
    height: int
    x: int
    y: int

    @property
    def geometry(self) -> str:
        return f"{self.width}x{self.height}+{self.x}+{self.y}"


def centered_placement(
    *,
    parent_x: int,
    parent_y: int,
    parent_width: int,
    parent_height: int,
    width: int,
    height: int,
    screen_width: int,
    screen_height: int,
) -> WindowPlacement:
    width = max(1, min(int(width), max(1, int(screen_width))))
    height = max(1, min(int(height), max(1, int(screen_height))))
    x = int(parent_x) + (max(1, int(parent_width)) - width) // 2
    y = int(parent_y) + (max(1, int(parent_height)) - height) // 2
    x = max(0, min(x, max(0, int(screen_width) - width)))
    y = max(0, min(y, max(0, int(screen_height) - height)))
    return WindowPlacement(width=width, height=height, x=x, y=y)


def configure_dialog(
    window,
    master,
    *,
    width: int,
    height: int,
    min_width: int | None = None,
    min_height: int | None = None,
    modal: bool = True,
    topmost: bool = False,
) -> None:
    apply_window_icon(window, master)
    if min_width is not None or min_height is not None:
        window.minsize(min_width or width, min_height or height)
    try:
        master.update_idletasks()
        window.update_idletasks()
        placement = centered_placement(
            parent_x=master.winfo_rootx(),
            parent_y=master.winfo_rooty(),
            parent_width=master.winfo_width(),
            parent_height=master.winfo_height(),
            width=width,
            height=height,
            screen_width=window.winfo_screenwidth(),
            screen_height=window.winfo_screenheight(),
        )
        window.geometry(placement.geometry)
    except Exception:
        window.geometry(f"{width}x{height}")
    try:
        window.transient(master)
    except Exception:
        pass
    if topmost:
        try:
            window.attributes("-topmost", True)
            window.after(100, lambda: window.attributes("-topmost", False))
        except Exception:
            pass
    if modal:
        try:
            window.grab_set()
        except Exception:
            pass
    try:
        window.focus()
    except Exception:
        pass


def apply_window_icon(window, master=None) -> bool:
    icons = _find_app_icon_candidates(master or window)
    if not icons:
        return False
    applied = _apply_icon_paths(window, icons)
    if applied:
        try:
            window.after(260, lambda: _apply_icon_paths(window, icons))
            window.after(520, lambda: _apply_icon_paths(window, icons))
        except Exception:
            pass
    return applied


def _find_app_icon(widget) -> Path | None:
    for icon in _find_app_icon_candidates(widget):
        if icon.suffix.casefold() == ".ico":
            return icon
    return next(iter(_find_app_icon_candidates(widget)), None)


def _find_app_icon_candidates(widget) -> list[Path]:
    checked = []
    current = widget
    candidates: list[Path] = []
    while current is not None and current not in checked:
        checked.append(current)
        for attr in ("app_icon_path", "app_icon_png_path"):
            path = getattr(current, attr, None)
            if path:
                candidates.append(Path(path))
        dirs = getattr(current, "dirs", None)
        assets_dir = getattr(dirs, "assets_dir", None)
        if assets_dir:
            candidates.extend([Path(assets_dir) / "app.ico", Path(assets_dir) / "app_icon.png"])
        try:
            parent = current.master
        except Exception:
            parent = None
        current = parent
    try:
        top = widget.winfo_toplevel()
    except Exception:
        top = None
    if top is not None and top not in checked:
        candidates.extend(_find_app_icon_candidates(top))
    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen or not candidate.is_file():
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _apply_icon_paths(window, icons: list[Path]) -> bool:
    applied = False
    ico = next((path for path in icons if path.suffix.casefold() == ".ico"), None)
    if ico is not None:
        try:
            window.iconbitmap(str(ico))
            window._iconbitmap_method_called = True
            applied = True
        except Exception:
            pass
        try:
            window.iconbitmap(default=str(ico))
            window._iconbitmap_method_called = True
            applied = True
        except Exception:
            pass
        if applied:
            return True

    png = next((path for path in icons if path.suffix.casefold() == ".png"), None)
    if png is not None:
        try:
            photos = getattr(window, "_s2mm_icon_photos", [])
            photo = tk.PhotoImage(file=str(png))
            photos.append(photo)
            window._s2mm_icon_photos = photos[-2:]
            window.iconphoto(False, photo)
            window.iconphoto(True, photo)
            applied = True
        except Exception:
            pass
    return applied


def open_path_in_shell(path: Path | None) -> tuple[bool, str]:
    if path is None:
        return False, "Path is not configured."
    path = Path(path)
    if not path.exists():
        return False, f"Path does not exist: {path}"
    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
    except Exception as exc:
        return False, f"Could not open path: {exc}"
    return True, f"Opened {path}"


def message_dialog(master, *, tokens, title: str, message: str, width: int = 560, height: int = 260) -> ctk.CTkToplevel:
    dialog = ctk.CTkToplevel(master)
    dialog.title(title)
    c = tokens.colors
    dialog.configure(fg_color=c.bg_abyss)
    frame = ctk.CTkFrame(
        dialog,
        fg_color=c.glass_black,
        corner_radius=tokens.panel_radius,
        border_width=1,
        border_color=c.shell_border_dim,
    )
    frame.pack(fill="both", expand=True, padx=14, pady=14)
    ctk.CTkLabel(
        frame,
        text=title,
        text_color=c.text_primary,
        font=(tokens.font_family, tokens.section_title, "bold"),
        anchor="w",
    ).pack(fill="x", padx=14, pady=(12, 4))
    ctk.CTkLabel(
        frame,
        text=message,
        text_color=c.text_secondary,
        font=(tokens.font_family, tokens.small),
        wraplength=max(240, width - 80),
        justify="left",
        anchor="w",
    ).pack(fill="both", expand=True, padx=14, pady=(0, 12))
    ctk.CTkButton(
        frame,
        text="OK",
        width=96,
        height=32,
        fg_color=c.glass_cyan,
        hover_color=c.panel_glass_hover,
        border_width=1,
        border_color=c.shell_border,
        text_color=c.text_primary,
        command=dialog.destroy,
    ).pack(anchor="e", padx=14, pady=(0, 12))
    configure_dialog(dialog, master, width=width, height=height, min_width=420, min_height=180, modal=True, topmost=True)
    return dialog


def prompt_dialog(
    master,
    *,
    tokens,
    title: str,
    message: str,
    initial_value: str = "",
    width: int = 430,
    height: int = 220,
) -> str | None:
    dialog = ctk.CTkToplevel(master)
    dialog.title(title)
    c = tokens.colors
    result: dict[str, str | None] = {"value": None}
    dialog.configure(fg_color=c.bg_abyss)
    dialog.grid_columnconfigure(0, weight=1)
    dialog.grid_rowconfigure(0, weight=1)

    frame = ctk.CTkFrame(
        dialog,
        fg_color=c.glass_black,
        corner_radius=tokens.panel_radius,
        border_width=1,
        border_color=c.shell_border_dim,
    )
    frame.grid(row=0, column=0, sticky="nsew", padx=14, pady=14)
    frame.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        frame,
        text=title,
        text_color=c.text_primary,
        font=(tokens.font_family, tokens.section_title, "bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 4))
    ctk.CTkLabel(
        frame,
        text=message,
        text_color=c.text_secondary,
        font=(tokens.font_family, tokens.small),
        wraplength=width - 70,
        justify="left",
        anchor="w",
    ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
    entry = ctk.CTkEntry(
        frame,
        fg_color="#020B12",
        border_width=1,
        border_color=c.border_cold,
        text_color=c.text_primary,
        font=(tokens.font_family, tokens.body),
    )
    entry.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
    if initial_value:
        entry.insert(0, initial_value)

    buttons = ctk.CTkFrame(frame, fg_color="transparent")
    buttons.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 14))
    buttons.grid_columnconfigure(0, weight=1)

    def _ok(_event=None) -> None:
        value = entry.get().strip()
        result["value"] = value or None
        dialog.destroy()

    def _cancel(_event=None) -> None:
        result["value"] = None
        dialog.destroy()

    ctk.CTkButton(
        buttons,
        text="Cancel",
        width=96,
        height=32,
        fg_color=c.glass_navy,
        hover_color=c.panel_glass,
        border_width=1,
        border_color=c.border_cold,
        text_color=c.text_secondary,
        command=_cancel,
    ).grid(row=0, column=1, padx=(0, 8))
    ctk.CTkButton(
        buttons,
        text="OK",
        width=96,
        height=32,
        fg_color=c.glass_cyan,
        hover_color=c.panel_glass_hover,
        border_width=1,
        border_color=c.shell_border,
        text_color=c.text_primary,
        command=_ok,
    ).grid(row=0, column=2)
    dialog.bind("<Return>", _ok)
    dialog.bind("<Escape>", _cancel)
    configure_dialog(dialog, master, width=width, height=height, min_width=360, min_height=190, modal=True, topmost=True)
    entry.focus_set()
    dialog.wait_window()
    return result["value"]


def report_dialog(
    master,
    *,
    tokens,
    title: str,
    message: str,
    width: int = 780,
    height: int = 560,
    copy_text: str | None = None,
    save_text: str | None = None,
) -> ctk.CTkToplevel:
    dialog = ctk.CTkToplevel(master)
    dialog.title(title)
    c = tokens.colors
    dialog.configure(fg_color=c.bg_abyss)
    dialog.grid_columnconfigure(0, weight=1)
    dialog.grid_rowconfigure(1, weight=1)
    header = ctk.CTkFrame(
        dialog,
        fg_color=c.glass_black,
        corner_radius=tokens.panel_radius,
        border_width=1,
        border_color=c.shell_border_dim,
    )
    header.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
    ctk.CTkLabel(
        header,
        text=title,
        text_color=c.text_primary,
        font=(tokens.font_family, tokens.section_title, "bold"),
        anchor="w",
    ).pack(fill="x", padx=14, pady=12)

    body = ctk.CTkTextbox(
        dialog,
        fg_color="#020B12",
        text_color=c.text_secondary,
        border_width=1,
        border_color=c.border_soft,
        font=(tokens.mono_family, tokens.mono),
        wrap="word",
    )
    body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))
    body.insert("1.0", message)
    body.configure(state="disabled")

    footer = ctk.CTkFrame(dialog, fg_color="transparent")
    footer.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
    footer.grid_columnconfigure(0, weight=1)
    result_label = ctk.CTkLabel(
        footer,
        text="",
        text_color=c.text_muted,
        font=(tokens.font_family, tokens.small),
        anchor="w",
    )
    result_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    def _copy() -> None:
        dialog.clipboard_clear()
        dialog.clipboard_append(copy_text if copy_text is not None else message)
        result_label.configure(text="Copied to clipboard.", text_color=c.accent_biolume)

    def _save() -> None:
        path = filedialog.asksaveasfilename(
            parent=dialog,
            title=f"Save {title}",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        Path(path).write_text(save_text if save_text is not None else message, encoding="utf-8")
        result_label.configure(text=f"Saved: {path}", text_color=c.accent_biolume)

    column = 1
    if copy_text is not None:
        ctk.CTkButton(
            footer,
            text="Copy",
            width=86,
            height=34,
            fg_color=c.glass_navy,
            hover_color=c.panel_glass,
            border_width=1,
            border_color=c.border_cold,
            text_color=c.text_secondary,
            command=_copy,
        ).grid(row=0, column=column, padx=(0, 8))
        column += 1
    if save_text is not None:
        ctk.CTkButton(
            footer,
            text="Save TXT",
            width=96,
            height=34,
            fg_color=c.glass_navy,
            hover_color=c.panel_glass,
            border_width=1,
            border_color=c.border_cold,
            text_color=c.text_secondary,
            command=_save,
        ).grid(row=0, column=column, padx=(0, 8))
        column += 1
    ctk.CTkButton(
        footer,
        text="Close",
        width=96,
        height=34,
        fg_color=c.glass_navy,
        hover_color=c.panel_glass,
        border_width=1,
        border_color=c.border_cold,
        text_color=c.text_secondary,
        command=dialog.destroy,
    ).grid(row=0, column=column)
    configure_dialog(dialog, master, width=width, height=height, min_width=560, min_height=360, modal=True, topmost=True)
    return dialog
