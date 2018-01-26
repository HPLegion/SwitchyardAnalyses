"""
Contains a class that represents a particle monitor
"""
import numpy as np
from scipy import optimize
from pandas import DataFrame

class ParticleMonitor:
    """
    A class that represents a particle monitor
    """

    def __init__(self, time0, trajectory=None,
                 r0=np.array([0, 0, 0]), u=np.array([0, 0, 0]),
                 v=np.array([0, 0, 0]), w=np.array([0, 0, 0]),
                 abs_vel=0, abs_mom=0):
        """
        Initialiser for the ParticleMonitor Object
        can either manually define the required parameters or
        hand over a trajectory from which they will be computed
        A time is always required!

        Keyword Args:
        time0 -- Arrival time of the design trajectory
        trajectory -- Default=None
        r0 -- [x,y,z] array of the design position
        u,v,w -- Local coordinate system, each a [x,z,y] array
        vel -- the absolute velocity of the design trajectory
        """

        self.time0 = time0
        #Create empty list for events to be saved in
        self.__events = list()
        self.__misses = 0
        # If no trajectory is given use defaults or manual user input
        if trajectory == None:
            self.r0 = r0.copy()
            self.u = u.copy()
            self.v = v.copy()
            self.w = w.copy()
            self.abs_vel = abs_vel
            self.abs_mom = abs_mom
        # Else compute r0, u,v,w and abs_vel from trajectory
        else:
            assert trajectory.tmin <= time0 <= trajectory.tmax, "Time out of bounds"
            self.r0 = trajectory.interp_pos(self.time0)
            self.abs_vel = trajectory.interp_abs_vel(self.time0)
            self.abs_mom = trajectory.interp_abs_mom(self.time0)
            self.__compute_uvw(trajectory)
        # Compose Rotation Matrix for x,y,z to u,v,w
        self.rotmat = np.linalg.inv(np.array([self.u, self.v, self.w]))


    def __compute_uvw(self, trajectory):
        # w shows in momentum direction
        w = trajectory.interp_mom(self.time0)
        w /= np.linalg.norm(w)

        # Calculate u
        u = w.copy() # start at w
        yrotmat = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]]) # rotate about y axis by 90deg
        u = u.dot(yrotmat)
        u[1] = 0 # project onto x,z plane
        u /= np.linalg.norm(u) # Normalise u

        # Calculate v
        v = np.cross(w,u) # v is cross product of w and u
        self.u = u
        self.v = v
        self.w = w


    def find_intersect(self, trajectory, lb=None, ub=None):
        """
        finds the intersection of trajectory with this monitor
        """

        if lb == None:
            lb = trajectory.tmin
        else:
            lb = np.maximum(trajectory.tmin, lb)
        if ub == None:
            ub = trajectory.tmax
        else:
            ub = np.minimum(trajectory.tmin, lb)

        # dot product of vector difference (traj_pos - monitor_pos) with w
        def f(t):
            return (trajectory.interp_pos(t)-self.r0).dot(self.w)
        # find root of f to find intersection
        (t_event, s_info) = optimize.brenth(f, lb, ub, full_output=True)

        # if no solution was found,i.e. the particle does not reach the monitor
        if not s_info.converged:
            return -1

        # Calculate u(i.e. x) and v(i.e. y) component of intersection in the monitor coordinates
        ps_u = (trajectory.interp_pos(t_event)-self.r0).dot(self.u)
        ps_v = (trajectory.interp_pos(t_event)-self.r0).dot(self.v)

        # Calculate longitudinal displacement
        ps_l = -self.abs_vel*(t_event-self.time0)

        # Calculate up(i.e. x') and vp(i.e. y')
        uvw_mom = trajectory.interp_mom(t_event).dot(self.rotmat)
        ps_up = 1000*np.arctan2(uvw_mom[0], uvw_mom[2])
        ps_vp = 1000*np.arctan2(uvw_mom[1], uvw_mom[2])

        # momentum spread
        ps_delta = (np.linalg.norm(uvw_mom)-self.abs_mom)/self.abs_mom

        inters_data = [trajectory.particleID, trajectory.sourceID, t_event,
                       ps_u, ps_up, ps_v, ps_vp, ps_l, ps_delta]
        return inters_data


    def record_intersect(self, trajectory, lb=None, ub=None):
        """
        finds the intersection of trajectory with this monitor and stores the event internally
        A dataframe of all recorded events can be accessed with
        get_events(), the return value of find_intersect is returned as well
        """

        result = self.find_intersect(trajectory, lb, ub)
        # Increase miss counter if no intersection (result = -1)
        if result == -1:
            self.__misses += 1
        # ELSE: Append the list of results to the event list containg all result lists
        else:
            self.__events.append(result.copy())
        return result

    def get_events(self):
        """
        Returns a dataframe with all events that have been recorded by this monitor
        """
        colnames = ["particleID", "sourceID", "t_event",
                    "ps_u", "ps_up", "ps_v", "ps_vp", "ps_l", "ps_delta"]
        return DataFrame(self.__events, columns=colnames)

    def get_misses(self):
        """
        Returns the number of events where the trajectory did not hit the monitor
        """
        return self.__misses

    def reset_events(self):
        """
        Resets the list of events
        """
        self.__events = list()

    def reset_misses(self):
        """
        Restes the number of misses
        """
        self.__misses = 0