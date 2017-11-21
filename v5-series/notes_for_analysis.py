import os
import numpy as np
import pandas as pd
import PhaseSpaceEval.monitor_quantities as monq
from PhaseSpaceEval.import_particle_data import *
from PhaseSpaceEval.trajectory import Trajectory
from PhaseSpaceEval.particlemonitor import ParticleMonitor


MODELNAME = "flatplates"
RAW_PATH = "rawdata_" + MODELNAME + "/"
EMIT_FILENAME = "emit_" + MODELNAME + ".csv" # Name for the emittance output file

particle_source_names = import_source_names(RAW_PATH + MODELNAME + "-source_names.txt")
particle_constants = import_particle_constants(RAW_PATH + MODELNAME + "-constants.txt")
particle_trajectories = import_particle_trajectories(RAW_PATH + MODELNAME + "-trajectories.txt")


# Delete the single_centre source, not required
for key in particle_source_names.keys():
    if particle_source_names[key] == "single_centre":
        del(particle_source_names[key])
        break
        
# Generate simple list with all source IDs
sourceIDs = list(particle_source_names.keys())
#print(sourceIDs)

# Create lists with all particles belonging to a source and with the id of the central particles
particlesBySrc = dict() # dict for all particleIDs
centresBySrc = dict() # dict with the ids of the central particles
for sID in sourceIDs:
    pIDs = particle_constants["particleID"].loc[particle_constants["sourceID"] == sID].tolist()
    particlesBySrc.update({sID : pIDs})
    centresBySrc.update({sID : min(pIDs)}) # the smallest pID for each source is the centre
#print(particlesBySrc)
#print(centresBySrc)


# Create Trajectories
trajsBySrc = dict() # Dict for all trajectories
ctrajsBySrc = dict() # Dict for central trajectories
lostParticles = list()
for sID in sourceIDs:
    # Compute central trajectory for each sID
    cID = centresBySrc[sID]
    ctr = Trajectory(particle_trajectories[cID],
                     particle_constants.loc[particle_constants["particleID"] == cID].squeeze())
    ctrajsBySrc.update({sID : ctr})

    # For each sID compute the trajectories of all pIDs
    # Note Particles that cannot be found in trajectory dataframe, these were lost
    pIDs = particlesBySrc[sID]
    trajs = list()
    for pID in pIDs:
        try:
            tr = Trajectory(particle_trajectories[pID],
                            particle_constants.loc[particle_constants["particleID"] == pID].squeeze())
        except KeyError:
            lostParticles.append(pID)
        trajs.append(tr)
    trajsBySrc.update({sID : trajs})
print(lostParticles)


# Create Monitors
monBySrc = dict()
for sID in sourceIDs:
    ctr = ctrajsBySrc[sID]
    t0 = ctr.find_time("z", 501)
    mon = ParticleMonitor(time0=t0, trajectory=ctr)
    monBySrc.update({sID : mon})