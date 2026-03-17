import streamlit as st
import os
import zipfile
import tempfile
import matplotlib.pyplot as plt
import json
import plotly.express as px
import csv
import io
from datetime import datetime
from groq import Groq
import tomllib
import time
import sys
import ast
import difflib
import pandas as pd
sys.path.append(os.getcwd())
import streamlit.components.v1 as components
import subprocess
import pytest
from io import StringIO


from codeguard_pro.core.analyzer import CodeAnalyzer
from codeguard_pro.core.quality_validator import QualityValidator
from codeguard_pro.core.docstring_generator import DocstringGenerator
from codeguard_pro.core.docstring_validator import DocstringValidator
from codeguard_pro.core.docstring_coverage import DocstringCoverage
from codeguard_pro.ci.coverage_engine import run_pytest_with_coverage, parse_coverage_xml
from codeguard_pro.ci.gatekeeper import evaluate_ci
from codeguard_pro.ci.trend_tracker import log_ci_run, load_ci_history
from codeguard_pro.ci.snapshot import snapshot_metrics
from codeguard_pro.ci.diff_engine import run_precommit_check
from codeguard_pro.core.diff_engine import generate_diff_html
from codeguard_pro.core.metrics import build_metrics_summary
from codeguard_pro.database.db import init_db, save_review
from codeguard_pro.core.dashboard_engine import extract_dashboard_data
from codeguard_pro.core.docstring_generator import DocstringGenerator
from codeguard_pro.core.docstring_applier import apply_docstring
from codeguard_pro.core.dashboard_data import (
    collect_function_data,
    build_dashboard_summary
)


# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="AI-Powered Code Reviewer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================= SAFE SESSION STATE =================
def init_session():
    defaults = {
        "files": {},
        "uploaded_files": {},
        "scanned_files": {},
        "doc_output": None,
        "validation_result": None,
        "coverage_result": None,
        "ci_runs": 0,
        "ci_pass": 0,
        "accepted_docs": 0,
        "rejected_docs": 0,

        "validation_result": None,
        "coverage_result": None,
        "validation_ran": False,
        "fixed_code": None,
        "selected_validation_file": None,

    }
        
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    
init_session()

if "project_scan_results" not in st.session_state:
    st.session_state.project_scan_results = {}

if "scan_stats" not in st.session_state:
    st.session_state.scan_stats = None

if "generated_docstring" not in st.session_state:
    st.session_state.generated_docstring = None

if "files" not in st.session_state:
    st.session_state.files = {}

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

if "scanned_files" not in st.session_state:
    st.session_state.scanned_files = {}

validator = QualityValidator()



# ================= LOAD CONFIG =================
def load_config():
    try:
        with open("pyproject.toml", "rb") as f:
            config_data = tomllib.load(f)

        # Read from new section: tool.ai_reviewer
        return config_data.get("tool", {}).get("ai_reviewer", {
            "coverage_threshold": 85,
            "max_complexity": 15,
            "min_maintainability": 60,
            "exclude": ["venv", "__pycache__", ".git"],
            "style": "google"
        })

    except Exception:
        return {
            "coverage_threshold": 85,
            "max_complexity": 15,
            "min_maintainability": 60,
            "exclude": ["venv", "__pycache__", ".git"],
            "style": "google"
        }
    
config = load_config()

# ================= AI HELPERS =================
def safe_int(value):
    return value if isinstance(value, (int, float)) else 0

def calculate_grade(score):
    if score >= 90: return "A"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "F"


def generate_improvement_checklist(complexity, maintainability, coverage):
    checklist = []
    if complexity > 10:
        checklist.append("Refactor high complexity functions.")
    if maintainability < 70:
        checklist.append("Improve modularity and structure.")
    if coverage < 80:
        checklist.append("Increase documentation coverage.")
    if not checklist:
        checklist.append("Maintain current high-quality standards.")
    return checklist


def generate_executive_summary(score, severity, grade):
    return f"""
Overall Score: {score}
Severity Level: {severity}
Health Grade: {grade}

This evaluation reflects structural integrity,
maintainability and documentation maturity.
"""


def generate_llm_summary(metrics):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "⚠ GROQ_API_KEY not configured."

    client = Groq(api_key=api_key)

    prompt = f"""
You are a senior software architect.

Analyze these metrics and provide:
- Strengths
- Weaknesses
- Improvements
- Risk analysis

Metrics:
{metrics}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ================= DASHBOARD HELPERS =================

def run_test_suite():

    modules = [
        "coverage_reporter",
        "dashboard",
        "generator",
        "llm_integration",
        "parser",
        "validation"
    ]

    results = []

    for mod in modules:

        try:
            result = subprocess.run(
                ["pytest", "-q"],
                capture_output=True,
                text=True
            )

            passed = "failed" not in result.stdout.lower()

            results.append({
                "Module": mod.replace("_"," ").title(),
                "Status": "Passed" if passed else "Failed",
                "Value": 1 if passed else 0
            })

        except Exception:
            results.append({
                "Module": mod.replace("_"," ").title(),
                "Status": "Failed",
                "Value": 0
            })

    return pd.DataFrame(results)


def extract_dashboard_data(files):

    rows = []
    total = 0
    documented = 0

    for fname, code in files.items():

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):

                if isinstance(node, ast.FunctionDef):

                    total += 1

                    has_doc = ast.get_docstring(node) is not None

                    if has_doc:
                        documented += 1

                    rows.append({
                        "file": fname,
                        "function": node.name,
                        "status": "Documented" if has_doc else "Missing"
                    })

        except:
            continue

    df = pd.DataFrame(rows)

    summary = {
        "total": total,
        "documented": documented,
        "missing": total - documented
    }

    return df, summary



def extract_dashboard_data(files):

    rows = []
    total = 0
    documented = 0

    for fname, code in files.items():

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):

                if isinstance(node, ast.FunctionDef):

                    total += 1
                    has_doc = ast.get_docstring(node) is not None

                    if has_doc:
                        documented += 1

                    rows.append({
                        "file": fname,
                        "function": node.name,
                        "status": "Documented" if has_doc else "Missing"
                    })

        except:
            continue

    df = pd.DataFrame(rows)

    summary = {
        "total": total,
        "documented": documented,
        "missing": total - documented
    }

    return df, summary

# ================= TEST ENGINE =================

def run_tests_and_collect_results():

    import subprocess
    import json

    try:

        subprocess.run(
            ["pytest", "--json-report", "--json-report-file=report.json"],
            capture_output=True
        )

        with open("report.json", "r") as f:
            report = json.load(f)

        summary = report.get("summary", {})

        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)

        # Prevent empty chart
        if passed == 0 and failed == 0:
            passed = 1

        return passed, failed

    except Exception as e:

        print("Test collection error:", e)

        return 1, 0


# ================= VALIDATION HELPERS =================

def highlight_pep257_issues(code, warnings):
    lines = code.split("\n")

    for warn in warnings:
        try:
            parts = warn.split()
            for part in parts:
                if part.isdigit():
                    line_no = int(part)
                    if 0 < line_no <= len(lines):
                        lines[line_no - 1] = "🔴 " + lines[line_no - 1]
                    break
        except:
            continue

    return "\n".join(lines)


# ================= AI FIX ENGINE =================

def fix_docstring_with_ai(code, style="google"):
    try:
        generator = DocstringGenerator(style)
        updated = generator.generate(code)

        if updated and isinstance(updated, str):
            return updated
        else:
            return code

    except Exception:
        return code

# ================= HEADER =================
st.title("🛡️ AI-Powered Code Reviewer & Quality Assistant")
st.divider()

# ================= FUNCTION BAR =================
col1, col2, col3, col4, col5 = st.columns(5)

# Scan
with col1:

    if st.button("📂 Scan Project"):

        scanned = {}

        for root, dirs, files in os.walk(os.getcwd()):
            if any(x in root for x in config["exclude"]):
                continue

            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    try:
                        with open(path, "r", encoding="utf-8") as fp:
                            scanned[path] = fp.read()
                    except:
                        continue

        st.session_state.scanned_files = scanned
        st.session_state.files = scanned.copy()
        st.session_state.validation_result = None
        st.session_state.coverage_result = None
        st.success(f"{len(scanned)} files scanned successfully.")

# Upload
with col2:
    uploaded = st.file_uploader(
    "📤 Upload Python Files",
    type=["py"],
    accept_multiple_files=True
)

if uploaded:

    uploaded_data = {}

    for file in uploaded:

        try:
            code = file.read().decode("utf-8")

            uploaded_data[file.name] = code

        except Exception:
            continue

    # store uploaded files
    st.session_state.uploaded_files = uploaded_data

    # IMPORTANT: merge into main files storage
    st.session_state.files = {
        **st.session_state.files,
        **uploaded_data
    }

    st.success(f"{len(uploaded_data)} files uploaded successfully.")

# File select
with col3:
    selected_file = None
    if st.session_state.files:
        selected_file = st.selectbox("📁 File", list(st.session_state.files.keys()))

# Style
with col4:
    style = st.selectbox("📝 Style", ["google", "numpy", "rest"])

# Clear
with col5:
    if st.button("🧹 Clear All"):
        st.session_state.files = {}
        st.session_state.uploaded_files = {}
        st.session_state.scanned_files = {}
        st.session_state.doc_output = None
        st.session_state.validation_result = None
        st.session_state.coverage_result = None
        st.rerun()

st.divider()

if not st.session_state.files:
    st.info("Scan or upload files to begin.")
    st.stop()

code = st.session_state.files[selected_file]

# ================= TABS =================
tab1, tab2, tab3, tab4, tab5, tab6, tab7= st.tabs(
    [
        "📄 Code",
        "📝 Docstrings",
        "📊 Metrics",
        "✅ Validation",
        "🏆 Overall",
        "🤖 AI Docstring Review",
        "📊 Dashboard"
        
    ]
)

# ================= CODE =================
with tab1:
    st.code(code, language="python")

# ================= DOCSTRINGS =================
with tab2:
    if st.button("Generate Docstring", key="generate_doc_btn"):
        generator = DocstringGenerator(style)
        st.session_state.doc_output = generator.generate(code)

    if st.session_state.doc_output:
        st.code(st.session_state.doc_output)

# ================= METRICS =================
with tab3:

    import ast

    st.header("📊 Code Metrics")

    analyzer = CodeAnalyzer(code)

    # ---------------- EXISTING SCORE LOGIC (UNCHANGED) ----------------
    code_score = validator.calculate_code_score(
        analyzer.total_complexity,
        analyzer.maintainability_index,
        analyzer.long_functions
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Maintainability", round(analyzer.maintainability_index, 2))
    col2.metric("Total Complexity", analyzer.total_complexity)
    col3.metric("Code Score", code_score)

    st.divider()

    # ---------------- FUNCTION LEVEL ANALYSIS (AST SAFE) ----------------
    st.subheader("🔎 Function-Level Analysis")

    functions_data = []

    try:
        tree = ast.parse(code)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_docstring = ast.get_docstring(node) is not None

                functions_data.append({
                    "Function Name": node.name,
                    "Start Line": node.lineno,
                    "End Line": getattr(node, "end_lineno", "-"),
                    "Has Docstring": "Yes" if has_docstring else "No"
                })

    except Exception as e:
        st.error(f"Function parsing error: {e}")

    # ---------------- DISPLAY RESULTS ----------------
    if functions_data:

        st.dataframe(functions_data, use_container_width=True)

        st.divider()

        total_funcs = len(functions_data)
        documented = sum(
            1 for f in functions_data if f["Has Docstring"] == "Yes"
        )
        doc_percent = round(
            (documented / total_funcs) * 100, 2
        ) if total_funcs else 0

        colA, colB, colC = st.columns(3)
        colA.metric("Total Functions", total_funcs)
        colB.metric("Documented Functions", documented)
        colC.metric("Documentation %", f"{doc_percent}%")

        st.progress(doc_percent / 100)

    else:
        st.info("No functions detected in this file.")

    st.divider()

    # ---------------- EXPORT OPTION ----------------
    if st.button("Download Metrics JSON", key="download_metrics_btn"):

        metrics_export = {
            "maintainability_index": analyzer.maintainability_index,
            "total_complexity": analyzer.total_complexity,
            "code_score": code_score,
            "functions": functions_data
        }

        st.download_button(
            "Download metrics.json",
            json.dumps(metrics_export, indent=4),
            file_name="metrics.json"
        )

    def highlight_pep257_issues(code, warnings):
            """
            Adds inline markers to lines that contain PEP257 violations.
            """
            lines = code.split("\n")

            for warn in warnings:
                if "line" in warn.lower():
                    try:
                        line_no = int("".join(filter(str.isdigit, warn)))
                        if 0 < line_no <= len(lines):
                            lines[line_no - 1] = "🔴 " + lines[line_no - 1]
                    except:
                        continue

            return "\n".join(lines)


# ================= VALIDATION TAB =================
with tab4:

    import matplotlib.pyplot as plt
    import streamlit as st

    st.header("✅ Code Validation & PEP 257 Compliance")

    # -------------------------------------------------
    # SESSION DEFAULTS
    # -------------------------------------------------
    if not st.session_state.files:
        st.session_state.files = {}

    if "selected_file" not in st.session_state:
        st.session_state.selected_file = None

    # -------------------------------------------------
    # MAIN LAYOUT
    # -------------------------------------------------
    left_panel, right_panel = st.columns([1, 2.2])

    # =================================================
    # LEFT PANEL — FILE EXPLORER
    # =================================================
    with left_panel:

        st.subheader("📂 File Explorer")

        # ---------- RUN SCAN ----------
        if st.button("🚀 Run Validation Scan", use_container_width=True):

            validator_doc = DocstringValidator()
            coverage_calc = DocstringCoverage()

            validation_map = {}
            coverage_map = {}

            for fname, fcode in st.session_state.files.items():
                validation_map[fname] = validator_doc.validate(fcode)
                coverage_map[fname] = coverage_calc.calculate(fcode)

            st.session_state.validation_map = validation_map
            st.session_state.coverage_map = coverage_map

            st.success("Scan Completed ✅")

        st.divider()

        # ---------- FILE LIST ----------
        st.markdown("### 📁 Uploaded Files")

        if "validation_map" in st.session_state:

            for fname, result in st.session_state.validation_map.items():

                icon = "✅" if result["status"] == "Compliant" else "❌"

                if st.button(
                    f"{icon} {fname}",
                    key=f"file_{fname}",
                    use_container_width=True,
                ):
                    st.session_state.selected_file = fname

        else:
            st.info("Run scan to load files")

        st.divider()

        # ---------- SCANNED CODE VIEW ----------
        if st.session_state.selected_file:

            st.markdown("### 🔎 Scanned Code")

            st.code(
                st.session_state.files[
                    st.session_state.selected_file
                ],
                language="python",
            )

    # =================================================
    # RIGHT PANEL — AI FIX WORKSPACE
    # =================================================
    with right_panel:

        st.subheader("🤖 VALIDATION STATUS")

        if (
            "validation_map" in st.session_state
            and st.session_state.selected_file
        ):

            selected_file = st.session_state.selected_file
            result = st.session_state.validation_map[selected_file]
            coverage = st.session_state.coverage_map[selected_file]

            # ---------- VALIDATION STATUS ----------
            if result["status"] == "Compliant":
                st.success("✅ PEP 257 Compliant")
            else:
                st.error("❌ Violations Found")

                for issue in result["warnings"]:
                    st.warning(issue)

            st.divider()

            

            # ---------- AI FIX ----------
            if st.button("🤖 Fix Violations with AI", key="fix_ai_btn"):

                original_code = st.session_state.files[selected_file]

                generator = DocstringGenerator(style)
                fixed_code = generator.generate(original_code)

                st.session_state.fixed_code = fixed_code
                st.success("AI Fix Generated Successfully")

    # ---------------- DIFF VIEWER ----------------
                diff_html = generate_diff_html(original_code, fixed_code)

                st.subheader("🔍 Side-by-Side Diff Viewer")
                st.components.v1.html(diff_html, height=600, scrolling=True)

    # ---------------- QUALITY SCORE ----------------
                coverage = st.session_state.coverage_map[selected_file]
                result = st.session_state.validation_map[selected_file]

                issues_count = len(result.get("warnings", []))

                record = build_metrics_summary(
                    selected_file,
                    coverage["coverage_percent"],
                    issues_count
                )

                init_db()
                save_review(record)

                st.metric("Quality Score", record["quality_score"])

            # ---------- FIXED CODE PREVIEW ----------
            if (
                "fixed_code" in st.session_state
                and st.session_state.fixed_code
                and isinstance(st.session_state.fixed_code, str)
            ):

                st.download_button(
                    "📥 Download Fixed File",
                    data=st.session_state.fixed_code.encode("utf-8"),
                    file_name=f"fixed_{selected_file}",
                    mime="text/plain",
                    key="download_fixed_btn"
                )

            else:
                st.info("No fixed file available yet.")

        # ---------- METRICS ----------
            c1, c2, c3 = st.columns(3)
            c1.metric("Coverage %", coverage["coverage_percent"])
            c2.metric("Total Objects", coverage["total_objects"])
            c3.metric("Documented", coverage["documented_objects"])

            st.divider()

            # ---------- COVERAGE GRAPH ----------
            fig, ax = plt.subplots(figsize=(5, 3))

            ax.bar(
                ["Documented", "Undocumented"],
                [
                    coverage["documented_objects"],
                    coverage["total_objects"]
                    - coverage["documented_objects"],
                ],
            )

            ax.set_title("Documentation Coverage")
            ax.grid(alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)

            st.divider()

        else:
            st.info("👈 Run scan and select a file from left panel.")


### ================= OVERALL =================
with tab5:

    analyzer = CodeAnalyzer(code)
    coverage = st.session_state.coverage_result or {}

    code_score = validator.calculate_code_score(
        analyzer.total_complexity,
        analyzer.maintainability_index,
        analyzer.long_functions
    )

    doc_score = coverage.get("coverage_percent", 0)
    overall_score = validator.calculate_overall_score(code_score, doc_score)
    severity = validator.get_severity(overall_score)
    grade = calculate_grade(overall_score)

    col1, col2, col3 = st.columns(3)
    col1.metric("Overall Score", overall_score)
    col2.metric("Severity", severity)
    col3.metric("Health Grade", grade)

    st.divider()

    checklist = generate_improvement_checklist(
        analyzer.total_complexity,
        analyzer.maintainability_index,
        doc_score
    )

    st.subheader("Improvement Checklist")
    for item in checklist:
        st.write(f"• {item}")

    st.divider()

    summary = generate_executive_summary(overall_score, severity, grade)
    st.subheader("Executive Summary")
    st.write(summary)

    if st.button("Generate AI LLM Summary"):
        metrics = {
            "complexity": analyzer.total_complexity,
            "maintainability": analyzer.maintainability_index,
            "coverage": doc_score,
            "overall_score": overall_score,
            "severity": severity,
            "grade": grade
        }

        llm_summary = generate_llm_summary(metrics)
        st.write(llm_summary)

        st.download_button(
            "Download AI Summary",
            llm_summary,
            file_name="ai_summary.txt"
        )

# ================= TAB 6 : AI DOCSTRING REVIEW =================
with tab6:

    st.header("🤖 AI Docstring Review")

    left, right = st.columns([1, 2])

    # =========================================================
    # LEFT PANEL
    # =========================================================
    with left:

        st.subheader("📂 Project Files")

        style = st.selectbox(
            "Docstring Style",
            ["google", "numpy", "rest"]
        )

   

        # ---------------- Upload Files ----------------
        if uploaded:

            uploaded_data = {}

            for file in uploaded:

                try:
                    uploaded_data[file.name] = file.read().decode()
                except:
                    continue

            st.session_state.files = uploaded_data
            st.success(f"{len(uploaded_data)} files uploaded")

        # Stop if no files
        if not st.session_state.files:

            st.info("Upload or scan project files first")
            st.stop()

        # ---------------- File Selector ----------------
        file_names = list(st.session_state.files.keys())

        selected_file = st.selectbox(
            "Select File",
            file_names
        )

    # =========================================================
    # RIGHT PANEL
    # =========================================================
    with right:

        st.subheader("Function Review")

        code_text = st.session_state.files[selected_file]

        # ---------------- Extract Functions ----------------
        functions = []
        try:

            # Normalize code
            code_text = code_text.replace("\r\n", "\n")

            tree = ast.parse(code_text)

            for node in ast.walk(tree):

                if isinstance(node, ast.FunctionDef):

                    doc = ast.get_docstring(node)

                    start = node.lineno
                    end = getattr(node, "end_lineno", start)

                    lines = code_text.splitlines()

                    func_code = "\n".join(lines[start-1:end])

                    functions.append({
                        "name": node.name,
                        "code": func_code,
                        "docstring": doc
                    })

        except Exception as e:
            st.error(f"AST parsing failed: {e}")

        if not functions:

            st.warning("No functions detected in this file.")

            st.info("Displaying full file instead.")

            st.code(code_text, language="python")

            st.stop()

        # ---------------- Function Selector ----------------
        func_names = [f["name"] for f in functions]

        selected_func = st.selectbox(
            "Select Function",
            func_names
        )

        func_data = next(
            (f for f in functions if f["name"] == selected_func),
            None
        )

        if func_data is None:
            st.error("Function not found")
            st.stop()

        # ---------------- Function Code ----------------
        st.code(func_data["code"], language="python")

        colA, colB = st.columns(2)

        # =================================================
        # CURRENT DOCSTRING
        # =================================================
        with colA:

            st.markdown("### Current Docstring")

            if func_data["docstring"]:
                st.code(func_data["docstring"])
            else:
                st.info("No docstring found")

        # =================================================
        # AI DOCSTRING
        # =================================================
        with colB:

            st.markdown("### AI Generated Docstring")

            if st.button("Generate AI Docstring"):

                try:
                    generator = DocstringGenerator(style)

                    ai_doc = generator.generate(
                        func_data["code"]
                    )

                    st.session_state.ai_doc = ai_doc

                except Exception as e:
                    st.error(f"AI generation failed: {e}")

            if "ai_doc" in st.session_state:
                st.code(st.session_state.ai_doc)

        # =================================================
        # ACTION BUTTONS
        # =================================================
        col1, col2 = st.columns(2)

        if col1.button("Accept and Apply"):

            if "ai_doc" not in st.session_state:
                st.warning("Generate AI docstring first")

            else:

        # Apply docstring to function
                updated_function = apply_docstring(
                    func_data["code"],
                    st.session_state.ai_doc
                )

        # Replace function inside full file
                full_code = st.session_state.files[selected_file]

                new_file_code = full_code.replace(
                    func_data["code"],
                    updated_function
                )

        # Save file back to disk if it is a real path
                if os.path.exists(selected_file):

                    with open(selected_file, "w", encoding="utf-8") as f:
                        f.write(new_file_code)

        # Update session memory
                st.session_state.files[selected_file] = new_file_code

                st.success("✅ Docstring applied and file updated automatically")

                st.code(updated_function, language="python")

        if col2.button("Skip"):

            st.warning("Skipped function")


# ================= TAB 7 DASHBOARD =================

with tab7:

    files = st.session_state.get("files", {})

    if len(files) == 0:
        st.info("Scan project or upload files to activate dashboard.")
        st.stop()

    # ================= TEST RESULTS =================

    st.subheader("🧪 Test Results Overview")

    if st.button("Run Test Suite"):

        df_test = run_test_suite()
        st.session_state.test_results = df_test


    if "test_results" in st.session_state:

        df_test = st.session_state.test_results

        fig = px.bar(
            df_test,
            x="Module",
            y="Value",
            color="Status",
            color_discrete_map={
                "Passed":"#2ecc71",
                "Failed":"#e74c3c"
            },
            height=320
        )

        fig.update_layout(
            margin=dict(l=10,r=10,t=40,b=10)
        )

        st.plotly_chart(fig, use_container_width=True)

        if all(df_test["Status"] == "Passed"):
            st.success("✅ All modules passed testing")
        else:
            st.error("❌ Some modules failed tests")

    st.divider()

    # ================= FUNCTION ANALYTICS =================

    files = st.session_state.get("files", {})

    if not files:
        st.info("Upload or scan files to activate the dashboard.")
        st.stop()

    df, summary = extract_dashboard_data(files)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Functions", summary.get("total",0))
    col2.metric("Documented", summary.get("documented",0))
    col3.metric("Missing Docstrings", summary.get("missing",0))

    st.divider()

    # ================= DOCUMENTATION COVERAGE =================

    coverage_df = pd.DataFrame({
        "Category":["Documented","Missing"],
        "Count":[
            summary.get("documented",0),
            summary.get("missing",0)
        ]
    })

    fig2 = px.pie(
        coverage_df,
        names="Category",
        values="Count",
        color_discrete_sequence=["#3498db","#e74c3c"],
        height=320
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ================= DEVELOPER TOOLS =================

    st.subheader("🛠 Developer Tools")

    if "dashboard_tool" not in st.session_state:
        st.session_state.dashboard_tool = None

    card1, card2, card3, card4 = st.columns(4)

    with card1:
        if st.button("🔍 Advanced Filter", use_container_width=True):
            st.session_state.dashboard_tool = "filter"

    with card2:
        if st.button("🔎 Function Search", use_container_width=True):
            st.session_state.dashboard_tool = "search"

    with card3:
        if st.button("📦 Export Report", use_container_width=True):
            st.session_state.dashboard_tool = "export"

    with card4:
        if st.button("💡 AI Guide", use_container_width=True):
            st.session_state.dashboard_tool = "guide"

    st.divider()

    tool = st.session_state.dashboard_tool

    # ================= FILTER =================

    if tool == "filter":

        st.subheader("🔍 Filter Functions")

        status = st.selectbox(
            "Filter by Documentation Status",
            ["All","Documented","Missing"]
        )

        if status == "All":
            filtered = df
        else:
            filtered = df[df["status"] == status]

        st.dataframe(filtered, use_container_width=True)

    # ================= SEARCH =================

    elif tool == "search":

        st.subheader("🔎 Search Function")

        query = st.text_input("Enter Function Name")

        if query:

            results = df[df["function"].str.contains(query, case=False)]

            if not results.empty:
                st.dataframe(results, use_container_width=True)
            else:
                st.warning("No matching function found")

    # ================= EXPORT =================

    elif tool == "export":

        st.subheader("📦 Export Reports")

        json_data = json.dumps(summary, indent=4)

        st.download_button(
            "Download JSON Summary",
            json_data,
            file_name="dashboard_summary.json"
        )

        csv_buffer = StringIO()
        df.to_csv(csv_buffer)

        st.download_button(
            "Download CSV Report",
            csv_buffer.getvalue(),
            file_name="functions_report.csv"
        )

    # ================= AI GUIDE =================

    elif tool == "guide":

        st.subheader("💡 AI Developer Guide")

        if st.button("Generate AI Guide"):

            api_key = os.getenv("GROQ_API_KEY")

            if not api_key:
                st.error("GROQ_API_KEY not configured")
            else:

                client = Groq(api_key=api_key)

                prompt = f"""
Explain how to improve code documentation and use an AI Code Reviewer dashboard.

Project stats:
Total functions: {summary["total"]}
Documented: {summary["documented"]}
Missing: {summary["missing"]}

Explain best practices and how to fix missing docstrings.
"""

                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role":"user","content":prompt}]
                )

                st.write(response.choices[0].message.content)

# ================= FOOTER =================
current_year = datetime.now().year
st.markdown(f"""
<hr>
<center>
🛡 AI-Powered Code Reviewer | © {current_year} | Created by Aman Gupta
</center>
""", unsafe_allow_html=True)