"""
function calculating the emittance
"""

import numpy as np

def emittance(x, xp):
    """
    returns the emittance of x and xp
    both input vectors have to be numpy arrays (1D) of the same length
    """
    return np.sqrt(np.linalg.det(np.cov(x, xp)))

def emittance_u(df):
    """
    takes a monitor output data frame and calculate the u emittance (x emittance)
    """
    return emittance(df.ps_u.values.copy(), df.ps_up.values.copy())

def emittance_v(df):
    """
    takes a monitor output data frame and calculate the v emittance (y emittance)
    """
    return emittance(df.ps_v.values.copy(), df.ps_vp.values.copy())