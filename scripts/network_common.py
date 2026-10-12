"""Bradbury 专用工具：仅打印公共信息，私钥只在内存中解密。"""
import json
import stat
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
RPC='https://rpc-bradbury.genlayer.com'
EXPLORER='https://explorer-bradbury.genlayer.com'
KEYSTORE=Path('/home/box/.genlayer/keystores/issue-bounty-deployer.json')
PASSWORD=Path('/home/box/.genlayer/deployer.pass')
MANIFEST=ROOT/'deployments/bradbury.json'

def rpc(method,params):
    # 当前 RPC 拒绝默认 Python requests UA；curl 的公开 RPC 请求已实测通过。
    result=subprocess.run(['curl','--max-time','20','-fsSL','-X','POST',RPC,
         '-H','Content-Type: application/json','--data-binary','@-'],
         input=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}),capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError('Bradbury HTTP transport failed')
    reply=json.loads(result.stdout)
    if 'error' in reply:
        raise RuntimeError('Bradbury RPC request failed')
    return reply['result']

def preflight():
    # 检查链身份先于私钥解密；不读取任何旧钱包环境变量。
    if int(rpc('eth_chainId',[]),16) != 4221:
        raise RuntimeError('Refusing a non-Bradbury chain')
    address='0x'+json.loads(KEYSTORE.read_text())['address'].removeprefix('0x')
    balance=int(rpc('eth_getBalance',[address,'latest']),16)
    return address,balance

def signer():
    from eth_account import Account
    from genlayer_py import create_account
    if stat.S_IMODE(PASSWORD.stat().st_mode) != 0o600:
        raise RuntimeError('Password file must have mode 0600')
    private_key=Account.decrypt(json.loads(KEYSTORE.read_text()),PASSWORD.read_text())
    account=create_account(private_key)
    del private_key
    return account

def client_with_signer():
    from genlayer_py import create_client
    from genlayer_py.chains import testnet_bradbury
    return create_client(chain=testnet_bradbury,endpoint=RPC,account=signer())

def load_manifest():
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}

def save_manifest(data):
    MANIFEST.parent.mkdir(exist_ok=True)
    temporary=MANIFEST.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,indent=2)+'\n')
    temporary.replace(MANIFEST)

def confirmed(client,tx_hash):
    from genlayer_py.transactions import is_successful
    receipt=client.wait_for_transaction_receipt(tx_hash,wait_until='finalized')
    if not is_successful(receipt):
        raise RuntimeError('Transaction did not finalize with successful execution')
    return receipt

def fee_options(path,method):
    data=json.loads(Path(path).read_text())
    chosen=data.get(method,data)
    if not isinstance(chosen,dict) or 'distribution' not in chosen or not any(k in chosen for k in ('feeValue','fee_value')):
        raise RuntimeError('Need a measured SDK fee estimate with distribution and feeValue')
    if method=='withdraw' and not chosen.get('messageAllocations',chosen.get('message_allocations')):
        raise RuntimeError('Withdraw requires measured external message allocations')
    return chosen

def hex_hash(value):
    text=value if isinstance(value,str) else value.hex()
    return text if text.startswith('0x') else '0x'+text

def safe_main(fn):
    # 第三方异常可能携带调用参数；只显示异常类型，避免凭据落入日志。
    try:
        return fn()
    except Exception as exc:
        print('Stopped safely:',type(exc).__name__,'(details suppressed to protect credentials)')
        return 1
