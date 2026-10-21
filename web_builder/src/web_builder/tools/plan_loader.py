import os
import re
from pathlib import Path
from typing import Dict, Any, List

# In-memory resident cache to ensure plans exist directly in volatile memory (RAM)
_PLAN_MEMORY_CACHE: Dict[str, Any] = {}


def load_plans(plans_dir: str | Path = "plans", force_reload: bool = False) -> Dict[str, Any]:
    """
    Scans the plans and docs directories and loads specification documents directly into memory.
    Maintains an in-memory resident cache (_PLAN_MEMORY_CACHE) for zero-latency retrieval.
    Extracts project topic and builds a concise, token-efficient executive summary.
    """
    cache_key = str(plans_dir)
    if not force_reload and cache_key in _PLAN_MEMORY_CACHE:
        return _PLAN_MEMORY_CACHE[cache_key]

    root_dir = Path.cwd()
    plans_path = Path(plans_dir)
    if not plans_path.is_absolute() and not plans_path.exists():
        candidate = Path(__file__).resolve().parents[3] / plans_dir
        if candidate.exists():
            plans_path = candidate

    # Standard directories to scan for specifications
    scan_paths = [plans_path]
    docs_candidate = Path("docs")
    if not docs_candidate.is_absolute() and not docs_candidate.exists():
        docs_candidate = Path(__file__).resolve().parents[3] / "docs"
    if docs_candidate.exists():
        scan_paths.append(docs_candidate)

    plan_files: List[Path] = []
    for sp in scan_paths:
        if sp.exists() and sp.is_dir():
            for ext in ("*.md", "*.txt"):
                plan_files.extend(sp.glob(ext))

    # Also check additional contract files
    extra_files = ["AGENTS.md", "design/DESIGN_SYSTEM.md", "qa/TEST_PLAN.md", "state/PROJECT_STATE.md", "state/HANDOFF.md"]
    for ef in extra_files:
        ef_path = Path(ef)
        if not ef_path.is_absolute() and not ef_path.exists():
            ef_path = Path(__file__).resolve().parents[3] / ef
        if ef_path.exists() and ef_path.is_file() and ef_path not in plan_files:
            plan_files.append(ef_path)

    plan_files = sorted(list(set(plan_files)), key=lambda p: (p.parent.name, p.name))

    if not plan_files:
        result = {
            "topic": "Autonomous Software Project",
            "plans_dir": str(plans_path),
            "plan_files": [],
            "plans_summary": f"No plan documents found in '{plans_dir}' or 'docs/'. Agents will proceed with default guidelines.",
            "plans_dict": {},
        }
        _PLAN_MEMORY_CACHE[cache_key] = result
        return result

    plans_dict: Dict[str, str] = {}
    doc_manifest: List[str] = []

    for p in plan_files:
        rel_key = p.as_posix()
        try:
            rel_key = p.relative_to(root_dir).as_posix()
        except Exception:
            rel_key = f"{p.parent.name}/{p.name}" if p.parent.name else p.name

        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
                plans_dict[p.name] = content
                plans_dict[rel_key] = content
                doc_manifest.append(f"- `{rel_key}` ({len(content):,} chars)")
        except Exception as e:
            doc_manifest.append(f"- `{rel_key}` (Error: {e})")

    # Infer topic dynamically from PRD or first markdown file
    inferred_topic = "Autonomous Software Project"
    prd_content = plans_dict.get("PRD.md") or plans_dict.get("docs/PRD.md") or plans_dict.get("prd.md") or ""
    if prd_content:
        match = re.search(r"(?:Product|Project) Name:\s*([^\n\r]+)", prd_content, re.IGNORECASE)
        if match:
            inferred_topic = match.group(1).strip().strip("*_`")
        else:
            first_header = re.search(r"^#\s+([^\n\r]+)", prd_content, re.MULTILINE)
            if first_header:
                clean_h = first_header.group(1).strip().replace("—", "-").replace("–", "-")
                clean_h = re.sub(r"^PRD\s*[-:]*\s*", "", clean_h, flags=re.IGNORECASE).strip()
                inferred_topic = clean_h or inferred_topic

    # Construct a high-density, concise executive summary
    manifest_str = "\n".join(doc_manifest)
    plans_summary = f"""# Project Specifications & Architecture Summary
- **Target Application**: {inferred_topic}
- **Architecture Pattern**: Fullstack Monorepo (`backend/` Spring Boot 3 + `frontend/` React 19 + TypeScript + TailwindCSS + `design/` UI Design System)
- **Database & Infrastructure**: PostgreSQL 16, Redis, Docker Compose
- **Standardized Work Contracts**:
  * `AGENTS.md`: Mandatory agent rules and engineering workflows
  * `docs/`: PRD.md, ARCHITECTURE.md, DATA_MODEL.md, API_CONTRACTS.md, BUSINESS_RULES.md
  * `design/`: DESIGN_SYSTEM.md (Fintech Prestige UI Tokens)
  * `plans/`: IMPLEMENT_PLAN.md, TASKS.md
  * `state/`: PROJECT_STATE.md, HANDOFF.md
  * `qa/`: TEST_PLAN.md
- **Mandatory Engineering Rules**:
  * **SOLID**: Single Responsibility, Open-Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.
  * **ACID**: All state-modifying service operations must use `@Transactional(rollbackFor = Exception.class)`.
  * **Zero-Float**: All monetary and numeric fields strictly use `Long` or `BigDecimal`, never `float` or `double`.
  * **Interface + Impl**: Service interfaces in `service/` and implementations in `service/impl/`.
  * **Contracts**: camelCase for REST DTO properties and TypeScript interfaces; snake_case for DB columns.
- **Available Specification Documents**:
{manifest_str}

> **Agent Note**: Detailed specifications reside in memory and on disk. Use `read_file('<file_path>')` to inspect schemas, contracts, or business rules."""

    result = {
        "topic": inferred_topic,
        "plans_dir": str(plans_path),
        "plan_files": [p.name for p in plan_files],
        "plans_summary": plans_summary,
        "plans_dict": plans_dict,
    }

    _PLAN_MEMORY_CACHE[cache_key] = result
    return result


def get_phase_scope(
    phase_arg: str | None,
    plans_dict: Dict[str, str],
    plans_dir: str | Path = "plans",
    task_arg: str | None = None,
) -> Dict[str, Any]:
    """
    Extracts a specific Phase or Subtask(s) from dedicated 'plans/phases/PHASE_<id>_*.md' or IMPLEMENT_PLAN.md.
    Enforces progress-aware execution by linking with 'output/progress.md'.
    Supports subtask isolation e.g. task_arg='1.1' or phase_arg='1.1'.
    """
    clean_arg = (phase_arg or "all").strip().lower()
    clean_arg = re.sub(r"^phase\s*", "", clean_arg)

    # Detect subtask filtering from task_arg or composite phase_arg (e.g. '1.1' or '1.1,1.2')
    target_tasks = []
    if task_arg:
        target_tasks = [t.strip().lstrip("task").strip() for t in task_arg.split(",") if t.strip()]
    elif "." in clean_arg:
        parts = clean_arg.split(",")
        clean_arg = parts[0].split(".")[0].strip()
        target_tasks = [p.strip().lstrip("task").strip() for p in parts if p.strip()]

    plans_path = Path(plans_dir)
    if not plans_path.is_absolute() and not plans_path.exists():
        candidate = Path(__file__).resolve().parents[3] / plans_dir
        if candidate.exists():
            plans_path = candidate

    phases_dir = plans_path / "phases"

    if clean_arg in ("all", "", "none"):
        # Automatically detect the first incomplete phase so agents have concrete files to code!
        if phases_dir.exists():
            for pf in sorted(phases_dir.glob("PHASE_*.md")):
                try:
                    with open(pf, "r", encoding="utf-8", errors="replace") as f:
                        fc = f.read()
                    m = re.search(r"PHASE_([A-Za-z0-9]+)", pf.name)
                    pid = m.group(1) if m else "0"
                    # Extract files mentioned in the phase
                    phase_files = []
                    for fm in re.finditer(r"-\s*\*\*Files?\*\*:\s*([^\r\n]+)", fc):
                        for rf in fm.group(1).replace("`", "").split(","):
                            c = rf.strip().strip("'\"").rstrip(".,;:)")
                            if c and c not in phase_files and not c.endswith("..."):
                                phase_files.append(c)
                    missing = [f for f in phase_files if not (Path(f).exists() and Path(f).stat().st_size > 0)]
                    if missing:
                        clean_arg = pid
                        break
                except Exception:
                    pass
        if clean_arg in ("all", "", "none"):
            clean_arg = "0" 

    # Match dedicated phase file e.g. plans/phases/PHASE_0_SETUP.md
    if phases_dir.exists():
        matched = list(phases_dir.glob(f"PHASE_{clean_arg}_*.md")) or list(phases_dir.glob(f"PHASE_{clean_arg}.md"))
        if matched:
            target_file = matched[0]
            try:
                with open(target_file, "r", encoding="utf-8", errors="replace") as f:
                    file_content = f.read().strip()
                first_line = file_content.splitlines()[0] if file_content else f"Phase {clean_arg}"
                clean_title = first_line.strip("# \t\r\n")
                # Subtask isolation if requested (e.g. Task 1.1 or Task 1.1 + 1.2)
                if target_tasks:
                    extracted_sections = []
                    for t_id in target_tasks:
                        pattern = r"(###\s+Task\s+" + re.escape(t_id) + r"[:\s\-]+[^\r\n]+)(.*?)(?=\r?\n###\s+Task|\Z)"
                        m = re.search(pattern, file_content, re.DOTALL | re.IGNORECASE)
                        if m:
                            extracted_sections.append(m.group(0).strip())
                    if extracted_sections:
                        focused_scope = "\n\n---\n\n".join(extracted_sections)
                        task_str = ", ".join(f"Task {t}" for t in target_tasks)
                        clean_title_focused = f"{clean_title} [{task_str}]"
                        return {
                            "target_phase": clean_title_focused,
                            "phase_id": clean_arg,
                            "phase_file": target_file.as_posix(),
                            "target_tasks": target_tasks,
                            "phase_scope": f"""### [TARGET SUBTASK EXECUTION SCOPE: {clean_title_focused}]
> **Dedicated Phase File**: `{target_file.as_posix()}`
> **Focused Subtasks**: {task_str}
> **Instruction**: You are strictly tasked with executing ONLY the subtask(s) specified below. Do not work on other tasks in this phase yet.

{focused_scope}""",
                            "is_single_phase": True,
                        }

                return {
                    "target_phase": clean_title,
                    "phase_id": clean_arg,
                    "phase_file": target_file.as_posix(),
                    "target_tasks": [],
                    "phase_scope": f"""### [TARGET PHASE EXECUTION SCOPE: {clean_title}]
> **Dedicated Phase File**: `{target_file.as_posix()}`
> **Progress Check**: Đọc file `output/progress.md` trước để nhận diện task đã hoàn thành `[x]` và bỏ qua không làm lại.

{file_content}""",
                    "is_single_phase": True,
                }
            except Exception:
                pass

    # Fallback to IMPLEMENT_PLAN.md regex
    implement_text = plans_dict.get("IMPLEMENT_PLAN.md") or plans_dict.get("implement_plan.md") or plans_dict.get("plans/IMPLEMENT_PLAN.md") or ""
    pattern = r"(#{2,3}\s+Phase\s+" + re.escape(clean_arg) + r"[:\s]+[^\n\r]+)(.*?)(?=\n#{2,3}\s+Phase|\Z)"
    match = re.search(pattern, implement_text, re.DOTALL | re.IGNORECASE)

    if match:
        header = match.group(1).strip("# \t\r\n")
        body = match.group(2).strip()
        full_phase = f"### [TARGET PHASE EXECUTION SCOPE: {header}]\n> Source: `plans/IMPLEMENT_PLAN.md`\n> State Check: Đọc `output/progress.md` trước khi code.\n\n{body}"
        return {
            "target_phase": header,
            "phase_id": clean_arg,
            "phase_file": "plans/IMPLEMENT_PLAN.md",
            "phase_scope": full_phase,
            "is_single_phase": True,
        }
    else:
        return {
            "target_phase": f"Phase {clean_arg}",
            "phase_id": clean_arg,
            "phase_file": f"plans/phases/PHASE_{clean_arg}.md",
            "phase_scope": f"Tập trung thực hiện các mục tiêu thuộc Phase {clean_arg}. Đọc `output/progress.md` tr??c khi th?c thi.",
            "is_single_phase": True,
        }
