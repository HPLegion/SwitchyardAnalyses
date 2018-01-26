"""
Contains a class that regulates the access to trajectory information
"""
import numpy as np
from scipy import interpolate
from scipy import optimize

class Trajectory:
    """
    A class that regulates the access to trajectory information
    For interpolation type check:
    https://docs.scipy.org/doc/scipy-0.19.1/reference/generated/scipy.interpolate.interp1d.html
    """
    def __init__(self, trajectory_frame, constants_frame, interpolation_type="linear"):
        """
        Initialise the Trajectory Object
        
        Keyword Arguments:
        trajectory_frame -- a data frame containing the trajectory information
        constants_frame -- a single line data series containing the static information
        interpolation_type -- default="linear", the interpolation method to be used (for scipy interp1d)
        """
        self.__trajectory_frame = trajectory_frame#.copy()
        self.__constants_frame = constants_frame#.copy()

        # Read in scalar constant properties
        self.particleID = int(self.__constants_frame.loc["particleID"])
        self.mass = self.__constants_frame.loc["mass"]
        self.macroCharge = self.__constants_frame.loc["macroCharge"]
        self.sourceID = int(self.__constants_frame.loc["sourceID"])

        # Read in trajectory points
        self.__time = self.__trajectory_frame["time"].values
        self.__x = self.__trajectory_frame["x"].values
        self.__y = self.__trajectory_frame["y"].values
        self.__z = self.__trajectory_frame["z"].values
        self.__px = self.__trajectory_frame["px"].values
        self.__py = self.__trajectory_frame["py"].values
        self.__pz = self.__trajectory_frame["pz"].values

        # Define Interpolators
        self.__in_x = interpolate.interp1d(self.__time, self.__x, kind=interpolation_type)
        self.__in_y = interpolate.interp1d(self.__time, self.__y, kind=interpolation_type)
        self.__in_z = interpolate.interp1d(self.__time, self.__z, kind=interpolation_type)
        self.__in_px = interpolate.interp1d(self.__time, self.__px, kind=interpolation_type)
        self.__in_py = interpolate.interp1d(self.__time, self.__py, kind=interpolation_type)
        self.__in_pz = interpolate.interp1d(self.__time, self.__pz, kind=interpolation_type)

        # Define Time Limits of trajectory
        self.tmin = self.__time.min()
        self.tmax = self.__time.max()


    def interp_x(self, time):
        """
        Returns an interpolation of x at given time 
        Can take array of times and return array of corresponding values
        """
        return self.__in_x(time)

    def interp_y(self, time):
        """
        Returns an interpolation of y at given time 
        Can take array of times and return array of corresponding values
        """
        return self.__in_y(time)

    def interp_z(self, time):
        """
        Returns an interpolation of z at given time 
        Can take array of times and return array of corresponding values
        """
        return self.__in_z(time)

    def interp_px(self, time):
        """
        Returns an interpolation of px at given time 
        Can take array of times and return array of corresponding values
        """
        return self.__in_px(time)

    def interp_py(self, time):
        """
        Returns an interpolation of py at given time 
        Can take array of times and return array of corresponding values
        """
        return self.__in_py(time)

    def interp_pz(self, time):
        """
        Returns an interpolation of pz at given time 
        Can take array of times and return array of corresponding values
        """
        return self.__in_pz(time)

    def interp_pos(self, time):
        """
        Returns an interpolation of [x,y,z] as row vector at given time 
        Only use scalars for time here!
        """
        assert not isinstance(time, (list, tuple, np.ndarray)), "time mus be a scalar"
        return np.array([self.interp_x(time), self.interp_y(time), self.interp_z(time)])

    def interp_mom(self, time):
        """
        Returns an interpolation of [px,py,pz] as row vector at given time 
        Only use scalars for time here!
        """
        assert not isinstance(time, (list, tuple, np.ndarray)), "time mus be a scalar"
        return np.array([self.interp_px(time), self.interp_py(time), self.interp_pz(time)])

    def interp_abs_vel(self, time):
        """
        Returns an interpolation of the absolute velocity at given time (in mm/ns)
        Only use scalars for time here!
        """
        assert not isinstance(time, (list, tuple, np.ndarray)), "time mus be a scalar"
        mom_abs = np.linalg.norm(self.interp_mom(time))
        return mom_abs * 299792458 * 1.0E3 / 1.0E9 / np.sqrt(1 + mom_abs**2)

    def interp_abs_mom(self, time):
        """
        Returns an interpolation of the absolute momentum at given time (in mm/ns)
        Only use scalars for time here!
        """
        assert not isinstance(time, (list, tuple, np.ndarray)), "time mus be a scalar"
        return np.linalg.norm(self.interp_mom(time))

    def find_time(self, axis, value, tmin=None, tmax=None):
        """
        returns the time of a given coordinate ("x", "y", "z") having a given value,
        tmin and tmax can be given to specify the search radius otherwise the tmin and tmax
        properties of the trajectory object are used
        """
        if tmin == None:
            tmin = self.tmin
        if tmax == None:
            tmax = self.tmax
            
        def f(t):
            if axis == "x":
                return self.interp_x(t) - value
            elif axis == "y":
                return self.interp_y(t) - value
            elif axis == "z":
                return self.interp_z(t) - value

        (t_event, s_info) = optimize.brenth(f, tmin, tmax, full_output=True)
        if s_info.converged:
            return t_event
        else:
            return float("NaN")
