"""Small deterministic planner for the offline Agent path."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Plan:
    intent: str
    calls: List[ToolCall]


class Planner:
    """Map natural-language requests to a small, inspectable tool plan."""

    # Keep natural-language words out of the match.  ``\w`` also matches
    # Chinese characters, so the old expression captured the whole request
    # (for example, ``请审查 sample/layer_stack.py``) as if it were a path.
    _path_pattern = re.compile(
        r"(?:(?:[A-Za-z]:)?[\\/])?[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)*\.py"
    )

    def plan(self, request: str, root: Path) -> Plan:
        lowered = request.lower()
        if any(word in lowered for word in ("搜索", "查找", "search", "find")):
            intent = "search"
            query = self._search_query(request)
            return Plan(intent, [ToolCall("search_files", {"query": query})])

        if any(word in lowered for word in ("测试", "test", "unittest")):
            intent = "test"
            path = self._extract_path(request)
            if not path:
                path = "tests" if (root / "tests").is_dir() else "."
            return Plan(intent, [ToolCall("run_tests", {"path": path})])

        intent = "review" if any(
            word in lowered for word in ("审查", "审阅", "review", "bug", "问题", "改进", "重构")
        ) else "explain"
        path = self._choose_path(request, root)
        calls: List[ToolCall] = []
        if path:
            calls.extend(
                [
                    ToolCall("inspect_python", {"path": path}),
                    ToolCall("read_file", {"path": path, "max_chars": 12000}),
                ]
            )
        else:
            calls.append(ToolCall("search_files", {"query": "class ", "glob": "*.py"}))
        return Plan(intent, calls)

    def _choose_path(self, request: str, root: Path) -> str:
        path = self._extract_path(request)
        if path:
            return path
        sample = root / "sample" / "layer_stack.py"
        if sample.is_file():
            return str(sample.relative_to(root))
        py_files = sorted(root.rglob("*.py"))
        return str(py_files[0].relative_to(root)) if py_files else ""

    def _extract_path(self, request: str) -> str:
        # Quoted paths may contain spaces; prefer the last match because the
        # filename is normally the most specific part of a natural-language
        # request.
        quoted = re.findall(r'["“]([^"”]+\.py)["”]', request)
        if quoted:
            return quoted[-1].strip()
        matches = self._path_pattern.findall(request)
        if matches:
            return matches[-1].strip().strip('"\'，。')
        return ""

    @staticmethod
    def _search_query(request: str) -> str:
        quoted = re.search(r"[\"“](.+?)[\"”]", request)
        if quoted:
            return quoted.group(1)
        for prefix in ("搜索", "查找", "search", "find"):
            if prefix in request.lower():
                tail = request.lower().split(prefix, 1)[1].strip(" ：:，,")
                if tail:
                    return tail.split()[0]
        return "TODO"

