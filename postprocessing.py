import os
SLURM_JOB_ID = os.environ.get("SLURM_JOB_ID", "")
print("SLURM_JOB_ID: {}".format(SLURM_JOB_ID))

# single process for postprocessing
# currently postprecessing is only used for reproducing SUMMA CAMELS Paper to calcuate KGE and other indices
# the script is only trigger if there is folder named "regress_data" inside "output" folder
# not used for general summa ensemble modelling purpose

print("postprocessing for CAMELS paper")
import os
import json
from natsort import natsorted
import xarray as xr
import pandas as pd

data_path = os.environ["data_folder"]
regress_folder_path = os.path.join(data_path, "output/regress_data")
if not os.path.isdir(regress_folder_path):
    exit()

instance_path = data_path
result_folder_path = os.environ["result_folder"]
# check output directory
output_path = os.path.join(result_folder_path, "output")
if not os.path.exists(os.path.join(output_path, 'merged_day')):
    os.makedirs(os.path.join(output_path, 'merged_day'))
truth_path = os.path.join(output_path, "truth")
def sort_nc_files(folder_path):
    name_list = os.listdir(folder_path)
    full_list1 = [os.path.join(folder_path, i) for i in name_list if i.endswith(".nc")]
    sorted_list = natsorted(full_list1)
    sorted_list = natsorted(sorted_list, key=lambda v: v.upper())
    print("Number of NC files: {}".format(len(sorted_list)))
    return sorted_list
sorted_list = sort_nc_files(truth_path)
all_ds = [xr.open_dataset(f) for f in sorted_list]
all_name = [n.split("_")[-2] for n in sorted_list]
all_merged = xr.concat(all_ds, pd.Index(all_name, name="decision"))
merged_truth_path = os.path.join(output_path, "merged_day/NLDAStruth_configs_latin.nc")
all_merged.to_netcdf(merged_truth_path)
print(merged_truth_path)
constant_path = os.path.join(output_path, "constant")
sorted_list = sort_nc_files(constant_path)
i = 0
all_ds = [xr.open_dataset(f) for f in sorted_list]
ens_decisions = []
for f in sorted_list:
    ens_decisions.append(f.split("_")[-2])
constant_vars= ['airpres','airtemp','LWRadAtm','pptrate','spechum','SWRadAtm','windspd']
for v in constant_vars:
    all_merged = xr.concat(all_ds[i:i+int(len(sorted_list)/7)], pd.Index(ens_decisions[i:i+int(len(sorted_list)/7)], name="decision"))
    merged_constant_path = os.path.join(output_path, 'merged_day/NLDASconstant_' + v +'_configs_latin.nc')
    all_merged.to_netcdf(merged_constant_path)
    print(merged_constant_path)
    i = i + int(len(sorted_list)/7)
#### KGE ##########
print("#################### KGE #########################")
import os
from natsort import natsorted
import xarray as xr
import pandas as pd
import numpy as np
initialization_days = 365
keep_raw_outputs = False
try:
    regress_param_path = os.path.join(regress_folder_path, "regress_param.json")
    with open(regress_param_path) as f:
        regress_param = json.load(f)
        initialization_days = int(regress_param["initialization_days"])
        keep_raw_outputs = regress_param.get("keep_raw_outputs", False)
except Exception as ex:
    print(ex)
    pass
print("initialization_days: {}; keep_raw_outputs: {}".format(str(initialization_days), str(keep_raw_outputs)))
print("#################### initialization_days: {}".format(initialization_days))
# Set forcings and create dictionaries, reordered forcings and output variables to match paper 
constant_vars= ['pptrate','airtemp','spechum','SWRadAtm','LWRadAtm','windspd','airpres'] 
allforcings = constant_vars+['truth']
comp_sim=['scalarInfiltration','scalarSurfaceRunoff','scalarAquiferBaseflow','scalarSoilDrainage',
          'scalarTotalSoilWat','scalarCanopyWat','scalarLatHeatTotal','scalarTotalET','scalarTotalRunoff',
          'scalarSWE','scalarRainPlusMelt','scalarSnowSublimation','scalarSenHeatTotal','scalarNetRadiation']
var_sim = np.concatenate([constant_vars, comp_sim])
# definitions for KGE computation, correlation with a constant (e.g. all SWE is 0) will be 0 here, not NA
def covariance(x,y,dims=None):
    return xr.dot(x-x.mean(dims), y-y.mean(dims), dims=dims) / x.count(dims)
def correlation(x,y,dims=None):#
    return (covariance(x,y,dims)) / (x.std(dims) * y.std(dims))
settings_folder = os.path.join(instance_path, "settings")
attrib = xr.open_dataset(settings_folder+'/attributes.nc')
the_hru = np.array(attrib['hruId'])

#save file
save_regress_folder_path = os.path.join(result_folder_path, "regress_data")
if not os.path.exists(save_regress_folder_path):
    os.makedirs(save_regress_folder_path)

# Names for each set of problem complexities.
choices = [1,0,0,0]
suffix = ['_configs_latin.nc','_latin.nc','_configs.nc','_hru.nc']
for i,k in enumerate(choices):
    if k==0: continue
    sim_truth = xr.open_dataset(os.path.join(output_path, 'merged_day/NLDAStruth'+suffix[i]))
    
# Get decision names off the files
    if i<3: decision_set = np.array(sim_truth['decision']) 
    if i==3: decision_set = np.array(['default'])
# set up error calculations
    summary = ['KGE','raw']
    shape = ( len(decision_set),len(the_hru), len(allforcings),len(summary))
    dims = ('decision','hru','var','summary')
    coords = {'decision':decision_set,'hru': the_hru, 'var':allforcings, 'summary':summary}
    error_data = xr.Dataset(coords=coords)
    for s in comp_sim:
        error_data[s] = xr.DataArray(data=np.full(shape, np.nan),
                                     coords=coords, dims=dims,
                                     name=s)
        
    # calculate summaries
    truth0_0 = sim_truth.drop_vars('hruId').load()
    for v in constant_vars:
        truth = truth0_0
        truth = truth.isel(time = slice(initialization_days*24,None)) #don't include first year, 5 years
        sim = xr.open_dataset(os.path.join(output_path, 'merged_day/NLDASconstant_' + v + suffix[i]))
        sim = sim.drop_vars('hruId').load()
        sim = sim.isel(time = slice(initialization_days*24,None)) #don't include first year, 5 years
        r = sim.mean(dim='time') #to set up xarray since xr.dot not supported on dataset and have to do loop
        for s in var_sim:         
            r[s] = correlation(sim[s],truth[s],dims='time')
        ds = 1 - np.sqrt( np.square(r-1) 
        + np.square( sim.std(dim='time')/truth.std(dim='time') - 1) 
        + np.square( (sim.mean(dim='time') - truth.mean(dim='time'))/truth.std(dim='time') ) )
        for s in var_sim:   
            #if constant and identical, want this as 1.0 -- correlation with a constant = 0 and std dev = 0
            for h in the_hru:
                if i<3: 
                        for d in decision_set:  
                            ss = sim[s].sel(hru=h,decision = d)
                            tt = truth[s].sel(hru=h,decision = d)
                            ds[s].loc[d,h] =ds[s].sel(hru=h,decision = d).where(np.allclose(ss,tt, atol = 1e-10)==False, other=1.0)
                else:
                    ss = sim[s].sel(hru=h)
                    tt = truth[s].sel(hru=h)
                    ds[s].loc[h] =ds[s].sel(hru=h).where(np.allclose(ss,tt, atol = 1e-10)==False, other=1.0)
        ds = ds/(2.0-ds)
        ds0 = ds.load()
        for s in comp_sim:
            error_data[s].loc[:,:,v,'KGE']  = ds0[s]
            error_data[s].loc[:,:,v,'raw']  = sim[s].sum(dim='time') #this is raw data, not error
        print(v)
    for s in comp_sim:
        error_data[s].loc[:,:,'truth','raw']  = truth[s].sum(dim='time') #this is raw data, not error      
        
    error_data.to_netcdf(os.path.join(save_regress_folder_path, 'error_data'+suffix[i]))
if not keep_raw_outputs:
    print("moving raw ouputs out of download folder")
    os.system("mv {} {}".format(os.path.join(result_folder_path, "output"), os.environ["executable_folder"]))
