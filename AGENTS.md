# AGENTS.md — Global Engineering Rules & Work Contracts (CoffeeFlow)

> **Mandatory Instructions for AI Coding Assistants & Autonomous Agents**  
> All agents (BA, Backend, Frontend, QA, or Pair-Programming Assistants) MUST strictly comply with this document and [docs/PRD.md](file:///C:/Users/Minnut/Desktop/VSCode/CrewAI%20-%20Copy/docs/PRD.md).

---

## 1. Project Overview & Architecture Blueprint
- **System**: CoffeeFlow (Coffee Shop Management System)
- **Monorepo Structure**:
  - `backend/`: Python 3.12+ REST API (FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, PostgreSQL, Pytest).
  - `frontend/`: React + TypeScript + Vite + Tailwind CSS (SPA for Cashier POS & Manager Dashboard).
  - `design/`: Design system tokens and Stitch desktop/tablet UI mockups (`design/DESIGN_SYSTEM.md`).
  - `docs/`: Product Requirements (`docs/PRD.md`), Architecture (`docs/ARCHITECTURE.md`), Data Models (`docs/DATA_MODEL.md`), API Contracts (`docs/API_CONTRACTS.md`), and Business Rules (`docs/BUSINESS_RULES.md`).
  - `plans/`: Implementation roadmap (`plans/IMPLEMENT_PLAN.md`) and task specifications (`plans/TASKS.md`).
  - `state/`: Runtime project status (`state/PROJECT_STATE.md`) and inter-agent handoff notes (`state/HANDOFF.md`).
  - `qa/`: Test strategy, acceptance criteria, and quality gates (`qa/TEST_PLAN.md`).
  - `web_builder/`: CrewAI Multi-Agent Flow orchestrator.

---

## 2. Core Engineering Standards (Zero-Tolerance Rules)

### 2.1. Backend Engineering (Python / FastAPI):
1. **Zero-Float Rule**: Monetary amounts (`base_price`, `unit_price`, `subtotal`, `total_amount`, `amount`) MUST strictly use integer minor units (VND: `int` / `BIGINT`) or Python `Decimal`. NEVER use `float` for currency.
2. **ACID Transactions**: Multi-step business mutations (e.g. order confirmation + stock deduction, or payment completion + order status update) MUST execute within a single database transaction with automatic rollback on error.
3. **Layered Architecture**:
   - Router layer (`api/v1/`): HTTP endpoints, route guards, dependency injection.
   - Schema layer (`schemas/`): Pydantic request and response models.
   - Service layer (`services/`): Business logic, transaction orchestration.
   - Repository layer (`repositories/`): Database queries and persistence.
   - Model layer (`models/`): SQLAlchemy ORM models.
4. **Idempotency & Concurrency**:
   - Use idempotency keys for payment and order confirmation requests to prevent duplicate charges or double stock deduction.
   - Use concurrency-safe updates (e.g., `SELECT ... FOR UPDATE` or atomic decrement) for inventory stock.
5. **Quality Gate**: Every backend change must pass `pytest` with 0 failures and 0 errors.

### 2.2. Frontend Engineering & Design Integrity:
1. **Design System Grounding**: Strictly adhere to `design/DESIGN_SYSTEM.md` and Stitch specifications. Reusable React components must follow responsive touch-friendly POS standards.
2. **Role-Based Views**: Cashier POS (`/pos`) must be lightning-fast (minimal clicks); Manager views (`/dashboard`, `/menu`, `/inventory`, `/reports`) must provide full analytical control.
3. **Type Safety & API Client**:
   - TypeScript interfaces in `src/types/` MUST synchronize 1:1 with backend Pydantic schemas.
   - ALWAYS use authenticated API client with interceptors for JWT Bearer tokens.
4. **Quality Gate**: Every frontend change must pass `npm run build` with 0 TypeScript/Vite errors.

### 2.3. Anti-Hallucination & Work Contract Constraints:
- **Do not invent missing requirements**: Only 2 roles exist (`CASHIER`, `MANAGER`). Do not introduce third roles or unauthorized features.
- **Never trust frontend pricing**: All totals and prices MUST be calculated and verified by backend.
- **Do not overwrite historical records**: Prices in historical orders must remain preserved via snapshots. Never delete transactions or audit logs.
- **Do not claim unverified success**: Never mark a task as completed without executing verification tests (`pytest`, `npm run build`).

---

## 3. Mandatory 8-Step Agent Workflow

Whenever assigned a task, every agent MUST execute these 8 steps sequentially:
1. **Read `AGENTS.md`**: Refresh architectural rules and constraints.
2. **Read Assigned Specifications**: Inspect the assigned task file and referenced documents in `docs/`, `design/`, `plans/`.
3. **Inspect Existing Repository**: Audit existing code on disk and review `state/PROJECT_STATE.md`.
4. **Resolve Dependencies**: Identify missing schemas, packages, or routes before coding.
5. **Implement Authorized Scope**: Write only the code required for the assigned task.
6. **Verify Every Acceptance Criterion**: Execute automated tests via terminal (`pytest` / `npm run build`).
7. **Report Verification Evidence**: Output actual execution logs, changed files, and test metrics.
8. **Prepare Structured Handoff**: Update `state/PROJECT_STATE.md` and record handoff context in `state/HANDOFF.md`.
