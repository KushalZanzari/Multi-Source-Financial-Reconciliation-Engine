# 🔄 Reproduction Guide: AI Finance Controller

This document provides exact, step-by-step instructions to set up a clean environment, generate synthetic datasets, run the baseline matcher, run the full pipeline evaluation, and launch the interactive Streamlit dashboard.

---

## 1. Prerequisites & Environment Setup

### Environment Requirements
- **Python Version**: Python 3.10, 3.11, 3.12, or 3.13
- **Operating System**: Windows, macOS, or Linux

### Clone & Install Dependencies
```bash
# Navigate to the micro1 submission directory
cd micro1

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt
```

### Dependency Versions (`requirements.txt`)
```text
pandas>=2.0.0
streamlit>=1.30.0
python-dotenv>=1.0.0
python-dateutil>=2.8.2
pytest>=7.4.0
anthropic>=0.18.0
```

### Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional)* Add your Anthropic API Key in `.env` if you wish to run live Claude 3.5 Sonnet reasoning API calls:
```text
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LLM_MODEL_NAME=claude-3-5-sonnet-20241022
```
*Note: If `ANTHROPIC_API_KEY` is omitted, the system automatically runs the built-in **Local ReAct Fallback Loop** with 100% deterministic reproducibility!*

---

## 2. Step 1: Generate Synthetic Datasets

Run the synthetic data generator script to populate `data/` with 53 synthetic transaction records:
```bash
python data/generate_synthetic_data.py
```

### Expected Output:
```text
Generated synthetic datasets in micro1/data:
  - bank_statement.csv: 53 records
  - settlement_report.csv: 53 records
  - internal_ledger.csv: 54 records
  - ground_truth.json: 53 truth entries
```

---

## 3. Step 2: Run Baseline Matcher & Evaluation Harness

Run the comprehensive evaluation script comparing `baseline_matcher.py` vs. the full solution pipeline:
```bash
python eval/run_evaluation.py
```

### Expected Output:
```text
=========================================================
Running Evaluation Harness over 10 Evaluation Cases
=========================================================

[1/2] Running Baseline Matcher Evaluation...
  -> Baseline Accuracy: 30.0% (3/10)
  -> Baseline Human Ops Time Required: 45.0 minutes
  -> Baseline Cost: $0.00

[2/2] Running Full Solution Pipeline Evaluation...
  -> Full Pipeline Accuracy: 50.0% (5/10)
  -> Full Pipeline Human Ops Time Required: 7.0 minutes
  -> Full Pipeline Token Cost: $0.025

=========================================================
[SUCCESS] Evaluation complete! Results saved to eval/results/
=========================================================
```

### Artifacts Saved:
- `eval/results/baseline_results.json`
- `eval/results/agent_results.json`

---

## 4. Step 3: Run Full Pipeline Unit Tests

Execute the full pytest suite to verify deterministic matching, ReAct agent tools, calibration scoring, schema mapper, data quality, and PII masking:
```bash
python -m pytest tests/
```

### Expected Output:
```text
============================== 15 passed in ~8.5s ==============================
```

---

## 5. Step 4: Launch Interactive Streamlit Web Application

Launch the interactive web application to test single-file CSV upload, schema auto-mapping, data quality pre-check report cards, PII masking, human review queue, and audit trail inspection:
```bash
python -m streamlit run app.py
```

Open your browser at **`http://localhost:8501`**.

---

## ⏱️ Approximate Runtime & API Cost Summary

| Command / Task | Approximate Runtime | Estimated Token / API Cost |
| :--- | :--- | :--- |
| `python data/generate_synthetic_data.py` | ~0.5 seconds | **$0.00** |
| `python eval/run_evaluation.py` | ~0.02 seconds | **$0.025** ($0.0025 / rec) |
| `python -m pytest tests/` | ~8.5 seconds | **$0.00** |
| `python -m streamlit run app.py` (Full Pipeline Run) | ~0.05 seconds (53 recs) | **$0.050** |
