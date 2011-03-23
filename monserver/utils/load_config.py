# -*- coding: utf-8 -*-

import os.path

from utils import parent_dir

DEFAULT_CONFIG_FILE = parent_dir(__file__) + os.path.sep + 'serverrc'


def load_config(confpath):
    exec(compile(open(confpath).read(), confpath, 'exec'))
    return locals()


def load_global_config():
    return load_config(DEFAULT_CONFIG_FILE)


if __name__ == '__main__':
    print load_config()
