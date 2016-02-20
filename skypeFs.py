#!/usr/bin/env python
import ServerFs.serverFs as serverFs
import ClientFs.clientFs as clientFs
import Skype4Py
import sys


if __name__ == '__main__':
    try:
        if len(sys.argv) >= 2:
            if sys.argv[1] == '-server':
                server = serverFs.ServerFs()
            elif sys.argv[1] == '-client':
                client = clientFs.ClientFs('live:yves2608')
    except Skype4Py.errors.SkypeError as e:
        print e


