
class QualityValidator:

    # ================= CODE SCORE =================
    def calculate_code_score(self, complexity, maintainability, long_functions):
        score = 100

        # Penalize high complexity
        if complexity > 15:
            score -= 25
        elif complexity > 10:
            score -= 15
        elif complexity > 5:
            score -= 5

        # Penalize low maintainability
        if maintainability < 40:
            score -= 30
        elif maintainability < 60:
            score -= 15
        elif maintainability < 75:
            score -= 5

        # Penalize long functions
        score -= len(long_functions) * 5

        return max(score, 0)

    # ================= DOC SCORE =================
    def calculate_doc_score(self, coverage_percent, status):
        score = coverage_percent

        if status != "Compliant":
            score -= 20

        return max(score, 0)

    # ================= OVERALL SCORE =================
    def calculate_overall_score(self, code_score, doc_score):
        return round((code_score * 0.6) + (doc_score * 0.4), 2)

    # ================= SEVERITY =================
    def get_severity(self, overall_score):
        if overall_score >= 85:
            return "Low"
        elif overall_score >= 60:
            return "Medium"
        else:
            return "High"
        
    
    