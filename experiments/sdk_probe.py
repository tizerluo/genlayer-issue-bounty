# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json

class Probe(gl.Contract):
    items: str
    def __init__(self):
        self.items = "[]"

    @gl.public.write.payable
    def capture(self, criteria: list[str]) -> int:
        self.items = json.dumps(criteria)
        return int(gl.message.value)

    @gl.public.write
    def fetch(self) -> str:
        def leader() -> str:
            r = gl.nondet.web.get('https://example.com/probe', headers={'User-Agent': 'genlayer-issue-bounty-escrow'})
            return json.dumps({'status': r.status, 'body_size': len(r.body)}, sort_keys=True)
        return gl.eq_principle.strict_eq(leader)
