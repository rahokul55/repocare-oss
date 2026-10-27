"""Public CLI contracts: repeat observations, CI policy, and GitHub output."""

from __future__ import annotations

import json

import pytest

from regressionproof.cli import main


@pytest.fixture
def xml(tmp_path):
    def write(name, status):
        marker = {'passed': '', 'failed': '<failure message="failed"/>',
                  'skipped': '<skipped/>'}[status]
        path = tmp_path / name
        path.write_text(f'<testsuite><testcase classname="x" name="case">'
                        f'{marker}</testcase></testsuite>', encoding='utf-8')
        return str(path)
    return write


def test_repeated_xml_marks_flaky_not_a_regression(xml, tmp_path):
    base_a = xml('a.xml', 'passed')
    base_b = xml('b.xml', 'failed')
    head_a = xml('c.xml', 'failed')
    head_b = xml('d.xml', 'failed')
    dest = tmp_path / 'report'
    args = ['compare', '--base-xml', base_a, '--base-xml', base_b,
            '--head-xml', head_a, '--head-xml', head_b, '--output', str(dest)]
    assert main(args) == 0
    result = json.loads((dest / 'result.json').read_text())
    assert result['status'] == 'unstable'
    assert result['counts']['flaky'] == 1
    assert result['counts']['regressions'] == 0
    assert main(args + ['--fail-on', 'unstable']) == 1
    assert main(args + ['--no-fail', '--fail-on', 'unstable']) == 0


def test_github_summary_and_output_are_explicit(xml, tmp_path, monkeypatch):
    before = xml('before.xml', 'passed')
    after = xml('after.xml', 'failed')
    summary = tmp_path / 'summary.md'
    output = tmp_path / 'output.txt'
    summary.write_text('# Existing job summary\n', encoding='utf-8')
    output.write_text('prior=value\n', encoding='utf-8')
    monkeypatch.setenv('GITHUB_STEP_SUMMARY', str(summary))
    monkeypatch.setenv('GITHUB_OUTPUT', str(output))
    args = ['compare', '--base-xml', before, '--head-xml', after,
            '--output', str(tmp_path / 'reports')]
    assert main(args) == 1
    assert 'RegressionProof' not in summary.read_text()
    assert main(args + ['--github-summary', '--github-output']) == 1
    assert '# Existing job summary' in summary.read_text()
    assert 'RegressionProof test comparison' in summary.read_text()
    assert 'prior=value' in output.read_text()
    assert 'regressions=1\n' in output.read_text()
    assert 'status=regression\n' in output.read_text()


def test_missing_github_environment_returns_configuration_error(xml, tmp_path, monkeypatch):
    monkeypatch.delenv('GITHUB_OUTPUT', raising=False)
    args = ['compare', '--base-xml', xml('base.xml', 'passed'),
            '--head-xml', xml('head.xml', 'failed'),
            '--github-output', '--output', str(tmp_path / 'out')]
    assert main(args) == 2


def test_too_many_observations_are_rejected(xml, tmp_path):
    path = xml('pass.xml', 'passed')
    args = ['compare', '--head-xml', path, '--output', str(tmp_path / 'out')]
    for _ in range(11):
        args.extend(['--base-xml', path])
    assert main(args) == 2


def test_skip_does_not_become_confirmed_regression(xml, tmp_path):
    args = ['compare', '--base-xml', xml('skip.xml', 'skipped'),
            '--head-xml', xml('fail.xml', 'failed'),
            '--output', str(tmp_path / 'out')]
    assert main(args + ['--fail-on', 'unstable']) == 0
    result = json.loads((tmp_path / 'out' / 'result.json').read_text())
    assert result['counts']['other'] == 1
