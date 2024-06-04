"""utils.py"""


def rgetattr(obj, attr):
    _this_func = rgetattr
    sp = attr.split(".", 1)
    if len(sp) == 1:
        left, right = sp[0], ""
    else:
        left, right = sp

    obj = getattr(obj, left)
    if right:
        obj = _this_func(obj, right)
    return obj
