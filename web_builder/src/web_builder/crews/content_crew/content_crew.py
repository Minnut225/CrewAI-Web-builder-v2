import sys
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import os
import sys
from pathlib import Path
from crewai import Agent, Crew, Process, Task, LLM
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from web_builder.tools.progress_tracker import ProgressTracker, global_step_callback, global_task_callback
from web_builder.tools.code_tools import (
    write_file,
    read_file,
    replace_lines,
    patch_file,
    list_dir,
    check_code_health,
    run_command,
    search_code,
    set_last_test_failed,
)


def normalize_messages_for_qwen(raw_msgs):
    if not isinstance(raw_msgs, list):
        if isinstance(raw_msgs, str):
            return [{"role": "user", "content": raw_msgs}]
        return raw_msgs

    # Step 1: Clean & standardize roles
    cleaned = []
    for m in raw_msgs:
        if isinstance(m, dict):
            msg = dict(m)
        elif hasattr(m, "role") and hasattr(m, "content"):
            msg = {"role": m.role, "content": m.content}
            if hasattr(m, "tool_calls"):
                msg["tool_calls"] = m.tool_calls
            if hasattr(m, "tool_call_id"):
                msg["tool_call_id"] = m.tool_call_id
        else:
            msg = {"role": "user", "content": str(m)}

        # Content hygiene: None -> string unless tool_calls
        if msg.get("content") is None and not msg.get("tool_calls"):
            msg["content"] = " "

        if msg.get("role") == "user":
            c_str = str(msg.get("content") or "").strip()
            if not c_str:
                msg["content"] = "Please proceed with executing the task according to specifications."

        cleaned.append(msg)

    # Step 2: Consolidate system messages at top
    system_parts = []
    non_sys_msgs = []
    first_non_sys_found = False
    for m in cleaned:
        if m.get("role") == "system" and not first_non_sys_found:
            c = str(m.get("content") or "").strip()
            if c:
                system_parts.append(c)
        else:
            first_non_sys_found = True
            non_sys_msgs.append(m)

    rebuilt = []
    if system_parts:
        rebuilt.append({"role": "system", "content": "\n\n".join(system_parts)})

    # Step 3: Ensure initial user message exists immediately after system
    user_msgs = [m for m in non_sys_msgs if m.get("role") == "user"]
    if not user_msgs:
        rebuilt.append({
            "role": "user",
            "content": "Please proceed with executing the task using the available tools according to system instructions."
        })
    elif non_sys_msgs and non_sys_msgs[0].get("role") != "user":
        rebuilt.append(user_msgs[0])
        non_sys_msgs = [m for i, m in enumerate(non_sys_msgs) if not (m.get("role") == "user" and i == non_sys_msgs.index(user_msgs[0]))]

    # Step 4: Process conversation flow with context trimming and tool turn anchoring
    last_assistant_idx = -1
    for i, m in enumerate(non_sys_msgs):
        if m.get("role") == "assistant" and m.get("tool_calls"):
            last_assistant_idx = i

    for i, m in enumerate(non_sys_msgs):
        role = m.get("role")
        # Context compaction: for older tool results (before the latest assistant turn),
        # truncate overly verbose outputs so context never exceeds server limits (< 8k tokens)
        if role == "tool" and i < last_assistant_idx:
            c = str(m.get("content") or "")
            if len(c) > 800:
                m["content"] = c[:750] + "\n... [older tool output trimmed for context size]"

        # Tool Turn Anchoring:
        # If an assistant message with tool_calls is preceded by a tool message or assistant message,
        # insert anchor user message so Qwen multi_step_tool template invariant is always satisfied.
        if role == "assistant" and (m.get("tool_calls") or not m.get("content")):
            prev_role = rebuilt[-1].get("role") if rebuilt else None
            if prev_role in ("tool", "assistant"):
                rebuilt.append({
                    "role": "user",
                    "content": "Tool execution results received. Please proceed with your analysis and next tool call or final response."
                })

        rebuilt.append(m)

    return rebuilt



def _calculate_backoff_and_wait(err_str: str, attempt: int, max_retries: int) -> bool:
    import time
    import re
    import sys

    err_lower = err_str.lower()
    
    # Check if hit daily quota / RPD 500 limit
    is_rpd_limit = any(
        k in err_lower
        for k in [
            "rpd",
            "requests per day",
            "per day",
            "daily limit",
            "daily quota",
            "quota exceeded for quota metric 'requests' and limit 'requests per day'",
            "exceeded your current quota",
            "limit of 500",
            "limit: 500",
        ]
    )
    if is_rpd_limit:
        print(f"\n🛑 [STOP TRIGGERED] Daily request quota reached (RPD 500 / Requests Per Day): {err_str[:250]}")
        print("Stopping workflow immediately per user instruction.")
        sys.exit(500)

    # Detect rate limit OR 503 high demand spikes (Gemini/OpenAI server congestion)
    is_demand_or_rate = any(
        k in err_lower
        for k in [
            "429", "resource_exhausted", "rate_limit", "quota", "too many requests",
            "503", "high demand", "spikes in demand", "try again later", "overloaded"
        ]
    )
    is_transient = is_demand_or_rate or any(
        k in err_str
        for k in [
            "524", "500", "502", "504", "timeout", "Connection reset",
            "RemoteDisconnected", "gateway", "UNAVAILABLE"
        ]
    )

    if not is_transient or attempt >= (max_retries - 1):
        return False

    if is_demand_or_rate:
        m_wait = re.search(r'(?:retry[-_ ]after|wait|reset in|retry in)\s*[:=]?\s*(\d+(?:\.\d+)?)', err_str, re.IGNORECASE)
        if m_wait:
            wait_sec = int(float(m_wait.group(1))) + 3
        else:
            backoffs = [30, 50, 70, 90, 120]
            wait_sec = backoffs[min(attempt, len(backoffs) - 1)]
        print(f"\n  [RATE_LIMIT / DEMAND SPIKE] Server busy or quota limit. Waiting {wait_sec}s for cooldown (Attempt {attempt + 1}/{max_retries})...")
    else:
        wait_sec = (attempt + 1) * 5
        print(f"\n  [TRANSIENT ERROR] Retrying in {wait_sec}s (Attempt {attempt + 1}/{max_retries})...")

    time.sleep(wait_sec)
    return True

def patch_openai_completion_for_resilience():
    """
    Universally patches:
    1. crewai_core.printer.Printer.print to prevent Windows cp1258 UnicodeEncodeError.
    2. OpenAICompletion._prepare_completion_params to guarantee Qwen chat templates
       never throw 'Jinja Exception: No user query found in messages' at line 100.
    3. OpenAICompletion._handle_completion and _handle_streaming_completion for automated transient retry.
    """
    import sys
    # Patch 1: Windows Console Unicode Printer
    try:
        import crewai_core.printer
        if not getattr(crewai_core.printer.Printer, "_is_safe_print_patched", False):
            _orig_printer_print = crewai_core.printer.Printer.print

            def _safe_printer_print(*args, **kwargs):
                call_args = args
                if call_args and isinstance(call_args[0], crewai_core.printer.Printer):
                    call_args = call_args[1:]
                try:
                    _orig_printer_print(*call_args, **kwargs)
                except (UnicodeEncodeError, UnicodeError):
                    try:
                        content = kwargs.get("content", call_args[0] if call_args else "")
                        end = kwargs.get("end", "\n")
                        target = kwargs.get("file") or sys.stdout
                        if isinstance(content, str):
                            text = content
                        elif isinstance(content, list):
                            text = "".join(getattr(c, "text", str(c)) for c in content)
                        else:
                            text = str(content)
                        if hasattr(target, "buffer"):
                            target.buffer.write(text.encode("utf-8", errors="replace") + str(end).encode("utf-8"))
                            if kwargs.get("flush", False):
                                target.buffer.flush()
                        else:
                            target.write(text.encode("ascii", errors="replace").decode("ascii") + str(end))
                    except Exception:
                        pass

            crewai_core.printer.Printer.print = staticmethod(_safe_printer_print)
            crewai_core.printer.Printer._is_safe_print_patched = True
    except Exception:
        pass

    # Patch 3: crewai.utilities.agent_utils safe fallback for empty LLM responses
    try:
        import crewai.utilities.agent_utils as agent_utils
        if not getattr(agent_utils, "_is_safe_validate_patched", False):
            orig_validate = agent_utils._validate_and_finalize_llm_response

            def _safe_validate(answer, executor_context, printer, verbose=True):
                if not answer:
                    if verbose:
                        printer.print(
                            content="[CrewAI Resilience] Received None or empty response from LLM call. Applying safe recovery fallback.",
                            color="yellow",
                        )
                    answer = "Action acknowledged. Ready to proceed with tool execution."
                return orig_validate(answer, executor_context, printer, verbose=verbose)

            agent_utils._validate_and_finalize_llm_response = _safe_validate
            agent_utils._is_safe_validate_patched = True
    except Exception:
        pass


    # Patch 2: OpenAICompletion Qwen Chat Template Normalization & Transient Retry
    try:
        from crewai.llms.providers.openai.completion import OpenAICompletion
    except ImportError:
        return

    if getattr(OpenAICompletion, "_is_resilience_patched", False):
        return

    orig_prepare_params = OpenAICompletion._prepare_completion_params
    orig_handle_completion = OpenAICompletion._handle_completion
    orig_handle_streaming = getattr(OpenAICompletion, "_handle_streaming_completion", None)

    def resilient_prepare_completion_params(self, messages, tools=None):
        params = orig_prepare_params(self, messages, tools=tools)
        norm_messages = normalize_messages_for_qwen(params.get("messages", []))

        has_write_or_patch = False
        if tools:
            for t in tools:
                t_name = getattr(t, "name", "") or (t.get("function", {}).get("name") if isinstance(t, dict) else "")
                if t_name in ("write_file", "patch_file", "replace_lines"):
                    has_write_or_patch = True
                    break

        if has_write_or_patch and norm_messages:
            last_user = next((m for m in reversed(norm_messages) if m.get("role") == "user"), None)
            if last_user and "[MANDATORY TOOL MANDATE]" not in last_user.get("content", ""):
                last_user["content"] += (
                    "\n\n[MANDATORY TOOL MANDATE]: You have code modification tools (`replace_lines`, `patch_file`, `write_file`). "
                    "\n1. For Auto-Repair / Bug Fixing (Backend or Frontend): After finding the failing file and line number via `read_file('output/DIAGNOSTICS.md')` or `search_code`, "
                    "you MUST IMMEDIATELY invoke `replace_lines` (by line number) or `patch_file`/`write_file` to fix the code on disk BEFORE re-running test or build commands. "
                    "STRICT PROHIBITION: The ANTI-LOOP GUARD will physically block `run_command` if you try to re-run tests on unmodified code! "
                    "Searching and testing without modifying files with `replace_lines`/`patch_file`/`write_file` is strictly prohibited. "
                    "If `patch_file` fails due to search text mismatch, IMMEDIATELY call `replace_lines` or `write_file` to overwrite with the complete corrected code. "
                    "\n2. For Frontend UI tasks: Only inspect the specific Stitch mockup file in `design/screen_<name>/code.html` relevant to the target page. "
                    "Do NOT read all mockups at once. You MUST invoke `write_file` or `patch_file` to save each component/page to disk. Do NOT return a text-only response."
                )

        params["messages"] = norm_messages
        return params

    def resilient_handle_completion(self, params, *args, **kwargs):
        import time
        import re
        max_retries = 6
        for attempt in range(max_retries):
            try:
                resp = orig_handle_completion(self, params, *args, **kwargs)
                # Check for empty response and retry
                if resp is None or resp == "" or resp == []:
                    if attempt < (max_retries - 1):
                        time.sleep(2 * (attempt + 1))
                        continue
                    # Safe fallback to prevent 'Invalid response from LLM call - None or empty'
                    return "Step execution completed. Ready to proceed with next step."

                # Auto-save fallback if LLM generated code blocks directly into text content
                try:
                    content_text = str(resp) if isinstance(resp, str) else ""
                    if hasattr(resp, "choices") and resp.choices:
                        msg = resp.choices[0].message
                        content_text = getattr(msg, "content", "") or ""
                    if content_text and "```" in content_text:
                        from web_builder.tools.code_tools import write_file as disk_writer
                        pattern = r'(?:file:\s*|File:\s*|implementation of\s+|create\s+|path:\s*|^|\n)([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)[:\s]*\n```[a-zA-Z0-9_-]*\n(.*?)\n```'
                        for file_path, code_body in re.findall(pattern, content_text, re.DOTALL | re.MULTILINE):
                            clean_fp = file_path.strip().strip("'\"`")
                            if ("/" in clean_fp or "\\" in clean_fp) and not clean_fp.endswith(".md"):
                                disk_writer.run(file_path=clean_fp, content=code_body)
                                print(f"  [? Auto-Saved Code to Disk]: {clean_fp}")
                except Exception:
                    pass
                return resp
            except Exception as e:
                if _calculate_backoff_and_wait(str(e), attempt, max_retries):
                    continue
                raise e

    def resilient_handle_streaming(self, params, *args, **kwargs):
        import time
        max_retries = 6
        for attempt in range(max_retries):
            try:
                return orig_handle_streaming(self, params, *args, **kwargs)
            except Exception as e:
                if _calculate_backoff_and_wait(str(e), attempt, max_retries):
                    continue
                raise e

    OpenAICompletion._prepare_completion_params = resilient_prepare_completion_params
    OpenAICompletion._handle_completion = resilient_handle_completion
    if orig_handle_streaming is not None:
        OpenAICompletion._handle_streaming_completion = resilient_handle_streaming
    OpenAICompletion._is_resilience_patched = True


# Run patch immediately when module loads
patch_openai_completion_for_resilience()


@CrewBase
class ContentCrew:
    """Autonomous Software Engineering Coding Crew powered by dynamic plan files"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def get_llm(self, role: str = "general") -> LLM:
        provider_pref = (os.getenv("LLM_PROVIDER") or os.getenv("PROVIDER") or "").strip().lower()
        raw_model = (os.getenv("MODEL") or "").strip()

        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        openai_base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")

        def is_valid(k: str | None) -> bool:
            return bool(k and not k.startswith("your_") and "placeholder" not in k.lower())

        role_temperatures = {
            "ba": 0.0,
            "backend": 0.0,
            "frontend": 0.05,
            "qa": 0.0,
            "general": 0.0,
        }
        env_temp = os.getenv("TEMPERATURE")
        temperature = float(env_temp) if env_temp else role_temperatures.get(role, 0.15)
        timeout = int(os.getenv("REQUEST_TIMEOUT", "180"))
        max_tokens = int(os.getenv("MAX_TOKENS", "8192"))

        # Determine target provider based on explicit choice, model prefix, base_url, or available keys
        use_openai = False
        use_openrouter = False
        use_gemini = False

        if provider_pref in ("openai", "azure", "ollama", "vllm", "local", "custom") or (not provider_pref and (raw_model.startswith("openai/") or raw_model.startswith("gpt-") or openai_base_url)):
            if is_valid(openai_key) or openai_base_url:
                use_openai = True
        elif provider_pref in ("openrouter", "or") or (not provider_pref and raw_model.startswith("openrouter/")):
            if is_valid(openrouter_key):
                use_openrouter = True
        elif provider_pref in ("gemini", "google") or (not provider_pref and raw_model.startswith("gemini/")):
            if is_valid(gemini_key):
                use_gemini = True

        # Fallback to available valid keys if provider was not explicitly determined
        if not (use_openai or use_openrouter or use_gemini):
            if is_valid(openai_key):
                use_openai = True
            elif is_valid(openrouter_key):
                use_openrouter = True
            elif is_valid(gemini_key):
                use_gemini = True

        if use_openai:
            if raw_model.startswith("openrouter/") or raw_model.startswith("gemini/"):
                model = "gpt-4o-mini"
            else:
                model = raw_model or "gpt-4o-mini"
            # Ensure model starts with openai/ so LiteLLM treats it as OpenAI-compatible
            if not model.startswith("openai/"):
                model = f"openai/{model}"
            kwargs = {
                "model": model,
                "api_key": openai_key or "ollama",
                "temperature": temperature,
                "timeout": timeout,
                "max_tokens": max_tokens,
            }
            if openai_base_url:
                kwargs["base_url"] = openai_base_url.strip()
            llm_inst = LLM(**kwargs)
            return self._wrap_resilient_llm(llm_inst)

        elif use_openrouter:
            model = raw_model if raw_model.startswith("openrouter/") else f"openrouter/{raw_model or 'google/gemini-2.5-flash'}"
            llm_inst = LLM(
                model=model,
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=temperature,
                timeout=timeout,
                max_tokens=max_tokens,
            )
            return self._wrap_resilient_llm(llm_inst)

        elif use_gemini:
            model = raw_model if raw_model.startswith("gemini/") else f"gemini/{raw_model or 'gemini-2.5-flash'}"
            llm_inst = LLM(
                model=model,
                api_key=gemini_key,
                temperature=temperature,
                timeout=timeout,
                max_tokens=max_tokens,
            )
            return self._wrap_resilient_llm(llm_inst)

        else:
            raise ValueError(
                "No valid API key configured! Please configure OPENAI_API_KEY (with optional OPENAI_BASE_URL) "
                "or OPENROUTER_API_KEY / GEMINI_API_KEY in the .env file."
            )



    def _wrap_resilient_llm(self, llm: LLM) -> LLM:
        """
        Instance-level wrapper ensuring that calls directly on this LLM instance
        also guarantee non-empty user messages, retry on transient errors/empty responses,
        and automatically persist generated code blocks to disk if emitted in text.
        """
        import time
        import re

        orig_call = llm.call

        def resilient_call(messages, *args, **kwargs):
            tools = kwargs.get("tools") or (args[0] if args else None)
            has_write_file = False
            if tools:
                for t in tools:
                    t_name = getattr(t, "name", "") or (t.get("function", {}).get("name") if isinstance(t, dict) else "")
                    if t_name == "write_file":
                        has_write_file = True
                        break

            norm_messages = normalize_messages_for_qwen(messages)

            if has_write_file and norm_messages:
                last_user = next((m for m in reversed(norm_messages) if m.get("role") == "user"), None)
                if last_user and "[MANDATORY TOOL MANDATE]" not in last_user.get("content", ""):
                    last_user["content"] += (
                        "\n\n[MANDATORY TOOL MANDATE]: You have the write_file tool. "
                        "For Frontend UI tasks: You MUST first invoke `read_file` on `design/screen_<name>/code.html` "
                        "to extract the exact Stitch HTML layout, Tailwind CSS classes, and Material Symbols before writing components. "
                        "CRITICAL: Frontend pages MUST NOT use only static mock data. You MUST import the API client (`import api from '../services/api'`) and wire dynamic state to backend endpoints (e.g. `api.getCategories()`, `api.getProducts()`, `api.createOrder()`, `api.getOrders()`), with fallback to default state if offline. "
                        "You MUST invoke the `write_file` tool call with file_path and content to create each required file on disk. "
                        "Do NOT return a text-only summary without calling write_file."
                    )

            max_retries = 6
            for attempt in range(max_retries):
                try:
                    resp = orig_call(norm_messages, *args, **kwargs)

                    # Check for empty response and retry
                    is_empty = False
                    if resp is None or resp == []:
                        is_empty = True
                    elif isinstance(resp, str) and not resp.strip():
                        is_empty = True

                    if is_empty:
                        if attempt < (max_retries - 1):
                            time.sleep(2 * (attempt + 1))
                            continue
                        return "⚠️ [Verification Warning] LLM returned empty response after retries. Task has been executed with fallback."

                    # Auto-save fallback if LLM generated code blocks directly into text content
                    try:
                        content_text = ""
                        if isinstance(resp, str):
                            content_text = resp
                        elif hasattr(resp, "content"):
                            content_text = resp.content or ""
                        elif hasattr(resp, "choices") and resp.choices:
                            msg = resp.choices[0].message
                            content_text = getattr(msg, "content", "") or ""

                        if content_text and "```" in content_text:
                            from web_builder.tools.code_tools import write_file as disk_writer
                            pattern = r'(?:file:\s*|File:\s*|path:\s*|`)([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)`?[:\s]*\n```[a-zA-Z0-9_-]*\n(.*?)\n```'
                            for file_path, code_body in re.findall(pattern, content_text, re.DOTALL | re.MULTILINE):
                                clean_fp = file_path.strip().strip("'\"`")
                                if ("/" in clean_fp or "\\" in clean_fp) and not clean_fp.endswith(".md"):
                                    disk_writer.run(file_path=clean_fp, content=code_body)
                                    print(f"  [? Auto-Saved Code to Disk]: {clean_fp}")
                    except Exception:
                        pass

                    return resp

                except Exception as e:
                    if _calculate_backoff_and_wait(str(e), attempt, max_retries):
                        continue
                    raise e

        llm.call = resilient_call
        return llm

    @agent
    def ba(self) -> Agent:
        max_rpm = int(os.getenv("MAX_RPM", "25"))
        max_iter = int(os.getenv("MAX_ITER_BA", os.getenv("MAX_ITER", "20")))
        return Agent(
            config=self.agents_config["ba"],
            tools=[write_file, read_file, list_dir, search_code, check_code_health],
            llm=self.get_llm(role="ba"),
            max_rpm=max_rpm,
            max_iter=max_iter,
            cache=True,
            verbose=True,
        )

    @agent
    def backend(self) -> Agent:
        max_rpm = int(os.getenv("MAX_RPM", "25"))
        max_iter = int(os.getenv("MAX_ITER_BACKEND", os.getenv("MAX_ITER", "35")))
        return Agent(
            config=self.agents_config["backend"],
            tools=[run_command, replace_lines, patch_file, write_file, read_file, list_dir, search_code],
            llm=self.get_llm(role="backend"),
            max_rpm=max_rpm,
            max_iter=max_iter,
            cache=True,
            verbose=True,
        )

    @agent
    def frontend(self) -> Agent:
        max_rpm = int(os.getenv("MAX_RPM", "25"))
        max_iter = int(os.getenv("MAX_ITER_FRONTEND", os.getenv("MAX_ITER", "35")))
        return Agent(
            config=self.agents_config["frontend"],
            tools=[run_command, replace_lines, patch_file, write_file, read_file, list_dir, search_code],
            llm=self.get_llm(role="frontend"),
            max_rpm=max_rpm,
            max_iter=max_iter,
            cache=True,
            verbose=True,
        )

    @agent
    def qa(self) -> Agent:
        max_rpm = int(os.getenv("MAX_RPM", "25"))
        max_iter = int(os.getenv("MAX_ITER_QA", os.getenv("MAX_ITER", "25")))
        return Agent(
            config=self.agents_config["qa"],
            tools=[run_command, replace_lines, read_file, write_file, patch_file, check_code_health, list_dir, search_code],
            llm=self.get_llm(role="qa"),
            max_rpm=max_rpm,
            max_iter=max_iter,
            cache=True,
            verbose=True,
        )

    def auto_repair_agent(self, role_type: str = "backend") -> Agent:
        component_name = "Backend (Python/FastAPI)" if role_type == "backend" else "Frontend (React/TypeScript)"
        return Agent(
            role=f"Emergency {role_type.capitalize()} Bug-Fix Specialist",
            goal=(
                f"Surgically resolve the failing {component_name} build or test error documented in output/DIAGNOSTICS.md. "
                "You must call tools to inspect and fix code on disk. "
                "Never provide Final Answer without having called replace_lines, patch_file, or write_file."
            ),
            backstory=(
                f"You are a battle-hardened emergency bug-fix specialist for {component_name}. "
                "You do not waste turns reading general guidelines or exploring unrelated files. "
                "You inspect output/DIAGNOSTICS.md, read the failing file around the error line, "
                "and IMMEDIATELY call replace_lines or patch_file to fix the bug on disk. "
                "STRICT PROTOCOL: You are strictly forbidden from outputting Final Answer until you have called file modification tools (replace_lines, patch_file, or write_file). Doing so will cause the build gate to fail."
            ),
            tools=[read_file, replace_lines, patch_file, write_file, run_command, search_code],
            llm=self.get_llm(role=role_type),
            max_iter=10,
            max_rpm=int(os.getenv("MAX_RPM", "25")),
            cache=True,
            verbose=True,
        )

    @task
    def ba_decomposition_task(self) -> Task:
        return Task(
            config=self.tasks_config["ba_decomposition_task"],
            agent=self.ba(),
        )

    @task
    def backend_contract_task(self) -> Task:
        return Task(
            config=self.tasks_config["backend_contract_task"],
            agent=self.backend(),
        )

    @task
    def backend_service_task(self) -> Task:
        return Task(
            config=self.tasks_config["backend_service_task"],
            agent=self.backend(),
            context=[self.backend_contract_task()],
        )

    @task
    def backend_controller_task(self) -> Task:
        return Task(
            config=self.tasks_config["backend_controller_task"],
            agent=self.backend(),
            context=[self.backend_contract_task(), self.backend_service_task()],
        )

    @task
    def frontend_contract_task(self) -> Task:
        return Task(
            config=self.tasks_config["frontend_contract_task"],
            agent=self.frontend(),
        )

    @task
    def frontend_ui_task(self) -> Task:
        return Task(
            config=self.tasks_config["frontend_ui_task"],
            agent=self.frontend(),
            context=[self.frontend_contract_task()],
        )

    @task
    def qa_verification_task(self) -> Task:
        return Task(
            config=self.tasks_config["qa_verification_task"],
            agent=self.qa(),
        )

    # Legacy method compatibility
    def design_analysis_task(self) -> Task:
        return self.ba_decomposition_task()

    def backend_coding_task(self) -> Task:
        return self.backend_contract_task()

    def frontend_coding_task(self) -> Task:
        return self.frontend_ui_task()

    def ba_crew(self) -> Crew:
        """Isolated Stage 1 Crew: BA Requirement Analysis & Task Decomposition"""
        return Crew(
            agents=[self.ba()],
            tasks=[self.ba_decomposition_task()],
            process=Process.sequential,
            step_callback=global_step_callback,
            task_callback=global_task_callback,
            verbose=True,
            memory=False,
            cache=True,
        )

    def backend_crew(self) -> Crew:
        """Isolated Stage 2 Crew: Backend Tiered Execution (BE-1 -> BE-2 -> BE-3)"""
        return Crew(
            agents=[self.backend()],
            tasks=[
                self.backend_contract_task(),
                self.backend_service_task(),
                self.backend_controller_task(),
            ],
            process=Process.sequential,
            step_callback=global_step_callback,
            task_callback=global_task_callback,
            verbose=True,
            memory=False,
            cache=True,
        )

    def frontend_crew(self) -> Crew:
        """Isolated Stage 3 Crew: Frontend Contract-Driven Execution (FE-1 -> FE-2)"""
        return Crew(
            agents=[self.frontend()],
            tasks=[
                self.frontend_contract_task(),
                self.frontend_ui_task(),
            ],
            process=Process.sequential,
            step_callback=global_step_callback,
            task_callback=global_task_callback,
            verbose=True,
            memory=False,
            cache=True,
        )

    def qa_crew(self) -> Crew:
        """Isolated Stage 4 Crew: QA Verification & Sign-off"""
        return Crew(
            agents=[self.qa()],
            tasks=[self.qa_verification_task()],
            process=Process.sequential,
            step_callback=global_step_callback,
            task_callback=global_task_callback,
            verbose=True,
            memory=False,
            cache=True,
        )

    @crew
    def crew(self) -> Crew:
        process_type = os.getenv("CREW_PROCESS", "sequential").strip().lower()
        is_hierarchical = process_type == "hierarchical"
        process = Process.hierarchical if is_hierarchical else Process.sequential

        tracker = ProgressTracker(total_tasks=len(self.tasks), process_name=process_type)

        crew_kwargs = {
            "agents": [self.ba(), self.backend(), self.frontend(), self.qa()],
            "tasks": [
                self.ba_decomposition_task(),
                self.backend_contract_task(),
                self.backend_service_task(),
                self.backend_controller_task(),
                self.frontend_contract_task(),
                self.frontend_ui_task(),
                self.qa_verification_task(),
            ],
            "process": process,
            "step_callback": global_step_callback,
            "task_callback": global_task_callback,
            "verbose": True,
            "memory": False,
            "cache": True,
        }

        if is_hierarchical:
            crew_kwargs["manager_llm"] = self.get_llm(role="ba")

        return Crew(**crew_kwargs)

    def repair_backend(self, error_log: str, phase_scope: str):
        set_last_test_failed()
        print("\n" + "=" * 65)
        print("🔧 AUTO-REPAIR TRIGGERED: Backend Repair Task")
        print("=" * 65)
        repair_agent = self.auto_repair_agent(role_type="backend")
        repair_task = Task(
            description=(
                f"Execute the assigned repair task using output/DIAGNOSTICS.md as the work contract.\n\n"
                f"CRITICAL BUILD OR TEST FAILURE in Backend for '{phase_scope}'.\n"
                f"BACKEND ERROR LOG:\n{error_log[:1500]}\n\n"
                "🚨 CRITICAL PROTOCOL:\n"
                "You are STRICTLY FORBIDDEN from outputting 'Final Answer' without having executed tools!\n"
                "Your first step MUST be a tool call to read the offending file or diagnostics.\n"
                "Your subsequent step MUST be a tool call to `replace_lines` or `patch_file` to write the code fix to disk.\n"
                "Only after modifying code on disk and verifying may you output your final structured report.\n\n"
                "Mandatory workflow:\n"
                "1. FIRST STEP: Call `read_file(file_path='output/DIAGNOSTICS.md')` to inspect the failure diagnostics, exact failing file, line number, and traceback.\n"
                "2. Inspect the offending file with `read_file` around the identified error line.\n"
                "3. CRITICAL ACTION: Fix the code immediately using `replace_lines` or `patch_file`.\n"
                "   - Use `replace_lines(file_path=..., start_line=..., end_line=..., replacement=...)` to surgically replace the failing line range directly.\n"
                "   - You MUST modify the code on disk BEFORE re-running tests!\n"
                "   - ANTI-LOOP GUARD: The system will automatically REJECT and BLOCK `run_command` if you try to run pytest on unmodified code!\n"
                "4. After applying the code modification, run `run_command(command='pytest --disable-warnings -v', cwd='backend')` to verify 0 failures.\n"
                "5. Report actual test results and changed files in your final report.\n\n"
                "Do not invent missing requirements.\n"
                "Do not claim unverified success.\n"
                "Do not overwrite unrelated changes.\n\n"
                f"Assigned task: Backend Auto-Repair - {phase_scope}\n"
                "State file: state/PROJECT_STATE.md\n"
                "Handoff file: state/HANDOFF.md"
            ),
            expected_output=(
                "Structured execution report containing:\n"
                "- Task ID and status\n"
                "- Implementation summary\n"
                "- Changed files\n"
                "- Acceptance criteria and verification evidence\n"
                "- Commands and actual test results (pytest --disable-warnings -v)\n"
                "- Deviations, blockers, and next actions"
            ),
            agent=repair_agent,
        )
        repair_crew = Crew(
            agents=[repair_agent],
            tasks=[repair_task],
            verbose=True,
            step_callback=global_step_callback,
            task_callback=global_task_callback,
        )
        return repair_crew.kickoff()

    def repair_frontend(self, error_log: str, phase_scope: str):
        set_last_test_failed()
        print("\n" + "=" * 65)
        print("🔧 AUTO-REPAIR TRIGGERED: Frontend Repair Task")
        print("=" * 65)
        repair_agent = self.auto_repair_agent(role_type="frontend")
        repair_task = Task(
            description=(
                f"Execute the assigned repair task using output/DIAGNOSTICS.md as the work contract.\n\n"
                f"CRITICAL BUILD FAILURE in Frontend ('npm run build') for '{phase_scope}'.\n"
                f"TYPESCRIPT / VITE ERROR LOG:\n{error_log[:1500]}\n\n"
                "🚨 CRITICAL PROTOCOL:\n"
                "You are STRICTLY FORBIDDEN from outputting 'Final Answer' without having executed tools!\n"
                "Your first step MUST be a tool call to read the offending file or diagnostics.\n"
                "Your subsequent step MUST be a tool call to `replace_lines` or `patch_file` to write the code fix to disk.\n"
                "Only after modifying code on disk and verifying may you output your final structured report.\n\n"
                "Mandatory workflow:\n"
                "1. FIRST STEP: Call `read_file(file_path='output/DIAGNOSTICS.md')` to inspect the exact TypeScript/Vite error, failing file, and line number.\n"
                "2. Inspect the offending file with `read_file` around the identified error line.\n"
                "3. CRITICAL ACTION: Fix the code immediately using `replace_lines` or `patch_file`.\n"
                "   - Use `replace_lines(file_path=..., start_line=..., end_line=..., replacement=...)` to surgically replace the failing line range directly.\n"
                "   - You MUST modify the code on disk BEFORE re-running build!\n"
                "   - ANTI-LOOP GUARD: The system will automatically REJECT and BLOCK `run_command` if you try to run npm run build on unmodified code!\n"
                "4. After modifying code on disk, verify: Run `run_command(command='npm run build', cwd='frontend')`.\n"
                "5. Report actual test results and changed files in your final report.\n\n"
                "Do not invent missing requirements.\n"
                "Do not claim unverified success.\n"
                "Do not overwrite unrelated changes.\n\n"
                f"Assigned task: Frontend Auto-Repair - {phase_scope}\n"
                "State file: state/PROJECT_STATE.md\n"
                "Handoff file: state/HANDOFF.md"
            ),
            expected_output=(
                "Structured execution report containing:\n"
                "- Task ID and status\n"
                "- Implementation summary\n"
                "- Changed files\n"
                "- Acceptance criteria and verification evidence\n"
                "- Commands and actual test results (npm run build)\n"
                "- Deviations, blockers, and next actions"
            ),
            agent=repair_agent,
        )
        repair_crew = Crew(
            agents=[repair_agent],
            tasks=[repair_task],
            verbose=True,
            step_callback=global_step_callback,
            task_callback=global_task_callback,
        )
        return repair_crew.kickoff()

