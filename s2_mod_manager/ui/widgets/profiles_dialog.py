from __future__ import annotations

import customtkinter as ctk

from ...models.profile import ModProfile
from ..ui_tokens import UiTokens
from ..window_utils import configure_dialog, prompt_dialog
from .mod_row import _fit_text


class ProfilesDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        *,
        tokens: UiTokens,
        get_profiles,
        get_active_profile,
        on_select,
        on_create,
        on_duplicate,
        on_rename,
        on_delete,
    ):
        super().__init__(master)
        self.tokens = tokens
        self.get_profiles = get_profiles
        self.get_active_profile = get_active_profile
        self.on_select = on_select
        self.on_create = on_create
        self.on_duplicate = on_duplicate
        self.on_rename = on_rename
        self.on_delete = on_delete
        self.body: ctk.CTkScrollableFrame | None = None
        self.result_label: ctk.CTkLabel | None = None
        self.title("Profiles")
        self.configure(fg_color=tokens.colors.bg_abyss)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        configure_dialog(self, master, width=780, height=580, min_width=680, min_height=460, modal=True, topmost=True)

    def _build(self) -> None:
        t = self.tokens
        c = t.colors
        header = ctk.CTkFrame(
            self,
            fg_color=c.glass_black,
            corner_radius=t.panel_radius,
            border_width=1,
            border_color=c.shell_border_dim,
        )
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        ctk.CTkLabel(
            header,
            text="Profiles",
            text_color=c.text_primary,
            font=(t.font_family, t.section_title, "bold"),
        ).pack(anchor="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(
            header,
            text="Choose which manager-side profile is active. Profile switches do not write to the game install.",
            text_color=c.text_secondary,
            font=(t.font_family, t.small),
        ).pack(anchor="w", padx=14, pady=(0, 10))

        self.body = ctk.CTkScrollableFrame(
            self,
            fg_color=c.glass_black,
            corner_radius=t.panel_radius,
            border_width=1,
            border_color=c.border_soft,
            scrollbar_button_color=c.glass_cyan,
            scrollbar_button_hover_color=c.panel_glass_hover,
        )
        self.body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 10))
        self.body.grid_columnconfigure(0, weight=1)
        self._populate_profiles()

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        footer.grid_columnconfigure(0, weight=1)
        self.result_label = ctk.CTkLabel(
            footer,
            text=f"Active profile: {self.get_active_profile().name}",
            text_color=c.text_muted,
            font=(t.font_family, t.small),
            anchor="w",
        )
        self.result_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        for column, (text, command, width) in enumerate(
            (
                ("New", self._create_clicked, 72),
                ("Copy Active", self._duplicate_clicked, 104),
                ("Rename", self._rename_clicked, 86),
                ("Delete", self._delete_clicked, 82),
                ("Close", self.destroy, 86),
            ),
            start=1,
        ):
            ctk.CTkButton(
                footer,
                text=text,
                width=width,
                height=34,
                fg_color=c.glass_navy,
                hover_color=c.panel_glass,
                border_width=1,
                border_color=c.border_cold,
                text_color=c.text_secondary,
                command=command,
            ).grid(row=0, column=column, padx=(0, 8 if text != "Close" else 0))

    def _populate_profiles(self) -> None:
        if self.body is None:
            return
        for child in self.body.winfo_children():
            child.destroy()
        active = self.get_active_profile()
        profiles = list(self.get_profiles())
        if not profiles:
            ctk.CTkLabel(
                self.body,
                text="No profiles found.",
                text_color=self.tokens.colors.text_muted,
                font=(self.tokens.font_family, self.tokens.small),
            ).grid(row=0, column=0, sticky="w", padx=12, pady=12)
            return
        for index, profile in enumerate(profiles):
            self._profile_row(profile, active.profile_id).grid(row=index, column=0, sticky="ew", padx=8, pady=6)

    def _profile_row(self, profile: ModProfile, active_profile_id: str) -> ctk.CTkFrame:
        t = self.tokens
        c = t.colors
        active = profile.profile_id == active_profile_id
        frame = ctk.CTkFrame(
            self.body,
            fg_color=c.glass_cyan if active else c.glass_navy,
            corner_radius=t.row_radius,
            border_width=1,
            border_color=c.shell_border if active else c.border_soft,
        )
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            frame,
            text="ACTIVE" if active else "",
            width=60,
            text_color=c.accent_biolume if active else c.text_muted,
            font=(t.font_family, t.tiny, "bold"),
        ).grid(row=0, column=0, rowspan=2, sticky="w", padx=10, pady=8)
        ctk.CTkLabel(
            frame,
            text=_fit_text(profile.name, 52),
            text_color=c.text_primary,
            font=(t.font_family, t.body, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(8, 0))
        mode = "protected vanilla baseline" if profile.protected else "editable"
        ctk.CTkLabel(
            frame,
            text=f"{mode} | {len(profile.entries)} component(s)",
            text_color=c.text_secondary,
            font=(t.font_family, t.tiny),
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(0, 8))
        ctk.CTkButton(
            frame,
            text="Use",
            width=76,
            height=30,
            fg_color=c.disabled if active else c.glass_black,
            hover_color=c.disabled if active else c.panel_glass,
            border_width=1,
            border_color=c.border_soft if active else c.border_cold,
            text_color=c.text_muted if active else c.text_secondary,
            state="disabled" if active else "normal",
            command=lambda name=profile.name: self._select_profile(name),
        ).grid(row=0, column=2, rowspan=2, sticky="e", padx=10, pady=8)
        return frame

    def _select_profile(self, name: str) -> None:
        self.on_select(name)
        self._refresh(f"Active profile: {self.get_active_profile().name}")

    def _create_clicked(self) -> None:
        name = prompt_dialog(self, tokens=self.tokens, title="New Profile", message="Profile name:")
        if not name:
            return
        self.on_create(name)
        self._refresh(f"Created profile: {self.get_active_profile().name}")

    def _duplicate_clicked(self) -> None:
        name = prompt_dialog(self, tokens=self.tokens, title="Copy Profile", message="New profile name:")
        if not name:
            return
        self.on_duplicate(name)
        self._refresh(f"Copied active profile: {self.get_active_profile().name}")

    def _rename_clicked(self) -> None:
        active = self.get_active_profile()
        name = prompt_dialog(self, tokens=self.tokens, title="Rename Profile", message="Profile name:", initial_value=active.name)
        if not name:
            return
        self.on_rename(name)
        self._refresh(f"Active profile: {self.get_active_profile().name}")

    def _delete_clicked(self) -> None:
        active = self.get_active_profile()
        self.on_delete()
        current = self.get_active_profile()
        status = "Delete refused for protected profile." if current.profile_id == active.profile_id else f"Deleted profile: {active.name}"
        self._refresh(status)

    def _refresh(self, message: str) -> None:
        self._populate_profiles()
        if self.result_label is not None:
            self.result_label.configure(text=message, text_color=self.tokens.colors.accent_biolume)
