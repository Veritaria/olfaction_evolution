import os
import task
import configs
from collections import OrderedDict
import numpy as np
import tools
import train
import standard.analysis as sa
import pickle
import model as network_models
import standard.analysis_activity as analysis_activity
import standard.analysis_pn2kc_training as analysis_training
import standard.analysis_metalearn as analysis_metalearn
import shutil
import matplotlib.pyplot as plt
import standard.analysis_multihead as analysis_multihead
import mamlmetatrain
import matplotlib as mpl

mpl.rcParams['font.size'] = 7
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
mpl.rcParams['font.family'] = 'arial'

def t(experiment, save_path,s=0,e=1000):
    """Train all models locally."""
    for i in range(s, e):
        config = tools.varying_config(experiment, i)
        if config:
            print('[***] Hyper-parameter: %2d' % i)
            config.save_path = os.path.join(save_path, str(i).zfill(6))
            train.train(config)


def st(experiment, save_path, s=0,e=1000):
    """Train all models locally."""
    for i in range(s, e):
        config = tools.varying_config_sequential(experiment, i)
        if config:
            print('[***] Hyper-parameter: %2d' % i)
            config.save_path = os.path.join(save_path, str(i).zfill(6))
            train.train(config)

def temp_meta():
    '''

    '''
    config = configs.MetaConfig()
    config.meta_lr = .001
    config.N_CLASS = 5
    config.save_every_epoch = True
    config.meta_output_dimension = 5
    config.meta_batch_size = 32
    config.meta_num_samples_per_class = 32
    config.meta_print_interval = 250

    config.replicate_orn_with_tiling = True
    config.N_ORN_DUPLICATION = 10
    config.train_kc_bias = True

    config.metatrain_iterations = 20000
    config.pn_norm_pre = 'batch_norm'
    config.kc_norm_pre = 'batch_norm'
    config.sparse_pn2kc = False
    config.train_pn2kc = True

    config.data_dir = './datasets/proto/test'
    config.save_path = './files/test/0'

    hp_ranges = OrderedDict()
    hp_ranges['dummy'] = [True]
    return config, hp_ranges

def temp():
    '''
    Train (with loss) from PN2KC with perfect ORN2PN connectivity, while varying levels of noise + dup
    Results:
        Claw count of 6-7 should be independent of noise and number of ORN duplicates

    '''
    config = configs.FullConfig()
    config.data_dir = './datasets/proto/concentration'
    config.max_epoch = 12

    config.save_every_epoch = True

    config.replicate_orn_with_tiling = True
    config.N_ORN_DUPLICATION = 10
    config.pn_norm_pre = 'batch_norm'
    config.N_PN = 200

    # config.train_pn2kc = True
    # config.sparse_pn2kc = False

    # Ranges of hyperparameters to loop over
    hp_ranges = OrderedDict()
    hp_ranges['dummy'] = [True]
    return config, hp_ranges


path = './files/test'
# mamlmetatrain.train(temp_meta()[0])
# try:
#     shutil.rmtree(path)
# except:
#     pass
# t(temp(), path)

# sa.plot_weights(path, var_name='w_glo', sort_axis=-1, dir_ix=-1)
# sa.plot_weights(path, var_name='w_orn', sort_axis=1, dir_ix=-1)

# path_ = os.path.join(path, '000000')
# glo_in, glo_out, kc_out, results = sa.load_activity(path_)
# b_orns = tools.load_pickle(path, 'b_glo')
# plt.hist(glo_in.flatten(), bins=20)
# plt.show()

w_orns = tools.load_pickle(path, 'w_orn')
w_orn = w_orns[0]
w_orn = tools._reshape_worn(w_orn, 50)
w_orn = w_orn.mean(axis=0)

avg_gs, all_gs = tools.compute_glo_score(w_orn, 50, mode='tile', w_or = None)

thres = .8
all_gs = np.array(all_gs)

gs_sorted =np.sort(all_gs)[::-1]
gs_ix = np.argsort(all_gs)[::-1]

w_orn_thres = w_orn[:, gs_ix[:60]]

w_plot = w_orn_thres
ind_max = np.argmax(w_plot, axis=0)
ind_sort = np.argsort(ind_max)
w_plot = w_plot[:, ind_sort]
plt.imshow(w_plot, cmap='RdBu_r', vmin=-1, vmax=1,
                   interpolation='none')
plt.show()

plt.hist(all_gs, bins=50)
plt.show()


# plt.hist(all_gs, bins=20, range=[0,1])
# sa._easy_save(path, 'hist')

# sa.plot_weights(path, var_name = 'w_or', sort_axis=0, dir_ix=0)
# sa.plot_weights(path, var_name = 'w_combined', dir_ix=0)
# sa.plot_weights(path, var_name = 'w_orn', sort_axis=1, dir_ix=0)
# sa.plot_weights(path, var_name = 'w_glo', dir_ix=0)
#

# analysis_multihead.main1(arg='multi_head')
#
# path = './files/metalearn'

# analysis_training.plot_distribution(path, xrange=.5, log=False)
# analysis_training.plot_distribution(path, xrange=.5, log=True)
# analysis_training.plot_sparsity(path, dynamic_thres=False, thres=.05, visualize=True)
#
# analysis_metalearn.plot_weight_change_vs_meta_update_magnitude(path, 'w_orn', dir_ix=0, xlim=25)
# analysis_metalearn.plot_weight_change_vs_meta_update_magnitude(path, 'w_glo', dir_ix=0, xlim=25)
# plt.show()

# analysis_training.plot_distribution(path)
# analysis_training.plot_pn2kc_claw_stats(path, x_key = 'n_trueclass', dynamic_thres=False)
# analysis_activity.sparseness_activity(path, 'glo_out')
# analysis_activity.sparseness_activity(path, 'kc_out', activity_threshold=.01)
# analysis_activity.plot_mean_activity_sparseness(path, 'kc_out', x_key='n_trueclass', loop_key='kc_dropout_rate')


# sa.plot_weights(path, var_name='model/layer3/kernel:0', dir_ix=0)