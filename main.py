#!/usr/bin/env python
#coding=utf-8
# date: 2021/05/25
import traceback
from file_libs.views import app
from file_libs.pub import *

cfg = get_conf()

if __name__ == "__main__":
    if __name__ == '__main__':
        try:
            applogger = app.logger
            app.logger.addHandler(log())
            app.run(
                debug=cfg["debug"],
                host=cfg["host"],
                port=cfg["port"],

            )
        except KeyboardInterrupt, e:
            pass
        except Exception, e:
            print traceback.format_exc()