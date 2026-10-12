"""公开 GitHub 样本的最小字段和完整 URL mock。"""
import json
import re

NOW = 1791763200
REPO = 'owner/project'
USER_URL = 'https://api.github.com/users/alice'
GISTS_URL = USER_URL + '/gists?per_page=100'
ISSUE_URL = f'https://api.github.com/repos/{REPO}/issues/12'
PR_URL = f'https://api.github.com/repos/{REPO}/pulls/34'
DIFF_URL = f'https://patch-diff.githubusercontent.com/raw/{REPO}/pull/34.diff'
DIFF = 'diff --git a/example.py b/example.py\n+def add(a, b):\n+    return a + b\n'

def web(vm, url, obj, status=200):
    body = obj if isinstance(obj, str) else json.dumps(obj)
    vm.mock_web('^'+re.escape(url)+'$', {'status': status, 'body': body})

def bind(vm, c, github_id=42, login='alice', proof=None):
    url = f'https://api.github.com/users/{login.lower()}'
    web(vm, url, {'id': github_id, 'login': login})
    web(vm, url+'/gists?per_page=100', [{'description': proof or 'genlayer-bounty-bind:'+vm.sender.as_hex.lower()}])
    c.bind_github(login)

def create(vm, c, value=0, **changes):
    vm.value = value
    web(vm, ISSUE_URL, {'state': 'open', 'title': 'Addition', 'body': 'Implement addition.'})
    args = {'repo': REPO, 'issue_number': 12, 'criteria': ['Implement addition', 'Document addition'], 'deadline': NOW+7200, 'min_score': 7}
    args.update(changes)
    try:
        return c.create_bounty(**args)
    finally:
        vm.value = 0

def pr(vm, **changes):
    obj = {'merged': True, 'merged_at': '2026-10-12T01:00:00Z', 'user': {'id': 42},
           'base': {'repo': {'full_name': REPO}}, 'title': 'Add addition', 'body': 'Fixes #12'}
    obj.update(changes)
    web(vm, PR_URL, obj)
    if obj.get('merged'):
        web(vm, DIFF_URL, DIFF)

def verdict(vm, met=(True, True), score=9, summary='Implemented'):
    vm.mock_llm('BOUNTY_JUDGE_V1', json.dumps({'criteria': [{'id': i+1, 'met': m} for i,m in enumerate(met)], 'score': score, 'summary': summary}))
