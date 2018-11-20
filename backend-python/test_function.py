#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2018/11/5
# @Author : lei.X

# coding: utf8
import os
import logging
logger = logging.getLogger(__name__)
# logging.basicConfig(
#     level = logging.DEBUG,
#     format = '%(name)s %(levelname)s %(message)s',
#     datefmt='%a, %d %b %Y %H:%M:%S',
#     filename=os.path.dirname(os.path.abspath(__file__))+'/debug.log',
#     filemode='w'
# )


def hello_world():
    # django在使用logger打印时请到日志文件中查看
    print "test"
    logger.info("Hello world called")
    print os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    hello_world()
