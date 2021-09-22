import sys
from main import (
    chunk,
    hex_addr_to_str,
    parse_routes,
    eitherify,
)


def test_chunk():
    test_input = "1122334455"
    assert chunk(test_input, 2) == ['11', '22', '33', '44', '55']
    test_input = "11223"
    assert chunk(test_input, 2) == ['11', '22', '3']

    
def test_hex_addr_to_str():
    test_input = "010011AC"
    assert hex_addr_to_str(test_input) == "172.17.0.1"

    
def test_parse_routes():
    test_input = """
Iface	Destination	Gateway 	Flags	RefCnt	Use	Metric	Mask		MTU	Window	IRTT                                                       
eth0	00000000	010011AC	0003	0	0	0	00000000	0	0	0                                                                               
eth0	000011AC	00000000	0001	0	0	0	0000FFFF	0	0	0                                                                               

""".strip()

    parsed = parse_routes(test_input)
    assert len(parsed) == 2
    assert {
        "interface": "eth0",
        "destination": "00000000",
        "gateway": "010011AC",
        "flags": "0003",
        "mask": "00000000"
    } in parsed

    
def test_eitherify():
    @eitherify
    def add(a,b):
        return (None, a+b)

    @eitherify
    def div(a,b):
        if(b == 0):
            return ("error_zero_div", None)
        return (None, a/b)

    @eitherify
    def fail(_):
        return "fail_error", None
    
    @eitherify
    def fail_b(_):
        return "fail_error_b", None
    
    err, res = add(2,div(4,2))
    assert err == None
    assert res == 2+(4/2)

    err, res = div(2,add(4,2))
    assert err == None
    assert res == 2/(4+2)

    err, res = add(2,add(2,(add(2,2))))
    assert err == None
    assert res == 2+2+2+2

    err, res = add(2, div(2, 0))
    assert err == "error_zero_div"
    assert res == None

    err, res = add(1,add(2,add(3,div(4,0))))
    assert err == "error_zero_div"
    assert res == None

    err, res = fail(fail_b(None))
    assert err == "fail_error_b"

    err, res = fail(fail_b(add(1,2)))
    assert err == "fail_error_b"

def run_tests(*tests):
    def run_test(test_fn):
        sys.stdout.write(f"running test {test_fn.__name__}...")
        test_fn()
        sys.stdout.write(u"\u001b[32m PASS\u001b[0m \U0001f60A")
        sys.stdout.write("\n")

    for test in tests:
        run_test(test)
    
run_tests(
    test_chunk,
    test_hex_addr_to_str,
    test_parse_routes,
    test_eitherify
)
