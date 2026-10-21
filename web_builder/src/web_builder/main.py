#!/usr/bin/env python
import os
import sys
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from crewai.flow import Flow, listen, start
from web_builder.tools.plan_loader import load_plans, get_phase_scope
from web_builder.tools.progress_tracker import progress_tracker
from web_builder.crews.content_crew.content_crew import ContentCrew


def extract_wbs_json(raw_output: str) -> dict:
    """Extracts the structured JSON Work Breakdown Structure from the BA output."""
    if not raw_output:
        return {}
    # 1. Try finding fenced json code block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_output, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    # 2. Try finding outermost JSON object containing key schema fields
    match = re.search(r'(\{[\s\S]*"(?:backend_tasks|phase_name)"[\s\S]*\})', raw_output)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return {}


def generate_wbs_from_scope(target_phase: str, phase_scope: str) -> tuple[dict, str]:
    """
    Deterministically generates a rich, valid WBS schema when the LLM BA output
    is empty or missing valid JSON blocks (e.g. due to rate limits or API hiccups).
    """
    be_files = []
    fe_files = []

    # Match referenced file paths in the phase scope
    for f in re.findall(r"(?:backend|frontend)[a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+", phase_scope):
        clean_f = f.replace("\\", "/")
        if clean_f.startswith("backend/"):
            if clean_f not in be_files:
                be_files.append(clean_f)
        elif clean_f.startswith("frontend/"):
            if clean_f not in fe_files:
                fe_files.append(clean_f)

    # Classify backend files into BE-1, BE-2, BE-3
    be_1_files = [f for f in be_files if any(k in f.lower() for k in ["entity", "dto", "repository", "model", "enum"])]
    be_2_files = [f for f in be_files if "service" in f.lower()]
    be_3_files = [f for f in be_files if any(k in f.lower() for k in ["controller", "config", "security", "test"])]

    leftover_be = [f for f in be_files if f not in be_1_files and f not in be_2_files and f not in be_3_files]
    if leftover_be:
        be_2_files.extend(leftover_be)

    # Classify frontend files into FE-1, FE-2
    fe_1_files = [f for f in fe_files if any(k in f.lower() for k in ["type", "service", "api"])]
    fe_2_files = [f for f in fe_files if any(k in f.lower() for k in ["page", "component", "modal", "view", "css"])]

    leftover_fe = [f for f in fe_files if f not in fe_1_files and f not in fe_2_files]
    if leftover_fe:
        fe_2_files.extend(leftover_fe)

    clean_title = target_phase or "Current Phase"
    summary = f"Architectural Work Breakdown Structure and Execution Plan for {clean_title}."

    wbs_dict = {
        "phase_name": clean_title,
        "summary": summary,
        "backend_tasks": [
            {
                "task_id": "BE-1",
                "title": "Data Contracts, Schemas & Models",
                "target_files": be_1_files if be_1_files else ["SQLAlchemy models, Pydantic schemas and Repositories"],
                "details": "Create SQLAlchemy 2.x models, Pydantic v2 schemas, and repositories."
            },
            {
                "task_id": "BE-2",
                "title": "Business Logic & Services (ACID & Precision)",
                "target_files": be_2_files if be_2_files else ["Service modules and Business Logic"],
                "details": "Create Service functions/classes in services/. Enforce ACID transactions and zero-float precision."
            },
            {
                "task_id": "BE-3",
                "title": "FastAPI Routers, Auth Guards & Tests",
                "target_files": be_3_files if be_3_files else ["FastAPI router endpoints and Pytest suites"],
                "details": "Implement FastAPI routers in api/v1/, dependency injection, route guards, and write pytest suites."
            }
        ],
        "frontend_tasks": [
            {
                "task_id": "FE-1",
                "title": "TypeScript Types & API Services",
                "target_files": fe_1_files if fe_1_files else ["TypeScript interfaces and API clients"],
                "details": "Create TypeScript types synced 1:1 with backend Pydantic schemas, and API client methods using authenticated client."
            },
            {
                "task_id": "FE-2",
                "title": "UI Pages, Components & Design System Layout",
                "target_files": fe_2_files if fe_2_files else ["UI Components and Pages"],
                "details": "Implement UI pages and components faithful to design mockups in design/, with navigation shell and design system tokens."
            }
        ],
        "acceptance_criteria": [
            "pytest passes with 0 failures and 0 errors",
            "npm run build passes with 0 TypeScript/Vite errors",
            "All endpoints and components specified in phase scope are operational"
        ]
    }

    json_str = json.dumps(wbs_dict, indent=2, ensure_ascii=False)
    md_content = f"""# Work Breakdown Structure (WBS) - {clean_title}

## Executive Summary
{summary}

## 1. Backend Implementation Plan
### [BE-1] Data Contracts & Repositories
- **Target Files**: {', '.join(wbs_dict['backend_tasks'][0]['target_files'])}
- **Scope**: {wbs_dict['backend_tasks'][0]['details']}

### [BE-2] Business Logic & Services (ACID & Precision)
- **Target Files**: {', '.join(wbs_dict['backend_tasks'][1]['target_files'])}
- **Scope**: {wbs_dict['backend_tasks'][1]['details']}

### [BE-3] REST Controllers, Security & Tests
- **Target Files**: {', '.join(wbs_dict['backend_tasks'][2]['target_files'])}
- **Scope**: {wbs_dict['backend_tasks'][2]['details']}

## 2. Frontend Implementation Plan
### [FE-1] TypeScript Types & API Services
- **Target Files**: {', '.join(wbs_dict['frontend_tasks'][0]['target_files'])}
- **Scope**: {wbs_dict['frontend_tasks'][0]['details']}

### [FE-2] UI Pages, Components & Design Layout
- **Target Files**: {', '.join(wbs_dict['frontend_tasks'][1]['target_files'])}
- **Scope**: {wbs_dict['frontend_tasks'][1]['details']}

## 3. Acceptance Criteria
1. mvn test passes with 0 failures and 0 errors.
2. npm run build passes with 0 TypeScript/Vite errors.
3. All target files exist with complete implementations.

```json
{json_str}
```
"""
    return wbs_dict, md_content


class CodingState(BaseModel):
    plans_dir: str = "plans"
    design_dir: str = "design"
    topic: str = ""
    phase: str = ""
    task: str = ""
    target_phase: str = ""
    phase_scope: str = ""
    plan_files: list[str] = Field(default_factory=list)
    plans_summary: str = ""

    # Stage 1: BA Decomposition Plan & Logs
    decomposition_raw: str = ""
    decomposition_plan: dict = Field(default_factory=dict)
    wbs_file_path: str = ""

    # Stage 2: Backend Tier Execution
    backend_result: str = ""
    backend_passed: bool = False

    # Stage 3: Frontend Tier Execution
    frontend_result: str = ""
    frontend_passed: bool = False

    # Stage 4: QA Sign-off
    qa_result: str = ""
    result: str = ""

    # Global Build Gate
    build_passed: bool = False
    repair_attempts: int = 0
    build_error_log: str = ""


ContentState = CodingState


def generate_diagnostics_markdown(component: str, command: str, err_log: str, attempt: int, max_attempts: int, phase_scope: str) -> Path:
    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    diag_file = out_dir / "DIAGNOSTICS.md"

    # Auto-extract failing files & lines
    detected_locations = []
    failed_tests = []

    # 1. Pytest traceback locations: (app/xxx.py:123 or tests/xxx.py:123)
    for m in re.finditer(r"(?:backend[/\\])?((?:app|tests)[/\\][a-zA-Z0-9_\-\.\/\\]+\.py):(\d+)", err_log):
        file_path = f"backend/{m.group(1).replace(chr(92), '/')}"
        line_num = m.group(2)
        loc = f"{file_path} (Line {line_num})"
        if loc not in detected_locations:
            detected_locations.append(loc)

    # 2. Pytest failed items: FAILED tests/test_foo.py::test_bar
    for m in re.findall(r"FAILED\s+([^\s]+)", err_log):
        failed_tests.append(f"FAILED {m}")

    # 3. Pytest root cause line (E   ...):
    for m in re.finditer(r"^E\s+([^\r\n]+)", err_log, re.MULTILINE):
        e_msg = m.group(1).strip()
        if e_msg and e_msg not in failed_tests and len(failed_tests) < 8:
            failed_tests.append(f"Root Cause: {e_msg}")

    # 4. TS errors: src/foo/bar.tsx(10,5): error TS...
    for m in re.finditer(r"((?:src|app)[/\\][a-zA-Z0-9_\-\.\/\\]+\.[tj]sx?)\((\d+)(?:,\d+)?\):\s*(error\s+TS\d+:\s*[^\r\n]+)", err_log):
        file_path = f"frontend/{m.group(1).replace(chr(92), '/')}"
        line_num = m.group(2)
        err_msg = m.group(3)
        loc = f"{file_path} (Line {line_num})"
        if loc not in detected_locations:
            detected_locations.append(loc)
        failed_tests.append(f"{loc}: {err_msg}")

    loc_str = "\n".join(f"- 🎯 `{loc}`" for loc in detected_locations) if detected_locations else "- Check the detailed traceback below."
    test_str = "\n".join(f"- ❌ `{t}`" for t in failed_tests) if failed_tests else "- Check the test summary below."

    clean_err = err_log.strip()
    if len(clean_err) > 8000:
        if "FAILURES" in clean_err:
            fail_idx = clean_err.find("FAILURES")
            clean_err = clean_err[max(0, fail_idx - 500) : fail_idx + 7500]
        else:
            clean_err = clean_err[-8000:]

    content = f"""# 🚨 ERROR DIAGNOSTICS & FIX GUIDE (Attempt {attempt}/{max_attempts})

- **Component**: {component}
- **Failing Command**: `{command}`
- **Scope**: {phase_scope[:180]}...

## 1. Failing Tests / Targets
{test_str}

## 2. Identified Source File Locations
{loc_str}

## 3. Failure Traceback
```
{clean_err}
```

## 4. Mandatory Fix Protocol for Agent
1. **Locate**: Read the identified file using `read_file(file_path=...)` around the failing line number.
2. **Apply Code Fix Immediately**:
   - Primary Recommendation: Use `replace_lines(file_path=..., start_line=..., end_line=..., replacement=...)` to replace the exact failing lines directly by line number.
   - Or use `patch_file(file_path=..., search_text=..., replace_text=...)`.
   - **FALLBACK**: If `patch_file` fails, IMMEDIATELY call `replace_lines` or `write_file` to write the fixed code!
   - **ANTI-LOOP GUARD**: `run_command` will physically REJECT executing `{command}` until code changes are saved on disk!
3. **Verify**: Run `run_command(command="{command}", cwd="{ 'backend' if component == 'Backend' else 'frontend' }")` to ensure 0 errors.
"""
    with open(diag_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n📄 [Saved Diagnostics File]: {diag_file.resolve().as_posix()}")
    return diag_file


class CodingFlow(Flow[CodingState]):

    @start()
    def initialize_flow(self):
        print("=" * 65)
        print("🚀 Initializing Autonomous Software Engineering Flow (Approach A)")
        print("=" * 65)

        if not self.state.phase:
            env_phase = os.getenv("PHASE", "").strip()
            if env_phase:
                self.state.phase = env_phase
            else:
                for idx, arg in enumerate(sys.argv):
                    if arg in ("--phase", "-p") and idx + 1 < len(sys.argv):
                        self.state.phase = sys.argv[idx + 1].strip()
                        break
                    elif arg.startswith("--phase=") or arg.startswith("phase="):
                        self.state.phase = arg.split("=", 1)[1].strip()
                        break

        plan_data = load_plans(self.state.plans_dir)
        phase_info = get_phase_scope(self.state.phase, plan_data.get("plans_dict", {}), task_arg=self.state.task or None)
        self.state.target_phase = phase_info["target_phase"]
        self.state.phase_scope = phase_info["phase_scope"]

        # Link phase context to real-time progress tracker
        progress_tracker.set_phase_context(
            target_phase=self.state.target_phase,
            phase_id=phase_info.get("phase_id", "0"),
            phase_file=phase_info.get("phase_file", ""),
        )

        if not self.state.topic:
            if phase_info["is_single_phase"]:
                self.state.topic = f"{plan_data['topic']} - {self.state.target_phase}"
            else:
                self.state.topic = plan_data["topic"]
        self.state.plan_files = plan_data["plan_files"]
        self.state.plans_summary = plan_data["plans_summary"]

        print(f"[+] Plans Folder : {plan_data['plans_dir']}")
        print(f"[+] Inferred Topic: {self.state.topic}")
        print(f"[+] Target Phase : {self.state.target_phase}")
        print(f"[+] Loaded Plans : {', '.join(self.state.plan_files) if self.state.plan_files else 'None'}")

    @listen(initialize_flow)
    def plan_and_decompose(self):
        """
        Stage 1: BA reads PRD/Architecture and decomposes phase into
        an atomic Work Breakdown Structure (WBS) with zero-touch automation and full logging.
        """
        print("\n" + "=" * 65)
        print("📋 STAGE 1: BA REQUIREMENT ANALYSIS & TASK DECOMPOSITION (Zero-Touch)")
        print("=" * 65)

        ba_crew_instance = ContentCrew().ba_crew()
        execution_result = ba_crew_instance.kickoff(
            inputs={
                "topic": self.state.topic,
                "plans_dir": self.state.plans_dir,
                "design_dir": self.state.design_dir,
                "target_phase": self.state.target_phase,
                "phase_scope": self.state.phase_scope,
                "plan_files": ", ".join(self.state.plan_files),
                "plans_summary": self.state.plans_summary,
            }
        )

        raw_text = str(execution_result.raw if hasattr(execution_result, "raw") else execution_result)
        self.state.decomposition_raw = raw_text
        wbs_dict = extract_wbs_json(raw_text)

        # 1. Check if BA agent wrote directly to output/plans/latest_wbs.json
        if not wbs_dict or not wbs_dict.get("backend_tasks"):
            disk_wbs = Path("output/plans/latest_wbs.json")
            if disk_wbs.exists():
                try:
                    with open(disk_wbs, "r", encoding="utf-8") as f:
                        candidate = json.load(f)
                    if candidate.get("backend_tasks"):
                        wbs_dict = candidate
                except Exception:
                    pass

        # 2. If still empty (e.g. rate limit 429 or empty LLM output), invoke deterministic generator
        if not wbs_dict or not wbs_dict.get("backend_tasks"):
            print("\n[!] BA LLM output missing JSON block or hit rate limit. Generating deterministic WBS from phase specifications...")
            wbs_dict, auto_md = generate_wbs_from_scope(self.state.target_phase, self.state.phase_scope)
            if not raw_text or "⚠️" in raw_text or "error" in raw_text.lower():
                raw_text = auto_md
            self.state.decomposition_raw = raw_text

        self.state.decomposition_plan = wbs_dict

        # Save WBS Plan to Disk (Structured JSON and Markdown)
        plans_out_dir = Path("output") / "plans"
        plans_out_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_phase = re.sub(r"[^\w\-_.]", "_", self.state.target_phase or "phase").strip("_")
        clean_phase = re.sub(r"_+", "_", clean_phase)[:50]

        json_path = plans_out_dir / f"wbs_{clean_phase}_{timestamp}.json"
        md_path = plans_out_dir / f"wbs_{clean_phase}_{timestamp}.md"
        latest_json = plans_out_dir / "latest_wbs.json"
        latest_md = plans_out_dir / "latest_wbs.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(wbs_dict, f, indent=2, ensure_ascii=False)
        with open(latest_json, "w", encoding="utf-8") as f:
            json.dump(wbs_dict, f, indent=2, ensure_ascii=False)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(raw_text)
        with open(latest_md, "w", encoding="utf-8") as f:
            f.write(raw_text)

        self.state.wbs_file_path = str(json_path)

        # Print Visual WBS Summary Table to Console
        print("\n" + "=" * 65)
        print("📋 BA WORK BREAKDOWN STRUCTURE (WBS) LOGGED")
        print("=" * 65)
        print(f"Target Phase : {self.state.target_phase}")
        print(f"Summary      : {wbs_dict.get('summary', 'Decomposition completed.')}")

        be_tasks = wbs_dict.get("backend_tasks", [])
        if be_tasks:
            print("\n[BACKEND ATOMIC SUB-TASKS]:")
            for t in be_tasks:
                tid = t.get("task_id", "BE")
                title = t.get("title", "")
                files = ", ".join(t.get("target_files", []))
                print(f"  • [{tid}] {title}")
                if files:
                    print(f"    Target Files: {files}")

        fe_tasks = wbs_dict.get("frontend_tasks", [])
        if fe_tasks:
            print("\n[FRONTEND ATOMIC SUB-TASKS]:")
            for t in fe_tasks:
                tid = t.get("task_id", "FE")
                title = t.get("title", "")
                files = ", ".join(t.get("target_files", []))
                print(f"  • [{tid}] {title}")
                if files:
                    print(f"    Target Files: {files}")

        criteria = wbs_dict.get("acceptance_criteria", [])
        if criteria:
            print("\n[ACCEPTANCE CRITERIA]:")
            for i, c in enumerate(criteria, 1):
                print(f"  {i}. {c}")

        print("=" * 65)
        print(f"📁 Plan JSON: {json_path.as_posix()}")
        print(f"📁 Plan Doc : {md_path.as_posix()}")
        print("=" * 65)

    @listen(plan_and_decompose)
    def execute_backend_tier(self):
        """
        Stage 2: Backend Tiered Execution (BE-1 -> BE-2 -> BE-3)
        followed by immediate Backend Build & Test Gate.
        """
        print("\n" + "=" * 65)
        print("⚙️ STAGE 2: BACKEND TIERED EXECUTION (BE-1 -> BE-2 -> BE-3)")
        print("=" * 65)

        inputs = {
            "topic": self.state.topic,
            "plans_dir": self.state.plans_dir,
            "design_dir": self.state.design_dir,
            "target_phase": self.state.target_phase,
            "phase_scope": self.state.phase_scope,
            "plan_files": ", ".join(self.state.plan_files),
            "plans_summary": self.state.plans_summary,
            "ba_wbs_plan": self.state.decomposition_raw,
        }

        be_crew = ContentCrew().backend_crew()
        be_res = be_crew.kickoff(inputs=inputs)
        self.state.backend_result = str(be_res.raw if hasattr(be_res, "raw") else be_res)

        # Immediate Backend Build & Test Gate (Fail-Fast)
        self._verify_and_repair_backend()

    def _verify_and_repair_backend(self):
        max_attempts = int(os.getenv("MAX_REPAIR_ATTEMPTS", "3"))
        crew_obj = ContentCrew()
        be_cmd = "mvn test" if (Path("backend") / "pom.xml").exists() else "pytest --disable-warnings -v"

        for attempt in range(1, max_attempts + 1):
            print(f"\n[?] Checking Backend Quality Gate: {be_cmd} (Attempt {attempt}/{max_attempts})...")
            try:
                proc = subprocess.run(
                    be_cmd,
                    cwd="backend",
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=300,
                )
                if proc.returncode == 0:
                    print("✅ BACKEND GATE PASSED: All unit and integration tests passed (0 errors)!")
                    self.state.backend_passed = True
                    return
                # In pytest, failure tracebacks and summaries are in stdout
                err_log = (proc.stdout or "") + ("\n--- STDERR ---\n" + proc.stderr if proc.stderr else "")
            except Exception as e:
                err_log = str(e)

            print(f"\n⚠️ Backend test/build FAILED! Triggering Backend Auto-Repair Agent (Attempt {attempt}/{max_attempts})...")
            clean_err = err_log.strip()
            generate_diagnostics_markdown(
                component="Backend",
                command=be_cmd,
                err_log=clean_err,
                attempt=attempt,
                max_attempts=max_attempts,
                phase_scope=self.state.phase_scope,
            )
            # If log is overly long, prioritize FAILURES and summary section rather than blind middle split
            if len(clean_err) > 6000:
                if "FAILURES" in clean_err:
                    fail_idx = clean_err.find("FAILURES")
                    # Keep 500 chars before FAILURES and up to 5500 chars after
                    start_pos = max(0, fail_idx - 500)
                    clean_err = clean_err[start_pos : start_pos + 6000]
                else:
                    clean_err = clean_err[-6000:]
            crew_obj.repair_backend(clean_err, self.state.phase_scope)

        print(f"⚠️ Backend reached max repair attempts ({max_attempts}) without 100% clean test suite.")

    @listen(execute_backend_tier)
    def execute_frontend_tier(self):
        """
        Stage 3: Frontend Contract-Driven Execution (FE-1 -> FE-2)
        using verified Backend DTOs and Stitch design tokens.
        """
        print("\n" + "=" * 65)
        print("🎨 STAGE 3: FRONTEND CONTRACT-DRIVEN EXECUTION (FE-1 -> FE-2)")
        print("=" * 65)

        inputs = {
            "topic": self.state.topic,
            "plans_dir": self.state.plans_dir,
            "design_dir": self.state.design_dir,
            "target_phase": self.state.target_phase,
            "phase_scope": self.state.phase_scope,
            "plan_files": ", ".join(self.state.plan_files),
            "plans_summary": self.state.plans_summary,
            "ba_wbs_plan": self.state.decomposition_raw,
            "backend_summary": self.state.backend_result,
        }

        fe_crew = ContentCrew().frontend_crew()
        fe_res = fe_crew.kickoff(inputs=inputs)
        self.state.frontend_result = str(fe_res.raw if hasattr(fe_res, "raw") else fe_res)

        # Immediate Frontend Build Gate (Fail-Fast)
        self._verify_and_repair_frontend()

    def _verify_and_repair_frontend(self):
        max_attempts = int(os.getenv("MAX_REPAIR_ATTEMPTS", "3"))
        crew_obj = ContentCrew()

        for attempt in range(1, max_attempts + 1):
            print(f"\n[?] Checking Frontend Quality Gate: npm run build (Attempt {attempt}/{max_attempts})...")
            try:
                proc = subprocess.run(
                    "npm run build",
                    cwd="frontend",
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=240,
                )
                if proc.returncode == 0:
                    print("✅ FRONTEND GATE PASSED: TypeScript and Vite build passed with 0 errors!")
                    self.state.frontend_passed = True
                    return
                err_log = (proc.stderr or "") + "\n" + (proc.stdout or "")
            except Exception as e:
                err_log = str(e)

            print(f"\n⚠️ Frontend build FAILED! Triggering Frontend Auto-Repair Agent (Attempt {attempt}/{max_attempts})...")
            clean_err = err_log.strip()
            generate_diagnostics_markdown(
                component="Frontend",
                command="npm run build",
                err_log=clean_err,
                attempt=attempt,
                max_attempts=max_attempts,
                phase_scope=self.state.phase_scope,
            )
            if len(clean_err) > 3000:
                clean_err = clean_err[:1500] + "\n...[log truncated]...\n" + clean_err[-1500:]
            crew_obj.repair_frontend(clean_err, self.state.phase_scope)

        print(f"⚠️ Frontend reached max repair attempts ({max_attempts}) without 100% clean build.")

    @listen(execute_frontend_tier)
    def verify_qa_and_signoff(self):
        """
        Stage 4: QA Acceptance Verification & Sign-off against
        the concrete acceptance criteria defined by BA.
        """
        print("\n" + "=" * 65)
        print("🛡️ STAGE 4: QA ACCEPTANCE VERIFICATION & SIGN-OFF")
        print("=" * 65)

        inputs = {
            "topic": self.state.topic,
            "plans_dir": self.state.plans_dir,
            "design_dir": self.state.design_dir,
            "target_phase": self.state.target_phase,
            "phase_scope": self.state.phase_scope,
            "plan_files": ", ".join(self.state.plan_files),
            "plans_summary": self.state.plans_summary,
            "ba_wbs_plan": self.state.decomposition_raw,
            "backend_summary": self.state.backend_result,
            "frontend_summary": self.state.frontend_result,
        }

        qa_crew = ContentCrew().qa_crew()
        qa_res = qa_crew.kickoff(inputs=inputs)
        self.state.qa_result = str(qa_res.raw if hasattr(qa_res, "raw") else qa_res)
        self.state.result = self.state.qa_result

    @listen(verify_qa_and_signoff)
    def final_build_gate(self):
        """
        Stage 5: Final Sanity Check & Global Quality Gate confirmation.
        """
        be_cmd = "mvn test" if (Path("backend") / "pom.xml").exists() else "pytest"
        print(f"\n⚡ FINAL QUALITY GATE VERIFICATION ({be_cmd} + npm run build)")
        print("=" * 65)

        be_ok = False
        fe_ok = False

        try:
            be_p = subprocess.run(be_cmd, cwd="backend", shell=True, capture_output=True, timeout=300)
            be_ok = be_p.returncode == 0
        except Exception:
            be_ok = False

        try:
            fe_p = subprocess.run("npm run build", cwd="frontend", shell=True, capture_output=True, timeout=240)
            fe_ok = fe_p.returncode == 0
        except Exception:
            fe_ok = False

        if be_ok and fe_ok:
            print("\n" + "★" * 65)
            print("✅ 100% GREEN BUILD: Backend tests passed, Frontend build succeeded!")
            print("★" * 65)
            self.state.build_passed = True
            progress_tracker.finish()
        else:
            print("\n" + "!" * 65)
            print(f"⚠️ Final Gate Status: Backend={'PASS' if be_ok else 'FAIL'}, Frontend={'PASS' if fe_ok else 'FAIL'}")
            print("!" * 65)
            self.state.build_passed = False

    @listen(final_build_gate)
    def save_report(self):
        output_dir = Path("output")
        reports_dir = output_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # 1. Latest report
        report_path = output_dir / "coding_team_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(self.state.result)

        # 2. Versioned archive
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_phase = re.sub(r"[^\w\-_.]", "_", self.state.target_phase or "phase").strip("_")
        clean_phase = re.sub(r"_+", "_", clean_phase)[:60]
        archived_path = reports_dir / f"report_{clean_phase}_{timestamp}.md"
        with open(archived_path, "w", encoding="utf-8") as f:
            f.write(self.state.result)

        # 3. Synchronize state files: state/PROJECT_STATE.md and state/HANDOFF.md
        state_dir = Path("state")
        state_dir.mkdir(parents=True, exist_ok=True)
        proj_state_path = state_dir / "PROJECT_STATE.md"
        handoff_path = state_dir / "HANDOFF.md"

        status_str = "PASSED (0 Errors)" if self.state.build_passed else "ATTENTION NEEDED (Build / Test Failures)"
        proj_state_content = f"""# Project State

- **Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Current Phase**: {self.state.target_phase}
- **Status**: {status_str}
- **Backend Quality Gate**: {"PASSED" if self.state.backend_passed else "FAILED"}
- **Frontend Quality Gate**: {"PASSED" if self.state.frontend_passed else "FAILED"}

## Latest Completed Milestones
- Executed {self.state.target_phase} via Autonomous Engineering Flow.
- Quality Gate verdict: {"APPROVED" if self.state.build_passed else "BLOCKED"}

## Blockers & Deviations
{"- None" if self.state.build_passed else "- Build or test failures occurred during execution. Review output/coding_team_report.md."}

## Next Actions
- Verify application runtime in staging / local environment.
- Proceed to next milestone defined in plans/IMPLEMENT_PLAN.md.
"""
        with open(proj_state_path, "w", encoding="utf-8") as f:
            f.write(proj_state_content)

        handoff_content = f"""# Engineering Handoff

- **Timestamp**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Sender**: QA & DevOps Verification Engineer
- **Recipient**: Next Sprint / Engineering Team
- **Phase Handed Off**: {self.state.target_phase}
- **Build Status**: {status_str}

## Handoff Summary
{self.state.result[:2000] if self.state.result else "Phase execution completed."}

## Verified Artifacts
- Backend source: `backend/src/main/java/`
- Frontend source: `frontend/src/`
- Mission report: `output/coding_team_report.md`
"""
        with open(handoff_path, "w", encoding="utf-8") as f:
            f.write(handoff_content)

        print(f"[✓] Mission report saved to: {report_path.as_posix()}")
        print(f"[✓] Versioned report archived to: {archived_path.as_posix()}")
        print(f"[✓] State synchronized: {proj_state_path.as_posix()} & {handoff_path.as_posix()}")


ContentFlow = CodingFlow


def kickoff():
    inputs = {}
    phase = os.getenv("PHASE", "").strip()
    for idx, arg in enumerate(sys.argv):
        if arg in ("--phase", "-p") and idx + 1 < len(sys.argv):
            phase = sys.argv[idx + 1].strip()
        elif arg.startswith("--phase=") or arg.startswith("phase="):
            phase = arg.split("=", 1)[1].strip()
    if phase:
        inputs["phase"] = phase

    flow = CodingFlow()
    flow.kickoff(inputs=inputs)


def plot():
    flow = CodingFlow()
    flow.plot()


def run_with_trigger():
    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    flow = CodingFlow()
    return flow.kickoff(inputs=trigger_payload)


if __name__ == "__main__":
    kickoff()
