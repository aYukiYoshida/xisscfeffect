# -*- coding: utf-8 -*-

import inspect
import os
import sys
from typing import Dict, List, Tuple, Union

import lmfit as lf
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import ticker

from ..util.common import Common
from ..util.error import InsufficientInputError, InvalidInputError
from ..util.object import ObjectLikeDict
from .model import energy_event_density_curve as scf_curve
from .plot import DPI, SimplePlot
from .parse import get_file_prefix, file_name_parse


class CurveFitParameter(object):
    PROPERTIES = {
        'value': 'float',
        'vary': 'bool[0,1]',
        'min': 'float',
        'max': 'float'}
    MODIFIERS = (float, bool, float, float)

    def __init__(self, name: str, value: float, min: float, max: float, vary: bool = True):
        self.name = name
        self.value = value
        self.vary = vary
        self.min = min
        self.max = max

    def _get_properties(self) -> Tuple:
        return tuple(self.__dict__.keys())[1:]

    def _get_values(self) -> Tuple:
        return tuple(self.__dict__.values())[1:]

    def set_value(self, name: str, value: Union[float, bool]):
        self.__dict__

    @property
    def properties(self) -> Tuple:
        return self._get_properties()

    @property
    def values(self) -> Tuple:
        return self._get_values()

    @property
    def parameters(self) -> Dict:
        return dict(zip(self.properties, self.values))


class CurveFit(Common):
    IMAGE_FILE_TYPE = 'pdf'
    IMAGE_FILE_DPI = DPI
    DUMMY_ENERGY = np.logspace(-5, -1, 100)

    def __init__(self, qdp: str, image_out_flag: bool = False, loglv: int = 1) -> None:
        super().__init__(loglv)
        self.image_out_flag = image_out_flag
        self.file_prefix = get_file_prefix(qdp)
        self.property: ObjectLikeDict = file_name_parse(qdp)
        self.xd, self.xe, self.yd, self.ye = self.read_qdp(qdp)
        self.scf_model = lf.Model(func=scf_curve, independent_vars=['E'])

    def read_qdp(self, qdp: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        self.debug('START', inspect.currentframe())
        self.info(f'READ QDP FILE: {qdp}')
        with open(qdp, 'r') as f:
            skiprows = f.read().splitlines().index('!')+1
        data = np.loadtxt(qdp, dtype=float, delimiter=' ', skiprows=skiprows, unpack=True)
        self.debug('END', inspect.currentframe())
        return (d for d in data)

    def entry_paramter(self) -> List[CurveFitParameter]:
        param_list = list()
        try:
            self.info('Input parameters')
            self.info('Enter the values separated by ","')
            self.info(', '.join(
                [f'{p} ({k})' for p, k in CurveFitParameter.PROPERTIES.items()]))
            for name in self.scf_model.param_names:
                self.info(f'for {name}')
                entry = input()
                values = tuple(
                    modifier(float(v.strip())) for v, modifier in zip(
                        entry.split(','), CurveFitParameter.MODIFIERS))
                params = dict(zip(CurveFitParameter.PROPERTIES.keys(), values))
                param_list.append(CurveFitParameter(name=name, **params))
        except ValueError:
            raise InvalidInputError('Input parameter is invalid')
        except TypeError:
            raise InsufficientInputError('Input parameter is insufficient')
        except InvalidInputError as err:
            self.abort(err)
        except InsufficientInputError as err:
            self.abort(err)
        else:
            return param_list

    def set_paratemeter(self) -> None:
        param_list = self.entry_paramter()
        for param in param_list:
            self.scf_model.set_param_hint(param.name, **param.parameters)
        self.debug(self.scf_model.param_hints)

    def fit(self, initial: str = None) -> None:
        self.debug('START', inspect.currentframe())
        self.set_paratemeter()
        self.result = self.scf_model.fit(
            E=self.xd, data=self.yd, weights=self.ye**(-1), method='leastsq')
        best_parameter = self.result.best_values
        self.debug(self.result.best_values)

        self.info('BEST FIT VALUES')
        for name in self.scf_model.param_names:
            self.info(f'parameter of {name}')
            self.info(
                f'  {self.result.result.params[name].value} +- {self.result.result.params[name].stderr}')

        log_file = f'{self.file_prefix}_result.log'
        with open(log_file, 'w') as log:
            log.write(
                '--------------------------------------------------------------------\n')
            log.write(self.result.fit_report())
            log.write('\n')
            log.write(
                '--------------------------------------------------------------------\n')
            log.write(
                f' Chi-squared value / d.o.f. = {self.result.chisqr} / {self.result.nfree}\n')
            log.write(f' Reduced Chi-squared value  = {self.result.redchi}\n')
            log.write('\n')
        self.info(f'Fitting results were recorded to {log_file}.')
        self.plot()
        self.debug('END', inspect.currentframe())

    def plot(self):
        self.debug('START', inspect.currentframe())
        spl = SimplePlot(configure=True,
                         figsize=(8, 6), nrows=2, height_ratios=[0.7, 0.3], fsize=20,
                         left=0.15, right=0.95, bottom=0.15, top=0.9)

        spl.fig.suptitle(f'{self.property.xis}',
                         x=0.53, y=0.93,
                         fontsize=spl.fsize, va=spl.valign, ha=spl.halign)

        # data & best-fit model
        spl.axes[0].errorbar(x=self.xd, y=self.yd, xerr=self.xe, yerr=self.ye,
                             marker=spl.marker, ms=spl.masize, fmt=spl.pltfmt,
                             color=spl.colors.orange, ecolor=spl.colors.orange,
                             capsize=0.0, elinewidth=spl.lwidth, mec=spl.colors.orange,
                             label=f'{self.property.phase}')
        spl.axes[0].plot(self.DUMMY_ENERGY, scf_curve(E=self.DUMMY_ENERGY, **self.result.best_values),
                         lw=spl.lwidth, ls=':', color=spl.colors.orange)
        spl.axes[0].set_ylabel('Energy (keV)', fontsize=spl.fsize)
        spl.axes[0].legend(fontsize=spl.legfsize, loc='upper left',
                           scatterpoints=1, numpoints=1, markerscale=0.7, handletextpad=0.,
                           fancybox=True, framealpha=0.0, frameon=True)
        spl.axes[0].set_ylim(6.52, 6.7)

        # residual
        spl.axes[1].errorbar(
            x=self.xd, y=self.yd-self.result.best_fit,
            xerr=self.xe, yerr=self.ye,
            marker=spl.marker, ms=spl.masize, fmt=spl.pltfmt,
            color=spl.colors.orange, ecolor=spl.colors.orange,
            capsize=0.0, elinewidth=spl.lwidth, mec=spl.colors.orange)
        spl.axes[1].axhline(y=0.0, color=spl.colors.black,
                            ls=spl.lstyle, lw=spl.lwidth, dashes=[2, 5])
        spl.axes[1].set_ylabel('residual', fontsize=spl.fsize)
        spl.axes[1].set_xlabel(r'Event density $({\rm events}\:{\rm frame}^{-1}\:{\rm pixel}^{-1}$)',
                               fontsize=spl.fsize)
        spl.axes[1].set_ylim(-3.5E-2, 3.5E-2)

        for ax in spl.axes:
            ax.set_xscale('log')
            ax.set_xlim(3E-5, 4E-2)
            ax.yaxis.set_major_locator(ticker.MultipleLocator(0.02))
            ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%4.2f'))
            ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.01))
            ax.xaxis.set_major_locator(ticker.LogLocator(base=10))
            ax.yaxis.set_label_coords(-0.11, 0.5)

        if self.image_out_flag:
            image_file = f'{self.file_prefix}.{self.IMAGE_FILE_TYPE}'
            spl.fig.savefig(image_file, format=self.IMAGE_FILE_TYPE,
                            bbox_inches='tight', dpi=self.IMAGE_FILE_DPI, transparent=True)
            self.info(f'{image_file} is generated')
            plt.close(spl.fig)
        else:
            plt.pause(1.0)
            plt.show()

        self.debug('END', inspect.currentframe())
