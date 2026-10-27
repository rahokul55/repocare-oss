import pytest

from regressionproof.junit import JUnitError, parse_junit
from regressionproof.model import Outcome


def test_junit_reads_multiple_suites_and_error_types(write_junit):
    path = write_junit('''<testsuites>
      <testsuite name="a">
        <testcase classname="test_a" name="pass" />
        <testcase classname="test_a" name="fail"><failure message="broken"/></testcase>
      </testsuite>
      <testsuite name="b">
        <testcase classname="test_b" name="skip"><skipped/></testcase>
        <testcase classname="test_b" name="error"><error>trace</error></testcase>
      </testsuite>
    </testsuites>''')
    results = parse_junit(path)
    assert results["test_a::pass"].outcome is Outcome.PASSED
    assert results["test_a::fail"].detail == "broken"
    assert results["test_b::skip"].outcome is Outcome.SKIPPED
    assert results["test_b::error"].outcome is Outcome.ERROR


@pytest.mark.parametrize("xml", [
    "<html/>",
    "<testsuite />",
    '<testsuite><testcase classname="a"/></testsuite>',
    '<testsuite><testcase name="x"/><testcase name="x"/></testsuite>',
    "not xml",
    '<!DOCTYPE testsuite [<!ENTITY x "secret">]><testsuite><testcase name="x"/></testsuite>',
])
def test_rejects_unreliable_reports(write_junit, xml):
    with pytest.raises(JUnitError):
        parse_junit(write_junit(xml))


def test_rejects_missing_report(tmp_path):
    with pytest.raises(JUnitError, match="missing"):
        parse_junit(tmp_path / "not-there.xml")
