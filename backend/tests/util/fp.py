from util import fp

def test_first():
    assert fp.first(None) == None
    assert fp.first(None, 1) == 1
    
