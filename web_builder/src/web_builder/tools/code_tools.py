import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from crewai.tools import tool

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


MODIFIED_FILES_REGISTRY = set()
LAST_TEST_EXIT_CODE = 0


def set_last_test_failed():
    global LAST_TEST_EXIT_CODE
    LAST_TEST_EXIT_CODE = 1


def reset_modified_files_registry():
    global MODIFIED_FILES_REGISTRY, LAST_TEST_EXIT_CODE
    MODIFIED_FILES_REGISTRY.clear()
    LAST_TEST_EXIT_CODE = 0


def _sanitize_path(file_path: str) -> Path:
    clean = file_path.strip().strip("'\"`")
    clean = re.sub(r"^```[a-zA-Z]*\n?", "", clean)
    clean = re.sub(r"\n?```$", "", clean)
    return Path(clean).resolve()


def _clean_code_fence(text: str) -> str:
    clean = text.strip()
    clean = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", clean)
    clean = re.sub(r"\n?```$", "", clean)
    return clean


def _strip_line_number_prefixes(text: str) -> str:
    """Strips line number prefixes like ' 123 | ' or '   1 | ' copied from read_file."""
    lines = text.split("\n")
    has_prefix = any(re.match(r"^\s*\d+\s*\|\s?", l) for l in lines if l.strip())
    if has_prefix:
        lines = [re.sub(r"^\s*\d+\s*\|\s?", "", l) for l in lines]
    return "\n".join(lines)


@tool("write_file")
def write_file(file_path: str, content: str) -> str:
    """
    Writes complete, production-ready source code or text content to a file on disk.
    Creates any missing parent directories automatically.
    Do NOT write empty content or partial code with placeholders.
    """
    try:
        clean_content = content.strip()
        if not clean_content:
            return f"Error: Refusing to write empty content to {file_path}. Always write complete code."

        # Guarantee standard Vietnamese precomposed Unicode (NFC)
        content = unicodedata.normalize("NFC", content)

        # Unescape literal unicode sequences if present (e.g. \u1edf -> ở)
        if "\\u" in content:
            try:
                content = re.sub(r"\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), content)
                content = unicodedata.normalize("NFC", content)
            except Exception:
                pass

        path = _sanitize_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

        MODIFIED_FILES_REGISTRY.add(path.as_posix())
        lines = content.count("\n") + 1
        return f"Successfully wrote {len(content)} characters ({lines} lines) to {path.as_posix()}"
    except Exception as e:
        return f"Error writing to {file_path}: {str(e)}"


@tool("read_file")
def read_file(file_path: str, start_line: int = 1, end_line: int = -1) -> str:
    """
    Reads and returns the content of a file on disk with optional line range slicing.
    """
    try:
        path = _sanitize_path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."
        if path.is_dir():
            return f"Error: '{file_path}' is a directory, not a file. Use list_dir instead."
        if path.stat().st_size == 0:
            return f"Warning: File '{file_path}' exists but is EMPTY (0 bytes)."

        lines = None
        for enc in ("utf-8-sig", "utf-8", "cp1258", "latin1"):
            try:
                with open(path, "r", encoding=enc) as f:
                    lines = [unicodedata.normalize("NFC", l) for l in f.readlines()]
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if lines is None:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = [unicodedata.normalize("NFC", l) for l in f.readlines()]

        total_lines = len(lines)
        if end_line == -1 or end_line > total_lines:
            end_line = total_lines

        start_idx = max(0, start_line - 1)
        end_idx = min(total_lines, end_line)

        selected_lines = lines[start_idx:end_idx]
        output = [f"--- File: {path.name} (Lines {start_line}-{end_idx} of {total_lines}) ---"]
        for idx, line in enumerate(selected_lines, start=start_idx + 1):
            output.append(f"{idx:4d} | {line.rstrip()}")

        return "\n".join(output)
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"


@tool("replace_lines")
def replace_lines(file_path: str, start_line: int, end_line: int, replacement: str) -> str:
    """
    Replaces lines between start_line and end_line (1-indexed, inclusive) in a file with new code.
    Use this tool to surgically fix a bug when the failing line number is known from DIAGNOSTICS.md or read_file.
    Automatically handles indentation, line endings, and strips line-number prefixes.
    """
    try:
        path = _sanitize_path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."

        replacement = _clean_code_fence(replacement)
        replacement = _strip_line_number_prefixes(replacement)

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw_content = f.read()

        is_crlf = "\r\n" in raw_content
        lines = raw_content.replace("\r\n", "\n").split("\n")
        total_lines = len(lines)

        if start_line < 1 or start_line > total_lines:
            return f"Error: start_line {start_line} out of range (file has {total_lines} lines)."
        if end_line < start_line:
            end_line = start_line
        if end_line > total_lines:
            end_line = total_lines

        # Detect original indentation from start_line
        orig_indent = ""
        target_first_line = lines[start_line - 1]
        m = re.match(r"^(\s*)", target_first_line)
        if m:
            orig_indent = m.group(1)

        rep_lines = replacement.replace("\r\n", "\n").split("\n")
        # If replacement lines have no leading indentation, apply orig_indent
        if rep_lines and orig_indent and not rep_lines[0].startswith(" ") and not rep_lines[0].startswith("\t"):
            rep_lines = [orig_indent + l if l.strip() else l for l in rep_lines]

        before = lines[:start_line - 1]
        after = lines[end_line:]

        new_lines = before + rep_lines + after
        final_content = "\n".join(new_lines)
        if is_crlf:
            final_content = final_content.replace("\n", "\r\n")

        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(final_content)

        MODIFIED_FILES_REGISTRY.add(path.as_posix())
        return f"Successfully replaced lines {start_line}-{end_line} in '{file_path}' ({len(rep_lines)} lines written)."
    except Exception as e:
        return f"Error replacing lines in '{file_path}': {str(e)}"


@tool("patch_file")
def patch_file(file_path: str, search_text: str, replace_text: str) -> str:
    """
    Surgically replaces a specific block of text in a file with new text.
    Handles CRLF/LF differences, markdown fences, line-number prefixes, and indentation variations automatically.
    """
    try:
        path = _sanitize_path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."

        search_text = _clean_code_fence(search_text)
        replace_text = _clean_code_fence(replace_text)
        search_text = _strip_line_number_prefixes(search_text)
        replace_text = _strip_line_number_prefixes(replace_text)

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw_content = f.read()

        normalized_content = raw_content.replace("\r\n", "\n")
        normalized_search = search_text.replace("\r\n", "\n")
        normalized_replace = replace_text.replace("\r\n", "\n")

        if normalized_search in normalized_content:
            normalized_content = normalized_content.replace(normalized_search, normalized_replace, 1)
        else:
            # Fallback 1: Try stripping trailing whitespace
            stripped_search = "\n".join(line.rstrip() for line in normalized_search.split("\n"))
            stripped_content = "\n".join(line.rstrip() for line in normalized_content.split("\n"))
            if stripped_search in stripped_content:
                normalized_content = stripped_content.replace(stripped_search, normalized_replace, 1)
            else:
                # Fallback 2: Intelligent multi-line matching ignoring blank lines
                search_non_empty = [l.strip() for l in normalized_search.split("\n") if l.strip()]
                content_lines = normalized_content.split("\n")
                matched = False
                if search_non_empty:
                    first_search = search_non_empty[0]
                    for i, c_line in enumerate(content_lines):
                        if c_line.strip() == first_search:
                            curr_c = i
                            match_start = i
                            match_end = i
                            all_found = True
                            for s_text in search_non_empty[1:]:
                                found_next = False
                                for next_c in range(curr_c + 1, min(len(content_lines), curr_c + 30)):
                                    if not content_lines[next_c].strip():
                                        continue
                                    if content_lines[next_c].strip() == s_text:
                                        curr_c = next_c
                                        match_end = next_c
                                        found_next = True
                                        break
                                if not found_next:
                                    all_found = False
                                    break
                            if all_found:
                                # Preserve original indentation
                                orig_indent_match = re.match(r"^(\s*)", content_lines[match_start])
                                orig_indent = orig_indent_match.group(1) if orig_indent_match else ""
                                rep_lines = normalized_replace.split("\n")
                                if rep_lines and orig_indent and not rep_lines[0].startswith(" ") and not rep_lines[0].startswith("\t"):
                                    rep_lines = [orig_indent + l if l.strip() else l for l in rep_lines]
                                    normalized_replace = "\n".join(rep_lines)

                                before = content_lines[:match_start]
                                after = content_lines[match_end + 1:]
                                normalized_content = "\n".join(before + [normalized_replace] + after)
                                matched = True
                                break

                if not matched:
                    return (
                        f"Error: Target search text not found in '{file_path}'. "
                        f"Tip: Use `replace_lines(file_path='{file_path}', start_line=..., end_line=..., replacement=...)` "
                        f"to replace lines directly by line number, or call write_file to overwrite the file."
                    )

        final_content = (
            normalized_content.replace("\n", "\r\n") if "\r\n" in raw_content else normalized_content
        )

        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(final_content)

        MODIFIED_FILES_REGISTRY.add(path.as_posix())
        return f"Successfully patched '{file_path}'."
    except Exception as e:
        return f"Error patching '{file_path}': {str(e)}"


@tool("list_dir")
def list_dir(directory_path: str = ".", max_depth: int = 2) -> str:
    """
    Lists files and directories under the specified directory path up to max_depth.
    """
    try:
        base = _sanitize_path(directory_path)
        if not base.exists():
            return f"Error: Directory '{directory_path}' does not exist."
        if not base.is_dir():
            return f"Error: '{directory_path}' is a file, not a directory."

        ignored_names = {".venv", "__pycache__", ".git", "node_modules", ".gemini", "target", ".idea"}
        results = []

        def traverse(current: Path, depth: int, prefix: str = ""):
            if depth > max_depth:
                return
            try:
                entries = sorted(
                    [e for e in current.iterdir() if e.name not in ignored_names],
                    key=lambda e: (not e.is_dir(), e.name.lower()),
                )
            except PermissionError:
                return

            for i, item in enumerate(entries):
                is_last = i == (len(entries) - 1)
                connector = "└── " if is_last else "├── "
                sub_prefix = "    " if is_last else "│   "

                if item.is_dir():
                    results.append(f"{prefix}{connector}{item.name}/")
                    traverse(item, depth + 1, prefix + sub_prefix)
                else:
                    size = item.stat().st_size
                    tag = " [EMPTY/0-BYTE - NEEDS CODE]" if size == 0 else f" ({size:,} B)"
                    results.append(f"{prefix}{connector}{item.name}{tag}")

        traverse(base, depth=1)
        header = f"=== Directory Tree: {base.name}/ (max_depth={max_depth}) ===\n"
        return header + ("\n".join(results) if results else "Directory is empty.")
    except Exception as e:
        return f"Error listing directory '{directory_path}': {str(e)}"


@tool("search_code")
def search_code(query: str, root_path: str = ".", file_ext: str = "") -> str:
    """
    Searches for a string or identifier across project files.
    """
    try:
        root = _sanitize_path(root_path)
        ignored_dirs = {".venv", "__pycache__", ".git", "node_modules", ".gemini", "target", ".idea"}
        matches = []
        max_matches = 30

        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if any(ig in p.parts for ig in ignored_dirs):
                continue
            if file_ext and not p.name.endswith(file_ext):
                continue

            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, start=1):
                        if query.lower() in line.lower():
                            rel = p.relative_to(root).as_posix()
                            matches.append(f"{rel}:{line_no} | {line.strip()[:140]}")
                            if len(matches) >= max_matches:
                                break
            except Exception:
                continue

            if len(matches) >= max_matches:
                break

        if not matches:
            return f"No matches found for '{query}' in '{root_path}'."
        header = f"Found {len(matches)} match(es) for '{query}':\n"
        return header + "\n".join(matches)
    except Exception as e:
        return f"Error searching code: {str(e)}"


@tool("check_code_health")
def check_code_health(root_path: str = ".") -> str:
    """
    Scans the codebase to detect 0-byte stub files, missing files, and verify overall code health.
    """
    try:
        root = _sanitize_path(root_path)
        empty_files = []
        valid_files = []
        ignored_dirs = {".venv", "__pycache__", ".git", "node_modules", ".gemini", "target"}

        for p in root.rglob("*"):
            if p.is_file():
                if any(ignored in p.parts for ignored in ignored_dirs):
                    continue
                rel_path = p.relative_to(root).as_posix()
                if p.stat().st_size == 0:
                    empty_files.append(rel_path)
                else:
                    valid_files.append(rel_path)

        summary = [
            f"=== Codebase Health Scan ===",
            f"Total Valid Files: {len(valid_files)}",
            f"Total Empty/Stub Files (0-byte): {len(empty_files)}",
        ]
        if empty_files:
            summary.append("\nEmpty files detected that MUST be implemented:")
            for ef in empty_files[:40]:
                summary.append(f"  - {ef}")
            if len(empty_files) > 40:
                summary.append(f"  ... and {len(empty_files) - 40} more empty files.")
        else:
            summary.append("\nCodebase is healthy: zero 0-byte stub files detected.")

        return "\n".join(summary)
    except Exception as e:
        return f"Error scanning codebase health: {str(e)}"


@tool("run_command")
def run_command(command: str, cwd: str = ".") -> str:
    """
    Executes a shell command (docker, maven, npm, python, etc.) in the project workspace.
    """
    global LAST_TEST_EXIT_CODE
    cmd_lower = command.lower()
    is_test_runner = any(k in cmd_lower for k in ["pytest", "npm run build", "npm test", "mvn test", "python -m pytest"])

    if is_test_runner and LAST_TEST_EXIT_CODE != 0 and len(MODIFIED_FILES_REGISTRY) == 0:
        return (
            f"ANTI-LOOP GUARD: Refusing to re-run '{command}'. Zero files have been modified on disk since the previous failure. "
            "Re-running the test suite on unmodified code causes an infinite loop. "
            "You MUST apply a code fix using `replace_lines`, `patch_file`, or `write_file` before running the verification command again!"
        )

    try:
        target_cwd = _sanitize_path(cwd)
        result = subprocess.run(
            command,
            cwd=target_cwd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=180,
            encoding="utf-8",
            errors="replace",
        )
        if is_test_runner:
            LAST_TEST_EXIT_CODE = result.returncode
            MODIFIED_FILES_REGISTRY.clear()

        output = []
        if result.stdout:
            stdout_text = result.stdout.strip()
            if len(stdout_text) > 4000:
                stdout_text = stdout_text[:2000] + "\n...[truncated]...\n" + stdout_text[-2000:]
            output.append(f"STDOUT:\n{stdout_text}")
        if result.stderr:
            stderr_text = result.stderr.strip()
            if len(stderr_text) > 4000:
                stderr_text = stderr_text[:2000] + "\n...[truncated]...\n" + stderr_text[-2000:]
            output.append(f"STDERR:\n{stderr_text}")
        output.append(f"EXIT CODE: {result.returncode}")
        return "\n".join(output)
    except subprocess.TimeoutExpired:
        return f"Error: Command '{command}' timed out after 180 seconds."
    except Exception as e:
        return f"Error executing command '{command}': {str(e)}"
