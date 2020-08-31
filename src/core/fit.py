# -*- coding: utf-8 -*-

import inspect
import os
import sys
from typing import Dict, List, Tuple, Union
from abc import abstractmethod, ABCMeta

import lmfit as lf
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import ticker

from ..util.common import Common
from ..util.error import InsufficientInputError, InvalidInputError
from ..util.object import ObjectLikeDict
from .plot import DPI, SimplePlot
from .model import energy_event_density_curve as scf_curve
from .parse import get_file_prefix, get_file_property
from .parse import get_unified_file_prefix, get_multiple_file_property


class CurveFitParameter(object):
    PROPERTIES = {
        'value': 'float',
        'vary': 'bool[0,1]',
        'min': 'float',
        'max': 'float',
        'expr': 'string'}
    MODIFIERS = (float, bool, float, float, str)

    def __init__(self, name:str, value:float, min:float, max:float, vary:bool=True, expr:str=None):
        self.name = name
        self.value = value
        self.vary = vary
        self.min = min
        self.max = max
        self.expr = expr

    def _get_properties(self) -> Tuple:
        return tuple(self.__dict__.keys())[1:]

    def _get_values(self) -> Tuple:
        return tuple(self.__dict__.values())[1:]

    def set_value(self, key: str, value: Union[float, bool]):
        self.__dict__[key] = value

    @property
    def properties(self) -> Tuple:
        return self._get_properties()

    @property
    def values(self) -> Tuple:
        return self._get_values()

    @property
    def hints(self) -> Dict:
        return dict(zip(self.properties, self.values))


class CurveFitFactory(object):
    @classmethod
    def get_instance(cls, qdp_list:List[str], **args):
        for f in qdp_list:
            if not os.path.exists(f):
                raise FileNotFoundError(f'No such qdp file: {f}')
        if len(qdp_list) == 1:
            return SingleCurveFit(qdp=qdp_list[0], **args)
        elif len(qdp_list) > 1:
            return MultipleCurveFit(qdp=qdp_list, **args)


class AbstractCurveFit(object, metaclass=ABCMeta):
    IMAGE_FILE_TYPE = 'pdf'
    IMAGE_FILE_DPI = DPI
    DUMMY_DATA_SIZE = 500
    DUMMY_ENERGY = np.logspace(-5, -1, DUMMY_DATA_SIZE)

    def __init__(self):
        pass # nothing to do
    
    @abstractmethod
    def entry_parameter(self):
        pass

    @abstractmethod
    def set_parameter(self):
        pass

    @abstractmethod
    def fit(self):
        pass

    @abstractmethod
    def plot(self):
        pass

    @abstractmethod
    def create_result_qdp(self):
        pass

class SingleCurveFit(Common, AbstractCurveFit):
    def __init__(self, qdp: str, image_out_flag: bool = False, loglv: int = 1) -> None:
        super().__init__(loglv)
        self.image_out_flag = image_out_flag
        self.file_prefix = get_file_prefix(qdp)
        self.property: ObjectLikeDict = get_file_property(qdp)
        self.xd, self.xe, self.yd, self.ye = self.read_qdp(qdp)
        self.scf_model = lf.Model(func=scf_curve, independent_vars=['E'])

    def read_qdp(self, qdp:str) -> np.ndarray:
        with open(qdp, 'r') as f:
            self.raw_data: List = f.read().splitlines()
        skiprows = self.raw_data.index('!')+1
        return np.loadtxt(qdp, dtype=float, delimiter=' ', skiprows=skiprows, unpack=True)

    def entry_parameter(self) -> List[CurveFitParameter]:
        param_list = list()
        try:
            self.info('Input parameters')
            self.info('Enter the values separated by ","')
            self.info(', '.join(
                [f'{p} ({k})' for p, k in CurveFitParameter.PROPERTIES.items()]))
            for name in self.scf_model.param_names:
                print(f'{name}', end=' >>> ')
                entry = input()
                values = tuple(
                    modifier(float(v.strip())) for v, modifier in zip(
                        entry.split(','), CurveFitParameter.MODIFIERS))
                params = dict(zip(CurveFitParameter.PROPERTIES.keys(), values))
                param_list.append(CurveFitParameter(name=name, **params))
            print('\n')
        except ValueError:
            raise InvalidInputError('Input parameter is invalid.')
        except TypeError:
            raise InsufficientInputError('Input parameter is insufficient.')
        except InvalidInputError as err:
            self.abort(err)
        except InsufficientInputError as err:
            self.abort(err)
        else:
            return param_list

    def set_parameter(self) -> None:
        param_list = self.entry_parameter()
        for param in param_list:
            self.scf_model.set_param_hint(param.name, **param.hints)
        self.debug(self.scf_model.param_hints)

    def fit(self) -> None:
        self.debug('START', inspect.currentframe())
        self.set_parameter()
        self.result = self.scf_model.fit(
            E=self.xd, data=self.yd, weights=self.ye**(-1), method='leastsq')
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
        self.info(f'Fitting results were recorded to {log_file}')
        self.create_result_qdp()
        self.plot()
        self.debug('END', inspect.currentframe())

    @property
    def result_curve(self):
        return scf_curve(E=self.DUMMY_ENERGY, **self.result.best_values)

    def create_result_qdp(self) -> None:
        self.debug('START', inspect.currentframe())
        qdp_file = f'{self.file_prefix}_result.qdp'
        self.raw_data.append('NO NO NO NO')
        header = '\n'.join(self.raw_data)
        result = np.array([
            self.DUMMY_ENERGY,
            np.zeros(self.DUMMY_DATA_SIZE),
            self.result_curve,
            np.zeros(self.DUMMY_DATA_SIZE)])
        np.savetxt(fname=qdp_file, X=result.T,
                   delimiter=' ', newline='\n', header=header, comments='')
        self.info(f'{qdp_file} is generated')
        self.debug('END', inspect.currentframe())

    def plot(self) -> None:
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
        spl.axes[0].plot(self.DUMMY_ENERGY, self.result_curve,
                         lw=spl.lwidth, ls=':', color=spl.colors.orange)
        spl.axes[0].set_ylabel('Energy (keV)', fontsize=spl.fsize)
        spl.axes[0].legend(fontsize=spl.legfsize, loc='upper left',
                           scatterpoints=1, numpoints=1, markerscale=0.7, handletextpad=0.,
                           fancybox=True, framealpha=0.0, frameon=True)
        # spl.axes[0].set_ylim(6.52, 6.7)
        spl.axes[0].yaxis.set_major_locator(ticker.MultipleLocator(0.04))
        spl.axes[0].yaxis.set_major_formatter(
            ticker.FormatStrFormatter('%4.2f'))
        spl.axes[0].yaxis.set_minor_locator(ticker.MultipleLocator(0.02))

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
        spl.axes[1].yaxis.set_major_locator(ticker.MultipleLocator(0.02))
        spl.axes[1].yaxis.set_major_formatter(
            ticker.FormatStrFormatter('%4.2f'))
        spl.axes[1].yaxis.set_minor_locator(ticker.MultipleLocator(0.01))

        for ax in spl.axes:
            ax.set_xscale('log')
            ax.set_xlim(3E-5, 4E-2)
            ax.xaxis.set_major_locator(ticker.LogLocator(base=10))
            ax.yaxis.set_label_coords(-0.11, 0.5)

        if self.image_out_flag:
            image_file = f'{self.file_prefix}_result.{self.IMAGE_FILE_TYPE}'
            spl.fig.savefig(image_file, format=self.IMAGE_FILE_TYPE,
                            bbox_inches='tight', dpi=self.IMAGE_FILE_DPI, transparent=True)
            self.info(f'{image_file} is generated')
            plt.close(spl.fig)
        else:
            plt.pause(1.0)
            plt.show()

        self.debug('END', inspect.currentframe())

class MultipleCurveFit(Common, AbstractCurveFit):
    def __init__(self, qdp: List[str], image_out_flag: bool = False, loglv: int = 1) -> None:
        super().__init__(loglv)
        self.image_out_flag = image_out_flag
        self.file_prefix = get_unified_file_prefix(qdp)
        self.property: ObjectLikeDict = get_multiple_file_property(qdp)
        self.ndata = len(qdp)
        self.xd, self.xe, self.yd, self.ye = self.read_multiple_qdp(qdp)
        self.scf_model = lf.Model(func=scf_curve, independent_vars=['E'])
        self.scf_model_parameters = lf.Parameters()

    def read_multiple_qdp(self, qdp_list:List[str]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        datasets = list()
        self.raw_data = list()
        for n in range(self.ndata):
            with open(qdp_list[n], 'r') as f:
                qdp: List = f.read().splitlines()
            skiprows = qdp.index('!')+1
            if n == 0:
                # header
                self.raw_data.extend(qdp[:skiprows])
            self.raw_data.extend(qdp[skiprows:])
            self.raw_data.append('NO NO NO NO')

            datasets.append(np.loadtxt(qdp_list[n], dtype=float, delimiter=' ',
                skiprows=skiprows, unpack=True))
        return tuple(np.array([dataset[i,:] for dataset in datasets]) for i in range(4))

    def entry_parameter(self) -> List[CurveFitParameter]:
        param_list = list()
        try:
            self.info('Input parameters')
            self.info('Enter the values separated by ","')
            self.info(', '.join(
                [f'{p} ({k})' for p, k in CurveFitParameter.PROPERTIES.items()]))
            for n in range(self.ndata):
                for name in self.scf_model.param_names:
                    if (n > 0) & (name in self.scf_model.param_names[1:]):
                        param_list.append(CurveFitParameter(
                            name=f'{name}_{n}', value=0, vary=False, min=0, max=1.E+10, expr=f'{name}_0'))
                    else:
                        print(f'{name}_{n} ({self.property.phase[n]})', end=' >>> ')
                        entry = input()
                        values = tuple(
                            modifier(float(v.strip())) for v, modifier in zip(
                                entry.split(','), CurveFitParameter.MODIFIERS))
                        params = dict(zip(CurveFitParameter.PROPERTIES.keys(), values))
                        param_list.append(CurveFitParameter(name=f'{name}_{n}', **params))
            print('\n')
        except ValueError:
            raise InvalidInputError('Input parameter is invalid.')
        except TypeError:
            raise InsufficientInputError('Input parameter is insufficient.')
        except InvalidInputError as err:
            self.abort(err)
        except InsufficientInputError as err:
            self.abort(err)
        else:
            return param_list

    def set_parameter(self) -> None:
        param_list = self.entry_parameter()
        for param in param_list:
            self.scf_model_parameters.add(param.name, **param.hints)
            self.debug(self.scf_model_parameters[param.name])

    def calculate_model(self, parameters:lf.Parameters, n:int, E:np.ndarray):
        """Calculate model lineshape from parameters for data set."""
        return scf_curve(E,
            **dict((name, parameters[f'{name}_{n}']) for name in self.scf_model.param_names))

    def objective(self, parameters:lf.Parameters, E:np.ndarray):
        """Calculate total residual for fits of models to several data sets."""
        # make residual per data set
        residual = 0.0 * self.yd

        for n in range(self.ndata):
            residual[n,:] = (self.yd[n,:] - self.calculate_model(parameters, n, E[n,:]))*self.ye[n,:]**(-2)

        # now flatten this to a 1D array, as minimize() needs
        return residual.flatten()

    def fit(self) -> None:
        self.debug('START', inspect.currentframe())
        self.set_parameter()
        self.result = lf.minimize(
            fcn=self.objective, params=self.scf_model_parameters, kws={'E':self.xd})

        if self.result.success:
            self.info(self.result.message)
            self.info('BEST FIT VALUES')
            for name in self.result.var_names:
                self.info(f'parameter of {name}')
                self.info(
                    f'  {self.result.params[name].value} +- {self.result.params[name].stderr}')
            log_file = f'{self.file_prefix}_result.log'
            with open(log_file, 'w') as log:
                log.write(
                    '--------------------------------------------------------------------\n')
                log.write(lf.fit_report(self.result))
                log.write('\n')
                log.write(
                    '--------------------------------------------------------------------\n')
                log.write(
                    f' Chi-squared value / d.o.f. = {self.result.chisqr} / {self.result.nfree}\n')
                log.write(f' Reduced Chi-squared value  = {self.result.redchi}\n')
                log.write('\n')
            self.info(f'Fitting results were recorded to {log_file}')
        self.debug('END', inspect.currentframe())
    
    def create_result_qdp(self):
        self.debug('START', inspect.currentframe())
        qdp_file = f'{self.file_prefix}_result.qdp'
        header = '\n'.join(self.raw_data)
        scf_curve(E,
            **dict((
                name,
                parameters[f'{name}_{n}']) for name in self.scf_model.param_names))

        result = np.array([
            self.DUMMY_ENERGY,
            np.zeros(self.DUMMY_DATA_SIZE),
            self.result_curve,
            np.zeros(self.DUMMY_DATA_SIZE)])
        np.savetxt(fname=qdp_file, X=result.T,
                   delimiter=' ', newline='\n', header=header, comments='')
        self.info(f'{qdp_file} is generated')
        self.debug('END', inspect.currentframe())

    def plot(self):
        self.warning('No implement', inspect.currentframe())