from codeguard_pro.core.docstring_coverage import DocstringCoverage

def test_empty_code():
    coverage = DocstringCoverage().calculate("")
    assert coverage["total_objects"] == 0