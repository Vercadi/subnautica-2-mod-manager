from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ..ui_tokens import UiTokens
from .mod_row import PlaceholderMod, _fit_text


class ModInspector(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        tokens: UiTokens,
        mod: PlaceholderMod,
        ue4ss_policy: dict[str, bool] | None = None,
        on_toggle_ue4ss_policy=None,
        on_preview_deployment=None,
    ):
        colors = tokens.colors
        super().__init__(
            master,
            width=tokens.inspector_width,
            fg_color=colors.glass_black,
            corner_radius=tokens.panel_radius,
            border_width=1,
            border_color=colors.border_cold,
        )
        self.tokens = tokens
        self.mod = mod
        self.ue4ss_policy = dict(ue4ss_policy or {})
        self.on_toggle_ue4ss_policy = on_toggle_ue4ss_policy
        self.on_preview_deployment = on_preview_deployment
        self.title_label: ctk.CTkLabel | None = None
        self.subtitle_label: ctk.CTkLabel | None = None
        self.metadata_labels: dict[str, ctk.CTkLabel] = {}
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build()

    def set_mod(self, mod: PlaceholderMod) -> None:
        self.mod = mod
        for child in self.winfo_children():
            child.destroy()
        self._build()

    def update_mod_summary(self, mod: PlaceholderMod) -> None:
        self.mod = mod
        if self.title_label is not None:
            self.title_label.configure(text=_fit_text(f"{self.mod.name}  *", 42))
        if self.subtitle_label is not None:
            self.subtitle_label.configure(text=_fit_text(f"{self.mod.version}     {_state_label(self.mod)}", 48))
        for label, value in _metadata_values(self.mod):
            widget = self.metadata_labels.get(label)
            if widget is not None:
                widget.configure(text=_fit_text(value, 52))

    def set_ue4ss_policy(self, policy: dict[str, bool]) -> None:
        self.ue4ss_policy = dict(policy or {})
        self.set_mod(self.mod)

    def _build(self) -> None:
        t = self.tokens
        c = t.colors
        self.metadata_labels = {}
        self.title_label = ctk.CTkLabel(
            self,
            text=_fit_text(f"{self.mod.name}  *", 42),
            font=(t.font_family, t.section_title, "bold"),
            text_color=c.text_primary,
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        self.subtitle_label = ctk.CTkLabel(
            self,
            text=_fit_text(f"{self.mod.version}     {_state_label(self.mod)}", 48),
            font=(t.font_family, t.small),
            text_color=c.text_secondary,
            anchor="w",
        )
        self.subtitle_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(2, 10))

        tabs = ctk.CTkTabview(
            self,
            height=260,
            fg_color=c.glass_navy,
            segmented_button_fg_color="#04131E",
            segmented_button_selected_color=c.glass_cyan,
            segmented_button_selected_hover_color=c.panel_glass_hover,
            segmented_button_unselected_color="#04131E",
            segmented_button_unselected_hover_color=c.glass_navy,
            text_color=c.text_primary,
        )
        tabs.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 10))
        for name in ("Info", "Files", "UE4SS"):
            tabs.add(name)

        self._overview(tabs.tab("Info"))
        self._files(tabs.tab("Files"))
        self._ue4ss(tabs.tab("UE4SS"))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 14))
        actions.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            actions,
            text="Preview & Apply Profile",
            height=40,
            fg_color=c.glass_cyan if self.on_preview_deployment else c.disabled,
            hover_color=c.panel_glass_hover if self.on_preview_deployment else c.disabled,
            border_width=1,
            border_color=c.shell_border if self.on_preview_deployment else c.border_soft,
            corner_radius=t.button_radius,
            text_color=c.text_primary if self.on_preview_deployment else c.text_muted,
            font=(t.font_family, t.body, "bold"),
            state="normal" if self.on_preview_deployment else "disabled",
            command=self._preview_apply,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(
            actions,
            text="Managed Profile",
            height=40,
            fg_color=c.glass_navy,
            hover_color=c.glass_navy,
            border_width=1,
            border_color=c.border_soft,
            corner_radius=t.button_radius,
            text_color=c.text_muted,
            font=(t.font_family, t.body, "bold"),
            state="disabled",
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _overview(self, parent) -> None:
        t = self.tokens
        c = t.colors
        ctk.CTkLabel(
            parent,
            text=self.mod.description,
            font=(t.font_family, t.small),
            text_color=c.text_secondary,
            wraplength=max(260, t.inspector_width - 72),
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 8))
        for label, value in _metadata_values(self.mod):
            self.metadata_labels[label] = _metadata_row(parent, self.tokens, label, value)

    def _files(self, parent) -> None:
        self._text_tab(
            parent,
            _files_text(self.mod),
        )

    def _ue4ss(self, parent) -> None:
        t = self.tokens
        c = t.colors
        ctk.CTkLabel(
            parent,
            text="Activation files to update during guarded apply:",
            text_color=c.text_primary,
            font=(t.font_family, t.small, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 4))
        for key, label in (
            ("ue4ss_write_enabled_txt", "Save enabled.txt"),
            ("ue4ss_write_mods_json", "Save mods.json"),
            ("ue4ss_write_mods_txt", "Save mods.txt"),
        ):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                row,
                text=label,
                text_color=c.text_secondary,
                font=(t.font_family, t.small),
                anchor="w",
            ).grid(row=0, column=0, sticky="ew")
            switch = ctk.CTkSwitch(
                row,
                text="",
                width=46,
                progress_color=c.accent_lagoon,
                button_color=c.text_primary,
                fg_color=c.disabled,
                command=lambda value=key: self._toggle_ue4ss_policy(value),
            )
            switch.grid(row=0, column=1, sticky="e")
            if self.ue4ss_policy.get(key, False):
                switch.select()
            else:
                switch.deselect()
        ctk.CTkLabel(
            parent,
            text=_ue4ss_text(self.mod),
            text_color=c.text_muted,
            font=(t.mono_family, t.mono),
            wraplength=max(250, t.inspector_width - 70),
            justify="left",
            anchor="w",
        ).pack(fill="both", expand=True, padx=12, pady=(10, 10))

    def _text_tab(self, parent, text: str) -> None:
        t = self.tokens
        c = t.colors
        box = ctk.CTkTextbox(
            parent,
            fg_color="#04131E",
            text_color=c.text_secondary,
            border_width=1,
            border_color=c.border_soft,
            font=(t.mono_family, t.mono),
            wrap="word",
        )
        box.pack(fill="both", expand=True, padx=10, pady=10)
        box.insert("1.0", text)
        box.configure(state="disabled")

    def _toggle_ue4ss_policy(self, key: str) -> None:
        if not self.on_toggle_ue4ss_policy:
            return
        updated = self.on_toggle_ue4ss_policy(key)
        if isinstance(updated, dict):
            self.ue4ss_policy = dict(updated)

    def _preview_apply(self) -> None:
        if self.on_preview_deployment:
            self.on_preview_deployment()


class _Preview(tk.Canvas):
    def __init__(self, master, *, tokens: UiTokens, color: str):
        self.tokens = tokens
        self.color = color
        super().__init__(master, height=136, highlightthickness=0, bd=0, bg=tokens.colors.glass_black)
        self.bind("<Configure>", self._draw)

    def _draw(self, _event=None) -> None:
        c = self.tokens.colors
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        self.delete("all")
        self.create_rectangle(0, 0, width, height, fill="#051D2D", outline=c.border_soft)
        for offset in range(0, width, 38):
            self.create_line(offset, height, offset + 90, 0, fill=c.shell_border_dim, width=1)
        cx = width // 2
        cy = height // 2
        for radius in (34, 58, 82):
            self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=c.shell_border_dim, width=1)
        self.create_arc(18, 18, width - 18, height + 40, start=35, extent=96, style="arc", outline=self.color, width=2)
        self.create_text(cx, cy - 8, text="MANAGED APPLY", fill=c.text_primary, font=("Segoe UI", 16, "bold"))
        self.create_text(cx, cy + 18, text="PREVIEW FIRST", fill=c.text_muted, font=("Segoe UI", 10, "bold"))


def _files_text(mod: PlaceholderMod) -> str:
    lines = [
        f"Source path: {mod.source_path or 'n/a'}",
        f"Managed path: {mod.managed_path or 'not imported yet'}",
        f"Target hint: {mod.target_hint or 'n/a'}",
        "",
        "Component files:",
    ]
    if mod.files:
        lines.extend(f"- {path}" for path in mod.files)
    else:
        lines.append("- no file details available")
    return "\n".join(lines)


def _ue4ss_text(mod: PlaceholderMod) -> str:
    lines = [
        f"Component type: {mod.component_type or 'unknown'}",
        f"Install kind: {mod.install_kind or 'unknown'}",
        f"Profile: {_profile_status(mod)}",
        "",
        "Notes:",
        "- These toggles persist manager policy only.",
        "- Preview & Apply writes managed activation files only when the plan is not blocked.",
        "- Mod config/settings editing should be added per-file once deployed/imported config shapes are known.",
        "- Root scripts/ folders still require review before layout rewrite.",
        "",
        "Warnings:",
    ]
    warnings = list(mod.dependency_warnings) + list(mod.source_warnings)
    if mod.review_policy_text:
        warnings.insert(0, mod.review_policy_text)
    if mod.profile_warning:
        warnings.insert(0, mod.profile_warning)
    if mod.warning:
        warnings.insert(0, mod.warning)
    if warnings:
        lines.extend(f"- {warning}" for warning in dict.fromkeys(warnings))
    else:
        lines.append("- none")
    return "\n".join(lines)


def _profile_status(mod: PlaceholderMod) -> str:
    if not mod.in_active_profile:
        return "Not in Profile"
    state = "Enabled" if mod.profile_enabled else "Disabled"
    return f"{state} in {mod.profile_name or 'Active Profile'} #{mod.profile_order + 1}"


def _metadata_values(mod: PlaceholderMod) -> tuple[tuple[str, str], ...]:
    return (
        ("State", _state_label(mod)),
        ("Source", mod.source_name or "Placeholder"),
        ("Profile", _profile_status(mod)),
        ("Files", str(mod.file_count or len(mod.files) or "n/a")),
        ("Target", mod.target_hint or "Deployment disabled"),
        ("Plan", mod.deployment_status or "No active plan"),
        ("Component", mod.component_id or mod.name.replace(" ", "_").upper()[:12]),
    )


def _metadata_row(parent, tokens: UiTokens, label: str, value: str) -> ctk.CTkLabel:
    c = tokens.colors
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=2)
    row.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(
        row,
        text=label,
        width=112,
        anchor="w",
        text_color=c.text_secondary,
        font=(tokens.font_family, tokens.tiny, "bold"),
    ).grid(row=0, column=0, sticky="nw")
    value_label = ctk.CTkLabel(
        row,
        text=_fit_text(value, 52),
        anchor="w",
        text_color=c.text_primary,
        font=(tokens.font_family, tokens.tiny),
        wraplength=max(170, tokens.inspector_width - 165),
        justify="left",
    )
    value_label.grid(row=0, column=1, sticky="ew")
    return value_label


def _state_label(mod: PlaceholderMod) -> str:
    if mod.review_policy_text or mod.warning or mod.profile_warning:
        return "Needs Review"
    if mod.in_active_profile:
        return "Enabled" if mod.profile_enabled else "Disabled"
    if mod.state == "library":
        return "Imported"
    if mod.state.startswith("candidate"):
        return "Ready to Import"
    return mod.state.replace("_", " ").title()
