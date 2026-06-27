from __future__ import annotations

import ctypes
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable


BG = "#eef6ff"
BAR = "#dcebfa"
PANEL = "#f6fbff"
FIELD = "#fbfdff"
TEXT = "#183452"
MUTED = "#5f7894"
GREEN = "#6da9e8"
BROWN = "#8dbdea"
BLUE = "#6da9e8"
RED = "#6d95c4"
LINE = "#bfd6ee"
SELECTED = "#d8ecff"
BUTTON_TEXT = "#ffffff"

THEME_PALETTES = {
    "蓝色": {
        "bg": "#eef6ff",
        "bar": "#dcebfa",
        "panel": "#f6fbff",
        "field": "#fbfdff",
        "text": "#183452",
        "muted": "#5f7894",
        "line": "#bfd6ee",
        "selected": "#d8ecff",
        "button": "#6da9e8",
        "button_active": "#3f82c8",
        "button_disabled": "#bfd8f3",
        "button_soft": "#d8ecff",
        "button_text": "#ffffff",
    },
    "薄荷": {
        "bg": "#effaf5",
        "bar": "#d9f0e8",
        "panel": "#f7fcfa",
        "field": "#fcfffd",
        "text": "#1e3f37",
        "muted": "#63877d",
        "line": "#bfe0d5",
        "selected": "#d9f3eb",
        "button": "#72bda5",
        "button_active": "#46957d",
        "button_disabled": "#bee0d5",
        "button_soft": "#d9f3eb",
        "button_text": "#ffffff",
    },
    "紫色": {
        "bg": "#f5f2ff",
        "bar": "#e5def7",
        "panel": "#fbf9ff",
        "field": "#fefcff",
        "text": "#332950",
        "muted": "#746994",
        "line": "#cfc3ee",
        "selected": "#e8e0fb",
        "button": "#9b83d4",
        "button_active": "#7660b5",
        "button_disabled": "#cfc3ee",
        "button_soft": "#e8e0fb",
        "button_text": "#ffffff",
    },
    "粉色": {
        "bg": "#fff2f6",
        "bar": "#f8dde7",
        "panel": "#fff9fb",
        "field": "#fffdfd",
        "text": "#512838",
        "muted": "#956b7a",
        "line": "#efc2d2",
        "selected": "#fbe0ea",
        "button": "#d985a2",
        "button_active": "#bb5f80",
        "button_disabled": "#efc2d2",
        "button_soft": "#fbe0ea",
        "button_text": "#ffffff",
    },
    "米杏": {
        "bg": "#fff8ed",
        "bar": "#f2e1c8",
        "panel": "#fffdf8",
        "field": "#fffefa",
        "text": "#4a3422",
        "muted": "#8a745d",
        "line": "#dfc7a9",
        "selected": "#f8e9d3",
        "button": "#c7985b",
        "button_active": "#a8793f",
        "button_disabled": "#dfc7a9",
        "button_soft": "#f8e9d3",
        "button_text": "#ffffff",
    },
}

FONT_UI = ("微软雅黑", 10)
FONT_UI_BOLD = ("微软雅黑", 10, "bold")
FONT_BUTTON = ("微软雅黑", 11, "bold")
FONT_SMALL = ("微软雅黑", 10)
FONT_SECTION = ("微软雅黑", 11, "bold")
FONT_TABLE = ("Microsoft YaHei UI", 10)
FONT_RULE_BUTTON = ("微软雅黑", 9, "bold")
FONT_TOGGLE_SMALL = ("微软雅黑", 9, "bold")

ACTION_BUTTON_WIDTH = 170
ACTION_BUTTON_HEIGHT = 71
EXECUTE_BUTTON_WIDTH = 206
TOGGLE_BUTTON_WIDTH = 150
TOGGLE_BUTTON_HEIGHT = 38
RULE_TYPE_ROW_CHAR_LIMIT = 12
RULE_TYPE_BUTTON_MIN_WIDTH = 100
RULE_TYPE_BUTTON_CHAR_WIDTH = 22
RULE_TYPE_BUTTON_PADDING = 44
RULE_TYPE_BUTTON_HEIGHT = 36
BUTTON_RADIUS = 22

STATUS_READY = "待重命名"
STATUS_NEED_RULE = "待设置规则"
CHECKED = "☑"
UNCHECKED = "☐"
PAGE_SIZES = {
    "small": (900, 600),
    "medium": (1000, 680),
    "large": (1200, 800),
}


def rule_label_length(label: str) -> int:
    return len(label)


def rule_type_button_width(label: str) -> int:
    return max(RULE_TYPE_BUTTON_MIN_WIDTH, rule_label_length(label) * RULE_TYPE_BUTTON_CHAR_WIDTH + RULE_TYPE_BUTTON_PADDING)


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


SETTINGS_FILE = app_base_dir() / "settings.json"

RULE_LABELS = {
    "delete": "删除词组",
    "replace": "替换词组",
    "insert": "固定位置添加",
    "sequence": "名称加序号",
    "case": "大小写转换",
    "increment": "编号+1",
    "pad": "编号补零",
}
LABEL_TO_RULE = {label: key for key, label in RULE_LABELS.items()}
INSERT_POSITIONS = ("开头", "结尾", "指定位置")
DELETE_MODES = (
    "词组",
    "从分隔符后删除",
    "条件删除后缀",
    "条件删除前缀",
    "删除首尾数字段",
    "删除括号内容",
    "清理多余符号",
    "删除首尾指定字符",
)
DELETE_OPTIONAL_TEXT_MODES = {"删除括号内容", "清理多余符号"}
CASE_MODES = ("小写", "大写", "首字母大写", "单词首字母大写")


@dataclass(frozen=True)
class RenamePlan:
    path: Path
    new_name: str
    status: str

    @property
    def new_path(self) -> Path:
        return self.path.with_name(self.new_name)


@dataclass
class RuleConfig:
    name: str = "未命名规则"
    kind: str = "delete"
    text: str = ""
    delete_mode: str = "词组"
    replacement: str = ""
    insert_position: str = "结尾"
    insert_index: int = 0
    sequence_prefix: str = "文件"
    sequence_start: int = 1
    sequence_digits: int = 3
    sequence_separator: str = "_"
    case_mode: str = "小写"


def split_phrases(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def clamp_index(index: int, length: int) -> int:
    return max(0, min(index, length))


def parse_int(value: str, default: int, minimum: int = 0) -> int:
    try:
        return max(minimum, int(value))
    except ValueError:
        return default


def parse_replacements(text: str, fallback_replacement: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in split_phrases(text):
        if "=>" in line:
            old, new = line.split("=>", 1)
        elif "=" in line:
            old, new = line.split("=", 1)
        else:
            old, new = line, fallback_replacement

        old = old.strip()
        if old:
            pairs.append((old, new.strip()))
    return pairs


def parse_conditional_suffix_rules(text: str) -> list[tuple[str, str]]:
    rules: list[tuple[str, str]] = []
    for line in split_phrases(text):
        if "=>" in line:
            marker, required = line.split("=>", 1)
        elif "=" in line:
            marker, required = line.split("=", 1)
        else:
            marker, required = line, ""

        marker = marker.strip()
        if marker:
            rules.append((marker, required.strip()))
    return rules


def remove_conditional_suffix(stem: str, rules: list[tuple[str, str]]) -> str:
    matched_index = -1
    for marker, required in rules:
        search_end = len(stem)
        while True:
            index = stem.rfind(marker, 0, search_end)
            if index < 0:
                break

            tail = stem[index + len(marker):]
            if not required or required in tail:
                matched_index = max(matched_index, index)
                break

            search_end = index

    if matched_index >= 0:
        return stem[:matched_index]
    return stem


def remove_conditional_prefix(stem: str, rules: list[tuple[str, str]]) -> str:
    matched_end = -1
    for marker, required in rules:
        search_start = 0
        while True:
            index = stem.find(marker, search_start)
            if index < 0:
                break

            head = stem[:index]
            if not required or required in head:
                matched_end = max(matched_end, index + len(marker))
                break

            search_start = index + len(marker)

    if matched_end >= 0:
        return stem[matched_end:]
    return stem


def remove_edge_number_parts(stem: str, separators: list[str]) -> str:
    for separator in separators:
        if not separator:
            continue

        parts = stem.split(separator)
        while parts and (not parts[0] or parts[0].isdigit()):
            parts.pop(0)
        while parts and (not parts[-1] or parts[-1].isdigit()):
            parts.pop()
        stem = separator.join(parts)

    return stem


def parse_bracket_pairs(text: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in split_phrases(text):
        if "=>" in line:
            left, right = line.split("=>", 1)
        elif len(line) >= 2:
            left, right = line[0], line[-1]
        else:
            continue

        left = left.strip()
        right = right.strip()
        if left and right:
            pairs.append((left, right))

    return pairs or [("[", "]"), ("(", ")"), ("（", "）"), ("【", "】"), ("{", "}")]


def remove_bracket_contents(stem: str, pairs: list[tuple[str, str]]) -> str:
    for left, right in pairs:
        while True:
            start = stem.find(left)
            if start < 0:
                break

            end = stem.find(right, start + len(left))
            if end < 0:
                break

            stem = stem[:start] + stem[end + len(right):]

    return stem.strip()


def clean_extra_symbols(stem: str, symbols: list[str]) -> str:
    symbols = symbols or ["_", "-", " ", ".", "·"]
    for symbol in symbols:
        if not symbol:
            continue

        if symbol.isspace():
            stem = re.sub(r"\s+", " ", stem).strip()
            continue

        repeated = re.escape(symbol) + r"{2,}"
        stem = re.sub(repeated, symbol, stem)
        if symbol in {"_", "-", "."}:
            stem = re.sub(rf"\s*{re.escape(symbol)}\s*", symbol, stem)

    strip_chars = "".join(symbols) + " "
    return stem.strip(strip_chars)


def strip_edge_chars(stem: str, text: str) -> str:
    chars = "".join(split_phrases(text))
    return stem.strip(chars) if chars else stem


def apply_case_mode(stem: str, mode: str) -> str:
    if mode == "大写":
        return stem.upper()
    if mode == "首字母大写":
        return stem[:1].upper() + stem[1:].lower()
    if mode == "单词首字母大写":
        return re.sub(r"[\w\u4e00-\u9fff]+", lambda match: match.group(0)[:1].upper() + match.group(0)[1:].lower(), stem)
    return stem.lower()


def increment_last_number(stem: str) -> str:
    match = re.search(r"(\d+)$", stem)
    if not match:
        return stem

    number = match.group(1)
    incremented = str(int(number) + 1).zfill(len(number))
    return f"{stem[:match.start()]}{incremented}{stem[match.end():]}"


def pad_leading_number(stem: str, digits: int) -> str:
    match = re.match(r"(\d+)", stem)
    if not match:
        return stem

    number = match.group(1)
    padded = number.zfill(digits)
    return f"{padded}{stem[match.end():]}"


def apply_rule_to_name(path: Path, rule: RuleConfig, sequence_number: int) -> str:
    stem = path.stem

    if rule.kind == "delete":
        if rule.delete_mode == "从分隔符后删除":
            for marker in split_phrases(rule.text):
                index = stem.rfind(marker)
                if index >= 0:
                    stem = stem[:index]
        elif rule.delete_mode == "条件删除后缀":
            stem = remove_conditional_suffix(stem, parse_conditional_suffix_rules(rule.text))
        elif rule.delete_mode == "条件删除前缀":
            stem = remove_conditional_prefix(stem, parse_conditional_suffix_rules(rule.text))
        elif rule.delete_mode == "删除首尾数字段":
            stem = remove_edge_number_parts(stem, split_phrases(rule.text))
        elif rule.delete_mode == "删除括号内容":
            stem = remove_bracket_contents(stem, parse_bracket_pairs(rule.text))
        elif rule.delete_mode == "清理多余符号":
            stem = clean_extra_symbols(stem, split_phrases(rule.text))
        elif rule.delete_mode == "删除首尾指定字符":
            stem = strip_edge_chars(stem, rule.text)
        else:
            for phrase in split_phrases(rule.text):
                stem = stem.replace(phrase, "")
    elif rule.kind == "replace":
        for old, new in parse_replacements(rule.text, rule.replacement):
            stem = stem.replace(old, new)
    elif rule.kind == "insert":
        insert_text = rule.text.strip()
        if rule.insert_position == "开头":
            stem = f"{insert_text}{stem}"
        elif rule.insert_position == "指定位置":
            index = clamp_index(rule.insert_index, len(stem))
            stem = f"{stem[:index]}{insert_text}{stem[index:]}"
        else:
            stem = f"{stem}{insert_text}"
    elif rule.kind == "sequence":
        number = str(sequence_number).zfill(rule.sequence_digits)
        prefix = rule.sequence_prefix.strip()
        stem = f"{prefix}{rule.sequence_separator}{number}" if prefix else number
    elif rule.kind == "case":
        stem = apply_case_mode(stem, rule.case_mode)
    elif rule.kind == "increment":
        stem = increment_last_number(stem)
    elif rule.kind == "pad":
        stem = pad_leading_number(stem, rule.sequence_digits)

    return f"{stem}{path.suffix}"


def is_rule_ready(rule: RuleConfig) -> bool:
    if rule.kind == "delete" and rule.delete_mode in DELETE_OPTIONAL_TEXT_MODES:
        return True
    if rule.kind in {"delete", "insert"}:
        return bool(rule.text.strip())
    if rule.kind == "replace":
        return bool(parse_replacements(rule.text, rule.replacement))
    if rule.kind == "sequence":
        return True
    if rule.kind == "case":
        return True
    if rule.kind == "increment":
        return True
    if rule.kind == "pad":
        return True
    return False


def build_rename_plan(directory: Path, rule: RuleConfig, recursive: bool) -> list[RenamePlan]:
    files = collect_files(directory, recursive)
    target_counts: dict[Path, int] = {}
    candidates: dict[Path, Path] = {}

    for index, path in enumerate(files, start=rule.sequence_start):
        new_name = apply_rule_to_name(path, rule, index)
        if new_name != path.name:
            new_path = path.with_name(new_name)
            target_counts[new_path] = target_counts.get(new_path, 0) + 1

    for index, path in enumerate(files, start=rule.sequence_start):
        new_name = apply_rule_to_name(path, rule, index)
        new_path = path.with_name(new_name)
        if new_name != path.name and Path(new_name).name and new_name != path.suffix and target_counts.get(new_path, 0) <= 1:
            candidates[path] = new_path

    while True:
        moving_sources = set(candidates)
        blocked = [
            path
            for path, new_path in candidates.items()
            if new_path.exists() and new_path not in moving_sources
        ]
        if not blocked:
            break
        for path in blocked:
            candidates.pop(path, None)

    plans: list[RenamePlan] = []
    for index, path in enumerate(files, start=rule.sequence_start):
        new_name = apply_rule_to_name(path, rule, index)
        new_path = path.with_name(new_name)

        if new_name == path.name:
            status = "未变化"
        elif not Path(new_name).name or new_name == path.suffix:
            status = "跳过：文件名为空"
        elif target_counts.get(new_path, 0) > 1:
            status = "跳过：目标重名"
        elif path not in candidates:
            status = "跳过：目标已存在"
        else:
            status = STATUS_READY

        plans.append(RenamePlan(path=path, new_name=new_name, status=status))

    return plans


def collect_files(directory: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    return sorted((path for path in directory.glob(pattern) if path.is_file()), key=lambda item: str(item).lower())


def unique_temp_path(path: Path, index: int) -> Path:
    token = f".__rename_tmp__{os.getpid()}_{index}_{path.name}"
    candidate = path.with_name(token)
    counter = 1
    while candidate.exists():
        candidate = path.with_name(f"{token}_{counter}")
        counter += 1
    return candidate


def enable_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def get_screen_size(root: tk.Tk) -> tuple[int, int]:
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    try:
        width = max(width, ctypes.windll.user32.GetSystemMetrics(0))
        height = max(height, ctypes.windll.user32.GetSystemMetrics(1))
    except Exception:
        pass
    return width, height


def detect_layout_scale(root: tk.Tk) -> float:
    try:
        dpi_scale = float(root.tk.call("tk", "scaling")) / (96 / 72)
    except Exception:
        dpi_scale = 1.0

    screen_width, screen_height = get_screen_size(root)
    dpi_ratio = max(1.0, dpi_scale / 1.25)
    resolution_ratio = max(1.0, min(screen_width / 2560, screen_height / 1440))
    return min(1.8, dpi_ratio, resolution_ratio)


def scaled_window_size(root: tk.Tk, page: str = "large", max_screen_ratio: float = 0.9) -> tuple[int, int, float]:
    scale = detect_layout_scale(root)
    base_width, base_height = PAGE_SIZES[page]
    screen_width, screen_height = get_screen_size(root)
    width = min(round(base_width * scale), round(screen_width * max_screen_ratio))
    height = min(round(base_height * scale), round(screen_height * max_screen_ratio))
    return width, height, scale


def rounded_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs: object) -> int:
    points = [
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        master: tk.Widget,
        text: str,
        command: Callable[[], None] | None,
        width: int,
        height: int,
        fill: str,
        active_fill: str,
        disabled_fill: str,
        text_color: str = BUTTON_TEXT,
        disabled_text_color: str = "#f2f2ea",
        bg: str = BAR,
    ) -> None:
        super().__init__(master, width=width, height=height, bg=bg, bd=0, highlightthickness=0)
        self.command = command
        self.fill = fill
        self.active_fill = active_fill
        self.disabled_fill = disabled_fill
        self.text_color = text_color
        self.disabled_text_color = disabled_text_color
        self.enabled = True
        self.current_fill = fill
        self.rect = rounded_rect(self, 0, 0, width, height, BUTTON_RADIUS, fill=fill, outline=fill)
        self.label = self.create_text(width // 2, height // 2, text=text, fill=text_color, font=FONT_BUTTON)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.configure(cursor="hand2")

    def _paint(self, fill: str, text_color: str | None = None) -> None:
        self.itemconfigure(self.rect, fill=fill, outline=fill)
        self.itemconfigure(self.label, fill=text_color or self.text_color)
        self.current_fill = fill

    def _on_enter(self, _event: tk.Event[tk.Canvas]) -> None:
        if self.enabled:
            self._paint(self.active_fill)

    def _on_leave(self, _event: tk.Event[tk.Canvas]) -> None:
        if self.enabled:
            self._paint(self.fill)

    def _on_press(self, _event: tk.Event[tk.Canvas]) -> None:
        if self.enabled:
            self._paint(self.active_fill)

    def _on_release(self, event: tk.Event[tk.Canvas]) -> None:
        if not self.enabled:
            return

        inside = 0 <= event.x <= int(self["width"]) and 0 <= event.y <= int(self["height"])
        self._paint(self.active_fill if inside else self.fill)
        if inside and self.command:
            self.command()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if enabled:
            self.configure(cursor="hand2")
            self._paint(self.fill)
        else:
            self.configure(cursor="")
            self._paint(self.disabled_fill, self.disabled_text_color)

    def state(self, states: list[str]) -> None:
        if "disabled" in states:
            self.set_enabled(False)
        elif "!disabled" in states:
            self.set_enabled(True)

    def set_colors(
        self,
        fill: str,
        active_fill: str,
        disabled_fill: str,
        text_color: str,
        disabled_text_color: str,
        bg: str,
    ) -> None:
        self.fill = fill
        self.active_fill = active_fill
        self.disabled_fill = disabled_fill
        self.text_color = text_color
        self.disabled_text_color = disabled_text_color
        self.configure(bg=bg)
        self._paint(self.fill if self.enabled else self.disabled_fill, self.text_color if self.enabled else self.disabled_text_color)


class RoundedToggle(tk.Canvas):
    def __init__(
        self,
        master: tk.Widget,
        text: str,
        command: Callable[[], None],
        width: int,
        height: int,
        bg: str = PANEL,
        font: tuple[str, int] | tuple[str, int, str] = FONT_UI_BOLD,
    ) -> None:
        super().__init__(master, width=width, height=height, bg=bg, bd=0, highlightthickness=0)
        self.command = command
        self.selected = False
        self.selected_fill = GREEN
        self.unselected_fill = "#d8dfd1"
        self.text_color = TEXT
        self.selected_text_color = BUTTON_TEXT
        self.rect = rounded_rect(self, 0, 0, width, height, BUTTON_RADIUS, fill=self.unselected_fill, outline=self.unselected_fill)
        self.label = self.create_text(width // 2, height // 2, text=text, fill=self.text_color, font=font)
        self.bind("<Button-1>", self._on_click)
        self.configure(cursor="hand2")

    def _on_click(self, _event: tk.Event[tk.Canvas]) -> None:
        self.command()

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        fill = self.selected_fill if selected else self.unselected_fill
        text_color = self.selected_text_color if selected else self.text_color
        self.itemconfigure(self.rect, fill=fill, outline=fill)
        self.itemconfigure(self.label, fill=text_color)

    def set_colors(
        self,
        selected_fill: str,
        unselected_fill: str,
        text_color: str,
        selected_text_color: str,
        bg: str,
    ) -> None:
        self.selected_fill = selected_fill
        self.unselected_fill = unselected_fill
        self.text_color = text_color
        self.selected_text_color = selected_text_color
        self.configure(bg=bg)
        self.set_selected(self.selected)


class RuleTypeButton(tk.Canvas):
    def __init__(
        self,
        master: tk.Widget,
        text: str,
        command: Callable[[], None],
        width: int,
        height: int = RULE_TYPE_BUTTON_HEIGHT,
        bg: str = PANEL,
    ) -> None:
        super().__init__(master, width=width, height=height, bg=bg, bd=0, highlightthickness=0)
        self.command = command
        self.selected = False
        self.selected_fill = GREEN
        self.unselected_fill = "#d8ecff"
        self.text_color = TEXT
        self.selected_text_color = BUTTON_TEXT
        self.rect = rounded_rect(self, 0, 0, width, height, 14, fill=self.unselected_fill, outline=self.unselected_fill)
        self.label = self.create_text(width // 2, height // 2, text=text, fill=self.text_color, font=FONT_RULE_BUTTON)
        self.bind("<Button-1>", self._on_click)
        self.configure(cursor="hand2")

    def _on_click(self, _event: tk.Event[tk.Canvas]) -> None:
        self.command()

    def set_selected(self, selected: bool) -> None:
        self.selected = selected
        fill = self.selected_fill if selected else self.unselected_fill
        text_color = self.selected_text_color if selected else self.text_color
        self.itemconfigure(self.rect, fill=fill, outline=fill)
        self.itemconfigure(self.label, fill=text_color)

    def set_colors(
        self,
        selected_fill: str,
        unselected_fill: str,
        text_color: str,
        selected_text_color: str,
        bg: str,
    ) -> None:
        self.selected_fill = selected_fill
        self.unselected_fill = unselected_fill
        self.text_color = text_color
        self.selected_text_color = selected_text_color
        self.configure(bg=bg)
        self.set_selected(self.selected)


def palette_for(name: str) -> dict[str, str]:
    return THEME_PALETTES.get(name, THEME_PALETTES["蓝色"])


def apply_theme(root: tk.Tk, palette: dict[str, str]) -> None:
    root.configure(bg=palette["bg"])
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", font=FONT_UI, background=palette["bg"], foreground=palette["text"])
    style.configure("TFrame", background=palette["bg"])
    style.configure("Toolbar.TFrame", background=palette["bar"])
    style.configure("Panel.TFrame", background=palette["panel"])
    style.configure("Status.TFrame", background=palette["bar"])
    style.configure("TLabel", background=palette["bg"], foreground=palette["text"])
    style.configure("Toolbar.TLabel", background=palette["bar"], foreground=palette["text"], font=FONT_UI_BOLD)
    style.configure("Panel.TLabel", background=palette["panel"], foreground=palette["text"])
    style.configure("Section.TLabel", background=palette["panel"], foreground=palette["text"], font=FONT_SECTION)
    style.configure("Status.TLabel", background=palette["bar"], foreground=palette["muted"], font=FONT_SMALL)
    style.configure(
        "TEntry",
        fieldbackground=palette["field"],
        background=palette["field"],
        foreground=palette["text"],
        bordercolor=palette["line"],
        lightcolor=palette["line"],
        darkcolor=palette["line"],
        padding=(8, 5),
    )
    style.configure("TCombobox", fieldbackground=palette["field"], background=palette["field"], foreground=palette["text"], padding=(8, 5))
    style.configure("TCheckbutton", background=palette["panel"], foreground=palette["text"], font=FONT_UI)
    style.map("TCheckbutton", background=[("active", palette["panel"])])
    style.configure("TButton", font=FONT_BUTTON, padding=(12, 15), borderwidth=0, relief="flat")
    style.configure("Blue.TButton", background=palette["button"], foreground=palette["button_text"])
    style.configure("Brown.TButton", background=palette["button"], foreground=palette["button_text"])
    style.configure("Green.TButton", background=palette["button"], foreground=palette["button_text"])
    style.map(
        "Blue.TButton",
        background=[("disabled", palette["button_disabled"]), ("active", palette["button_active"])],
        foreground=[("disabled", "#f2f2ea")],
    )
    style.map(
        "Brown.TButton",
        background=[("disabled", palette["button_disabled"]), ("active", palette["button_active"])],
        foreground=[("disabled", "#f2f2ea")],
    )
    style.map(
        "Green.TButton",
        background=[("disabled", palette["button_disabled"]), ("active", palette["button_active"])],
        foreground=[("disabled", "#f2f2ea")],
    )
    style.configure(
        "Treeview",
        background=palette["field"],
        fieldbackground=palette["field"],
        foreground=palette["text"],
        rowheight=34,
        bordercolor=palette["line"],
        borderwidth=1,
        font=FONT_TABLE,
    )
    style.configure(
        "Treeview.Heading",
        background=palette["bar"],
        foreground=palette["text"],
        relief="flat",
        font=FONT_UI_BOLD,
        padding=(8, 6),
    )
    style.map("Treeview", background=[("selected", palette["selected"])], foreground=[("selected", palette["text"])])


class RenameApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.theme_var = tk.StringVar(value="蓝色")
        self.palette = palette_for(self.theme_var.get())
        apply_theme(self, self.palette)
        self.title("重命名助手 v1.2")
        window_width, window_height, _scale = scaled_window_size(self, page="large")
        min_width, min_height, _min_scale = scaled_window_size(self, page="medium", max_screen_ratio=0.82)
        self.geometry(f"{window_width}x{window_height}")
        self.minsize(min_width, min_height)

        self.directory_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="请选择目录，并设置重命名规则。")
        self.rule_name_var = tk.StringVar()
        self.rule_type_var = tk.StringVar(value=RULE_LABELS["delete"])
        self.delete_mode_var = tk.StringVar(value="词组")
        self.saved_rule_var = tk.StringVar()
        self.replacement_var = tk.StringVar()
        self.insert_position_var = tk.StringVar(value="结尾")
        self.insert_index_var = tk.StringVar(value="0")
        self.sequence_prefix_var = tk.StringVar(value="文件")
        self.sequence_start_var = tk.StringVar(value="1")
        self.sequence_digits_var = tk.StringVar(value="3")
        self.sequence_separator_var = tk.StringVar(value="_")
        self.case_mode_var = tk.StringVar(value="小写")

        self.saved_rules: list[RuleConfig] = []
        self.plans: list[RenamePlan] = []
        self.plan_by_item: dict[str, RenamePlan] = {}
        self.path_by_item: dict[str, Path] = {}
        self.unchecked_plan_keys: set[str] = set()
        self.rounded_buttons: list[RoundedButton] = []
        self.rule_type_buttons: dict[str, RuleTypeButton] = {}
        self.editing_rule_name = ""
        self._loading_rule = False

        self._build_ui()
        self.load_settings()
        self._on_rule_type_changed()
        self._update_recursive_toggle()
        self._update_action_state()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=(16, 10, 16, 10), style="Toolbar.TFrame")
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(6, weight=1)

        self.choose_button = RoundedButton(
            toolbar,
            text="选择目录",
            command=self.choose_directory,
            width=ACTION_BUTTON_WIDTH,
            height=ACTION_BUTTON_HEIGHT,
            fill=self.palette["button"],
            active_fill=self.palette["button_active"],
            disabled_fill=self.palette["button_disabled"],
            text_color=self.palette["button_text"],
            bg=self.palette["bar"],
        )
        self.choose_button.grid(row=0, column=0, padx=(0, 10))
        self.rounded_buttons.append(self.choose_button)
        self.save_button = RoundedButton(
            toolbar,
            text="保存规则",
            command=self.save_rule_from_ui,
            width=ACTION_BUTTON_WIDTH,
            height=ACTION_BUTTON_HEIGHT,
            fill=self.palette["button"],
            active_fill=self.palette["button_active"],
            disabled_fill=self.palette["button_disabled"],
            text_color=self.palette["button_text"],
            bg=self.palette["bar"],
        )
        self.save_button.grid(row=0, column=1, padx=(0, 10))
        self.rounded_buttons.append(self.save_button)
        self.new_rule_button = RoundedButton(
            toolbar,
            text="新建规则",
            command=self.new_rule_from_ui,
            width=ACTION_BUTTON_WIDTH,
            height=ACTION_BUTTON_HEIGHT,
            fill=self.palette["button"],
            active_fill=self.palette["button_active"],
            disabled_fill=self.palette["button_disabled"],
            text_color=self.palette["button_text"],
            bg=self.palette["bar"],
        )
        self.new_rule_button.grid(row=0, column=2, padx=(0, 10))
        self.rounded_buttons.append(self.new_rule_button)
        self.delete_button = RoundedButton(
            toolbar,
            text="删除规则",
            command=self.delete_selected_rule,
            width=ACTION_BUTTON_WIDTH,
            height=ACTION_BUTTON_HEIGHT,
            fill=self.palette["button"],
            active_fill=self.palette["button_active"],
            disabled_fill=self.palette["button_disabled"],
            text_color=self.palette["button_text"],
            bg=self.palette["bar"],
        )
        self.delete_button.grid(row=0, column=3, padx=(0, 10))
        self.rounded_buttons.append(self.delete_button)
        self.refresh_button = RoundedButton(
            toolbar,
            text="刷新预览",
            command=self.refresh_preview,
            width=ACTION_BUTTON_WIDTH,
            height=ACTION_BUTTON_HEIGHT,
            fill=self.palette["button"],
            active_fill=self.palette["button_active"],
            disabled_fill=self.palette["button_disabled"],
            text_color=self.palette["button_text"],
            bg=self.palette["bar"],
        )
        self.refresh_button.grid(row=0, column=4, padx=(0, 10))
        self.rounded_buttons.append(self.refresh_button)
        self.execute_button = RoundedButton(
            toolbar,
            text="执行重命名",
            command=self.execute_rename,
            width=EXECUTE_BUTTON_WIDTH,
            height=ACTION_BUTTON_HEIGHT,
            fill=self.palette["button"],
            active_fill=self.palette["button_active"],
            disabled_fill=self.palette["button_disabled"],
            text_color=self.palette["button_text"],
            bg=self.palette["bar"],
        )
        self.execute_button.grid(row=0, column=5)
        self.rounded_buttons.append(self.execute_button)

        ttk.Label(toolbar, text="配色", style="Toolbar.TLabel").grid(row=0, column=7, padx=(14, 8), sticky="e")
        self.theme_combo = ttk.Combobox(
            toolbar,
            textvariable=self.theme_var,
            state="readonly",
            values=list(THEME_PALETTES),
            width=8,
        )
        self.theme_combo.grid(row=0, column=8, sticky="e")
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_changed)

        content = ttk.Frame(self, padding=(12, 12, 12, 8), style="TFrame")
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, minsize=448)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        left_panel = ttk.Frame(content, padding=(16, 14, 16, 14), style="Panel.TFrame")
        left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        left_panel.configure(width=448)
        left_panel.grid_propagate(False)
        left_panel.columnconfigure(0, weight=1)

        directory_frame = ttk.Frame(left_panel, style="Panel.TFrame")
        directory_frame.grid(row=0, column=0, sticky="ew")
        directory_frame.columnconfigure(0, weight=1)

        directory_title = ttk.Frame(directory_frame, style="Panel.TFrame")
        directory_title.grid(row=0, column=0, sticky="ew")
        directory_title.columnconfigure(1, weight=1)
        ttk.Label(directory_title, text="目录", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        self.recursive_toggle = RoundedToggle(
            directory_title,
            text="包含子目录",
            command=self.on_recursive_toggled,
            width=TOGGLE_BUTTON_WIDTH,
            height=TOGGLE_BUTTON_HEIGHT,
            bg=self.palette["panel"],
            font=FONT_TOGGLE_SMALL,
        )
        self.recursive_toggle.grid(row=0, column=1, padx=(12, 0), sticky="w")
        ttk.Entry(directory_frame, textvariable=self.directory_var).grid(row=1, column=0, pady=(10, 0), sticky="ew")

        rules = ttk.Frame(left_panel, style="Panel.TFrame")
        rules.grid(row=1, column=0, sticky="new", pady=(18, 0))
        rules.columnconfigure(0, weight=1)

        rule_type_frame = ttk.Frame(rules, style="Panel.TFrame")
        rule_type_frame.grid(row=0, column=0, sticky="ew")

        row = 0
        column = 0
        row_chars = 0
        for label in RULE_LABELS.values():
            label_length = rule_label_length(label)
            if row_chars and row_chars + label_length > RULE_TYPE_ROW_CHAR_LIMIT:
                row += 1
                column = 0
                row_chars = 0

            button = RuleTypeButton(
                rule_type_frame,
                text=label,
                command=lambda value=label: self.select_rule_type(value),
                width=rule_type_button_width(label),
                bg=self.palette["panel"],
            )
            button.grid(row=row, column=column, padx=(0 if column == 0 else 6, 0), pady=(0 if row == 0 else 6, 0), sticky="w")
            self.rule_type_buttons[label] = button
            row_chars += label_length
            column += 1

        rule_list_frame = ttk.Frame(rules, style="Panel.TFrame")
        rule_list_frame.grid(row=1, column=0, pady=(10, 0), sticky="ew")
        rule_list_frame.columnconfigure(0, weight=1)
        self.rule_listbox = tk.Listbox(
            rule_list_frame,
            height=5,
            activestyle="none",
            exportselection=False,
            bg=self.palette["field"],
            fg=self.palette["text"],
            selectbackground=self.palette["selected"],
            selectforeground=self.palette["text"],
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.palette["line"],
            highlightcolor=self.palette["button"],
            font=FONT_UI,
        )
        self.rule_listbox.grid(row=0, column=0, sticky="ew")
        self.rule_listbox.bind("<<ListboxSelect>>", self.load_selected_rule)
        rule_list_scrollbar = ttk.Scrollbar(rule_list_frame, orient="vertical", command=self.rule_listbox.yview)
        rule_list_scrollbar.grid(row=0, column=1, sticky="ns")
        self.rule_listbox.configure(yscrollcommand=rule_list_scrollbar.set)

        name_frame = ttk.Frame(rules, style="Panel.TFrame")
        name_frame.grid(row=2, column=0, pady=(10, 0), sticky="ew")
        name_frame.columnconfigure(0, weight=1)
        ttk.Label(name_frame, text="规则名称", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(name_frame, textvariable=self.rule_name_var).grid(row=1, column=0, pady=(6, 0), sticky="ew")

        self.rule_text = tk.Text(
            rules,
            height=6,
            width=36,
            wrap="word",
            undo=True,
            bg=self.palette["field"],
            fg=self.palette["text"],
            insertbackground=self.palette["text"],
            selectbackground=self.palette["selected"],
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.palette["line"],
            highlightcolor=self.palette["button"],
            font=FONT_UI,
            padx=8,
            pady=6,
        )
        self.rule_text.grid(row=3, column=0, pady=(10, 0), sticky="ew")
        self.rule_text.bind("<<Modified>>", self.on_rule_text_modified)

        self.delete_frame = ttk.Frame(rules, style="Panel.TFrame")
        self.delete_frame.grid(row=4, column=0, pady=(10, 0), sticky="ew")
        self.delete_frame.columnconfigure(1, weight=1)
        ttk.Label(self.delete_frame, text="删除方式", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            self.delete_frame,
            textvariable=self.delete_mode_var,
            state="readonly",
            values=DELETE_MODES,
            width=14,
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

        self.replace_frame = ttk.Frame(rules, style="Panel.TFrame")
        self.replace_frame.grid(row=5, column=0, pady=(10, 0), sticky="ew")
        self.replace_frame.columnconfigure(1, weight=1)
        ttk.Label(self.replace_frame, text="统一替换为", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.replace_frame, textvariable=self.replacement_var).grid(row=0, column=1, padx=(8, 0), sticky="ew")

        self.insert_frame = ttk.Frame(rules, style="Panel.TFrame")
        self.insert_frame.grid(row=6, column=0, pady=(10, 0), sticky="ew")
        ttk.Label(self.insert_frame, text="位置", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            self.insert_frame,
            textvariable=self.insert_position_var,
            state="readonly",
            values=INSERT_POSITIONS,
            width=10,
        ).grid(row=0, column=1, padx=(8, 18), sticky="w")
        ttk.Label(self.insert_frame, text="索引", style="Panel.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Entry(self.insert_frame, textvariable=self.insert_index_var, width=8).grid(row=0, column=3, padx=(8, 0), sticky="w")

        self.sequence_frame = ttk.Frame(rules, style="Panel.TFrame")
        self.sequence_frame.grid(row=7, column=0, pady=(10, 0), sticky="ew")
        self.sequence_frame.columnconfigure(1, weight=1)
        self.sequence_frame.columnconfigure(3, weight=1)
        ttk.Label(self.sequence_frame, text="名称", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.sequence_frame, textvariable=self.sequence_prefix_var, width=12).grid(row=0, column=1, padx=(8, 12), sticky="ew")
        ttk.Label(self.sequence_frame, text="起始", style="Panel.TLabel").grid(row=0, column=2, sticky="w")
        ttk.Entry(self.sequence_frame, textvariable=self.sequence_start_var, width=6).grid(row=0, column=3, padx=(8, 0), sticky="ew")
        ttk.Label(self.sequence_frame, text="位数", style="Panel.TLabel").grid(row=1, column=0, pady=(8, 0), sticky="w")
        ttk.Entry(self.sequence_frame, textvariable=self.sequence_digits_var, width=6).grid(row=1, column=1, padx=(8, 12), pady=(8, 0), sticky="ew")
        ttk.Label(self.sequence_frame, text="分隔", style="Panel.TLabel").grid(row=1, column=2, pady=(8, 0), sticky="w")
        ttk.Entry(self.sequence_frame, textvariable=self.sequence_separator_var, width=6).grid(row=1, column=3, padx=(8, 0), pady=(8, 0), sticky="ew")

        self.case_frame = ttk.Frame(rules, style="Panel.TFrame")
        self.case_frame.grid(row=8, column=0, pady=(10, 0), sticky="ew")
        self.case_frame.columnconfigure(1, weight=1)
        ttk.Label(self.case_frame, text="转换方式", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            self.case_frame,
            textvariable=self.case_mode_var,
            state="readonly",
            values=CASE_MODES,
            width=14,
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

        self.pad_frame = ttk.Frame(rules, style="Panel.TFrame")
        self.pad_frame.grid(row=9, column=0, pady=(10, 0), sticky="ew")
        self.pad_frame.columnconfigure(1, weight=1)
        ttk.Label(self.pad_frame, text="补零位数", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.pad_frame, textvariable=self.sequence_digits_var, width=8).grid(row=0, column=1, padx=(8, 0), sticky="w")

        for var in (
            self.delete_mode_var,
            self.replacement_var,
            self.insert_position_var,
            self.insert_index_var,
            self.sequence_prefix_var,
            self.sequence_start_var,
            self.sequence_digits_var,
            self.sequence_separator_var,
            self.case_mode_var,
        ):
            var.trace_add("write", self.on_rule_changed)

        table_frame = ttk.Frame(content, padding=(16, 14, 16, 12), style="Panel.TFrame")
        table_frame.grid(row=0, column=1, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(1, weight=1)

        ttk.Label(table_frame, text="文件名预览", style="Section.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))

        columns = ("check", "old", "new", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("check", text="可选")
        self.tree.heading("old", text="原文件名")
        self.tree.heading("new", text="新文件名")
        self.tree.heading("status", text="状态")
        self.tree.column("check", width=72, anchor="center", stretch=False)
        self.tree.column("old", width=420, anchor="w", minwidth=180)
        self.tree.column("new", width=420, anchor="w", minwidth=180)
        self.tree.column("status", width=150, anchor="w")
        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.tag_configure("ready", foreground=self.palette["button_active"])
        self.tree.tag_configure("skip", foreground=self.palette["muted"])
        self.tree.tag_configure("idle", foreground=self.palette["muted"])
        self.tree.bind("<Configure>", self.resize_columns)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Button-3>", self.show_tree_context_menu)

        self.tree_menu = tk.Menu(self, tearoff=False)
        self.tree_menu.add_command(label="打开文件", command=self.open_selected_file)
        self.tree_menu.add_command(label="打开目录", command=self.open_selected_directory)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        bottom = ttk.Frame(self, padding=(16, 10, 16, 12), style="Status.TFrame")
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)

        ttk.Label(bottom, textvariable=self.status_var, style="Status.TLabel").grid(row=0, column=0, sticky="w")

    def choose_directory(self) -> None:
        directory = filedialog.askdirectory(title="选择要批量重命名的目录")
        if directory:
            self.directory_var.set(directory)
            self.refresh_preview()

    def on_theme_changed(self, _event: tk.Event[ttk.Combobox] | None = None) -> None:
        self.apply_current_theme()
        self.save_settings()

    def apply_current_theme(self) -> None:
        self.palette = palette_for(self.theme_var.get())
        apply_theme(self, self.palette)

        for button in self.rounded_buttons:
            button.set_colors(
                fill=self.palette["button"],
                active_fill=self.palette["button_active"],
                disabled_fill=self.palette["button_disabled"],
                text_color=self.palette["button_text"],
                disabled_text_color="#f2f2ea",
                bg=self.palette["bar"],
            )

        for button in self.rule_type_buttons.values():
            button.set_colors(
                selected_fill=self.palette["button"],
                unselected_fill=self.palette["button_soft"],
                text_color=self.palette["text"],
                selected_text_color=self.palette["button_text"],
                bg=self.palette["panel"],
            )

        if hasattr(self, "rule_text"):
            self.rule_text.configure(
                bg=self.palette["field"],
                fg=self.palette["text"],
                insertbackground=self.palette["text"],
                selectbackground=self.palette["selected"],
                highlightbackground=self.palette["line"],
                highlightcolor=self.palette["button"],
            )

        if hasattr(self, "rule_listbox"):
            self.rule_listbox.configure(
                bg=self.palette["field"],
                fg=self.palette["text"],
                selectbackground=self.palette["selected"],
                selectforeground=self.palette["text"],
                highlightbackground=self.palette["line"],
                highlightcolor=self.palette["button"],
            )

        if hasattr(self, "tree"):
            self.tree.tag_configure("ready", foreground=self.palette["button_active"])
            self.tree.tag_configure("skip", foreground=self.palette["muted"])
            self.tree.tag_configure("idle", foreground=self.palette["muted"])

        self._update_recursive_toggle()
        self._update_rule_type_buttons()

    def on_recursive_toggled(self, _event: tk.Event[tk.Canvas] | None = None) -> None:
        self.recursive_var.set(not self.recursive_var.get())
        self._update_recursive_toggle()
        self.refresh_preview()

    def select_rule_type(self, label: str) -> None:
        if self.rule_type_var.get() == label:
            return

        kind = LABEL_TO_RULE.get(label, "delete")
        self.editing_rule_name = ""
        self.saved_rule_var.set("")
        if hasattr(self, "rule_listbox"):
            self.rule_listbox.selection_clear(0, "end")

        self.clear_rule_editor(kind)
        self.update_saved_rule_list()
        self._update_action_state()

    def _update_rule_type_buttons(self) -> None:
        if not hasattr(self, "rule_type_buttons"):
            return

        current = self.rule_type_var.get()
        for label, button in self.rule_type_buttons.items():
            button.set_selected(label == current)

    def _update_recursive_toggle(self) -> None:
        if not hasattr(self, "recursive_toggle"):
            return

        self.recursive_toggle.set_colors(
            selected_fill=self.palette["button"],
            unselected_fill=self.palette["button_soft"],
            text_color=self.palette["text"],
            selected_text_color=self.palette["button_text"],
            bg=self.palette["panel"],
        )
        self.recursive_toggle.set_selected(self.recursive_var.get())

    def current_rule(self) -> RuleConfig:
        kind = LABEL_TO_RULE.get(self.rule_type_var.get(), "delete")
        return RuleConfig(
            name=self.rule_name_var.get().strip() or RULE_LABELS[kind],
            kind=kind,
            text=self.rule_text.get("1.0", "end").strip(),
            delete_mode=self.delete_mode_var.get(),
            replacement=self.replacement_var.get(),
            insert_position=self.insert_position_var.get(),
            insert_index=parse_int(self.insert_index_var.get(), 0, 0),
            sequence_prefix=self.sequence_prefix_var.get().strip(),
            sequence_start=parse_int(self.sequence_start_var.get(), 1, 0),
            sequence_digits=parse_int(self.sequence_digits_var.get(), 3, 1),
            sequence_separator=self.sequence_separator_var.get(),
            case_mode=self.case_mode_var.get(),
        )

    def apply_rule_to_ui(self, rule: RuleConfig) -> None:
        self._loading_rule = True
        try:
            self.rule_name_var.set(rule.name)
            self.rule_type_var.set(RULE_LABELS.get(rule.kind, RULE_LABELS["delete"]))
            self.delete_mode_var.set(rule.delete_mode if rule.delete_mode in DELETE_MODES else "词组")
            self.rule_text.delete("1.0", "end")
            self.rule_text.insert("1.0", rule.text)
            self.rule_text.edit_modified(False)
            self.replacement_var.set(rule.replacement)
            self.insert_position_var.set(rule.insert_position if rule.insert_position in INSERT_POSITIONS else "结尾")
            self.insert_index_var.set(str(rule.insert_index))
            self.sequence_prefix_var.set(rule.sequence_prefix)
            self.sequence_start_var.set(str(rule.sequence_start))
            self.sequence_digits_var.set(str(rule.sequence_digits))
            self.sequence_separator_var.set(rule.sequence_separator)
            self.case_mode_var.set(rule.case_mode if rule.case_mode in CASE_MODES else "小写")
        finally:
            self._loading_rule = False

        self._on_rule_type_changed()
        self.refresh_preview()

    def on_rule_text_modified(self, _event: tk.Event[tk.Text]) -> None:
        if self.rule_text.edit_modified():
            self.rule_text.edit_modified(False)
            self.mark_rule_as_draft()
            self.refresh_preview()

    def on_rule_changed(self, *_args: object) -> None:
        self.mark_rule_as_draft()
        self._on_rule_type_changed()
        self.update_saved_rule_list()
        self.refresh_preview()

    def mark_rule_as_draft(self) -> None:
        if self._loading_rule:
            return

        if self.saved_rule_var.get() and not self.editing_rule_name:
            self.editing_rule_name = self.saved_rule_var.get()

    def _on_rule_type_changed(self) -> None:
        kind = LABEL_TO_RULE.get(self.rule_type_var.get(), "delete")
        self._update_rule_type_buttons()
        for frame in (self.delete_frame, self.replace_frame, self.insert_frame, self.sequence_frame, self.case_frame, self.pad_frame):
            frame.grid_remove()

        if kind == "delete":
            self.delete_frame.grid()
        elif kind == "replace":
            self.replace_frame.grid()
        elif kind == "insert":
            self.insert_frame.grid()
        elif kind == "sequence":
            self.sequence_frame.grid()
        elif kind == "case":
            self.case_frame.grid()
        elif kind == "pad":
            self.pad_frame.grid()

        if kind == "delete":
            if self.delete_mode_var.get() == "从分隔符后删除":
                self.status_var.set("删除：内容框里填分隔符，例如 -；会删除从最后一个分隔符开始到末尾的内容。")
            elif self.delete_mode_var.get() == "条件删除后缀":
                self.status_var.set("删除：每行写 分隔符=>包含符号，例如 -=>[；只有分隔符后包含该符号才删除。")
            elif self.delete_mode_var.get() == "条件删除前缀":
                self.status_var.set("删除：每行写 分隔符=>包含符号，例如 -=>[；只有分隔符前包含该符号才删除。")
            elif self.delete_mode_var.get() == "删除首尾数字段":
                self.status_var.set("删除：内容框里填分隔符，例如 _；会删除开头和结尾的纯数字段。")
            elif self.delete_mode_var.get() == "删除括号内容":
                self.status_var.set("删除：内容框留空会清理常见括号；也可每行写一组括号，例如 []。")
            elif self.delete_mode_var.get() == "清理多余符号":
                self.status_var.set("删除：内容框留空会清理重复的 _、-、空格等；也可每行写一个符号。")
            elif self.delete_mode_var.get() == "删除首尾指定字符":
                self.status_var.set("删除：内容框填写要从开头和结尾去掉的字符，例如 _- 空格。")
            else:
                self.status_var.set("删除词组：每行一个要删除的词组。")
        elif kind == "replace":
            self.status_var.set("替换词组：每行写 旧词=>新词；也可写旧词并填写统一替换内容。")
        elif kind == "insert":
            self.status_var.set("固定位置添加：内容框里填写要添加的词组。")
        elif kind == "sequence":
            self.status_var.set("名称加序号：名称留空时只生成 001 这类编号，不加默认文字。")
        elif kind == "case":
            self.status_var.set("大小写转换：只转换文件名主体，不改变扩展名。")
        elif kind == "increment":
            self.status_var.set("编号+1：自动把文件名主体里最后一段数字加 1，并尽量保留原位数。")
        elif kind == "pad":
            self.status_var.set("编号补零：把文件名开头的数字补到指定位数，例如 1.png -> 001.png。")

    def refresh_preview(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.plan_by_item.clear()
        self.path_by_item.clear()

        directory_text = self.directory_var.get().strip()
        rule = self.current_rule()

        if not directory_text:
            self.plans = []
            self.status_var.set("请选择目录。")
            self._update_action_state()
            return

        directory = Path(directory_text)
        if not directory.exists() or not directory.is_dir():
            self.plans = []
            self.status_var.set("目录不存在。")
            self._update_action_state()
            return

        if not is_rule_ready(rule):
            self.plans = []
            files = collect_files(directory, self.recursive_var.get())
            for path in files:
                old_display = path.name
                item = self.tree.insert("", "end", values=("", old_display, "", STATUS_NEED_RULE), tags=("idle",))
                self.path_by_item[item] = path

            self.status_var.set(f"已扫描 {len(files)} 个文件，请设置重命名规则。")
            self._update_action_state()
            return

        self.plans = build_rename_plan(directory, rule, self.recursive_var.get())
        ready_count = sum(1 for plan in self.plans if plan.status == STATUS_READY)

        for plan in self.plans:
            old_display = plan.path.name
            new_display = plan.new_name
            tag = "ready" if plan.status == STATUS_READY else "skip" if plan.status.startswith("跳过") else "idle"
            check = CHECKED if self.is_plan_checked(plan) else UNCHECKED if plan.status == STATUS_READY else ""
            item = self.tree.insert("", "end", values=(check, old_display, new_display, plan.status), tags=(tag,))
            self.plan_by_item[item] = plan
            self.path_by_item[item] = plan.path

        self.status_var.set(f"已扫描 {len(self.plans)} 个文件，{ready_count} 个文件可重命名。")
        self._update_action_state()

    def execute_rename(self) -> None:
        ready_plans = [plan for plan in self.plans if plan.status == STATUS_READY and self.is_plan_checked(plan)]
        if not ready_plans:
            messagebox.showinfo("无需处理", "当前没有勾选可重命名的文件。")
            return

        confirmed = messagebox.askyesno("确认重命名", f"确定要重命名 {len(ready_plans)} 个文件吗？")
        if not confirmed:
            return

        self.save_rule_to_history(self.current_rule())
        success_count = 0
        errors: list[str] = []
        temp_pairs: list[tuple[Path, RenamePlan]] = []

        for index, plan in enumerate(ready_plans):
            try:
                temp_path = unique_temp_path(plan.path, index)
                plan.path.rename(temp_path)
                temp_pairs.append((temp_path, plan))
            except OSError as exc:
                errors.append(f"{plan.path.name}: {exc}")

        for temp_path, plan in temp_pairs:
            try:
                temp_path.rename(plan.new_path)
                success_count += 1
            except OSError as exc:
                errors.append(f"{plan.path.name}: {exc}")
                try:
                    temp_path.rename(plan.path)
                except OSError as restore_exc:
                    errors.append(f"{plan.path.name}: 恢复失败，临时文件 {temp_path.name}: {restore_exc}")

        self.refresh_preview()

        if errors:
            messagebox.showwarning(
                "部分完成",
                f"已重命名 {success_count} 个文件，{len(errors)} 个失败。\n\n" + "\n".join(errors[:5]),
            )
        else:
            messagebox.showinfo("完成", f"已重命名 {success_count} 个文件。")

    def plan_key(self, plan: RenamePlan) -> str:
        return str(plan.path.resolve()).lower()

    def is_plan_checked(self, plan: RenamePlan) -> bool:
        return plan.status == STATUS_READY and self.plan_key(plan) not in self.unchecked_plan_keys

    def on_tree_click(self, event: tk.Event[ttk.Treeview]) -> str | None:
        if self.tree.identify_region(event.x, event.y) != "cell":
            return None

        if self.tree.identify_column(event.x) != "#1":
            return None

        item = self.tree.identify_row(event.y)
        plan = self.plan_by_item.get(item)
        if not plan or plan.status != STATUS_READY:
            return "break"

        key = self.plan_key(plan)
        if self.is_plan_checked(plan):
            self.unchecked_plan_keys.add(key)
            check = UNCHECKED
        else:
            self.unchecked_plan_keys.discard(key)
            check = CHECKED

        values = list(self.tree.item(item, "values"))
        values[0] = check
        self.tree.item(item, values=values)
        self._update_action_state()
        return "break"

    def tree_item_path(self, item: str) -> Path | None:
        path = self.path_by_item.get(item)
        return path if path and path.exists() else None

    def show_tree_context_menu(self, event: tk.Event[ttk.Treeview]) -> str:
        item = self.tree.identify_row(event.y)
        if not item:
            return "break"

        self.tree.selection_set(item)
        self.tree.focus(item)
        path = self.tree_item_path(item)
        state = "normal" if path else "disabled"
        self.tree_menu.entryconfigure("打开文件", state=state)
        self.tree_menu.entryconfigure("打开目录", state=state)
        self.tree_menu.tk_popup(event.x_root, event.y_root)
        self.tree_menu.grab_release()
        return "break"

    def selected_tree_path(self) -> Path | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree_item_path(selection[0])

    def open_selected_file(self) -> None:
        path = self.selected_tree_path()
        if not path:
            messagebox.showinfo("无法打开", "当前文件不存在。")
            return

        try:
            os.startfile(path)
        except OSError as exc:
            messagebox.showwarning("打开失败", str(exc))

    def open_selected_directory(self) -> None:
        path = self.selected_tree_path()
        if not path:
            messagebox.showinfo("无法打开", "当前文件不存在。")
            return

        try:
            subprocess.Popen(["explorer", "/select,", str(path)])
        except OSError:
            try:
                os.startfile(path.parent)
            except OSError as exc:
                messagebox.showwarning("打开失败", str(exc))

    def save_rule_from_ui(self) -> None:
        name = self.rule_name_var.get().strip()
        if not name:
            messagebox.showinfo("需要名称", "请先填写规则名称。")
            return

        rule = self.current_rule()
        rule.name = name
        old_name = self.editing_rule_name or self.saved_rule_var.get()
        was_update = bool(old_name and any(saved.name == old_name for saved in self.saved_rules))
        self.save_rule_to_history(rule, old_name=old_name)
        action = "更新" if was_update else "保存"
        messagebox.showinfo(f"已{action}", f"规则“{rule.name}”已{action}。")

    def save_rule_to_history(self, rule: RuleConfig, old_name: str = "") -> None:
        remove_names = {rule.name}
        if old_name:
            remove_names.add(old_name)
        self.saved_rules = [saved for saved in self.saved_rules if saved.name not in remove_names]
        self.saved_rules.insert(0, rule)
        self.saved_rules = self.saved_rules[:30]
        self.editing_rule_name = rule.name
        self.rule_name_var.set(rule.name)
        self.saved_rule_var.set(rule.name)
        self.update_saved_rule_list(select_name=rule.name)
        self.save_settings()
        self._update_action_state()

    def delete_selected_rule(self) -> None:
        name = self.saved_rule_var.get() or self.editing_rule_name
        if not name:
            messagebox.showinfo("无需处理", "当前没有选中的规则。")
            return

        self.saved_rules = [rule for rule in self.saved_rules if rule.name != name]
        if self.editing_rule_name == name:
            self.editing_rule_name = ""
            self.rule_name_var.set("")
        self.saved_rule_var.set("")
        self.update_saved_rule_list()
        self.save_settings()
        self._update_action_state()

    def load_selected_rule(self, _event: tk.Event[tk.Listbox] | None = None) -> None:
        if not hasattr(self, "rule_listbox"):
            return

        selection = self.rule_listbox.curselection()
        if not selection:
            return

        name = self.rule_listbox.get(selection[0])
        kind = LABEL_TO_RULE.get(self.rule_type_var.get(), "delete")
        for rule in self.saved_rules:
            if rule.name == name and rule.kind == kind:
                self.saved_rule_var.set(name)
                self.editing_rule_name = name
                self.apply_rule_to_ui(rule)
                self.update_saved_rule_list(select_name=name)
                self._update_action_state()
                return

    def update_saved_rule_list(self, select_name: str = "") -> None:
        if not hasattr(self, "rule_listbox"):
            return

        kind = LABEL_TO_RULE.get(self.rule_type_var.get(), "delete")
        names = [rule.name for rule in self.saved_rules if rule.kind == kind]
        target = select_name or (self.saved_rule_var.get() if self.saved_rule_var.get() in names else "")

        self.rule_listbox.delete(0, "end")
        for name in names:
            self.rule_listbox.insert("end", name)

        if target in names:
            index = names.index(target)
            self.rule_listbox.selection_set(index)
            self.rule_listbox.see(index)
            self.saved_rule_var.set(target)
        else:
            self.saved_rule_var.set("")

    def clear_rule_editor(self, kind: str) -> None:
        self._loading_rule = True
        try:
            self.rule_name_var.set("")
            self.rule_type_var.set(RULE_LABELS.get(kind, RULE_LABELS["delete"]))
            self.delete_mode_var.set("词组")
            self.rule_text.delete("1.0", "end")
            self.rule_text.edit_modified(False)
            self.replacement_var.set("")
            self.insert_position_var.set("结尾")
            self.insert_index_var.set("0")
            self.sequence_prefix_var.set("")
            self.sequence_start_var.set("1")
            self.sequence_digits_var.set("3")
            self.sequence_separator_var.set("_")
            self.case_mode_var.set("小写")
        finally:
            self._loading_rule = False

        self._on_rule_type_changed()
        self.refresh_preview()

    def new_rule_from_ui(self) -> None:
        kind = LABEL_TO_RULE.get(self.rule_type_var.get(), "delete")
        self.editing_rule_name = ""
        self.saved_rule_var.set("")
        if hasattr(self, "rule_listbox"):
            self.rule_listbox.selection_clear(0, "end")

        self.clear_rule_editor(kind)
        self.update_saved_rule_list()
        self.status_var.set("已新建空白规则，请填写规则名称和内容。")
        self._update_action_state()

    def load_settings(self) -> None:
        if not SETTINGS_FILE.exists():
            return

        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        self.directory_var.set(data.get("directory", ""))
        self.recursive_var.set(bool(data.get("recursive", False)))
        saved_theme = data.get("theme", "蓝色")
        if saved_theme in THEME_PALETTES:
            self.theme_var.set(saved_theme)
            self.apply_current_theme()
        self.saved_rules = []
        for item in data.get("rules", []):
            if isinstance(item, dict):
                defaults = asdict(RuleConfig())
                defaults.update({key: value for key, value in item.items() if key in defaults})
                self.saved_rules.append(RuleConfig(**defaults))

        self.update_saved_rule_list()
        self.saved_rule_var.set("")
        self.rule_name_var.set("")
        self.editing_rule_name = ""

    def save_settings(self) -> None:
        data = {
            "directory": self.directory_var.get().strip(),
            "recursive": self.recursive_var.get(),
            "theme": self.theme_var.get(),
            "last_rule": self.saved_rule_var.get(),
            "rules": [asdict(rule) for rule in self.saved_rules],
        }
        SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def on_close(self) -> None:
        self.save_settings()
        self.destroy()

    def _update_action_state(self) -> None:
        if not hasattr(self, "execute_button"):
            return

        has_ready_files = any(plan.status == STATUS_READY and self.is_plan_checked(plan) for plan in self.plans)
        self.execute_button.state(["!disabled"] if has_ready_files else ["disabled"])

    def resize_columns(self, event: tk.Event[ttk.Treeview]) -> None:
        check_width = 72
        status_width = 150
        available = max(event.width - check_width - status_width - 18, 420)
        old_width = available // 2
        self.tree.column("check", width=check_width)
        self.tree.column("old", width=old_width)
        self.tree.column("new", width=available - old_width)
        self.tree.column("status", width=status_width)


def main() -> None:
    enable_dpi_awareness()
    app = RenameApp()
    app.mainloop()


if __name__ == "__main__":
    main()
