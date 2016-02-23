#!/usr/bin/env python
# -*- coding: utf-8 -*-
from Skype4Py.errors import SkypeError
import sys


def main():
    def usage():
        '''Print usage and exit '''
        sys.stderr.write('USAGE: %s < -server | -client > <directory> [username]\n')
        sys.stderr.flush()
        sys.exit()

    # ARG parsing
    if len(sys.argv) < 3:
        usage()
    config_server = sys.argv[1] == '-server'
    directory = sys.argv[2]
    if not config_server:
        if len(sys.argv) >= 4:
            username = sys.argv[3]
        else:
            usage()
    # Run
    if config_server:
        import ServerFs.serverFs as serverFs
        skypeFs = serverFs.ServerFs(directory)
    else:
        import ClientFs.clientFs as clientFs
        skypeFs = clientFs.ClientFs(username, directory)
    try:
        skypeFs.run()
    except SkypeError as skypeError:
        print skypeError
    except KeyboardInterrupt:
        pass
    finally:
        skypeFs.close()


if __name__ == '__main__':
    main()
