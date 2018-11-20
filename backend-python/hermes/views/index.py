# coding: utf8
import logging
logger = logging.getLogger(__name__)

from django.http import HttpResponse


def hello_world(request):
    # django在使用logger打印时请到日志文件中查看
    print "test"
    logger.info("Hello world called")
    # return HttpResponse("Hello, world!")

def home_view():
    pass

if __name__ == "__main__":
    hello_world("test")
