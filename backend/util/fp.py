def first(*args):
    for arg in args:
        if arg is not None:
            return arg

    return None
