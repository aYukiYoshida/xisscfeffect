# -*- coding: utf-8 -*-

from typing import List, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib._color_data as mcd
from numpy import ndarray
import seaborn as sns

from ..util.object import ObjectLikeDict

# DEFAULT PARAMETERS
FIGSIZE = ObjectLikeDict(x=16, y=9)
GRIDNUM = ObjectLikeDict(v=1, h=1)
GRIDPOS = ObjectLikeDict(l=0.1, r=0.95, b=0.2, t=0.95)
GRIDSPACE = ObjectLikeDict(w=0.03, h=0.02)
GRIDRATIO = ObjectLikeDict(w=[1], h=[1])
FSIZE = 25.0                       # font size
LABFSIZE = FSIZE*0.8               # font size for label
LEGFSIZE = FSIZE*0.5               # font size for legend
TCKFSIZE = FSIZE                   # font size for ticks
CALIGN = 'center'                  # common alignment
VALIGN = 'center'                  # vertival alignment
HALIGN = 'center'                  # horizontal alignment
LSTYLE = 'solid'                   # line style
LWIDTH = 2.0                       # line width
MARKER = 'o'                       # marker
PLTFMT = ','                       # format for plot with errors
MASIZE = 5.0                       # marker size
DPI = 100                          # resolution of the figure
IGFONT = ObjectLikeDict(family='IPAexGothic')
COLORS = ObjectLikeDict({
    'blue': sns.color_palette('muted').as_hex()[0],
    'orange': sns.color_palette('muted').as_hex()[1],
    'green': sns.color_palette('muted').as_hex()[2],
    'red': sns.color_palette('muted').as_hex()[3],
    'violet': sns.color_palette('muted').as_hex()[4],
    'brown': sns.color_palette('muted').as_hex()[5],
    'pink': sns.color_palette('muted').as_hex()[6],
    'gray': sns.color_palette('muted').as_hex()[7],
    'ocher': sns.color_palette('muted').as_hex()[8],
    'cyan': sns.color_palette('muted').as_hex()[9],
    'white': mcd.CSS4_COLORS['white'],
    'black': mcd.CSS4_COLORS['black'],
    'yellow': mcd.CSS4_COLORS['gold'],
    'peach': sns.color_palette("husl", 8).as_hex()[0],
    'emerald': sns.color_palette("husl", 8).as_hex()[4],
    'turquoise': sns.color_palette("husl", 8).as_hex()[5],
    'purple': sns.color_palette("husl", 8).as_hex()[6],
    'magenta': sns.color_palette("husl", 8).as_hex()[7],
})


def configure_figure(figsize: Tuple[int, int] = (FIGSIZE.x, FIGSIZE.y),
                     nrows: int = GRIDNUM.v, ncols: int = GRIDNUM.h,
                     left: float = GRIDPOS.l, right: float = GRIDPOS.r,
                     top: float = GRIDPOS.t, bottom: float = GRIDPOS.b,
                     wspace: float = GRIDSPACE.w, hspace: float = GRIDSPACE.h,
                     sharex: bool = True, sharey: bool = True,
                     width_ratios: List = GRIDRATIO.w,
                     height_ratios: List = GRIDRATIO.h) -> (mpl.figure.Figure, Union[ndarray, mpl.axes.Subplot]):
    if sharex:
        sharex = 'col'
    if sharey:
        sharey = 'row'
    if nrows > GRIDNUM.v and height_ratios == GRIDRATIO.h:
        height_ratios = GRIDRATIO.h * nrows
    if ncols > GRIDNUM.v and width_ratios == GRIDRATIO.w:
        width_ratios = GRIDRATIO.w * ncols

    fig, ax = plt.subplots(
        nrows=nrows, ncols=ncols,
        sharex=sharex, sharey=sharey,
        figsize=figsize, dpi=DPI,
        gridspec_kw={'height_ratios': height_ratios, 'width_ratios': width_ratios})
    fig.subplots_adjust(
        left=left, right=right, bottom=bottom, top=top,
        wspace=wspace, hspace=hspace)
    # grd = fig.add_gridspec(grid_num_v,grid_num_h)
    return fig, ax


class SimplePlot(object):
    def __init__(self, configure: bool = True, **args) -> None:
        self.figsize: Tuple[int, int] = args.get(
            'figsize', (FIGSIZE.x, FIGSIZE.y))
        self.nrows: int = args.get('nrows', GRIDNUM.v)
        self.ncols: int = args.get('ncols', GRIDNUM.h)
        self.left: float = args.get('left', GRIDPOS.l)
        self.right: float = args.get('right', GRIDPOS.r)
        self.top: float = args.get('top', GRIDPOS.t)
        self.bottom: float = args.get('bottom', GRIDPOS.b)
        self.wspace: float = args.get('wspace', GRIDSPACE['w'])
        self.hspace: float = args.get('hspace', GRIDSPACE.h)
        self.fsize: float = args.get('fsize', FSIZE)
        self.labfsize: float = args.get('labfsize', LABFSIZE)
        self.legfsize: float = args.get('legfsize', LEGFSIZE)
        self.tckfsize: float = args.get('tckfsize', TCKFSIZE)
        self.calign: str = args.get('calign', CALIGN)
        self.valign: str = args.get('valign', VALIGN)
        self.halign: str = args.get('halign', HALIGN)
        self.lstyle: str = args.get('lstyle', LSTYLE)
        self.lwidth: float = args.get('lwidth', LWIDTH)
        self.marker: str = args.get('marker', MARKER)
        self.pltfmt: str = args.get('pltfmt', PLTFMT)
        self.masize: float = args.get('masize', MASIZE)
        self.igfont: ObjectLikeDict = args.get('igfont', IGFONT)
        self.colors: ObjectLikeDict = args.get('colors', COLORS)
        self.sharex: bool = args.get('sharex', True)
        self.sharey: bool = args.get('sharey', True)
        self.width_ratios: List = args.get('width_ratios', GRIDRATIO.w)
        self.height_ratios: List = args.get('height_ratios', GRIDRATIO.h)
        if configure:
            self.configure()

    def configure(self) -> None:
        self.set_rcparams()
        self.fig, self.axes = configure_figure(
            figsize=self.figsize,
            nrows=self.nrows, ncols=self.ncols,
            left=self.left, right=self.right,
            top=self.top, bottom=self.bottom,
            wspace=self.wspace, hspace=self.hspace,
            sharex=self.sharex, sharey=self.sharey,
            width_ratios=self.width_ratios,
            height_ratios=self.height_ratios)

    def set_rcparams(self) -> None:
        plt.rcParams['font.family'] = 'Times New Roman'
        plt.rcParams['mathtext.fontset'] = 'cm'
        plt.rcParams['mathtext.rm'] = 'serif'
        plt.rcParams['axes.titleweight'] = 'bold'
        # plt.rcParams['axes.labelweight'] = 'bold'
        plt.rcParams['axes.linewidth'] = self.lwidth
        plt.rcParams['grid.linestyle'] = 'solid'
        plt.rcParams['grid.linewidth'] = 1.0
        plt.rcParams['grid.alpha'] = 0.2
        plt.rcParams['xtick.major.size'] = 8
        plt.rcParams['xtick.minor.size'] = 5
        plt.rcParams['xtick.major.width'] = self.lwidth
        plt.rcParams['xtick.minor.width'] = self.lwidth
        plt.rcParams['xtick.major.pad'] = 5
        plt.rcParams['ytick.major.size'] = 8
        plt.rcParams['xtick.top'] = True
        plt.rcParams['ytick.minor.size'] = 5
        plt.rcParams['ytick.major.width'] = self.lwidth
        plt.rcParams['ytick.minor.width'] = self.lwidth
        plt.rcParams['ytick.major.pad'] = 5
        plt.rcParams['xtick.direction'] = 'in'
        plt.rcParams['ytick.direction'] = 'in'
        plt.rcParams['xtick.labelsize'] = self.labfsize
        plt.rcParams['ytick.labelsize'] = self.labfsize
        plt.rcParams['ytick.right'] = True

    def get(self, name):
        return self.__dict__.get(name)

    def set(self, name, value):
        self.__dict__[name] = value
        return self.get(name)
