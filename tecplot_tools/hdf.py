from pathlib import Path
from typing import Tuple

import h5py
import numpy as np


def create_hdf5(filename, variables, taxis=None, tstart=0, dt=1, write_macro=True) -> Tuple[Path, Path]:
    """
    Creates an HDF5 file that can be read by tecplot. A tecplot
    macro is created to assist with loading and assigning
    time stamps to zones if data is transient.

    Per default, no transient data is expected, thus taxis=None.
    If data has a time dimension, taxis must specify which array axis
    is associated with the time.

    Parameters
    ---------
    filename : Path
        H5 filename. Note: must have extension .h5, otherwise
        not excepted by Tecplot
    variables : dict
        Dictionary of variables. Values must be numpy arrays
    taxis : int, optional=None
        Specifies the time axis in the array. Default is None,
        thus not expecting time data.
    tstart : float, optional
        Time stamp of first zone. Default is 0
    dt : float, optional
        Time delta between zones. Default is 1
    write_macro : bool, optional
        Writes macro next to filename, which can be called
        along with starting tecplot: tec360ex <macro_file>

    Returns
    -------
    filename : Path
        H5 filename.
    """
    filename = Path(filename).absolute()

    all_rank = [v.ndim for v in variables.values()]
    max_rank = np.max(all_rank)
    is_transient_data = taxis is not None

    for v in variables.values():
        if v.ndim == max_rank:
            if is_transient_data:
                nt = v.shape[taxis]

    if max_rank > 4:
        raise ValueError('Max. rank is 4, which describes time resolved '
                         '3d data --> (nt, nz, ny, nx).')

    nvariables = len(variables)
    _varnames = list(variables.keys())

    with h5py.File(filename, 'w') as h5:
        if is_transient_data:
            for it in range(nt):
                for vname, data in variables.items():
                    if data.ndim == 4:
                        _data = np.take(data, it, axis=taxis)
                        h5.create_dataset(f'Z{it}/{vname}', data=_data)
                    else:
                        h5.create_dataset(f'Z{it}/{vname}', data=data)
        else:
            for vname, data in variables.items():
                h5.create_dataset(vname, data=data[:])

    str_zones = ''
    if is_transient_data:
        for it in range(nt):
            str_zones += f'"/Z{it}/" '

    str_variable = ''
    for vname in _varnames:
        str_variable += f'"{vname}" '

    if is_transient_data:
        str_filename = f'"{filename}" ' * nt
        macro_str = f'#!MC 1410\n' \
                    f'$!READDATASET  \'"-F" "{nt}" {str_filename}"-D" "{nt}" {str_zones}"-G" "{nvariables}"' \
                    f' {str_variable} ' \
                    '"-K" "1" "1" "1"\'\n' \
                    '  DATASETREADER = \'HDF5 Loader\'\n' \
                    '  READDATAOPTION = NEW\n' \
                    '  RESETSTYLE = YES\n' \
                    '  ASSIGNSTRANDIDS = NO\n' \
                    '  INITIALPLOTTYPE = CARTESIAN3D\n' \
                    '  INITIALPLOTFIRSTZONEONLY = NO\n' \
                    '  ADDZONESTOEXISTINGSTRANDS = NO\n' \
                    '  VARLOADMODE = BYNAME\n' \
                    '$!THREEDAXIS XDETAIL{VARNUM = 1}\n' \
                    '$!THREEDAXIS YDETAIL{VARNUM = 2}\n' \
                    '$!THREEDAXIS ZDETAIL{VARNUM = 3}\n' \
                    '$!EXTENDEDCOMMAND\n' \
                    '   COMMANDPROCESSORID = \'Strand Editor\'\n' \
                    f'COMMAND = \'ZoneSet=1-{nt};MultiZonesPerTime=TRUE;ZoneGrouping=Time;' \
                    f'GroupSize={nt};AssignStrands=TRUE;StrandValue={nt};AssignSolutionTime=TRUE;' \
                    f'TimeValue={tstart};DeltaValue={dt};TimeOption=Automatic;\''

    else:  # no transient data
        macro_str = f'#!MC 1410\n' \
                    f'$!READDATASET  \'"-F" "1" {filename} "-D" "{nvariables}"' \
                    f' {str_variable} ' \
                    '"-K" "1" "1" "1"\'\n' \
                    '  DATASETREADER = \'HDF5 Loader\'\n' \
                    '  READDATAOPTION = NEW\n' \
                    '  RESETSTYLE = YES\n' \
                    '  ASSIGNSTRANDIDS = NO\n' \
                    '  INITIALPLOTTYPE = CARTESIAN3D\n' \
                    '  INITIALPLOTFIRSTZONEONLY = NO\n' \
                    '  ADDZONESTOEXISTINGSTRANDS = NO\n' \
                    '  VARLOADMODE = BYNAME\n' \
                    '$!THREEDAXIS XDETAIL{VARNUM = 1}\n' \
                    '$!THREEDAXIS YDETAIL{VARNUM = 2}\n' \
                    '$!THREEDAXIS ZDETAIL{VARNUM = 3}\n'
    if write_macro:
        filename_str = str(filename)
        macro_filename = filename_str.replace(filename.suffix, '.mcr')
        with open(macro_filename, 'w') as f:
            f.writelines(macro_str)
    return filename, Path(macro_filename)
