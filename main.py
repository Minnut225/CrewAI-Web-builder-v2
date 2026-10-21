import os
import sys
import argparse
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

in_venv = sys.prefix != sys.base_prefix or "VIRTUAL_ENV" in os.environ
if not in_venv:
    venv_py = Path(__file__).resolve().parent / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        import subprocess
        sub_env = os.environ.copy()
        sub_env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run([str(venv_py), *sys.argv], env=sub_env)
        sys.exit(result.returncode)

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.abspath("web_builder/src"))
from web_builder.crews.content_crew.content_crew import ContentCrew
from web_builder.tools.plan_loader import load_plans, get_phase_scope
from web_builder.tools.progress_tracker import progress_tracker


def check_environment() -> bool:
    provider_pref = (os.getenv("LLM_PROVIDER") or os.getenv("PROVIDER") or "").strip().lower()
    raw_model = (os.getenv("MODEL") or "").strip()

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")

    def is_valid(k: str | None) -> bool:
        return bool(k and not k.startswith("your_") and "placeholder" not in k.lower())

    chosen_provider = None
    default_m = "gpt-4o-mini"

    if provider_pref in ("openai", "azure", "ollama", "vllm", "local", "custom") or (not provider_pref and (raw_model.startswith("openai/") or raw_model.startswith("gpt-") or openai_base_url)):
        if is_valid(openai_key) or openai_base_url:
            chosen_provider = "Ollama (OpenAI-compatible)" if provider_pref == "ollama" else "OpenAI"
            default_m = "gpt-4o-mini"

    if not chosen_provider:
        if provider_pref in ("openrouter", "or") or (not provider_pref and raw_model.startswith("openrouter/")):
            if is_valid(openrouter_key):
                chosen_provider = "OpenRouter AI"
                default_m = "openrouter/google/gemini-2.5-flash"
        elif provider_pref in ("gemini", "google") or (not provider_pref and raw_model.startswith("gemini/")):
            if is_valid(gemini_key):
                chosen_provider = "Gemini"
                default_m = "gemini/gemini-2.5-flash"

    if not chosen_provider:
        if is_valid(openai_key):
            chosen_provider = "OpenAI"
            default_m = "gpt-4o-mini"
        elif is_valid(openrouter_key):
            chosen_provider = "OpenRouter AI"
            default_m = "openrouter/google/gemini-2.5-flash"
        elif is_valid(gemini_key):
            chosen_provider = "Gemini"
            default_m = "gemini/gemini-2.5-flash"
        else:
            print("[!] No valid API key detected!")
            print("Please configure OPENAI_API_KEY or OPENROUTER_API_KEY in your .env file.")
            print("Example: OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx")
            print("         OPENAI_BASE_URL=https://api.openai.com/v1 (optional)")
            return False

    model = raw_model or default_m
    info = f"[+] Using {chosen_provider} LLM Engine (Model: {model}"
    if chosen_provider == "OpenAI" and openai_base_url:
        info += f", Base URL: {openai_base_url}"
    info += ")"
    print(info)
    return True


def run_coding_pipeline(plans_dir: str = "plans", design_dir: str = "design", phase: str = "all", topic_override: str | None = None, task: str | None = None, resume: bool = False, mode: str = "flow"):
    print("=" * 70)
    print(" 🚀 Autonomous Software Engineering Team (Dynamic Plans Architecture)")
    print("=" * 70)

    if not check_environment():
        sys.exit(1)

    plan_data = load_plans(plans_dir)
    phase_info = get_phase_scope(phase, plan_data.get("plans_dict", {}), task_arg=task)
    target_phase = phase_info["target_phase"]
    phase_scope = phase_info["phase_scope"]
    
    if phase_info["is_single_phase"]:
        topic = f"{plan_data['topic']} - {target_phase}" if not topic_override else topic_override
    else:
        topic = topic_override if topic_override else plan_data["topic"]

    process_mode = os.getenv("CREW_PROCESS", "sequential").upper()
    print(f"[*] Target Mission  : '{topic}'")
    print(f"[*] Pipeline Mode   : '{mode.upper()}' (Hierarchical Decomposition & Tiered Gates)")
    print(f"[*] Plans Directory : '{plan_data['plans_dir']}'")
    print(f"[*] Plan Documents  : {', '.join(plan_data['plan_files']) if plan_data['plan_files'] else 'None found'}")
    design_path = Path(design_dir)
    design_status = "DETECTED" if design_path.exists() else "NOT FOUND"
    print(f"[*] Process Mode    : '{process_mode}' (Live Progress Tracking: ACTIVE)")
    print(f"[*] Design Directory: '{design_dir}' (Stitch UI Templates: {design_status})")
    print(f"[*] Target Phase    : '{target_phase}'")

    progress_tracker.set_phase_context(
        target_phase=target_phase,
        phase_id=phase_info.get("phase_id", "0"),
        phase_file=phase_info.get("phase_file", "")
    )

    if mode == "flow":
        print("\n[*] Initializing multi-stage CodingFlow (Stage 1 BA -> Stage 2 BE -> Stage 3 FE -> Stage 4 QA)...")
        from web_builder.main import CodingFlow
        flow = CodingFlow()
        return flow.kickoff(inputs={
            "plans_dir": plans_dir,
            "design_dir": design_dir,
            "phase": phase,
            "task": task or "",
            "topic": topic,
        })

    print("\n[*] Initializing agents from configuration...")
    crew_instance = ContentCrew().crew()

    from crewai.state.checkpoint_config import CheckpointConfig
    checkpoint_config = None
    if resume:
        checkpoint_dir = Path(".checkpoints/main")
        if checkpoint_dir.exists():
            cp_files = sorted(checkpoint_dir.glob("*.json"), key=os.path.getmtime)
            if cp_files:
                latest_cp = cp_files[-1]
                print(f"[🔄 Checkpoint Detected] Resuming pipeline from: {latest_cp.as_posix()}")
                checkpoint_config = CheckpointConfig(
                    location="./.checkpoints",
                    restore_from=str(latest_cp),
                )
            else:
                print("[*] No checkpoint found in .checkpoints/main/, starting clean run.")
        else:
            print("[*] No .checkpoints directory found, starting clean run.")

    print("[*] Starting sequential execution pipeline (BA -> Backend -> Frontend -> QA)...\n")
    result = crew_instance.kickoff(
        inputs={
            "topic": topic,
            "plans_dir": plans_dir,
            "design_dir": design_dir,
            "target_phase": target_phase,
            "phase_scope": phase_scope,
            "plan_files": ", ".join(plan_data["plan_files"]),
            "plans_summary": plan_data["plans_summary"],
        },
        from_checkpoint=checkpoint_config,
    )
    progress_tracker.finish()

    print("\n" + "=" * 70)
    print(" 🏁 Mission Execution & QA Verification Summary:")
    print("=" * 70)
    print(result)

    output_dir = Path("output")
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_content = str(result.raw if hasattr(result, "raw") else result)

    # 1. Save latest report (convenient pointer for VSCode / IDE)
    latest_report_file = output_dir / "coding_team_report.md"
    with open(latest_report_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    # 2. Automatically archive versioned copy with phase and timestamp to avoid overwriting
    import re
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_phase = re.sub(r'[^\w\-_.]', '_', target_phase or "phase").strip('_')
    clean_phase = re.sub(r'_+', '_', clean_phase)[:60]
    archived_report_file = reports_dir / f"report_{clean_phase}_{timestamp}.md"
    with open(archived_report_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n[+] Latest Mission Report updated: {latest_report_file.as_posix()}")
    print(f"[+] Versioned Report archived: {archived_report_file.as_posix()} (Never overwritten)")
    print(f"[+] Live Progress JSON saved: output/progress.json")
    print(f"[+] Live Progress Markdown saved: output/progress.md")


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Coding Crew powered by plans folder (PRD, Architecture, Implementation, Test)."
    )
    parser.add_argument(
        "--plans-dir",
        type=str,
        default="plans",
        help="Path to the directory containing plan documents (PRD.md, ARCHITECTURE_PLAN.md, etc.).",
    )
    parser.add_argument(
        "--design-dir",
        type=str,
        default="design",
        help="Path to the directory containing Stitch UI design mockups and DESIGN.md (default: 'design').",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Override mission topic or application description (defaults to PRD inferred topic).",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "openrouter", "gemini"],
        default=None,
        help="Explicitly choose LLM provider (openai, openrouter, gemini).",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Custom base URL for OpenAI or OpenAI-compatible endpoints.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override model name (e.g. gpt-4o, gpt-4o-mini, deepseek-chat).",
    )
    parser.add_argument(
        "--process",
        type=str,
        choices=["sequential", "hierarchical"],
        default="sequential",
        help="Execution process mode ('sequential' for ordered pipeline, 'hierarchical' with Manager LLM).",
    )
    parser.add_argument(
        "--phase",
        type=str,
        default="all",
        help="Run a specific development phase (0 to 9, or 'all', or subtask like '1.1').",
    )
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="Specify one or more subtasks within the phase (e.g. '1.1' or '1.1,1.2').",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume pipeline from the last completed task checkpoint in .checkpoints/.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["flow", "crew"],
        default="flow",
        help="Pipeline execution engine: 'flow' (Hierarchical Flow with BA WBS decomposition, tiered gates, and auto-repair, default) or 'crew' (pure sequential crew).",
    )

    args, unknown = parser.parse_known_args()

    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    if args.base_url:
        os.environ["OPENAI_BASE_URL"] = args.base_url
    if args.model:
        os.environ["MODEL"] = args.model
    if args.process:
        os.environ["CREW_PROCESS"] = args.process

    topic = args.topic
    if not topic and unknown:
        topic = " ".join(unknown)

    run_coding_pipeline(plans_dir=args.plans_dir, design_dir=args.design_dir, phase=args.phase, topic_override=topic, task=args.task, resume=args.resume, mode=args.mode)


if __name__ == "__main__":
    main()
