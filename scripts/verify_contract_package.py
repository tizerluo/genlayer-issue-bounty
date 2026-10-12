"""Execute the ZIP locally in a pinned GenVM; no RPC, keys, or chain writes."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import threading

from genlayer_py.abi import calldata
from genlayer_py.abi.calldata.encoder import CalldataAddress

if __package__:
    from .build_contract_package import OUTPUT, ROOT, SOURCE, build_package
else:
    from build_contract_package import OUTPUT, ROOT, SOURCE, build_package


def execute_package(runtime_root: Path, code: bytes, invocation: dict, initializing: bool) -> dict:
    """Use a zero-filled local host; return the executor's actual receipt."""
    with tempfile.TemporaryDirectory(prefix='issue-bounty-vm-') as temporary:
        temporary = Path(temporary)
        config = {
            'modules': {'llm': {'address': 'ws://127.0.0.1:3031'},
                        'web': {'address': 'ws://127.0.0.1:3032'}},
            'threads': 2, 'blocking_threads': 4, 'log_disable': 'genvm::rt::memlimiter',
            'log_level': 'warn', 'cache_dir': str(runtime_root / 'cache'),
            'runners_dir': str(runtime_root / 'runners'),
            'registry_dir': str(runtime_root / 'executor/v0.2.12/data'),
        }
        config_path = temporary / 'config.json'
        config_path.write_text(json.dumps(config))
        socket_path = temporary / 'host.sock'
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(socket_path))
        listener.listen()
        listener.settimeout(30)
        results = []
        errors = []

        def serve():
            try:
                connection, _ = listener.accept()
                connection.settimeout(30)
                with connection:
                    def read(size):
                        data = bytearray()
                        while len(data) < size:
                            chunk = connection.recv(size - len(data))
                            if not chunk:
                                raise EOFError('Executor closed its local host connection')
                            data.extend(chunk)
                        return bytes(data)

                    def integer(size=4):
                        return int.from_bytes(read(size), 'little')

                    while True:
                        operation = integer(1)
                        if operation == 1:  # STORAGE_READ
                            read(1 + 20 + 32)
                            integer()
                            size = integer()
                            connection.sendall(b'\0' + bytes(size))
                        elif operation == 3:  # CONSUME_RESULT
                            results.append(read(integer()))
                            connection.sendall(b'\0')
                            break
                        elif operation == 4:  # GET_LEADER_NONDET_RESULT: local leader
                            integer()
                            connection.sendall(b'\x03')
                        elif operation == 5:  # POST_NONDET_RESULT: local receipt only
                            integer()
                            read(integer())
                            connection.sendall(b'\0')
                        elif operation == 8:  # CONSUME_FUEL
                            integer(8)
                        elif operation == 12:  # GET_BALANCE
                            read(20)
                            connection.sendall(b'\0' + bytes(32))
                        else:
                            raise RuntimeError(f'Unexpected host operation {operation}')
            except Exception as error:
                errors.append(type(error).__name__)
            finally:
                listener.close()

        worker = threading.Thread(target=serve, daemon=True)
        worker.start()
        message = {
            'contract_address': CalldataAddress('0x' + '3' * 40),
            'sender_address': CalldataAddress('0x' + '4' * 40),
            'origin_address': CalldataAddress('0x' + '4' * 40),
            'chain_id': '4221', 'value': 0, 'is_init': initializing,
            'datetime': '2026-10-12T00:00:00Z',
        }
        execution = {
            'message': message, 'host_data': '{"node_address":"0x","tx_id":"0x"}',
            'calldata': list(calldata.encode(invocation)), 'code': list(code),
        }
        # The release binary uses musl; invoking its shipped loader works on glibc hosts.
        command = [str(runtime_root / 'lib/libc.so'),
                   str(runtime_root / 'executor/v0.2.12/bin/genvm'),
                   '--config', str(config_path), 'run', '--host', 'unix://' + str(socket_path),
                   '--storage-pages', '1000', '--print', 'result']
        reply = subprocess.run(command, input=calldata.encode(execution), capture_output=True, timeout=55)
        if reply.returncode or errors or not results:
            raise RuntimeError('Local GenVM execution failed; inspect the pinned runtime setup')
        worker.join(timeout=1)
        if results[0][0] != 0:
            raise RuntimeError('Local GenVM returned a failed receipt')
        receipt = calldata.decode(results[0][1:])
        if receipt['kind'] != 'Return':
            raise RuntimeError('Local GenVM returned a non-success result')
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--genvm-root', type=Path, required=True,
                        help='Extracted v0.2.12 support, executor, and pinned runners')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/package-runtime-validation.json')
    args = parser.parse_args()
    runtime_root = args.genvm_root.resolve()
    package = OUTPUT.read_bytes()
    if package != build_package():
        raise RuntimeError('Rebuild the package from the current readable source')
    constructor = execute_package(runtime_root, package, {'args': [259200, 3]}, True)
    assert constructor['data'] is None
    schema = execute_package(runtime_root, package, {'method': '#get-schema'}, False)
    assert json.loads(schema['data']) == json.loads((ROOT / 'artifacts/abi.json').read_text())

    # Exercise the same loader in real nondeterministic and sandbox child VMs.
    # This temporary probe method is not part of the shipped contract or its ABI.
    with tempfile.TemporaryDirectory(prefix='issue-bounty-callback-') as temporary:
        probe_path = Path(temporary) / 'probe.py'
        probe_path.write_bytes(SOURCE.read_bytes() + b'''
    @gl.public.view
    def verify_package_callbacks(self) -> dict:
        def rerun():
            return _normalize_verdict({"criteria":[{"id":1,"met":True}],"score":7}, 1)
        leader = gl.vm.run_nondet_unsafe(rerun, lambda result: True)
        sandbox = gl.vm.spawn_sandbox(rerun).calldata
        return {"leader":leader, "sandbox":sandbox}
''')
        callback = execute_package(runtime_root, build_package(probe_path),
                                   {'method': 'verify_package_callbacks'}, False)['data']
        expected = {'criteria_met': [True], 'score': 7, 'summary': ''}
        assert callback == {'leader': expected, 'sandbox': expected}
    evidence = {
        'runtime': 'GenVM v0.2.12 / pinned CPython Wasm',
        'package_sha256': hashlib.sha256(package).hexdigest(),
        'constructor': 'RETURN null', 'sdk_schema_matches_abi': True,
        'nondeterministic_child_loader': 'passed', 'sandbox_child_loader': 'passed',
        'abi_methods': len(json.loads(schema['data'])['methods']),
        'scope': 'local executor with an in-memory host; no live provider or Bradbury execution',
        'transactions_sent': 0,
    }
    args.output.write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
