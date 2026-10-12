"""M0：支付参数、数组解码及 strict_eq 重放实验。"""
def test_probe(direct_vm, direct_deploy, replay_validator):
    direct_vm.check_pickling = True
    direct_vm.strict_mocks = True
    c = direct_deploy('experiments/sdk_probe.py')
    direct_vm.value = 123
    assert c.capture(['first', 'second']) == 123
    direct_vm.value = 0
    direct_vm.mock_web(r'https://example.com/probe', {'status': 200, 'body': 'abc'})
    assert 'body_size' in c.fetch()
    assert replay_validator() is True
    direct_vm.clear_mocks()
    direct_vm.mock_web(r'https://example.com/probe', {'status': 404, 'body': 'abc'})
    assert replay_validator() is False
