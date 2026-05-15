from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorTokens:
    bg_abyss: str = "#03101A"
    bg_trench: str = "#061722"
    panel_deep: str = "#09222D"
    panel_glass: str = "#0D3444"
    panel_glass_hover: str = "#143E4B"
    border_cold: str = "#2A6170"
    border_soft: str = "#123A49"
    text_primary: str = "#E7F8F8"
    text_secondary: str = "#A9CDD0"
    text_muted: str = "#6F969C"
    accent_lagoon: str = "#38D6D6"
    accent_biolume: str = "#7CF7C8"
    accent_coral: str = "#FF7A59"
    accent_pressure: str = "#FFD166"
    accent_kelp: str = "#67D38A"
    danger: str = "#FF5E6C"
    warning: str = "#FFD166"
    success: str = "#67D38A"
    disabled: str = "#355862"
    shadow: str = "#02080B"
    shell_border: str = "#1AC9F4"
    shell_border_dim: str = "#0B5570"
    glass_black: str = "#020B13"
    glass_navy: str = "#061A29"
    glass_cyan: str = "#08384B"
    chip_blue: str = "#154D78"
    chip_purple: str = "#4A3B84"
    chip_green: str = "#0D5E4C"
    chip_orange: str = "#7A4312"


@dataclass(frozen=True)
class UiTokens:
    colors: ColorTokens
    font_family: str
    mono_family: str
    page_title: int
    section_title: int
    panel_title: int
    row_title: int
    body: int
    small: int
    tiny: int
    mono: int
    shell_radius: int
    panel_radius: int
    row_radius: int
    button_radius: int
    outer_margin: int
    panel_gap: int
    row_gap: int
    nav_width: int
    inspector_width: int
    bottom_strip_height: int
    top_bar_height: int


def ui_tokens_for_size(size_name: str = "default") -> UiTokens:
    size = (size_name or "default").strip().lower()
    colors = ColorTokens()

    if size == "compact":
        return UiTokens(
            colors=colors,
            font_family="Segoe UI",
            mono_family="Cascadia Mono",
            page_title=20,
            section_title=13,
            panel_title=12,
            row_title=11,
            body=11,
            small=10,
            tiny=9,
            mono=10,
            shell_radius=10,
            panel_radius=7,
            row_radius=5,
            button_radius=5,
            outer_margin=12,
            panel_gap=8,
            row_gap=5,
            nav_width=184,
            inspector_width=350,
            bottom_strip_height=130,
            top_bar_height=64,
        )

    if size == "large":
        return UiTokens(
            colors=colors,
            font_family="Segoe UI",
            mono_family="Cascadia Mono",
            page_title=26,
            section_title=17,
            panel_title=15,
            row_title=14,
            body=14,
            small=12,
            tiny=11,
            mono=12,
            shell_radius=12,
            panel_radius=9,
            row_radius=6,
            button_radius=6,
            outer_margin=18,
            panel_gap=14,
            row_gap=8,
            nav_width=240,
            inspector_width=430,
            bottom_strip_height=160,
            top_bar_height=80,
        )

    return UiTokens(
        colors=colors,
        font_family="Segoe UI",
        mono_family="Cascadia Mono",
        page_title=22,
        section_title=15,
        panel_title=13,
        row_title=12,
        body=12,
        small=11,
        tiny=10,
        mono=11,
        shell_radius=10,
        panel_radius=8,
        row_radius=5,
        button_radius=5,
        outer_margin=16,
        panel_gap=12,
        row_gap=6,
            nav_width=205,
            inspector_width=388,
        bottom_strip_height=145,
        top_bar_height=72,
    )
