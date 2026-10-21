import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

AGENT_ROLES = [
    ("Business Analyst", "Requirement Analysis & Technical Blueprint", "ba"),
    ("Backend Engineer", "Backend Architecture & REST APIs", "backend"),
    ("Frontend Engineer", "Frontend & UI Implementation", "frontend"),
    ("QA Engineer", "Codebase Health & Quality Verification", "qa"),
]


class ProgressTracker:
    def __init__(self, total_tasks: int = 4, process_name: str = "sequential"):
        self.total_tasks = total_tasks
        self.process_name = process_name
        self.target_phase = "Phase 0: Project Setup & Architecture"
        self.phase_id = "0"
        self.phase_file = ""
        self.subtasks: List[Dict[str, Any]] = []
        self.completed_tasks: List[Dict[str, Any]] = []
        self.step_count = 0
        self.start_time = time.time()
        self.task_start_time = time.time()
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.json_file = self.output_dir / "progress.json"
        self.md_file = self.output_dir / "progress.md"

        self._load_phase_subtasks()
        if not self.json_file.exists() or not self.md_file.exists():
            self._update_files(status="INITIALIZED", current_task_name="Pipeline starting...")

    def set_phase_context(self, target_phase: str, phase_id: str = "0", phase_file: str = ""):
        self.target_phase = target_phase
        self.phase_id = str(phase_id)
        if phase_file:
            self.phase_file = phase_file
        self._load_phase_subtasks()
        self._update_files(status="RUNNING", current_task_name=f"Starting {target_phase}")

    def _check_file_exists(self, f_path: str) -> bool:
        """
        Dynamically verifies if a file exists on disk, supporting both absolute/relative paths
        and subpaths within backend, frontend, or other source trees regardless of language.
        """
        if not f_path or f_path.endswith("..."):
            return False
        p = Path(f_path)
        if p.exists() and p.is_file() and p.stat().st_size > 0:
            return True

        filename = p.name
        parts = p.parts
        search_roots = [Path("backend"), Path("frontend"), Path("src")]
        for base in search_roots:
            if not base.exists():
                continue
            direct = base / f_path
            if direct.exists() and direct.is_file() and direct.stat().st_size > 0:
                return True
            try:
                for match in base.glob(f"**/{filename}"):
                    if match.is_file() and match.stat().st_size > 0:
                        norm_match = match.as_posix()
                        norm_target = p.as_posix()
                        if norm_match.endswith(norm_target) or all(part in match.parts for part in parts):
                            return True
            except Exception:
                pass
        return False

    def _load_phase_subtasks(self):
        self.subtasks = []

        # 1. Try loading from latest WBS Plan (output/plans/latest_wbs.json)
        latest_wbs = self.output_dir / "plans" / "latest_wbs.json"
        if latest_wbs.exists():
            try:
                with open(latest_wbs, "r", encoding="utf-8", errors="replace") as f:
                    wbs_data = json.load(f)
                all_tasks = wbs_data.get("backend_tasks", []) + wbs_data.get("frontend_tasks", [])
                if all_tasks:
                    for t in all_tasks:
                        tid = t.get("task_id", "")
                        title = t.get("title", "")
                        target_files = t.get("target_files", [])
                        valid_files = [
                            f.strip().strip("'\"`") for f in target_files
                            if f and not f.endswith("...") and " " not in f
                        ]
                        all_exist = bool(valid_files and all(self._check_file_exists(f) for f in valid_files))
                        self.subtasks.append({
                            "id": tid,
                            "title": title,
                            "files": valid_files,
                            "completed": all_exist,
                        })
                    if self.subtasks:
                        return
            except Exception:
                pass

        # 2. Try loading from dedicated phase file
        target_path = Path(self.phase_file) if self.phase_file else None
        if target_path and target_path.exists():
            try:
                with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                matches = re.finditer(r"^###\s+(Task\s+[\d\.]+)[:\s\-]+([^\r\n]+)", content, re.MULTILINE)
                for m in matches:
                    task_id = m.group(1).strip()
                    task_title = m.group(2).strip()

                    section_start = m.end()
                    next_section = content.find("### Task", section_start)
                    section_body = content[section_start:next_section] if next_section != -1 else content[section_start:]

                    files_match = re.search(r"-\s*\*\*Files?\*\*:\s*([^\r\n]+)", section_body)
                    files_list = []
                    if files_match:
                        raw_files = files_match.group(1).replace("`", "").split(",")
                        for rf in raw_files:
                            clean_rf = rf.strip().strip("'\"").rstrip(".,;:)")
                            if clean_rf and not clean_rf.endswith("..."):
                                files_list.append(clean_rf)

                    all_exist = bool(files_list and all(self._check_file_exists(f) for f in files_list))

                    self.subtasks.append({
                        "id": task_id,
                        "title": task_title,
                        "files": files_list,
                        "completed": all_exist,
                    })
            except Exception:
                pass

    def _get_all_phases_roadmap(self) -> List[Dict[str, Any]]:
        roadmap = []

        # 1. Check plans/phases/ directory
        phases_dir = Path("plans/phases")
        if not phases_dir.exists():
            phases_dir = Path(__file__).resolve().parents[4] / "plans" / "phases"

        if phases_dir.exists():
            for pf in sorted(phases_dir.glob("PHASE_*.md")):
                try:
                    with open(pf, "r", encoding="utf-8", errors="replace") as f:
                        fc = f.read()
                    first_line = fc.splitlines()[0].strip("# \t\r\n") if fc else pf.stem
                    m = re.search(r"PHASE_([A-Za-z0-9]+)", pf.name)
                    pid = m.group(1) if m else "█"
                    tasks = re.findall(r"^###\s+Task\s+[\d\.]+", fc, re.MULTILINE)

                    key_files = []
                    for fm in re.finditer(r"-\s*\*\*Files?\*\*:\s*([^\r\n]+)", fc):
                        for rf in fm.group(1).replace("`", "").split(","):
                            clean_rf = rf.strip().strip("'\"").rstrip(".,;:)")
                            if clean_rf and clean_rf not in key_files:
                                key_files.append(clean_rf)

                    if str(self.phase_id) == str(pid):
                        st = "⏳ Active"
                    elif key_files and all(self._check_file_exists(kf) for kf in key_files[:2]):
                        st = "✅ Completed"
                    else:
                        st = "⚪ Pending"

                    roadmap.append({
                        "id": pid,
                        "title": first_line,
                        "task_count": len(tasks),
                        "status": st,
                    })
                except Exception:
                    pass

        # 2. Fallback to plans/IMPLEMENT_PLAN.md or docs/IMPLEMENT_PLAN.md
        if not roadmap:
            candidate_plans = [
                Path("plans/IMPLEMENT_PLAN.md"),
                Path("docs/IMPLEMENT_PLAN.md"),
                Path(__file__).resolve().parents[4] / "plans" / "IMPLEMENT_PLAN.md",
            ]
            for plan_path in candidate_plans:
                if plan_path.exists():
                    try:
                        with open(plan_path, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                        matches = re.finditer(r"^#{2,3}\s+Phase\s+([A-Za-z0-9]+)[:\s\-]+([^\r\n]+)", content, re.MULTILINE)
                        for m in matches:
                            pid = m.group(1).strip()
                            title = m.group(2).strip()
                            st = "⏳ Active" if str(self.phase_id) == str(pid) else "⚪ Pending"
                            roadmap.append({
                                "id": pid,
                                "title": title,
                                "task_count": "-",
                                "status": st,
                            })
                    except Exception:
                        pass
                    if roadmap:
                        break

        return roadmap

    def _render_progress_bar(self, percent: int, width: int = 25) -> str:
        clamped = max(0, min(100, percent))
        filled = int(width * (clamped / 100.0))
        empty = width - filled
        return "█" * filled + "░" * empty

    def _format_time(self, seconds: float) -> str:
        mins, secs = divmod(int(seconds), 60)
        return f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

    def _match_agent_to_role_key(self, agent_name: str) -> Optional[str]:
        a = (agent_name or "").lower()
        if "backend" in a:
            return "backend"
        if "frontend" in a or "ui" in a:
            return "frontend"
        if "qa" in a or "verification" in a or "devops" in a or "quality" in a or "gatekeeper" in a:
            return "qa"
        if "analyst" in a or "architect" in a or "business" in a or a.strip() in ("ba", "business analyst"):
            return "ba"
        return None

    def _update_files(self, status: str, current_task_name: str = ""):
        # Load phase subtasks if not loaded yet
        if not self.subtasks:
            self._load_phase_subtasks()

        for st in self.subtasks:
            if st.get("files"):
                st["completed"] = all(self._check_file_exists(f) for f in st["files"])

        # Group completed tasks by agent milestone
        role_tasks_map: Dict[str, List[Dict[str, Any]]] = {
            "ba": [],
            "backend": [],
            "frontend": [],
            "qa": [],
        }
        for t in self.completed_tasks:
            rk = self._match_agent_to_role_key(t.get("agent", ""))
            if rk in role_tasks_map:
                role_tasks_map[rk].append(t)

        # Determine milestone statuses and elapsed durations
        milestone_data = []
        completed_milestones = 0
        is_finished = status in ("FINISHED", "COMPLETED")

        for idx, (role_name, role_desc, role_key) in enumerate(AGENT_ROLES, start=1):
            tasks_for_role = role_tasks_map.get(role_key, [])
            role_duration = sum(t.get("duration", 0) for t in tasks_for_role)
            subtask_count = len(tasks_for_role)

            # Check if any subsequent role has already run
            subsequent_has_tasks = any(
                len(role_tasks_map.get(k, [])) > 0
                for _, _, k in AGENT_ROLES[idx:]
            )

            if is_finished or subsequent_has_tasks:
                role_status = "✅ Completed"
                completed_milestones += 1
            elif subtask_count > 0:
                if status == "RUNNING":
                    role_status = "⏳ Running"
                else:
                    role_status = "✅ Completed"
                    completed_milestones += 1
            elif idx == completed_milestones + 1 and status in ("RUNNING", "INITIALIZED"):
                role_status = "⏳ Running"
            else:
                role_status = "⏸️ Queued"

            milestone_data.append({
                "index": idx,
                "role_name": role_name,
                "role_desc": role_desc,
                "role_key": role_key,
                "duration": role_duration,
                "subtask_count": subtask_count,
                "status": role_status,
            })

        if is_finished:
            completed_milestones = self.total_tasks

        percent = int((completed_milestones / self.total_tasks) * 100) if self.total_tasks > 0 else 0
        percent = max(0, min(100, percent))
        elapsed = time.time() - self.start_time
        roadmap = self._get_all_phases_roadmap()

        data = {
            "status": status,
            "process": self.process_name,
            "target_phase": self.target_phase,
            "phase_id": self.phase_id,
            "phase_subtasks": self.subtasks,
            "completed_milestones": completed_milestones,
            "total_milestones": self.total_tasks,
            "completed_agent_tasks": len(self.completed_tasks),
            "progress_percent": percent,
            "current_step": self.step_count,
            "current_task": current_task_name,
            "elapsed_seconds": round(elapsed, 1),
            "elapsed_formatted": self._format_time(elapsed),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "milestones": milestone_data,
            "agent_tasks": self.completed_tasks,
            "phases_roadmap": roadmap,
        }

        try:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        try:
            bar = self._render_progress_bar(percent, 25)
            lines = [
                "# 🚀 Autonomous Software Engineering - Live Progress Tracker",
                "",
                f"- **Target Phase:** `{self.target_phase}`",
                f"- **Process Mode:** `{self.process_name.upper()}` (BA -> Backend -> Frontend -> QA)",
                f"- **Status:** `{status}`",
                f"- **Overall Pipeline Progress:** `[{bar}] {percent}%` ({completed_milestones}/{self.total_tasks} Agent Milestones)",
                f"- **Total Agent Tasks Executed:** {len(self.completed_tasks)}",
                f"- **Total Agent Steps:** {self.step_count}",
                f"- **Elapsed Time:** {self._format_time(elapsed)}",
                f"- **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "---",
                "",
            ]

            if self.subtasks:
                lines.append(f"### 📋 Phase {self.phase_id} Checklist & Work Breakdown")
                for st in self.subtasks:
                    mark = "[x]" if st["completed"] else "[ ]"
                    files_hint = f" *(Files: {', '.join(st['files'])})*" if st.get("files") else ""
                    status_tag = " ✅ Done" if st["completed"] else ""
                    lines.append(f"- {mark} **{st['id']}**: {st['title']}{files_hint}{status_tag}")
                lines.append("")
                lines.append("---")
                lines.append("")

            lines.extend([
                "### 🤖 CrewAI Agent Milestones",
                "| # | Agent Role | Task Description | Duration | Status |",
                "|---|------------|------------------|----------|--------|",
            ])

            for m in milestone_data:
                dur_str = self._format_time(m["duration"]) if m["duration"] > 0 else "-"
                lines.append(f"| {m['index']} | {m['role_name']} | {m['role_desc']} | {dur_str} | {m['status']} |")

            lines.append("")
            lines.append("---")
            lines.append("")

            if roadmap:
                lines.extend([
                    "### 🗺️ Project Roadmap",
                    "| Phase | Milestone | Subtasks | Status |",
                    "|-------|-----------|----------|--------|",
                ])
                for pm in roadmap:
                    lines.append(f"| **Phase {pm['id']}** | {pm['title']} | {pm['task_count']} subtasks | {pm['status']} |")

            with open(self.md_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception:
            pass

    def on_step(self, step_output: Any):
        self.step_count += 1
        elapsed = time.time() - self.start_time
        tool_name = "Step action"
        if hasattr(step_output, "tool"):
            tool_name = f"Tool '{step_output.tool}'"
        elif isinstance(step_output, tuple) and len(step_output) > 0 and hasattr(step_output[0], "tool"):
            tool_name = f"Tool '{step_output[0].tool}'"
        elif isinstance(step_output, dict) and "tool" in step_output:
            tool_name = f"Tool '{step_output['tool']}'"

        print(f"  [⚡ Step #{self.step_count:02d} | {self._format_time(elapsed)}] Executing: {tool_name}")
        self._update_files(status="RUNNING")

    def on_task_completed(self, task_output: Any):
        task_duration = time.time() - self.task_start_time
        self.task_start_time = time.time()

        agent_role = getattr(task_output, "agent", "Unknown Agent")
        if isinstance(agent_role, str):
            agent_role = agent_role.split("\n")[0].strip()

        task_name = getattr(task_output, "name", None)
        if not task_name:
            task_desc = getattr(task_output, "description", "")
            first_line = task_desc.strip().split("\n")[0] if task_desc else f"Task {len(self.completed_tasks) + 1}"
            task_name = first_line[:50] + ("..." if len(first_line) > 50 else "")

        task_entry = {
            "index": len(self.completed_tasks) + 1,
            "name": task_name,
            "agent": agent_role,
            "duration": round(task_duration, 2),
            "completed_at": datetime.now().strftime("%H:%M:%S"),
        }
        self.completed_tasks.append(task_entry)

        # Re-compute overall milestone progress
        role_tasks_map: Dict[str, List[Dict[str, Any]]] = {
            "ba": [],
            "backend": [],
            "frontend": [],
            "qa": [],
        }
        for t in self.completed_tasks:
            rk = self._match_agent_to_role_key(t.get("agent", ""))
            if rk in role_tasks_map:
                role_tasks_map[rk].append(t)

        completed_milestones = sum(1 for rk, tlist in role_tasks_map.items() if len(tlist) > 0)
        completed_milestones = max(0, min(self.total_tasks, completed_milestones))
        percent = int((completed_milestones / self.total_tasks) * 100) if self.total_tasks > 0 else 0
        percent = max(0, min(100, percent))
        elapsed = time.time() - self.start_time
        bar = self._render_progress_bar(percent, 25)

        print("\n" + "█" * 72)
        print(f" 🚀 PROGRESS MILESTONE: [{bar}] {percent}% ({completed_milestones}/{self.total_tasks} Milestones | Task #{len(self.completed_tasks)})")
        print(f"    [✔] Completed : {task_name}")
        print(f"    [🤖] Agent     : {agent_role}")
        print(f"    [⏱️] Task Time : {self._format_time(task_duration)} (Total Elapsed: {self._format_time(elapsed)})")
        print("█" * 72 + "\n")

        self._update_files(status="RUNNING" if percent < 100 else "FINISHED", current_task_name=task_name)

    def finish(self):
        total_time = time.time() - self.start_time
        self._update_files(status="COMPLETED")
        
        # Auto-archive coding_team_report.md to output/reports/
        try:
            report_src = self.output_dir / "coding_team_report.md"
            if report_src.exists() and report_src.stat().st_size > 0:
                reports_dir = self.output_dir / "reports"
                reports_dir.mkdir(parents=True, exist_ok=True)
                clean_name = re.sub(r'[^\w\-_.]', '_', self.target_phase or "phase").strip('_')
                clean_name = re.sub(r'_+', '_', clean_name)[:60]
                t_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dst_report = reports_dir / f"report_{clean_name}_{t_stamp}.md"
                import shutil
                shutil.copy2(report_src, dst_report)
        except Exception:
            pass
        bar = self._render_progress_bar(100, 25)
        print("\n" + "█" * 72)
        print(f" 🎉 MISSION COMPLETED: [{bar}] 100%")
        print(f"    Total Tasks Completed : {len(self.completed_tasks)}/{self.total_tasks}")
        print(f"    Total Agent Steps     : {self.step_count}")
        print(f"    Total Pipeline Time   : {self._format_time(total_time)}")
        print(f"    Progress Files Saved  : {self.json_file.as_posix()} | {self.md_file.as_posix()}")
        print("█" * 72 + "\n")

    def fail(self, error_message: str = "Build validation failed"):
        total_time = time.time() - self.start_time
        self._update_files(status="FAILED_NEEDS_HUMAN", current_task_name=f"Failed: {error_message[:60]}")
        print("\n" + "!" * 72)
        print(f" ❌ PIPELINE FAILED: {error_message}")
        print(f"    Total Pipeline Time   : {self._format_time(total_time)}")
        print(f"    Progress Files Saved  : {self.json_file.as_posix()} | {self.md_file.as_posix()}")
        print("!" * 72 + "\n")


progress_tracker = ProgressTracker(total_tasks=4)


def global_step_callback(step_output: Any):
    progress_tracker.on_step(step_output)


def global_task_callback(task_output: Any):
    progress_tracker.on_task_completed(task_output)
