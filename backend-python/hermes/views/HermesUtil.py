#!/usr/bin/env python
# encoding: utf-8
import datetime

from django.core.paginator import Page
from django.core.serializers.json import DjangoJSONEncoder
from django.http.response import JsonResponse
from backend_python.utils import map_dict

import logging

logger = logging.getLogger(__name__)


class ResponseContainer(object):
    def __init__(self, status, message, data):
        self.status = status
        self.message = message
        self.data = data
        self.transform_page()

    def transform_page(self):
        logger.info("dataType: %s" % self.data.__class__)
        if not isinstance(self.data, Page):
            return
        page = self.data
        item_list = []
        for item in page:
            item_list.append(item)
        self.data = Pageable(item_list, page.paginator.count, page.paginator.per_page, page.number)

    @staticmethod
    def success(data):
        return ResponseContainer(0, None, data)

    @staticmethod
    def success_pageable(page):
        if not isinstance(page, Page):
            raise Exception('param must be %s' % Page.__class__)
        return ResponseContainer.success(
            Pageable(page.object_list, page.paginator.count, page.paginator.per_page, page.number))

    @staticmethod
    def failed(message, status=-1):
        return ResponseContainer(status, message, None)

    @staticmethod
    def from_json(json_object):
        return ResponseContainer(json_object['status'], json_object['message'], json_object['data'])


class Pageable(object):
    # 构造一个和java spring data结构相同的分页对象，这样可以复用同一套前端UI
    def __init__(self, content, total, size, num):
        self.content = content
        self.totalElements = total
        self.numberOfElements = len(content)
        self.size = size
        self.num = num
        self.totalPages = None
        self.first = False
        self.last = False
        self.calculate_meta()

    def calculate_meta(self):
        self.totalPages = (self.numberOfElements + self.size - 1) // self.size
        self.first = self.num == 0
        self.last = self.num != self.totalPages


INTEGER_TYPES = (int, long)


def bigint2str(obj, pkeys=None):
    if not isinstance(obj, bool) and isinstance(obj, INTEGER_TYPES):
        if type(obj) not in INTEGER_TYPES:
            # from simplejson, do not trust custom str/repr, see https://github.com/simplejson/simplejson/issues/118
            obj = int(obj)
        if (-1 << 53) < obj < (1 << 53):
            return obj
        return str(obj)
    if isinstance(obj, datetime.datetime):
        return str(obj)
    return obj


def transfer_with_json_function(obj):
    if not hasattr(obj, 'as_json'):
        return None
    json_function = obj.__dict__.get('as_json')
    if json_function is None:
        return None
    if not callable(json_function):
        return None
    return json_function(obj)


def transfer_with_attribute(obj):
    ret = {}
    if isinstance(obj, datetime.datetime):
        return str(obj)
    if not hasattr(obj, '__dict__'):
        return None
    for key, value in obj.__dict__.items():
        if value is None:
            continue
        if callable(value):
            continue
        if str(key).startswith('_'):
            continue
        ret[key] = value
    return ret


class MyJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        try:
            return super(DjangoJSONEncoder, self).default(obj)
        except TypeError:
            ret = transfer_with_json_function(obj)
            if not (ret is None):
                return ret
            return transfer_with_attribute(obj)

    def encode(self, obj):
        obj = map_dict(obj, func=lambda k, v, pkeys: (k, v), atom_op=bigint2str)
        return super(MyJSONEncoder, self).encode(obj)


class ForceDumpJsonResponse(JsonResponse):
    def __init__(self, data, encoder=MyJSONEncoder, safe=False, **kwargs):
        super(ForceDumpJsonResponse, self).__init__(data, encoder, safe, **kwargs)


def to_boolean(param):
    if param is None:
        return False
    if isinstance(param, bool):
        return param
    if isinstance(param, basestring):
        str_param = str(param).lower().strip()
        if len(str_param) == 0:
            return False
        if str_param == 'false':
            return False
        if str_param.isdigit():
            if float(str_param) < 0:
                return False
        return True
    if isinstance(param, int) or isinstance(param, float) or isinstance(param, long):
        return param > 0
    if param:
        return True
    return False
