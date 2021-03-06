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
from ..util.parse import get_file_prefix
from .plot import DPI, SimplePlot
from .model import energy_event_density_curve as scf_curve


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
    def __init__(self, qdp:str, log_file:str, plot_flag:bool=True, loglv:int=1) -> None:
        super().__init__(loglv)
        self.plot_flag = plot_flag
        self.log_file = log_file
        self.xd, self.xe, self.yd, self.ye = self.read_qdp(qdp)
        self.scf_model = lf.Model(func=scf_curve, independent_vars=['E'])

    def read_qdp(self, qdp:str) -> np.ndarray:
        with open(qdp, 'r') as f:
            raw_data = f.read().splitlines()
        skiprows = raw_data.index('!')+1
        self.raw_data = {qdp: raw_data}
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

        with open(self.log_file, 'w') as log:
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
        self.info(f'Fitting results were recorded to {self.log_file}')
        self.create_result_qdp()
        if self.plot_flag:
            self.plot()
        self.debug('END', inspect.currentframe())

    @property
    def result_curve(self):
        return scf_curve(E=self.DUMMY_ENERGY, **self.result.best_values)

    def create_result_qdp(self) -> None:
        self.debug('START', inspect.currentframe())
        raw_name = list(self.raw_data.keys())[0]
        raw_data = list(self.raw_data.values())[0]
        qdp_file = f'{get_file_prefix(raw_name)}_result.qdp'

        raw_data.append('NO NO NO NO')
        header = '\n'.join(raw_data)
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

        # data & best-fit model
        spl.axes[0].errorbar(x=self.xd, y=self.yd, xerr=self.xe, yerr=self.ye,
                             marker=spl.marker, ms=spl.masize, fmt=spl.pltfmt,
                             color=spl.colors.orange, ecolor=spl.colors.orange,
                             capsize=0.0, elinewidth=spl.lwidth, mec=spl.colors.orange,
                             label=f'{list(self.raw_data.keys())[0]}')
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

        plt.pause(1.0)
        plt.show()

        self.debug('END', inspect.currentframe())

class MultipleCurveFit(Common, AbstractCurveFit):
    def __init__(self, qdp:List[str], log_file:str, plot_flag:bool=True, loglv:int=1) -> None:
        super().__init__(loglv)
        self.plot_flag = plot_flag
        self.log_file = log_file
        self.ndata = len(qdp)
        self.xd, self.xe, self.yd, self.ye = self.read_multiple_qdp(qdp)
        self.scf_model = lf.Model(func=scf_curve, independent_vars=['E'])
        self.scf_model_parameters = lf.Parameters()

    def read_multiple_qdp(self, qdp_list:List[str]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        datasets = list()
        self.raw_data = dict()
        for qdp in qdp_list:
            with open(qdp, 'r') as f:
                raw_data: List = f.read().splitlines()
            skiprows = raw_data.index('!')+1
            self.raw_data[qdp] = raw_data

            datasets.append(np.loadtxt(qdp, dtype=float, delimiter=' ',
                skiprows=skiprows, unpack=True))
        return tuple(np.array([dataset[i,:] for dataset in datasets]) for i in range(4))

    def entry_parameter(self) -> List[CurveFitParameter]:
        param_list = list()
        try:
            self.info('Input parameters')
            self.info('Enter the values separated by ","')
            self.info(', '.join(
                [f'{p} ({k})' for p, k in CurveFitParameter.PROPERTIES.items()]))
            for n, raw_name in zip(range(self.ndata), self.raw_data.keys()):
                for param_name in self.scf_model.param_names:
                    if (n > 0) & (param_name in self.scf_model.param_names[1:]):
                        param_list.append(CurveFitParameter(
                            name=f'{param_name}_{n}', value=0, vary=False, min=0, max=1.E+10, expr=f'{param_name}_0'))
                    else:
                        print(f'{param_name}_{n} (for {raw_name})', end=' >>> ')
                        entry = input()
                        values = tuple(
                            modifier(float(v.strip())) for v, modifier in zip(
                                entry.split(','), CurveFitParameter.MODIFIERS))
                        params = dict(zip(CurveFitParameter.PROPERTIES.keys(), values))
                        param_list.append(CurveFitParameter(name=f'{param_name}_{n}', **params))
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
            residual[n,:] = (self.yd[n,:] - self.calculate_model(parameters, n, E[n,:]))**2*self.ye[n,:]**(-2)

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
            with open(self.log_file, 'w') as log:
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
            self.info(f'Fitting results were recorded to {self.log_file}')
            self.create_result_qdp()
            if self.plot_flag:
                self.plot()
        self.debug('END', inspect.currentframe())

    @property
    def result_curve(self) -> List:
        return [
            scf_curve(
                E=self.DUMMY_ENERGY,
                **dict((
                    param_name,
                    self.result.params[f'{param_name}_{n}']) 
                for param_name in self.scf_model.param_names)
            )
        for n in range(self.ndata) ]

    @property
    def result_residuals(self) -> List:
        return [
            self.yd[n] - scf_curve(
                E=self.xd[n],
                **dict((
                    param_name,
                    self.result.params[f'{param_name}_{n}']) 
                for param_name in self.scf_model.param_names)
            )
        for n in range(self.ndata) ]


    def create_result_qdp(self):
        self.debug('START', inspect.currentframe())
        for n, raw_name, raw_data in zip(
            range(self.ndata), self.raw_data.keys(), self.raw_data.values()):

            qdp_file = f'{get_file_prefix(raw_name)}_result.qdp'
            raw_data.append('NO NO NO NO')
            header = '\n'.join(raw_data)

            result = np.array([
                self.DUMMY_ENERGY,
                np.zeros(self.DUMMY_DATA_SIZE),
                self.result_curve[n],
                np.zeros(self.DUMMY_DATA_SIZE)])
            np.savetxt(fname=qdp_file, X=result.T,
                delimiter=' ', newline='\n', header=header, comments='')
            self.info(f'{qdp_file} is generated')
        self.debug('END', inspect.currentframe())

    def plot(self):
        self.debug('START', inspect.currentframe())
        spl = SimplePlot(configure=True,
                         figsize=(8, 6), nrows=2, height_ratios=[0.7, 0.3], fsize=20,
                         left=0.15, right=0.95, bottom=0.15, top=0.9)

        # data & best-fit model
        for n, raw_name, color in zip(range(self.ndata), self.raw_data.keys(), spl.colors.values()):
            # data
            spl.axes[0].errorbar(
                x=self.xd[n], y=self.yd[n],
                xerr=self.xe[n], yerr=self.ye[n],
                marker=spl.marker, ms=spl.masize, fmt=spl.pltfmt,
                color=color, ecolor=color, mec=color,
                capsize=0.0, elinewidth=spl.lwidth,
                label=f'{raw_name}')
            # model
            spl.axes[0].plot(self.DUMMY_ENERGY, self.result_curve[n],
                lw=spl.lwidth, ls=':', color=color)
            # residual
            spl.axes[1].errorbar(
                x=self.xd[n], y=self.result_residuals[n],
                xerr=self.xe[n], yerr=self.ye[n],
                marker=spl.marker, ms=spl.masize, fmt=spl.pltfmt,
                color=color, ecolor=color, mec=color,
                capsize=0.0, elinewidth=spl.lwidth)

        spl.axes[0].set_ylabel('Energy (keV)', fontsize=spl.fsize)
        spl.axes[0].legend(fontsize=spl.legfsize, loc='upper left',
            scatterpoints=1, numpoints=1, markerscale=0.7, handletextpad=0.,
            fancybox=True, framealpha=0.0, frameon=True)
        # spl.axes[0].set_ylim(6.52, 6.7)
        spl.axes[0].yaxis.set_major_locator(ticker.MultipleLocator(0.04))
        spl.axes[0].yaxis.set_major_formatter(
            ticker.FormatStrFormatter('%4.2f'))
        spl.axes[0].yaxis.set_minor_locator(ticker.MultipleLocator(0.02))

        spl.axes[1].axhline(y=0.0, color=spl.colors.black,
                            ls=spl.lstyle, lw=spl.lwidth, dashes=[2, 5])
        spl.axes[1].set_ylabel('residual', fontsize=spl.fsize)
        spl.axes[1].set_xlabel(r'Event density $({\rm events}\:{\rm frame}^{-1}\:{\rm pixel}^{-1}$)',
                               fontsize=spl.fsize)
        # spl.axes[1].set_ylim(-3.5E-2, 3.5E-2)
        spl.axes[1].yaxis.set_major_locator(ticker.MultipleLocator(0.05))
        spl.axes[1].yaxis.set_major_formatter(
            ticker.FormatStrFormatter('%4.2f'))
        spl.axes[1].yaxis.set_minor_locator(ticker.MultipleLocator(0.025))

        for ax in spl.axes:
            ax.set_xscale('log')
            ax.set_xlim(3E-5, 4E-2)
            ax.xaxis.set_major_locator(ticker.LogLocator(base=10))
            ax.yaxis.set_label_coords(-0.11, 0.5)

        plt.pause(1.0)
        plt.show()

        self.debug('END', inspect.currentframe())