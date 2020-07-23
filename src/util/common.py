# -*- coding: utf-8 -*-

import os
import sys
import inspect
from typing import Union, List, Dict, Tuple


# -----------------------------------------------------------------------
# GLOBAL VARIABLES
# -----------------------------------------------------------------------
ROOT_DIR = './'
PKG_DIR = os.path.join(ROOT_DIR, 'src')
OUT_DIR = os.path.join(ROOT_DIR, 'out')
DAT_DIR = os.path.join(ROOT_DIR, 'data')


# -----------------------------------------------------------------------
class StringColor(object):
    # -----------------------------------------------------------------------
    BLACK = '\033[30m'  # (文字)黒
    RED = '\033[31m'  # (文字)赤
    GREEN = '\033[32m'  # (文字)緑
    YELLOW = '\033[33m'  # (文字)黄
    BLUE = '\033[34m'  # (文字)青
    MAGENTA = '\033[35m'  # (文字)マゼンタ
    CYAN = '\033[36m'  # (文字)シアン
    WHITE = '\033[37m'  # (文字)白
    COLOR_DEFAULT = '\033[39m'  # 文字色をデフォルトに戻す
    BOLD = '\033[1m'  # 太字
    UNDERLINE = '\033[4m'  # 下線
    INVISIBLE = '\033[08m'  # 不可視
    REVERCE = '\033[07m'  # 文字色と背景色を反転
    BG_BLACK = '\033[40m'  # (背景)黒
    BG_RED = '\033[41m'  # (背景)赤
    BG_GREEN = '\033[42m'  # (背景)緑
    BG_YELLOW = '\033[43m'  # (背景)黄
    BG_BLUE = '\033[44m'  # (背景)青
    BG_MAGENTA = '\033[45m'  # (背景)マゼンタ
    BG_CYAN = '\033[46m'  # (背景)シアン
    BG_WHITE = '\033[47m'  # (背景)白
    BG_DEFAULT = '\033[49m'  # 背景色をデフォルトに戻す
    RESET = '\033[0m'  # 全てリセット


# -----------------------------------------------------------------------
class Log(object):
    # -----------------------------------------------------------------------
    STATUS = {
        0: 'DEBUG',
        1: 'INFO',
        2: 'WARNING',
        3: 'ERROR'}

    STRING_COLORS = {
        0: StringColor.COLOR_DEFAULT,
        1: StringColor.COLOR_DEFAULT,
        2: StringColor.YELLOW,
        3: StringColor.RED}

    # -------------------------------------------------------------------
    def __init__(self, loglv: Union[int, str] = 1) -> None:
        # -------------------------------------------------------------------
        if type(loglv) is str:
            try:
                loglv = list(self.STATUS.values()).index(loglv.upper())
            except ValueError:
                raise ValueError(
                    f'loglv should be set to an integer between 0 and 3 or a one of '+', '.join(self.STATUS.values())+'.')
        self.loglv: int = loglv

    # -------------------------------------------------------------------
    def logger(self, string: str, level: int, frame=None) -> None:
        # -------------------------------------------------------------------
        if not frame == None:
            function_name = inspect.getframeinfo(frame)[2]
            console_msg = f'[{self.STATUS[level]}] {function_name} : {str(string)}'
        else:
            console_msg = f'[{self.STATUS[level]}] {str(string)}'
        if (level >= self.loglv):
            print(
                f'{self.STRING_COLORS[level]}{console_msg}{StringColor.RESET}')

    # -------------------------------------------------------------------
    def debug(self, string: str, frame=None) -> None:
        # -------------------------------------------------------------------
        self.logger(string, 0, frame)

    # -------------------------------------------------------------------
    def info(self, string: str, frame=None) -> None:
        # -------------------------------------------------------------------
        self.logger(string, 1, frame)

    # -------------------------------------------------------------------
    def warning(self, string: str, frame=None) -> None:
        # -------------------------------------------------------------------
        self.logger(string, 2, frame)

    # -------------------------------------------------------------------
    def error(self, string: str, frame=None) -> None:
        # -------------------------------------------------------------------
        self.logger(string, 3, frame)


# -----------------------------------------------------------------------
class Common(Log):
    # -----------------------------------------------------------------------
    # -------------------------------------------------------------------
    def __init__(self, loglv: Union[int, str] = 1) -> None:
        # -------------------------------------------------------------------
        super().__init__(loglv)

    # -------------------------------------------------------------------
    def abort(self, string: str, frame=None) -> None:
        # ------------------------------------------------------------------
        self.error(string, frame)
        sys.exit(1)
