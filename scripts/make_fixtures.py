"""抓取公开证据并脱敏；交易时间、账号和仓库归一化以便离线测试。"""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]

def get(url):
    request=Request(url,headers={'User-Agent':'genlayer-issue-bounty-escrow','Accept':'application/vnd.github+json'})
    with urlopen(request,timeout=20) as response:
        return response.read()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',default='tizerluo/bounty-sandbox')
    parser.add_argument('--login',default='tizerluo')
    parser.add_argument('--issue',type=int,default=1)
    parser.add_argument('--pr',type=int,default=3)
    args=parser.parse_args()
    urls={'user':f'https://api.github.com/users/{args.login}',
          'issue':f'https://api.github.com/repos/{args.repo}/issues/{args.issue}',
          'pr':f'https://api.github.com/repos/{args.repo}/pulls/{args.pr}',
          'diff':f'https://patch-diff.githubusercontent.com/raw/{args.repo}/pull/{args.pr}.diff'}
    user,issue,pr=[json.loads(get(urls[k])) for k in ('user','issue','pr')]
    diff=get(urls['diff'])
    if not pr['merged'] or pr['user']['id']!=user['id']:
        raise SystemExit('Public fixture PR must be merged and authored by specified login')
    folder=ROOT/'tests/fixtures'
    folder.mkdir(parents=True,exist_ok=True)
    def save(name,data):
        (folder/name).write_text(json.dumps(data,indent=2)+'\n')
    save('user_alice.json',{'id':42,'login':'alice'})
    save('gists_alice.json',[{'description':'genlayer-bounty-bind:0x'+'0'*40+':0x'+'0'*40+':0','owner':{'id':42}}])
    save('issue_open.json',{'state':issue['state'],'title':issue['title'],'body':issue.get('body') or ''})
    normalized={'merged':True,'merged_at':'2026-10-12T01:00:00Z','user':{'id':42},
        'merged_by':{'id':99},'merge_commit_sha':'a'*40,
        'base':{'ref':'main','repo':{'full_name':'owner/project','default_branch':'main'}},'title':pr['title'],'body':'Fixes #12'}
    save('pr_merged.json',normalized)
    save('pr_unmerged.json',{**normalized,'merged':False,'merged_at':None})
    (folder/'pr_merged.diff').write_bytes(diff)
    save('provenance.json',{'captured_at':datetime.now(timezone.utc).isoformat(),'source_urls':urls,
          'raw_diff_sha256':hashlib.sha256(diff).hexdigest(),'source_merged_at':pr['merged_at'],
          'normalizations':['user/login/id and repo replaced by alice/42 and owner/project',
          'issue/pr numbers mapped to 12/34','merge time fixed to direct test timestamp',
          'gist marker is synthetic; helpers substitute contract, caller and current nonce',
          'independent merger id 99, default branch main and merge commit SHA a*40 are synthetic security test metadata',
          'merge commit message Fixes #12 is synthetic mocked evidence, not live sandbox eligibility',
          'unmerged variant derived from merged PR; raw public diff preserved']})
    print('Saved sanitized fixtures from public merged PR:',urls['pr'])

if __name__=='__main__':
    main()
