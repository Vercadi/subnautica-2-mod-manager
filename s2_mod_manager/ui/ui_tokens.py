from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColorTokens:
    bg_abyss: str = "#031018"
    bg_trench: str = "#071D28"
    panel_deep: str = "#082735"
    panel_glass: str = "#113F4B"
    panel_glass_hover: str = "#185263"
    border_cold: str = "#3B8BA0"
    border_soft: str = "#164756"
    text_primary: str = "#E9FBFC"
    text_secondary: str = "#AEE7EE"
    text_muted: str = "#72A9B4"
    accent_lagoon: str = "#86EDFF"
    accent_biolume: str = "#60F0C8"
    accent_coral: str = "#FF7A59"
    accent_pressure: str = "#F2B26B"
    accent_kelp: str = "#6FEA96"
    active_amber: str = "#76543C"
    active_amber_hover: str = "#95674A"
    limited_red: str = "#E35B55"
    danger: str = "#F66D72"
    warning: str = "#F2B26B"
    success: str = "#6FEA96"
    disabled: str = "#34545B"
    shadow: str = "#02080B"
    shell_border: str = "#82E9FA"
    shell_border_dim: str = "#1E6E82"
    glass_black: str = "#031019"
    glass_navy: str = "#082231"
    glass_cyan: str = "#0B4452"
    chip_blue: str = "#145A77"
    chip_purple: str = "#3F427E"
    chip_green: str = "#0A664E"
    chip_orange: str = "#795139"
    pda_grid: str = "#19566A"


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
            button_radius=12,
            outer_margin=12,
            panel_gap=8,
            row_gap=5,
            nav_width=184,
            inspector_width=320,
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
            button_radius=14,
            outer_margin=18,
            panel_gap=14,
            row_gap=8,
            nav_width=240,
            inspector_width=380,
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
        button_radius=13,
        outer_margin=16,
        panel_gap=12,
        row_gap=6,
            nav_width=205,
        inspector_width=340,
        bottom_strip_height=145,
        top_bar_height=72,
    )
