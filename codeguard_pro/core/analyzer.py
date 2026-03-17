from radon.complexity import cc_visit
from radon.metrics import mi_visit


class CodeAnalyzer:

    def __init__(self, code):
        self.blocks = cc_visit(code)

        self.total_complexity = sum(b.complexity for b in self.blocks)
        self.avg_complexity = (
            self.total_complexity / len(self.blocks)
            if self.blocks else 0
        )

        self.long_functions = [
            b.name for b in self.blocks if b.complexity > 10
        ]

        self.maintainability_index = mi_visit(code, multi=True)