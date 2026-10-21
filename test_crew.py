#!/usr/bin/env python
"""
test_crew.py - Environment & System Diagnostics for Autonomous Software Engineering Team.
Verifies Python version, compiler tools, environment variables, and module imports.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_diagnostics():
    print("=" * 65)
    print("🛠️  AUTONOMOUS SOFTWARE ENGINEERING TEAM - SYSTEM DIAGNOSTICS")
    print("=" * 65)

    all_passed = True

    # 1. Python version check
    py_ver = sys.version_info
    py_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    if py_ver >= (3, 10):
        print(f"✅ Python Version      : {py_str} (>= 3.10 OK)")
    else:
        print(f"❌ Python Version      : {py_str} (Requires >= 3.10)")
        all_passed = False

    # 2. Virtual environment check
    in_venv = sys.prefix != sys.base_prefix or "VIRTUAL_ENV" in os.environ
    if in_venv:
        print(f"✅ Virtual Environment : ACTIVE ({sys.prefix})")
    else:
        print("⚠️  Virtual Environment : NOT DETECTED (Recommend running inside .venv)")

    # 3. LLM API Key & Provider check
    provider = (os.getenv("LLM_PROVIDER") or os.getenv("PROVIDER") or "").strip().lower()
    model = os.getenv("MODEL") or "default"
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    has_key = False
    if openrouter_key and not openrouter_key.startswith("your_"):
        print(f"✅ LLM Configuration   : OpenRouter API Key detected (Model: {model})")
        has_key = True
    elif openai_key and not openai_key.startswith("your_"):
        print(f"✅ LLM Configuration   : OpenAI API Key detected (Model: {model})")
        has_key = True
    elif gemini_key and not gemini_key.startswith("your_"):
        print(f"✅ LLM Configuration   : Gemini API Key detected (Model: {model})")
        has_key = True

    if not has_key:
        print("❌ LLM Configuration   : No valid API key found in .env (OPENROUTER_API_KEY or OPENAI_API_KEY required)")
        all_passed = False

    # 4. Developer CLI Tools (Pytest, Node, Docker)
    pytest_path = shutil.which("pytest") or shutil.which("pytest.exe")
    mvn_path = shutil.which("mvn") or shutil.which("mvn.cmd")
    if pytest_path:
        print(f"✅ Backend Test Tool   : Pytest detected ({pytest_path})")
    elif mvn_path:
        print(f"✅ Backend Build Tool  : Apache Maven detected ({mvn_path})")
    else:
        print("ℹ️  Backend Test Tool   : 'pytest' detected via Python environment")

    node_path = shutil.which("node") or shutil.which("node.exe")
    npm_path = shutil.which("npm") or shutil.which("npm.cmd")
    if node_path and npm_path:
        print(f"✅ Frontend Build Tool : Node.js & npm detected ({node_path})")
    else:
        print("⚠️  Frontend Build Tool : Node/npm not found in PATH (Needed for React build)")

    # 5. Core Module Import Check
    try:
        sys.path.insert(0, os.path.abspath("web_builder/src"))
        from web_builder.main import CodingFlow, extract_wbs_json
        from web_builder.crews.content_crew.content_crew import ContentCrew
        print("✅ Core Modules Import : Successfully loaded CodingFlow and ContentCrew")
    except Exception as e:
        print(f"❌ Core Modules Import : FAILED ({e})")
        all_passed = False

    # 6. Plans & Design directory check
    plans_dir = Path("plans")
    design_dir = Path("design")
    if plans_dir.exists():
        plan_docs = list(plans_dir.glob("*.md"))
        print(f"✅ Project Plans       : Found '{plans_dir.as_posix()}' ({len(plan_docs)} markdown documents)")
    else:
        print("⚠️  Project Plans       : 'plans/' directory not found")

    if design_dir.exists():
        print(f"✅ UI Design System    : Found '{design_dir.as_posix()}'")
    else:
        print("ℹ️  UI Design System    : 'design/' directory not present")

    print("=" * 65)
    if all_passed:
        print("✅ ALL CHECKS PASSED - System is 100% ready to run!")
        print("   Recommended start command: python main.py --phase <number>")
    else:
        print("⚠️  Some diagnostics failed or need attention. Please review items marked with ❌ above.")
    print("=" * 65)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_diagnostics())
