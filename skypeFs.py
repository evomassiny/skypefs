#!/usr/bin/env python
import ServerFs.serverFs as serverFs
import ClientFs.clientFs as clientFs
import Skype4Py
import sys


def main():
    if len(sys.argv) < 3:
        return

    # ARG parsing
    if sys.argv[1] == '-server':
        skypeFs = serverFs.ServerFs(sys.argv[2])
    elif sys.argv[1] == '-client':
        skypeFs = clientFs.ClientFs('live:yves2608', sys.argv[2])
    try:
        skypeFs.run()
    except Skype4Py.errors.SkypeError as skypeError:
        print skypeError
    except KeyboardInterrupt:
        pass
    finally:
        skypeFs.close()


if __name__ == '__main__':
    main()
