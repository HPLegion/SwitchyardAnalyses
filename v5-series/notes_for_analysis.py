import os
import numpy as np
import pandas as pd
import altair as alt

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





# Record Monitor Interactions
for sID in sourceIDs:
    mon = monBySrc[sID]
    mon.reset_events()
    mon.reset_misses()
    for tr in trajsBySrc[sID]:
        mon.record_intersect(tr)

# Read Out misses and events
missesBySrc = dict()
eventsBySrc = dict()
for sID in sourceIDs:
    missesBySrc.update({sID : monBySrc[sID].get_misses()})
    eventsBySrc.update({sID : monBySrc[sID].get_events()})
#print(missesBySrc)

# Add lost particles to miss counter
for pID in lostParticles:
    for sID in sourceIDs:
        if pID in particlesBySrc[sID]:
            missesBySrc[sID] += 1
#print(missesBySrc)


# Compute and save emittances

colnames = ["sourceID", "sourceName", "x_offset", "y_offset", "x_emittance", "y_emittance", "losses"]
emit_df = pd.DataFrame(columns=colnames)
emit_temp = pd.DataFrame([np.zeros(len(colnames))], columns=colnames)
for sID in sourceIDs:
    name = particle_source_names[sID]
    xoff = float(name.split('_')[1])
    yoff = float(name.split('_')[3])
    xemit = monq.emittance_u(eventsBySrc[sID])
    yemit = monq.emittance_v(eventsBySrc[sID])
    losses = missesBySrc[sID]
    
    emit_temp["sourceID"] = sID
    emit_temp["sourceName"] = name
    emit_temp["x_offset"] = xoff
    emit_temp["y_offset"] = yoff
    emit_temp["x_emittance"] = xemit
    emit_temp["y_emittance"] = yemit
    emit_temp["losses"] = losses

    emit_df = emit_df.append(emit_temp, ignore_index=True)

emit_df.sort_values(["x_offset", "y_offset"], inplace=True)
emit_df.reset_index(inplace=True, drop=True)
emit_df