/** Encode a Bradbury deployment and estimate it; this tool cannot sign or send. */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const sourcePath = resolve(process.argv[2] || 'artifacts/issue_bounty_escrow.zip');
const sdkRoot = process.argv[3] || '/home/box/genlayer-testnet';
const requireSdk = createRequire(resolve(sdkRoot, 'package.json'));
const { abi, chains } = await import(pathToFileURL(requireSdk.resolve('genlayer-js')));
const { encodeFunctionData, zeroAddress } = await import(pathToFileURL(requireSdk.resolve('viem')));
const chain = chains.testnetBradbury;
const rpcUrl = 'https://rpc-bradbury.genlayer.com';
const sender = '0x8f374a83965b2143bea962a48c8dacaf0db62d16';

function rpc(method, params) {
  if (!['eth_chainId', 'eth_estimateGas'].includes(method)) throw new Error('Read-only RPC required');
  const response = spawnSync('curl', ['--max-time', '30', '-fsSL', '-X', 'POST', rpcUrl,
    '-H', 'Content-Type: application/json', '--data-binary', '@-'], {
    input: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }), encoding: 'utf8',
  });
  if (response.status !== 0) throw new Error('Bradbury HTTP transport failed');
  const reply = JSON.parse(response.stdout);
  if (reply.error) throw new Error(`Bradbury ${method}: ${JSON.stringify(reply.error)}`);
  return reply.result;
}

if (Number(BigInt(rpc('eth_chainId', []))) !== 4221) throw new Error('Bradbury chain required');
const source = readFileSync(sourcePath);
const constructorArgs = [259200, 3, sender];
const payload = abi.transactions.serialize([
  source, abi.calldata.encode(abi.calldata.makeCalldataObject(undefined, constructorArgs)), false,
]);
const transactionData = encodeFunctionData({
  abi: chain.consensusMainContract.abi, functionName: 'addTransaction',
  args: [sender, zeroAddress, chain.defaultNumberOfInitialValidators,
    chain.defaultConsensusMaxRotations, payload, BigInt(Math.floor(Date.now() / 1000) + 3600)],
});
const gas = Number(BigInt(rpc('eth_estimateGas', [{
  from: sender, to: chain.consensusMainContract.address, data: transactionData, value: '0x0',
}])));
console.log(JSON.stringify({
  code_path: sourcePath, code_bytes: source.length,
  code_sha256: createHash('sha256').update(source).digest('hex'),
  chain_id: 4221, rpc: rpcUrl, method: 'eth_estimateGas',
  consensus: chain.consensusMainContract.address, constructor_args: constructorArgs,
  initial_validators: chain.defaultNumberOfInitialValidators,
  max_rotations: chain.defaultConsensusMaxRotations,
  transaction_data_bytes: (transactionData.length - 2) / 2, gas_estimate: gas,
  target_gas: 15500000, meets_target: gas < 15500000,
  checked_at: new Date().toISOString(), transactions_sent: 0,
}, null, 2));
if (gas >= 15500000) process.exitCode = 1;
