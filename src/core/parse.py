# -*- coding: utf-8 -*-

import os
import re
from typing import List

from ..util.object import ObjectLikeDict
from ..util.error import InvalidInputError


def get_file_prefix(name: str) -> str:
    return os.path.splitext(os.path.basename(name))[0]
