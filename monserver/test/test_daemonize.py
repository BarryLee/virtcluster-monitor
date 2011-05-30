import sys
import time

from monserver.includes.daemonize import startstop

def on_exit(exit_msg):
    sys.stdout.write('%s\n' % exit_msg)


def main():
    sys.stdout.write ('Message to stdout...')
    sys.stderr.write ('Message to stderr...')
    c = 0
    while 1:
        sys.stdout.write ('%d: %s\n' % (c, time.ctime(time.time())) )
        sys.stdout.flush()
        c = c + 1
        time.sleep(1)

if __name__ == '__main__':
    startstop(stdout='/tmp/test_daemonize.log',
              pidfile='/tmp/test_daemonize.pid',
              on_exit=on_exit,
              on_exit_args=('Going down!',))
    main()

