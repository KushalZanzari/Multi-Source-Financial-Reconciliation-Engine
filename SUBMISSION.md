# 📋 Official Submission Checklist: AI Finance Controller (`micro1`)

This document details the exact map of required hackathon deliverables to project files in `micro1/`.

---

## 📦 Required Deliverables & Project File Mapping

| # | Required Deliverable | Satisfying Project Files / Location | Verification Command |
| :-: | :--- | :--- | :--- |
| **1** | **Complete Solution Code + Improvement Changelog** | • Full source code: `micro1/src/`, `micro1/config/`, `micro1/data/`, `micro1/baseline/`, `micro1/app.py`<br>• Improvement Changelog Table: [`README.md`](README.md#-%EF%B8%8F-improvement-changelog) | `python eval/run_evaluation.py`<br>`python -m pytest tests/` |
| **2** | **Reproduction Guide** | • [`REPRODUCTION.md`](REPRODUCTION.md) | Follow commands in REPRODUCTION.md |
| **3** | **Solution Video (≤5 min)** | • Complete word-for-word narration script: [`docs/video_script.md`](docs/video_script.md)<br>• **Note**: The video file must be recorded by the user reading `docs/video_script.md` and uploaded via the platform submission form. | Read `docs/video_script.md` during video recording |
| **4** | **Agent Trajectories** | • Sample Trajectories Directory: [`trajectories/sample_trajectories/`](trajectories/sample_trajectories/)<br>  - `trajectory_auto_resolved.json` (Clean auto-resolved typo case)<br>  - `trajectory_tool_use.json` (Multi-tool reasoning case)<br>  - `trajectory_human_review.json` (Human review checkpoint gated case) | Inspect JSON files in `trajectories/sample_trajectories/` |

---

## 📌 Ground Rules Compliance Summary

- [x] **Synthetic Data Only**: All evaluation cases in `eval/eval_cases.json` and datasets in `data/` are synthetically generated.
- [x] **Human Review Checkpoint**: Any match decision with confidence <70.0% is enqueued into `src/review.py` for human approval before execution.
- [x] **No Secrets Committed**: Credentials managed via `.env.example` and `python-dotenv`. Zero hardcoded API keys.
- [x] **Real Metric Citations**: Every accuracy, human ops time, and token cost number cited in `README.md`, `docs/hot_take.md`, and `docs/video_script.md` ties directly to `eval/results/baseline_results.json` and `eval/results/agent_results.json`.

---

> 📢 **Important Note for Submitter**: Antigravity has generated the complete solution codebase, evaluation harness, test suite, trajectory logs, and word-for-word narration script (`docs/video_script.md`). Please record your screen following `docs/video_script.md` (under 5 minutes) and upload the video link along with the repository files to complete your submission!
