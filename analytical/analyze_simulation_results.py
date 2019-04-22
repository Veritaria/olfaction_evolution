#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 12:16:04 2019

@author: gryang
"""

import os
import sys
import pickle

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

rootpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(rootpath)

import tools
import standard.analysis_pn2kc_training as analysis_pn2kc_training


mpl.rcParams['font.size'] = 7
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
mpl.rcParams['font.family'] = 'arial'

def get_optimal_K(m):
    fn = 'all_value_m' + str(m)
    with open('../files/analytical/'+fn+'.pkl', "rb") as f:
        all_values = pickle.load(f)
    
    v_name = 'E[norm_dY/norm_Y]'
    
    optimal_Ks = [v['K'][np.argmin(v[v_name])] for v in all_values]
    
    means = [np.mean(np.random.choice(optimal_Ks, size=len(optimal_Ks), replace=True)) for _ in range(1000)]
    
    optimal_K = np.mean(optimal_Ks)
    conf_int = np.percentile(means, [2.5, 97.5])
    K_range = all_values[0]['K']
    return optimal_K, conf_int, K_range


def get_sparsity_from_training(path):
    dirs = [os.path.join(path, n) for n in os.listdir(path)]
    sparsitys = list()
    n_ors = list()
    for i, d in enumerate(dirs):
        config = tools.load_config(d)
        print(config.N_PN)
        sparsity = analysis_pn2kc_training.compute_sparsity(
            d, epoch=-1, dynamic_thres=False, visualize=True)
        
        n_ors.append(config.N_PN)
        sparsitys.append(sparsity[sparsity>0].mean())

    n_ors = np.array(n_ors)
    sparsitys = np.array(sparsitys)

    indsort = np.argsort(n_ors)

    return sparsitys[indsort], n_ors[indsort]


# def main():
dirs = os.listdir('../files/analytical/')
ms = [int(d[len('all_value_m'):-len('.pkl')]) for d in dirs]
ms = np.sort(ms)

# ms = np.array([50, 150, 1000])
optimal_Ks = list()
conf_ints = list()
yerr_low = list()
yerr_high = list()
for m in ms:
    optimal_K, conf_int, K_range = get_optimal_K(m)
    print('m:' + str(m))
    print('optimal K:' + str(optimal_K))
    print('confidence interval: ' + str(conf_int))
    print('K range: ' + str(K_range))
    print('')

    optimal_K = np.log(optimal_K)
    conf_int = np.log(conf_int)

    optimal_Ks.append(optimal_K)
    conf_ints.append(conf_int)
    yerr_low.append(optimal_K-conf_int[0])
    yerr_high.append(conf_int[1]-optimal_K)

x = np.log(ms)
y = optimal_Ks
x_plot = np.linspace(x[0], x[-1], 100)

# model = Ridge()
model = LinearRegression()
model.fit(x[:, np.newaxis], y)
y_plot = model.predict(x_plot[:, np.newaxis])


# Get results from training
path = os.path.join(rootpath, 'files', 'vary_n_orn')
sparsitys, n_ors = get_sparsity_from_training(path)
ind_show = n_ors>=50

x_training = np.log(n_ors[ind_show])
y_training = np.log(sparsitys[ind_show])

fig = plt.figure(figsize=(2.5, 2.))
ax = fig.add_axes([0.2, 0.2, 0.7, 0.7])

ax.scatter(x_training, y_training, marker='+', label='training', s=40,
           color='green')

fit_txt = '$log k = {:0.3f}log m + {:0.3f}$'.format(model.coef_[0], model.intercept_)
ax.plot(x_plot, y_plot, label=fit_txt)

ax.errorbar(x, y, yerr=[yerr_low, yerr_high], fmt='o', label='simulation',
            markersize=3)

ax.set_xlabel('m')
ax.set_ylabel('optimal K')
xticks = np.array([50, 100, 500, 1000])
ax.set_xticks(np.log(xticks))
ax.set_xticklabels([str(t) for t in xticks])
yticks = np.array([10, 100])
ax.set_yticks(np.log(yticks))
ax.set_yticklabels([str(t) for t in yticks])
ax.legend(bbox_to_anchor=(0., 1), loc=2, frameon=False)
fname = 'optimal_k_simulation'
plt.savefig('../figures/analytical/'+fname+'.pdf', transparent=True)
plt.savefig('../figures/analytical/'+fname+'.png')
    
    



