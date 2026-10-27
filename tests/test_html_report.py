"""Offline HTML reports must not interpret test names as markup."""

from regressionproof.compare import compare_revisions
from regressionproof.model import Outcome, RevisionResult, TestCase, TestRun
from regressionproof.report import to_html, write_report


def test_html_report_escapes_test_data(tmp_path):
    malicious = '<img src=x onerror="alert(1)">::run'
    baseline = RevisionResult('<main>', 'a' * 40,
                              (TestRun({malicious: TestCase(malicious, Outcome.PASSED)}, 0, 1),))
    candidate = RevisionResult('feature', 'b' * 40,
                               (TestRun({malicious: TestCase(malicious, Outcome.FAILED)}, 1, 1),))
    comparison = compare_revisions(baseline, candidate)
    html = to_html(comparison)
    assert '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;' in html
    assert '<img src=x onerror' not in html
    assert '<code><main></code>' not in html
    assert '&lt;main&gt;' in html
    assert '<script' not in html
    assert 'default-src' in html
    write_report(comparison, tmp_path)
    assert (tmp_path / 'report.html').read_text() == html
