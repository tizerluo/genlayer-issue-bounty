"""部署安全边界：链检查先于读取密钥，零余额时不解密。"""
from pathlib import Path
import sys
import pytest

# 脚本直接执行与测试导入共享同一模块。
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import network_common
import deploy_bradbury
import demo_flow

def test_wrong_chain_stops_before_key_read(monkeypatch):
    monkeypatch.setattr(network_common,'rpc',lambda method,params:'0x1')
    with pytest.raises(RuntimeError,match='non-Bradbury'):
        network_common.preflight()

def test_zero_balance_never_decrypts(monkeypatch,tmp_path):
    monkeypatch.setattr(sys,'argv',['deploy_bradbury.py','--preflight'])
    monkeypatch.setattr(deploy_bradbury,'preflight',lambda:('0x'+'1'*40,0))
    monkeypatch.setattr(deploy_bradbury,'load_manifest',lambda:{})
    saved=[]
    monkeypatch.setattr(deploy_bradbury,'save_manifest',saved.append)
    monkeypatch.setattr(deploy_bradbury,'client_with_signer',lambda:pytest.fail('Must not decrypt/sign'))
    assert deploy_bradbury.main() == 2
    assert saved[0]['address'] is None and saved[0]['status']=='blocked'

@pytest.mark.parametrize('reward',['0','-1','1000000000000001'])
def test_demo_amount_cap_before_rpc(monkeypatch,reward):
    monkeypatch.setattr(sys,'argv',['demo_flow.py','--fees-file','unused.json','--reward-wei',reward])
    monkeypatch.setattr(demo_flow,'preflight',lambda:pytest.fail('Must not query/sign'))
    with pytest.raises(RuntimeError,match='at most'):
        demo_flow.main()
