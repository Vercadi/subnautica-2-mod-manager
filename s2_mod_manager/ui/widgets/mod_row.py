from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass, field

import customtkinter as ctk

from ..ui_tokens import UiTokens


@dataclass(frozen=True)
class PlaceholderMod:
    name: str
    version: str
    description: str
    badges: list[str] = field(default_factory=list)
    status: str = "Compatible"
    enabled: bool = True
    warning: str = ""
    accent: str = "#38D6D6"
    state: str = "placeholder"
    source_name: str = ""
    source_path: str = ""
    managed_path: str = ""
    component_id: str = ""
    source_id: str = ""
    component_type: str = ""
    install_kind: str = ""
    target_hint: str = ""
    file_count: int = 0
    files: list[str] = field(default_factory=list)
    dependency_warnings: list[str] = field(default_factory=list)
    source_warnings: list[str] = field(default_factory=list)
    review_policy_text: str = ""
    in_active_profile: bool = False
    profile_enabled: bool = False
    profile_order: int = -1
    profile_name: str = ""
    profile_warning: str = ""
    deployment_status: str = ""
    deployment_preview: str = ""


class ModRow(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        tokens: UiTokens,
        mod: PlaceholderMod,
        selected: bool = False,
        command=None,
        can_toggle: bool = False,
        can_reorder: bool = False,
        profile_protected: bool = False,
        compact: bool = False,
        bulk_selected: bool = False,
        on_toggle=None,
        on_menu=None,
        on_warning=None,
        on_move=None,
        on_bulk_select=None,
    ):
        colors = tokens.colors
        warned = bool(mod.warning or mod.profile_warning)
        super().__init__(
            master,
            fg_color=colors.glass_cyan if selected else colors.glass_navy,
            corner_radius=tokens.row_radius,
            border_width=1,
            border_color=colors.shell_border if selected else colors.warning if warned else colors.border_soft,
        )
        self.tokens = tokens
        self.mod = mod
        self.command = command
        self.can_toggle = can_toggle
        self.can_reorder = can_reorder
        self.profile_protected = profile_protected
        self.compact = compact
        self.bulk_selected = bulk_selected
        self.on_toggle = on_toggle
        self.on_menu = on_menu
        self.on_warning = on_warning
        self.on_move = on_move
        self.on_bulk_select = on_bulk_select
        self.bulk_var: tk.BooleanVar | None = None
        self.indicator: tk.Canvas | None = None
        self.title_label: ctk.CTkLabel | None = None
        self.badges_label: ctk.CTkLabel | None = None
        self.profile_switch: ctk.CTkSwitch | None = None
        self._has_warning_button = bool(mod.warning or mod.profile_warning)
        if self.compact:
            self.configure(height=44)
            self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)
        self._build()
        self.bind("<Button-1>", self._clicked)
        self._bind_selectable_children(self)

    def _build(self) -> None:
        if self.compact:
            self._build_compact()
            return
        t = self.tokens
        c = t.colors
        thumb = _Thumbnail(self, tokens=t, mod=self.mod)
        thumb.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=8, pady=8)

        title = ctk.CTkLabel(
            self,
            text=_fit_text(f"{self.mod.name}  {self.mod.version}", 72),
            font=(t.font_family, t.row_title, "bold"),
            text_color=c.text_primary,
            anchor="w",
        )
        title.grid(row=0, column=1, sticky="ew", padx=(8, 8), pady=(8, 0))

        desc = ctk.CTkLabel(
            self,
            text=_fit_text(self.mod.description, 94),
            font=(t.font_family, t.small),
            text_color=c.text_secondary,
            anchor="w",
            wraplength=360,
        )
        desc.grid(row=1, column=1, sticky="ew", padx=(8, 8), pady=(0, 4))

        badges = ctk.CTkFrame(self, fg_color="transparent")
        badges.grid(row=2, column=1, sticky="w", padx=(8, 8), pady=(0, 8))
        for index, (badge, color) in enumerate(_row_badges(self.mod, t)):
            _badge(badges, t, badge, color).grid(row=0, column=index, padx=(0, 5))

        if self.mod.warning or self.mod.profile_warning:
            ctk.CTkButton(
                self,
                text="WARN",
                width=48,
                height=24,
                fg_color="transparent",
                hover_color=c.panel_glass_hover,
                border_width=1,
                border_color=c.warning,
                corner_radius=5,
                font=(t.font_family, t.tiny, "bold"),
                text_color=c.warning,
                command=self._warning_clicked,
            ).grid(row=0, column=2, rowspan=3, padx=(0, 8))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=3, rowspan=3, sticky="e", padx=(0, 10), pady=6)
        actions.grid_columnconfigure((0, 1, 2, 3), weight=0)
        switch = ctk.CTkSwitch(
            actions,
            text="",
            width=48,
            progress_color=c.accent_lagoon,
            button_color=c.text_primary,
            fg_color=c.disabled,
            state="normal" if self.can_toggle else "disabled",
            command=self._toggle_clicked,
        )
        switch.grid(row=0, column=0, columnspan=3, sticky="e", padx=(0, 6))
        if self.mod.enabled:
            switch.select()
        else:
            switch.deselect()

        menu_button = ctk.CTkButton(
            actions,
            text="...",
            width=34,
            height=30,
            fg_color="transparent",
            hover_color=c.panel_glass_hover,
            text_color=c.text_secondary,
            corner_radius=5,
            command=lambda: self._menu_clicked(menu_button),
        )
        menu_button.grid(row=0, column=3, sticky="e")

        for index, (label, direction) in enumerate((("⇈", "top"), ("↑", "up"), ("↓", "down"), ("⇊", "bottom"))):
            ctk.CTkButton(
                actions,
                text=label,
                width=24,
                height=22,
                fg_color=c.glass_black if self.can_reorder else c.disabled,
                hover_color=c.panel_glass if self.can_reorder else c.disabled,
                border_width=1,
                border_color=c.border_cold if self.can_reorder else c.border_soft,
                text_color=c.text_secondary if self.can_reorder else c.text_muted,
                font=(t.font_family, t.tiny, "bold"),
                state="normal" if self.can_reorder else "disabled",
                command=lambda value=direction: self._move_clicked(value),
            ).grid(row=1, column=index, padx=(0, 3), pady=(3, 0))
        ctk.CTkLabel(
            actions,
            text=_row_action_hint(self.mod, can_toggle=self.can_toggle, profile_protected=self.profile_protected),
            text_color=c.text_muted,
            font=(t.font_family, t.tiny),
        ).grid(row=2, column=0, columnspan=4, sticky="e", pady=(2, 0))

    def _build_compact(self) -> None:
        t = self.tokens
        c = t.colors
        self.grid_columnconfigure(2, weight=1)
        self.bulk_var = tk.BooleanVar(value=self.bulk_selected)
        ctk.CTkCheckBox(
            self,
            text="",
            width=18,
            variable=self.bulk_var,
            fg_color=c.accent_lagoon,
            hover_color=c.panel_glass_hover,
            border_color=c.border_cold,
            command=self._bulk_select_clicked,
        ).grid(row=0, column=0, sticky="w", padx=(8, 0), pady=8)
        self.indicator = tk.Canvas(self, width=18, height=30, highlightthickness=0, bd=0, bg=self.cget("fg_color"))
        self.indicator.grid(row=0, column=1, sticky="nsw", padx=(4, 4), pady=6)
        self._draw_indicator()

        title_text = self.mod.name
        self.title_label = ctk.CTkLabel(
            self,
            text=_fit_text(title_text, 92),
            font=(t.font_family, t.row_title, "bold"),
            text_color=c.text_primary,
            anchor="w",
        )
        self.title_label.grid(row=0, column=2, sticky="ew", padx=(4, 8), pady=8)

        self.badges_label = ctk.CTkLabel(
            self,
            text=_fit_text(_compact_badges(self.mod), 28),
            font=(t.font_family, t.tiny, "bold"),
            text_color=c.text_muted,
            anchor="e",
        )
        self.badges_label.grid(row=0, column=3, sticky="e", padx=(0, 10))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=4, sticky="e", padx=(0, 10), pady=6)
        if self.mod.warning or self.mod.profile_warning:
            ctk.CTkButton(
                actions,
                text="!",
                width=28,
                height=26,
                fg_color="transparent",
                hover_color=c.panel_glass_hover,
                border_width=1,
                border_color=c.warning,
                corner_radius=5,
                font=(t.font_family, t.small, "bold"),
                text_color=c.warning,
                command=self._warning_clicked,
            ).grid(row=0, column=0, padx=(0, 6))
        self.profile_switch = ctk.CTkSwitch(
            actions,
            text="",
            width=46,
            progress_color=c.accent_lagoon,
            button_color=c.text_primary,
            fg_color=c.disabled,
            state="normal" if self.can_toggle else "disabled",
            command=self._toggle_clicked,
        )
        self.profile_switch.grid(row=0, column=1, padx=(0, 6), pady=(3, 0))
        if self.mod.enabled:
            self.profile_switch.select()
        else:
            self.profile_switch.deselect()
        menu_button = ctk.CTkButton(
            actions,
            text="...",
            width=30,
            height=26,
            fg_color="transparent",
            hover_color=c.panel_glass_hover,
            text_color=c.text_secondary,
            corner_radius=5,
            command=lambda: self._menu_clicked(menu_button),
        )
        menu_button.grid(row=0, column=2, pady=(3, 0))

    def _bind_selectable_children(self, widget) -> None:
        for child in widget.winfo_children():
            if isinstance(child, (ctk.CTkButton, ctk.CTkSwitch)):
                continue
            try:
                child.bind("<Button-1>", self._clicked, add="+")
            except Exception:
                pass
            self._bind_selectable_children(child)

    def _clicked(self, _event=None) -> None:
        if self.command:
            self.command(self.mod)

    def set_selected(self, selected: bool) -> None:
        colors = self.tokens.colors
        warned = bool(self.mod.warning or self.mod.profile_warning)
        self.configure(
            fg_color=colors.glass_cyan if selected else colors.glass_navy,
            border_color=colors.shell_border if selected else colors.warning if warned else colors.border_soft,
        )
        if self.indicator is not None:
            self.indicator.configure(bg=self.cget("fg_color"))

    def update_compact_state(
        self,
        *,
        mod: PlaceholderMod,
        selected: bool,
        can_toggle: bool,
        profile_protected: bool,
        bulk_selected: bool,
    ) -> bool:
        """Update a compact row without rebuilding all row widgets.

        Returns False when the row shape changed enough that the caller should
        rebuild this list. The warning action is the only compact-row shape
        branch today.
        """
        if not self.compact:
            return False
        if bool(mod.warning or mod.profile_warning) != self._has_warning_button:
            return False
        self.mod = mod
        self.can_toggle = can_toggle
        self.profile_protected = profile_protected
        self.bulk_selected = bulk_selected
        if self.bulk_var is not None:
            self.bulk_var.set(bulk_selected)
        if self.title_label is not None:
            self.title_label.configure(text=_fit_text(mod.name, 92))
        if self.badges_label is not None:
            self.badges_label.configure(text=_fit_text(_compact_badges(mod), 28))
        if self.profile_switch is not None:
            self.profile_switch.configure(state="normal" if can_toggle else "disabled")
            if mod.enabled:
                self.profile_switch.select()
            else:
                self.profile_switch.deselect()
        self.set_selected(selected)
        self._draw_indicator()
        return True

    def _draw_indicator(self) -> None:
        if self.indicator is None:
            return
        self.indicator.delete("all")
        self.indicator.configure(bg=self.cget("fg_color"))
        self.indicator.create_oval(4, 13, 12, 21, fill=_compact_status_color(self.mod, self.tokens), outline="")

    def _toggle_clicked(self) -> None:
        if self.on_toggle and self.can_toggle:
            self.on_toggle(self.mod)

    def _menu_clicked(self, button) -> None:
        if self.on_menu:
            self.on_menu(self.mod, button.winfo_rootx(), button.winfo_rooty() + button.winfo_height())

    def _warning_clicked(self) -> None:
        if self.on_warning:
            self.on_warning(self.mod)

    def _move_clicked(self, direction: str) -> None:
        if self.on_move and self.can_reorder:
            self.on_move(self.mod, direction)

    def _bulk_select_clicked(self) -> None:
        if self.on_bulk_select and self.bulk_var is not None:
            self.on_bulk_select(self.mod, bool(self.bulk_var.get()))


class _Thumbnail(tk.Canvas):
    def __init__(self, master, *, tokens: UiTokens, mod: PlaceholderMod):
        self.tokens = tokens
        self.mod = mod
        self.color = mod.accent
        super().__init__(
            master,
            width=116,
            height=62,
            highlightthickness=0,
            bd=0,
            bg=tokens.colors.glass_black,
        )
        self._draw()

    def _draw(self) -> None:
        c = self.tokens.colors
        label = _thumbnail_label(self.mod)
        self.create_rectangle(0, 0, 116, 62, fill="#061E2E", outline=c.border_soft)
        self.create_line(0, 50, 116, 18, fill=c.shell_border_dim, width=2)
        self.create_line(20, 0, 102, 62, fill="#0C4054", width=1)
        for radius in (18, 30):
            self.create_oval(18 - radius, 31 - radius, 18 + radius, 31 + radius, outline=c.shell_border_dim, width=1)
        self.create_oval(32, 10, 84, 52, outline=self.color, width=2)
        self.create_rectangle(47, 20, 69, 42, outline=self.color, width=2)
        if self.mod.warning or self.mod.profile_warning:
            self.create_polygon(93, 10, 106, 34, 80, 34, fill="", outline=c.warning, width=2)
        self.create_text(58, 31, text=label, fill=c.text_primary, font=("Segoe UI", 12, "bold"))


def _badge(master, tokens: UiTokens, text: str, color: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        master,
        text=_fit_text(text, 18),
        fg_color=color,
        text_color=tokens.colors.text_primary,
        corner_radius=4,
        padx=7,
        pady=2,
        font=(tokens.font_family, tokens.tiny, "bold"),
    )


def _fit_text(text: str, max_chars: int) -> str:
    value = str(text or "").strip()
    if max_chars <= 0 or len(value) <= max_chars:
        return value
    if max_chars <= 8:
        return value[:max_chars]
    left = (max_chars - 5) // 2
    right = max_chars - 5 - left
    return f"{value[:left]} ... {value[-right:]}"


def _row_badges(mod: PlaceholderMod, tokens: UiTokens) -> list[tuple[str, str]]:
    c = tokens.colors
    badges: list[tuple[str, str]] = [(mod.status, _status_color(mod.status, tokens))]
    if mod.in_active_profile:
        badges.append((f"Loadout #{mod.profile_order + 1}", c.glass_cyan))
        badges.append(("On" if mod.profile_enabled else "Off", c.chip_green if mod.profile_enabled else c.disabled))
    elif mod.state == "library":
        badges.append(("Imported", c.chip_green))
    elif mod.state.startswith("candidate"):
        badges.append(("Ready", c.chip_orange))
    for badge in mod.badges:
        badges.append((badge, _badge_color(badge, tokens)))
    if mod.deployment_status:
        badges.append((f"Plan {mod.deployment_status}", c.chip_blue))
    if mod.warning or mod.profile_warning:
        badges.append(("Needs Review", c.chip_orange))
    if len(badges) > 6:
        return badges[:5] + [(f"+{len(badges) - 5}", c.border_cold)]
    return badges


def _status_color(status: str, tokens: UiTokens) -> str:
    c = tokens.colors
    normalized = status.casefold()
    if normalized in {"library", "scanned", "imported", "compatible", "ready to apply"}:
        return c.chip_green
    if normalized in {"candidate", "review", "needs review", "ready to import"}:
        return c.chip_orange
    if "conflict" in normalized or "missing" in normalized:
        return c.chip_orange
    return c.chip_blue


def _badge_color(text: str, tokens: UiTokens) -> str:
    c = tokens.colors
    normalized = text.casefold()
    if "ue4ss" in normalized:
        return c.chip_blue
    if "pak" in normalized:
        return c.chip_purple
    if "runtime" in normalized:
        return c.chip_green
    if "loose" in normalized or "review" in normalized:
        return c.chip_orange
    return c.border_cold


def _thumbnail_label(mod: PlaceholderMod) -> str:
    tags = " ".join(mod.badges + [mod.component_type, mod.install_kind]).casefold()
    if "runtime" in tags:
        return "CORE"
    if "ue4ss" in tags:
        return "UE"
    if "pak" in tags:
        return "PAK"
    return "MOD"


def _compact_summary(mod: PlaceholderMod) -> str:
    pieces = []
    if mod.in_active_profile:
        pieces.append(f"{mod.profile_name or 'Profile'}: {'Enabled' if mod.profile_enabled else 'Disabled'}")
    elif mod.state == "library":
        pieces.append("Imported")
    elif mod.state.startswith("candidate"):
        pieces.append("Ready to Import")
    else:
        pieces.append(mod.state.replace("_", " ").title())
    if mod.component_type:
        pieces.append(mod.component_type.replace("_", " ").upper())
    if mod.target_hint:
        pieces.append(mod.target_hint)
    if mod.warning or mod.profile_warning:
        pieces.append("needs review")
    return " | ".join(pieces)


def _compact_status_color(mod: PlaceholderMod, tokens: UiTokens) -> str:
    c = tokens.colors
    if mod.warning or mod.profile_warning:
        return c.warning
    if mod.in_active_profile:
        return c.accent_biolume if mod.profile_enabled else c.disabled
    if mod.state == "library":
        return c.accent_lagoon
    if mod.state.startswith("candidate"):
        return c.accent_pressure
    return c.text_muted


def _compact_badges(mod: PlaceholderMod) -> str:
    values = []
    if mod.in_active_profile:
        values.append("ENABLED" if mod.profile_enabled else "DISABLED")
    elif mod.state.startswith("candidate"):
        values.append("READY")
    elif mod.state == "library":
        values.append("IMPORTED")
    values.extend(str(value).upper() for value in mod.badges[:2])
    return " / ".join(dict.fromkeys(values))


def _row_action_hint(mod: PlaceholderMod, *, can_toggle: bool, profile_protected: bool = False) -> str:
    if mod.review_policy_text and not mod.in_active_profile:
        return "needs review"
    if profile_protected:
        if mod.in_active_profile:
            return "vanilla protected"
        if _is_imported_profile_source(mod):
            return "enable creates profile"
    if mod.in_active_profile:
        return "enabled" if mod.profile_enabled and can_toggle else "disabled" if can_toggle else "protected"
    if _is_imported_profile_source(mod):
        return "toggle adds" if can_toggle else "needs review"
    if mod.state.startswith("candidate"):
        return "import first"
    return "not ready"


def _is_imported_profile_source(mod: PlaceholderMod) -> bool:
    return bool(mod.component_id) and mod.state in {"library", "imported_candidate"}
