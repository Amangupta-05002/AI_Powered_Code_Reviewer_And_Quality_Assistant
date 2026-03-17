# codeguard_pro/core/diff_engine.py

import difflib

def generate_diff_html(original: str, updated: str) -> str:
    diff = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)

    return diff.make_file(
        original.splitlines(),
        updated.splitlines(),
        fromdesc="Original",
        todesc="AI Fixed",
        context=True,
        numlines=3
    )