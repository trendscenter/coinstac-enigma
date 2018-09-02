#import json
#import os
#import sys
#from utils import listRecursive
#
#
#def remote_1(args):
#    input_list = args["input"]
#    site_ids = list(input_list.keys())
#
#    # Getting all the file names
#    file_names = list(input_list[site_ids[0]]["output_contents"].keys())
#    
#    # Getting the header from each file
#    file_headers = [
#        input_list[site_ids[0]]["output_contents"][key][0]
#        for key in file_names
#    ]
#
#    # Associating file names with their headers as a dictionary
#    file_headers = dict(zip(file_names, file_headers))
#
#    # Creating files and concatenating contents from different local sites and
#    # putting then in the file
#    for file in file_names:
#        with open(
#                os.path.join(args["state"]["outputDirectory"], file + '.csv'),
#                'w+') as f:
#            f.writelines(['"site",', file_headers[file]])
#            for site in site_ids:
#                for line in input_list[site]["output_contents"][file][1:]:
#                    f.writelines(['"' + site + '",', line])
#
##    for file in file_names:
##        a = list()
##        for site in site_ids:
##            df = pd.DataFrame(input_list[site]["output_contents"][file])
##            df = df[0].apply(lambda x: pd.Series(x.split(',')))
##            df.columns = df.iloc[0]
##            df.columns = df.columns.str.replace('"', '').str.replace('\n','')
##            df.drop(df.index[0], inplace=True)
##            a.append(df)
##
##        df = pd.concat(a, ignore_index=True)
##
##        file_name = os.path.join(args["state"]["outputDirectory"],
##                                 file + '.csv')
##        df.to_csv(file_name, index=False)
#
#    computation_output = {
#        "output": "Results files sent to remote",
#        "success": True
#    }
#
#    return json.dumps(computation_output)
#


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script includes the remote computations for single-shot ridge
regression with decentralized statistic calculation
"""
import numpy as np
import regression as reg
import sys
import scipy as sp
import ujson as json
from itertools import repeat
from remote_ancillary import get_stats_to_dict
from utils import listRecursive


def remote_1(args):
    """Computes the global beta vector, mean_y_global & dof_global

    Args:
        args (dictionary): {"input": {
                                "beta_vector_local": list/array,
                                "mean_y_local": list/array,
                                "count_local": int,
                                "computation_phase": string
                                },
                            "cache": {}
                            }

    Returns:
        computation_output (json) : {"output": {
                                        "avg_beta_vector": list,
                                        "mean_y_global": ,
                                        "computation_phase":
                                        },
                                    "cache": {
                                        "avg_beta_vector": ,
                                        "mean_y_global": ,
                                        "dof_global":
                                        },
                                    }

    """
    input_list = args["input"]
    userId = list(input_list)[0]
    X_labels = input_list[userId]["X_labels"]
    y_labels = input_list[userId]["y_labels"]

    all_local_stats_dicts = [
        input_list[site]["local_stats_dict"] for site in input_list
    ]

    avg_beta_vector = np.average(
        [
            np.array(input_list[site]["beta_vector_local"])
            for site in input_list
        ],
        axis=0)

    mean_y_local = [input_list[site]["mean_y_local"] for site in input_list]
    count_y_local = [
        np.array(input_list[site]["count_local"]) for site in input_list
    ]
    mean_y_global = np.array(mean_y_local) * np.array(count_y_local)
    mean_y_global = np.sum(
        mean_y_global, axis=0) / np.sum(
            count_y_local, axis=0)

    dof_global = sum(count_y_local) - avg_beta_vector.shape[1]

    output_dict = {
        "avg_beta_vector": avg_beta_vector.tolist(),
        "mean_y_global": mean_y_global.tolist(),
        "computation_phase": 'remote_1'
    }

    cache_dict = {
        "avg_beta_vector": avg_beta_vector.tolist(),
        "mean_y_global": mean_y_global.tolist(),
        "dof_global": dof_global.tolist(),
        "X_labels": X_labels,
        "y_labels": y_labels,
        "local_stats_dict": all_local_stats_dicts
    }

    computation_output = {"output": output_dict, "cache": cache_dict}

    return json.dumps(computation_output)


def remote_2(args):
    """
    Computes the global model fit statistics, r_2_global, ts_global, ps_global

    Args:
        args (dictionary): {"input": {
                                "SSE_local": ,
                                "SST_local": ,
                                "varX_matrix_local": ,
                                "computation_phase":
                                },
                            "cache":{},
                            }

    Returns:
        computation_output (json) : {"output": {
                                        "avg_beta_vector": ,
                                        "beta_vector_local": ,
                                        "r_2_global": ,
                                        "ts_global": ,
                                        "ps_global": ,
                                        "dof_global":
                                        },
                                    "success":
                                    }
    Comments:
        Generate the local fit statistics
            r^2 : goodness of fit/coefficient of determination
                    Given as 1 - (SSE/SST)
                    where   SSE = Sum Squared of Errors
                            SST = Total Sum of Squares
            t   : t-statistic is the coefficient divided by its standard error.
                    Given as beta/std.err(beta)
            p   : two-tailed p-value (The p-value is the probability of
                  seeing a result as extreme as the one you are
                  getting (a t value as large as yours)
                  in a collection of random data in which
                  the variable had no effect.)

    """
    input_list = args["input"]
    cache_list = args["cache"]

    X_labels = args["cache"]["X_labels"]
    y_labels = args["cache"]["y_labels"]

    all_local_stats_dicts = args["cache"]["local_stats_dict"]

    avg_beta_vector = cache_list["avg_beta_vector"]
    dof_global = cache_list["dof_global"]

    SSE_global = sum(
        [np.array(input_list[site]["SSE_local"]) for site in input_list])
    SST_global = sum(
        [np.array(input_list[site]["SST_local"]) for site in input_list])
    varX_matrix_global = sum([
        np.array(input_list[site]["varX_matrix_local"]) for site in input_list
    ])

    r_squared_global = 1 - (SSE_global / SST_global)
    MSE = SSE_global / np.array(dof_global)

    ts_global = []
    ps_global = []

    for i in range(len(MSE)):
#        raise Exception(varX_matrix_global[i])
        var_covar_beta_global = MSE[i] * sp.linalg.inv(varX_matrix_global[i])
        se_beta_global = np.sqrt(var_covar_beta_global.diagonal())
        ts = (avg_beta_vector[i] / se_beta_global)
        ps = reg.t_to_p(ts, dof_global[i])
        ts_global.append(np.nan_to_num(ts, copy=True).tolist())
        ps_global.append(np.nan_to_num(ps, copy=True).tolist())

    # Block of code to print local stats as well
    sites = [site for site in input_list]

    all_local_stats_dicts = list(map(list, zip(*all_local_stats_dicts)))

    a_dict = [{key: value
               for key, value in zip(sites, stats_dict)}
              for stats_dict in all_local_stats_dicts]

    # Block of code to print just global stats
    keys1 = [
        "Coefficient", "R Squared", "t Stat", "P-value", "Degrees of Freedom",
        "covariate_labels"
    ]
    global_dict_list = get_stats_to_dict(keys1, avg_beta_vector,
                                         r_squared_global, ts_global,
                                         ps_global, dof_global,
                                         repeat(X_labels, len(y_labels)))

    # Print Everything
    keys2 = ["ROI", "global_stats", "local_stats"]
    dict_list = get_stats_to_dict(keys2, y_labels, global_dict_list, a_dict)

    output_dict = {"regressions": dict_list}

    computation_output = {"output": output_dict, "success": True}
    
    return json.dumps(computation_output)


if __name__ == '__main__':

    parsed_args = json.loads(sys.stdin.read())
    phase_key = list(listRecursive(parsed_args, 'computation_phase'))

    if "local_1" in phase_key:
        computation_output = remote_1(parsed_args)
        sys.stdout.write(computation_output)
    elif "local_2" in phase_key:
        computation_output = remote_2(parsed_args)
        sys.stdout.write(computation_output)
    else:
        raise ValueError("Error occurred at Remote")
