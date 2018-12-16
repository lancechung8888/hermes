#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2018/11/6
# @Author : lei.X
from  settings import BASE_DIR
import os


def map_dict(d, func, pkeys=[], atom_op=None):
    '''
    >>> map_dict(dict(a=1, b=dict(x=1)), lambda k, v, pkeys: (k + 'x', v))
    {'ax': 1, 'bx': {'xx': 1}}
    >>> map_dict([dict(a=1, b=dict(x=1))], lambda k, v, pkeys: (k + 'x', v))
    [{'ax': 1, 'bx': {'xx': 1}}]
    >>> map_dict(dict(a=1, b=dict(x=1)), lambda k, v, pkeys: None)
    {}
    >>> map_dict(dict(a=[1, 2]), lambda k, v, pkeys: (k, v), atom_op=lambda v, pkeys: v + 1)
    {'a': [2, 3]}
    '''
    if isinstance(d, (list, tuple)):
        return type(d)([map_dict(x, func, pkeys, atom_op=atom_op) for x in d])
    elif isinstance(d, dict):
        nd = {}
        for k, v in d.iteritems():
            nv = map_dict(v, func, pkeys + [k], atom_op=atom_op)
            res = func(k, nv, pkeys)
            if res is not None:
                nk, nv = func(k, nv, pkeys)
                nd[nk] = nv
        return nd
    else:
        return atom_op(d, pkeys) if atom_op else d


def get_upload_path(sub_dir=None):
    the_upload_path = None
    try:
        from settings import upload_path
        if upload_path:
            the_upload_path = upload_path
    except:
        pass
    if not the_upload_path:
        the_upload_path = BASE_DIR + '/upload/'
    if not sub_dir:
        return the_upload_path
    if str(sub_dir).startswith('/'):
        sub_dir = sub_dir[1:]
    return os.path.abspath(the_upload_path) + '/' + sub_dir
