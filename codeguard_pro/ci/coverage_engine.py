import subprocess
import xml.etree.ElementTree as ET


def run_pytest_with_coverage():
    """
    Runs pytest with coverage and generates coverage.xml
    """
    subprocess.run(
        ["pytest", "--cov=.", "--cov-report=xml"],
        capture_output=True,
        text=True
    )


def parse_coverage_xml():
    """
    Parses coverage.xml and returns coverage %
    """
    try:
        tree = ET.parse("coverage.xml")
        root = tree.getroot()
        coverage = float(root.attrib.get("line-rate")) * 100
        return round(coverage, 2)
    except Exception:
        return 0.0