"""Small, strict JUnit XML reader.

JUnit does not standardise test identity across all producers. We require stable
(classname, name) identities. Collisions abort the comparison instead of
silently overwriting a test result.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from .model import Outcome, TestCase

MAX_XML_BYTES = 16 * 1024 * 1024


class JUnitError(ValueError):
    """The test report cannot be trusted for comparison."""


def parse_junit(path: Path) -> dict[str, TestCase]:
    if not path.is_file():
        raise JUnitError(f"JUnit report missing: {path}")
    if path.stat().st_size > MAX_XML_BYTES:
        raise JUnitError(f"JUnit report exceeds {MAX_XML_BYTES} bytes: {path}")
    # Reject DTDs entirely; no JUnit producer needs them, and custom entities
    # are an avoidable XML attack surface.
    if b"<!DOCTYPE" in path.read_bytes().upper():
        raise JUnitError("DTD/DOCTYPE declarations are not supported")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise JUnitError(f"Invalid JUnit XML at {path}: {exc}") from exc
    if root.tag not in {"testsuite", "testsuites"}:
        raise JUnitError(f"Expected testsuite(s) root, got {root.tag!r}")
    result: dict[str, TestCase] = {}
    for entry in root.iter("testcase"):
        name = entry.get("name", "").strip()
        if not name:
            raise JUnitError("Found a testcase without a name")
        classname = entry.get("classname", "").strip()
        key = f"{classname}::{name}" if classname else name
        if key in result:
            raise JUnitError(f"Duplicate testcase identity: {key}")
        failure = entry.find("failure")
        error = entry.find("error")
        skipped = entry.find("skipped")
        if error is not None:
            status, node = Outcome.ERROR, error
        elif failure is not None:
            status, node = Outcome.FAILED, failure
        elif skipped is not None:
            status, node = Outcome.SKIPPED, skipped
        else:
            status, node = Outcome.PASSED, None
        detail = (node.get("message") or node.text or "") if node is not None else ""
        result[key] = TestCase(key=key, outcome=status, detail=detail[:800])
    if not result:
        raise JUnitError(f"JUnit report contains no testcases: {path}")
    return result
