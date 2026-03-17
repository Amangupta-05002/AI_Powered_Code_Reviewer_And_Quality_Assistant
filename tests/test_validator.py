from codeguard_pro.core.quality_validator import QualityValidator

def test_code_score():
    validator = QualityValidator()
    score = validator.calculate_code_score(5, 80, [])
    assert score >= 90

def test_severity():
    validator = QualityValidator()
    assert validator.get_severity(90) == "Low"