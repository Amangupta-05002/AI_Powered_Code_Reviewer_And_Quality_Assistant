# codeguard_pro/core/metrics.py

from datetime import datetime

def calculate_quality_score(coverage: float, issue_count: int):
    score = coverage - (issue_count * 2)
    return max(round(score, 2), 0)

def build_metrics_summary(filename, coverage, issues):
    return {
        "filename": filename,
        "coverage": coverage,
        "issues": issues,
        "quality_score": calculate_quality_score(coverage, issues),
        "timestamp": datetime.utcnow().isoformat()
    }