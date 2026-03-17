def evaluate_ci(coverage, complexity, maintainability, config):
    """
    CI gate logic
    """

    if coverage < config["coverage_threshold"]:
        return False, "Coverage below threshold"

    if complexity > config["max_complexity"]:
        return False, "Complexity too high"

    if maintainability < config["min_maintainability"]:
        return False, "Maintainability too low"

    return True, "CI Passed"