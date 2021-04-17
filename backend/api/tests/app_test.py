
def test_pid_endpoint(api_client):
    res = api_client.get('/api/pid')
    res_json = res.get_json()
    pid = res_json['data']['pid']
    assert pid == "test_pid"
