# -*- coding: utf-8 -*-

import os

from .object import ObjectLikeDict
from .error import InvalidInputError


def get_file_prefix(name: str) -> str:
    return os.path.splitext(os.path.basename(name))[0]
