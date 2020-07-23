Correction tools for Self Charge Filling Effect in Suzaku XIS
---

## Overview

In principle, charge traps can be filled not only by artificially injected charges, but also by charges created by X-ray events. This effect is called Self Charge Filling (SCF) effect. Apparent in observation of a very bright source (Cygnus X-3) is demonstrated by Todoroki et al. (2012, PASJ, 64, 101), and they proposed a correction method of the SCF effect. Even if XIS is operated with the SCI, the SCF effect can be seen. Yoshida et al. (2017, ApJ, 838, 30) shows an apparently inconsistent energy scale of XIS 1 data compared to those of XIS 0 and 3 in the observation conducted the SCI, since the events for XIS 0 and 3 were well recovered from the degradation of the CTE with the SCI performed with 2 keV equivalent electrons for three XIS sensors, though it was insufficient for XIS 1. However, this effect is not included in the calibration. It may be encountered that a better energy resolution than the RMF indicate.


## REQUIREMENTS

### Python
- Python 3.7
- Packages
    - [Numpy](https://numpy.org/)
    - [pandas](https://pandas.pydata.org/)
    - [Matplotlib](https://matplotlib.org/)
    - [seaborn](https://seaborn.pydata.org/)
    - [absl-py](https://github.com/abseil/abseil-py)
    - [lmfit](https://lmfit.github.io/lmfit-py/index.html)

#### How to install
```shellscript
$ pip install -r requirements.txt
```

### analysis tools for astronomy

- [HEASOFT](https://heasarc.gsfc.nasa.gov/docs/software/heasoft/) (version 6.26 or later)
- [FUNTOOLS](https://github.com/ericmandel/funtools)