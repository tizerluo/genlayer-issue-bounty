"""Closing references link merged PRs to issues before diff-only judging."""
import importlib

import pytest

from tests.helpers import pr, verdict


@pytest.mark.parametrize('source', ['commit_message', 'title', 'body'])
@pytest.mark.parametrize('message', [
    'Implement addition\n\nFixes #12\n\nDocument usage',
    'Implement addition (Fixes #12) and document usage',
    'Documentation: cLoSeD: OwNeR/PrOjEcT#12 with usage examples',
    'Resolves: https://github.com/owner/project/issues/12.',
    'This fix RESOLVED HTTPS://GITHUB.COM/OWNER/PROJECT/issues/12!',
    'Fixes #13, #12',
    'Fixes other/project#12, https://github.com/owner/project/issues/12',
])
def test_each_linking_source_reaches_judging(ready, direct_vm, source, message):
    changes = {'commit_message': 'Merge pull request #34 from alice/addition',
               'title': 'Implement addition', 'body': None}
    changes[source] = message
    pr(direct_vm, **changes)
    verdict(direct_vm)
    ready.submit_claim(0, 34)
    claim = ready.get_claim(0)
    assert claim['status'] == 'ACCEPTED' and claim['reason'] == 'OK'
    assert claim['criteria_met'] == [True, True] and claim['score'] == 9


@pytest.mark.parametrize('keyword', [
    'Fixes', 'Fixed', 'Fix', 'Closes', 'Closed', 'Close', 'Resolves', 'Resolved', 'Resolve',
])
@pytest.mark.parametrize('reference', [
    '#1', 'OwNeR/PrOjEcT#1', 'https://github.com/OWNER/PROJECT/issues/1',
])
def test_closing_keywords_and_reference_formats(escrow, keyword, reference):
    module = importlib.import_module('_contract_issue_bounty_escrow')
    for separator in (' ', ': ', ':'):
        message = f'An inline change {keyword.swapcase()}{separator}{reference} adds coverage.'
        assert module._references_issue(message, 'OWNER/PROJECT', 1)


@pytest.mark.parametrize('message', [
    'Fixes #2, #1',
    '* Fixes owner/project#2, OWNER/PROJECT#1.\r\n',
    'Fixes https://github.com/owner/project/issues/2, #1',
    'Fixes #2, https://github.com/owner/project/issues/1',
])
def test_comma_list_finds_exact_issue(escrow, message):
    module = importlib.import_module('_contract_issue_bounty_escrow')
    assert module._references_issue(message, 'owner/project', 1)


@pytest.mark.parametrize('message', [
    'Fixes #2', 'Fixes #12', 'Fixes #21', 'Fixes #11',
    'Fixes #1suffix', 'Fixes #1_2', 'Fixes #1/2',
    'Fixes other/project#1', 'Fixes owner/other#1',
    'Fixes https://github.com/other/project/issues/1',
    'Fixes https://github.com/owner/other/issues/1',
    'Fixes https://github.com/owner/project/issues/12',
    'Fixes https://github.com/owner/project/issues/21',
    'Fixes https://github.com/owner/project/issues/1suffix',
    'Fixes https://github.com/owner/project/issues/1/2',
    'Fixes https://github.com.evil/owner/project/issues/1',
    'prefixes #1', 'unresolved #1', 'fixess #1',
    '#1', 'owner/project#1', 'https://github.com/owner/project/issues/1',
    'Mentions #1 in passing', 'Fixes #2, other/project#1', '',
])
def test_reference_boundaries_and_wrong_targets(escrow, message):
    module = importlib.import_module('_contract_issue_bounty_escrow')
    assert not module._references_issue(message, 'owner/project', 1)


def test_issue_url_with_repo_named_issues(escrow):
    module = importlib.import_module('_contract_issue_bounty_escrow')
    assert module._references_issue('Fixes https://github.com/owner/issues/issues/1',
                                    'owner/issues', 1)


def test_null_body_without_reference_does_not_reach_judging(ready, direct_vm):
    pr(direct_vm, commit_message='Merge pull request #34 from alice/addition\n\nAdd addition',
       title='Add addition', body=None, events=[{'event': 'closed', 'commit_id': None}])
    ready.submit_claim(0, 34)
    claim = ready.get_claim(0)
    assert claim['reason'] == 'NO_ISSUE_REFERENCE'
    assert claim['criteria_met'] == [] and claim['score'] == 0


def test_default_merge_with_body_only_reference_is_judged(ready, direct_vm, monkeypatch):
    module = importlib.import_module('_contract_issue_bounty_escrow')
    pr(direct_vm, commit_message='Merge pull request #34 from alice/addition\n\nAdd addition',
       title='Add addition', body='This implements addition. Fixes #12. BODY_ONLY_MARKER')
    verdict(direct_vm, met=(False, True), score=8)
    original = module.gl.nondet.exec_prompt
    prompts = []

    def judge(prompt, **kwargs):
        prompts.append(prompt)
        assert 'BODY_ONLY_MARKER' not in prompt
        return original(prompt, **kwargs)

    monkeypatch.setattr(module.gl.nondet, 'exec_prompt', judge)
    ready.submit_claim(0, 34)
    claim = ready.get_claim(0)
    assert prompts
    assert claim['status'] == 'REJECTED' and claim['reason'] == 'CRITERIA_NOT_MET'
    assert claim['criteria_met'] == [False, True] and claim['score'] == 8
    assert ready.get_bounty(0)['status'] == 'OPEN'
    assert ready.get_claim_count(0, direct_vm.sender) == 1
    assert ready.get_credit(direct_vm.sender) == 0
