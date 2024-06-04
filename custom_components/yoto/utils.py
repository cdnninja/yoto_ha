"""utils.py"""


def rgetattr(obj, attr):
    _this_func = rgetattr
    sp = attr.split(".", 1)
    if len(sp) == 1:
        l, r = sp[0], ""
    else:
        l, r = sp

    obj = getattr(obj, l)
    if r:
        obj = _this_func(obj, r)
    return obj
