Correction tools for Self Charge Filling Effect in Suzaku XIS
---

## Overview

In principle, charge traps can be filled not only by artificially injected charges, but also by charges created by X-ray events. This effect is called Self Charge Filling (SCF) effect. Apparent in observation of a very bright source (Cygnus X-3) is demonstrated by Todoroki et al. (2012, PASJ, 64, 101), and they proposed a correction method of the SCF effect. Even if XIS is operated with the SCI, the SCF effect can be seen. Yoshida et al. (2017, ApJ, 838, 30) shows an apparently inconsistent energy scale of XIS 1 data compared to those of XIS 0 and 3 in the observation conducted the SCI, since the events for XIS 0 and 3 were well recovered from the degradation of the CTE with the SCI performed with 2 keV equivalent electrons for three XIS sensors, though it was insufficient for XIS 1. However, this effect is not included in the calibration. It may be encountered that a better energy resolution than the RMF indicate.

This repository provides the SCF effect correction tools based on the method established by Todoroki et al. (2012, PASJ, 64, 101).


## REQUIREMENTS

- [Python 3.7](https://www.python.org/)
    - [Numpy](https://numpy.org/)
    - [pandas](https://pandas.pydata.org/)
    - [Matplotlib](https://matplotlib.org/)
    - [seaborn](https://seaborn.pydata.org/)
    - [absl-py](https://github.com/abseil/abseil-py)
    - [lmfit](https://lmfit.github.io/lmfit-py/index.html)
- [GCC](https://gcc.gnu.org/)
- [GNU Make](https://www.gnu.org/software/make/)
- [HEASOFT](https://heasarc.gsfc.nasa.gov/docs/software/heasoft/) (version 6.26 or later)
- [FUNTOOLS](https://github.com/ericmandel/funtools)

## SETUP

1. Install FUNTOOLS
    ```shellscript
    $ sudo mkdir -p /usr/local/xray/funtools/src
    $ sudo mkdir -p /usr/local/xray/funtools/sys
    $ cd /usr/local/xray/funtools
    $ git clone git@github.com:ericmandel/funtools.git src && cd src
    $ ./mkconfigure
    $ ./configure --prefix=/usr/local/xray/funtools/sys
    $ make
    $ make install
    ```
1. Compile `pigaincorrect` (This command is utilized in `xisscfpigaincorrect.sh`)
    ```shellscript
    $ cd {REPOSITORY_ROOT}
    $ make
    ```
1. Install python packages for `xisscfcurvefit.py`
    ```shellscript
    $ cd {REPOSITORY_ROOT}
    $ pip install -r requirements.txt
    ```

## Procedure

1. Make regions using `xismkscfreg.sh`.
2. Using [`xselect`](https://heasarc.gsfc.nasa.gov/ftools/xselect/), extract spectra filtered the regions created in step 1 from cleaned event files.
3. Using [`xissimarfgen`](https://heasarc.gsfc.nasa.gov/docs/suzaku/analysis/xissimarfgen/), generate ancillary response files with the regions created in step 1.
4. Fitting the spectra extracted in step 2, determine the emission line center energies in each regions. When you fit the spectra, use the ancillary response files generated in step 3.
5. Using [`xselect`](https://heasarc.gsfc.nasa.gov/ftools/xselect/), extract images of all grade (0-7) from unfiltered event files.
6. Make [QDP](https://heasarc.gsfc.nasa.gov/ftools/others/qdp/qdp.html) file of the relation between the event densities and the center energies. Here, the event density is calculated with the image extracted in step 5, and the center energy is determined in step 4. The order of data is as follows; `{d_dat, d_err, e_dat, e_err}`, where `d_dat` is the event density, `d_err` is the error of the event density, `e_dat` is the emission line energy, and `e_err` is the error of the emission line energy, respectively. Note that in the QDP file the values should be separated by a space.
7. Using `xisscfcurvefit.py`, fit the curve of the relation between the event densities and the center energies. The amount of gain correction can be determined by this task.
8. Using `xisscfpigaincorrect.sh`, correct the gain for each spectra with the amount of correction determined in step 7.
