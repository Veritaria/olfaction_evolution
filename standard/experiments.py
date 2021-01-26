"""Experiments and corresponding analysis.

Each experiment is described by a function that returns a list of configurations
function name is the experiment name

Analysis functions by convention are named
def name_analysis()
"""

from collections import OrderedDict
import copy
import numpy as np

from configs import FullConfig, MetaConfig, RNNConfig, SingleLayerConfig
from tools import vary_config
import tools
import settings

try:
    import standard.analysis as sa
    import standard.analysis_pn2kc_training as analysis_pn2kc_training
    import standard.analysis_pn2kc_random as analysis_pn2kc_random
    import standard.analysis_orn2pn as analysis_orn2pn
    import standard.analysis_rnn as analysis_rnn
    import standard.analysis_activity as analysis_activity
    import standard.analysis_multihead as analysis_multihead
except ImportError as e:
    print(e)


use_torch = settings.use_torch


def standard():
    """Standard training setting"""
    config = FullConfig()
    config.save_every_epoch = True
    config.kc_dropout_rate = 0.

    config.initial_pn2kc = 4. / config.N_PN  # explicitly set for clarity
    config.kc_prune_weak_weights = True
    config.kc_prune_threshold = 1. / config.N_PN

    config_ranges = OrderedDict()
    config_ranges['dummy'] = [True]

    configs = vary_config(config, config_ranges, mode='combinatorial')
    return configs


def standard_analysis(path):
    modeldirs = tools.get_modeldirs(path)
    dir = modeldirs[0]

    # accuracy
    sa.plot_progress(modeldirs, ykeys=['val_acc', 'glo_score', 'K_smart'])

    # weight matrices
    sa.plot_weights(dir)

    if not use_torch:
        # This currently doesn't work for pytorch
        try:
            analysis_orn2pn.correlation_across_epochs(path, arg='weight')
            analysis_orn2pn.correlation_across_epochs(path, arg='activity')
        except ModuleNotFoundError:
            pass

    # pn-kc
    analysis_pn2kc_training.plot_distribution(dir, xrange=1.5)
    analysis_pn2kc_training.plot_sparsity(dir, epoch=-1)

    # TODO: Broken now
    # analysis_pn2kc_training.plot_log_distribution_movie(dir)

    # pn-kc random
    # analysis_pn2kc_random.plot_cosine_similarity(
    #     dir, shuffle_arg='preserve', log=False)
    # analysis_pn2kc_random.plot_distribution(dir)
    # analysis_pn2kc_random.claw_distribution(dir, shuffle_arg='random')
    # analysis_pn2kc_random.pair_distribution(dir, shuffle_arg='preserve')

    # Activity
    analysis_activity.distribution_activity(path, ['glo', 'kc'])
    analysis_activity.sparseness_activity(path, ['glo', 'kc'])


def receptor():
    """Standard training setting with full network including receptors."""
    config = FullConfig()

    config.receptor_layer = True
    config.ORN_NOISE_STD = 0.1
    config.kc_dropout_rate = 0.
    config.lr = 1e-4  # For receptor, this is the default LR
    config.pn_norm_pre = None
    config.kc_norm_pre = 'batch_norm'

    config.initial_pn2kc = 4. / config.N_PN  # explicitly set for clarity
    config.kc_prune_weak_weights = True
    config.kc_prune_threshold = 1. / config.N_PN

    config_ranges = OrderedDict()
    config_ranges['lr'] = [5e-4, 2e-4, 1e-4, 5e-5, 2e-5]
    config_ranges['ORN_NOISE_STD'] = [0, 0.1, 0.2]
    config_ranges['pn_norm_pre'] = [None, 'batch_norm']
    config_ranges['kc_norm_pre'] = [None, 'batch_norm']

    configs = vary_config(config, config_ranges, mode='control')
    return configs


def receptor_analysis(path):
    # This is the only combination of normalization that works, not sure why
    default = {'ORN_NOISE_STD': 0.1, 'kc_norm_pre': 'batch_norm',
               'pn_norm_pre': None, 'lr': 1e-4}

    # Analyze all
    ykeys = ['val_acc', 'glo_score', 'K_smart']

    for xkey in default.keys():
        select_dict = copy.deepcopy(default)
        select_dict.pop(xkey)
        modeldirs = tools.get_modeldirs(path, select_dict=select_dict)
        sa.plot_results(modeldirs, xkey=xkey, ykey=ykeys,
                        show_ylabel=(xkey == 'lr'))
        sa.plot_progress(modeldirs, ykeys=ykeys, legend_key=xkey)
        sa.plot_xy(modeldirs, xkey='lin_bins', ykey='lin_hist',
                   legend_key=xkey)

    # Analyze default network
    modeldir = tools.get_modeldirs(path, select_dict=default)[0]
    # accuracy
    sa.plot_progress(modeldir, ykeys=['val_acc', 'K_smart'])

    # weight matrices
    sa.plot_weights(modeldir)
    sa.plot_weights(modeldir, zoomin=True)

    # pn-kc
    analysis_pn2kc_training.plot_distribution(modeldir, xrange=0.5)
    analysis_pn2kc_training.plot_sparsity(modeldir, epoch=-1)
    # analysis_pn2kc_training.plot_log_distribution_movie(dir)

    # Compute glo-score metric for OR-ORN connectivity
    print('ORN score for OR-ORN connectivity',
          tools.compute_glo_score(tools.load_pickle(modeldir)['w_or'], 50)[0])


def singlelayer():
    """Standard single layer training setting"""
    config = SingleLayerConfig()
    config.max_epoch = 30

    config_ranges = OrderedDict()
    config_ranges['dummy'] = [True]

    configs = vary_config(config, config_ranges, mode='combinatorial')
    return configs


def scaling_analysis(path):
    del path
    name_or_paths = ['./files/vary_or']
    name_or_paths += ['./files/meta_vary_or']
    analysis_pn2kc_training.plot_all_K(
        ['./files/vary_or'],
        name_or_paths + ['data'],
        name_or_paths + ['dim', 'data'])


def rnn():
    config = RNNConfig()
    config.max_epoch = 100
    config.rec_dropout = True
    config.rec_dropout_rate = 0.5
    config.rec_norm_pre = None
    config.diagonal = True
    config.ORN_NOISE_STD = 0.0

    config_ranges = OrderedDict()
    config_ranges['TIME_STEPS'] = [2]
    config_ranges['rec_dropout_rate'] = [0, 0.1, 0.2, 0.3, 0.4, 0.5]

    configs = vary_config(config, config_ranges, mode='combinatorial')
    return configs


def rnn_tf():
    # TODO: To be removed in the future
    config = FullConfig()
    config.data_dir = './datasets/proto/standard'
    config.max_epoch = 30
    config.model = 'rnn'

    config.NEURONS = 2500
    config.BATCH_NORM = False

    config.dropout = True
    config.dropout_rate = 0
    config.DIAGONAL = True

    config_ranges = OrderedDict()
    config_ranges['TIME_STEPS'] = [1, 2, 3]
    config_ranges['replicate_orn_with_tiling'] = [False, True, True]
    config_ranges['N_ORN_DUPLICATION'] = [1, 10, 10]

    configs = vary_config(config, config_ranges, mode='sequential')
    return configs


def rnn_analysis(path):
    # sa.plot_progress(path, ykeys=['val_acc'], legend_key='TIME_STEPS')
    # analysis_rnn.analyze_t0(path, dir_ix=0)
    analysis_rnn.analyze_t_greater(path, dir_ix=1)
    # analysis_rnn.analyze_t_greater(path, dir_ix=2)


def rnn_relabel():
    config = RNNConfig()
    config.data_dir = './datasets/proto/relabel_200_100'
    config.max_epoch = 100
    config.rec_dropout = True
    config.rec_dropout_rate = 0.0
    config.rec_norm_pre = None
    config.diagonal = True
    config.ORN_NOISE_STD = 0.0

    config_ranges = OrderedDict()
    config_ranges['TIME_STEPS'] = [1, 2, 3]
    config_ranges['diagonal'] = [True, False]
    config_ranges['lr'] = [1e-3, 5e-4, 2e-4, 1e-4]
    config_ranges['data_dir'] = [
        './datasets/proto/relabel_100_100',
        './datasets/proto/relabel_200_100',
        './datasets/proto/relabel_500_100']

    configs = vary_config(config, config_ranges, mode='combinatorial')
    return configs


def rnn_relabel_analysis(path):
    select_dict = {'diagonal': True}
    sa.plot_progress(path, ykeys=['val_acc'], legend_key='lr', select_dict=select_dict)
    sa.plot_results(path, xkey='lr', ykey='val_acc', select_dict=select_dict)


def rnn_relabel_prune():
    config = RNNConfig()
    config.data_dir = './datasets/proto/relabel_200_100'
    config.max_epoch = 100
    config.rec_dropout = False
    config.rec_dropout_rate = 0.0
    config.rec_norm_pre = None
    config.diagonal = False
    config.ORN_NOISE_STD = 0.0

    config.prune_weak_weights = True
    config.prune_threshold = 1. / config.NEURONS
    config.initial_rec = 4./config.NEURONS

    config_ranges = OrderedDict()
    config_ranges['TIME_STEPS'] = [1, 2, 3]
    config_ranges['lr'] = [1e-3, 5e-4, 2e-4, 1e-4]

    configs = vary_config(config, config_ranges, mode='combinatorial')
    return configs


def rnn_relabel_prune_analysis(path):
    for t in [1, 2, 3]:
        select_dict = {'TIME_STEPS': t}
        sa.plot_progress(path, ykeys=['val_acc'], legend_key='lr', select_dict=select_dict)
        sa.plot_results(path, xkey='lr', ykey='val_acc', select_dict=select_dict)
    sa.plot_results(path, xkey='lr', ykey='val_acc', loop_key='TIME_STEPS')


def vary_kc_activity_fixed():
    #TODO: use this one or the other one below
    '''

    :param argTest:
    :return:
    '''

    config = FullConfig()
    config.data_dir = './datasets/proto/standard'
    config.max_epoch = 30

    config.direct_glo = True
    config.pn_norm_pre = 'batch_norm'
    config.save_every_epoch = True

    config.train_pn2kc = False

    # config.train_pn2kc = True
    # config.sparse_pn2kc = False
    # config.initial_pn2kc = .1
    # config.extra_layer = True
    # config.extra_layer_neurons = 200

    config_ranges = OrderedDict()
    config_ranges['kc_dropout_rate'] = [0, .5]
    x = [100, 200, 500, 1000, 2000, 5000]
    config_ranges['data_dir'] = ['./datasets/proto/' + str(i) + '_100' for i in x]
    configs = vary_config(config, config_ranges, mode='combinatorial')

    return configs


def vary_kc_activity_trainable():
    ''''''
    config = FullConfig()
    config.data_dir = './datasets/proto/standard'
    config.max_epoch = 30

    config.direct_glo = True
    config.pn_norm_pre = 'batch_norm'
    config.save_every_epoch = True

    # config.extra_layer = True
    # config.extra_layer_neurons = 200

    config_ranges = OrderedDict()
    config_ranges['kc_dropout_rate'] = [0, .5]
    x = [100, 200, 500, 1000, 2000, 5000]
    config_ranges['data_dir'] = ['./datasets/proto/' + str(i) + '_100' for i in x]

    configs = vary_config(config, config_ranges, mode='combinatorial')
    return configs


def pn_norm():
    '''
    Assesses the effect of PN normalization on glo score and performance
    '''
    config = FullConfig()
    config.max_epoch = 10

    config.skip_orn2pn = True
    config.N_ORN_DUPLICATION = 1

    config.kc_dropout_rate = 0.

    config.initial_pn2kc = 4. / config.N_PN  # explicitly set for clarity
    config.kc_prune_weak_weights = False
    config.kc_prune_threshold = 1. / config.N_PN

    # Ranges of hyperparameters to loop over
    config_ranges = OrderedDict()
    spreads = [0, 0.3, 0.6, 0.9]
    dataset_base = './datasets/proto/concentration_mask_row'
    datasets = [dataset_base + '_{:0.1f}'.format(s) for s in spreads]
    # config_ranges['kc_prune_weak_weights'] = [True, False]
    config_ranges['data_dir'] = datasets
    # config_ranges['pn_norm_pre'] = [None, 'batch_norm', 'olsen',
    #                                 'fixed_activity']
    config_ranges['pn_norm_pre'] = [None, 'olsen', 'fixed_activity']

    configs = vary_config(config, config_ranges, mode='combinatorial')
    return configs


def pn_norm_relabel():
    configs = pn_norm()
    new_configs = list()
    for c in configs:
        c.data_dir = c.data_dir.replace('_mask_row', '_relabel_mask_row')
        new_configs.append(c)
    return new_configs


def pn_norm_analysis(path):
    select_dict = {'kc_prune_weak_weights': False}
    modeldirs = tools.get_modeldirs(path, select_dict=select_dict)
    ykeys = ['val_acc', 'K_smart']
    sa.plot_results(modeldirs, xkey='spread_orn_activity', ykey=ykeys,
                    loop_key='pn_norm_pre')
    select_dict = {'spread_orn_activity': 0.6, 'kc_prune_weak_weights': False}
    modeldirs = tools.get_modeldirs(path, select_dict=select_dict)
    sa.plot_progress(modeldirs, ykeys=ykeys, legend_key='pn_norm_pre')
    sa.plot_xy(path, xkey='lin_bins', ykey='lin_hist',
               legend_key='pn_norm_pre')

    # import tools
    # rmax = tools.load_pickles(path, 'model/layer1/r_max:0')
    # rho = tools.load_pickles(path, 'model/layer1/rho:0')
    # m = tools.load_pickles(path, 'model/layer1/m:0')
    # print(rmax)
    # print(rho)
    # print(m)
    #
    # analysis_activity.image_activity(path, 'glo')
    # analysis_activity.image_activity(path, 'kc')
    # analysis_activity.distribution_activity(path, 'glo')
    # analysis_activity.distribution_activity(path, 'kc')
    # analysis_activity.sparseness_activity(path, 'kc')


def pn_norm_relabel_analysis(path):
    pn_norm_analysis(path)


def vary_or(n_pn=50):
    """Training networks with different number of PNs and vary hyperparams.

    Latest default.
    """
    config = FullConfig()
    config.max_epoch = 100
    config.save_log_only = True

    config.N_PN = n_pn
    config.data_dir = './datasets/proto/relabel_orn' + str(n_pn)
    config.kc_dropout_rate = 0.

    config.N_ORN_DUPLICATION = 1
    config.skip_orn2pn = True  # Skip ORN-to-PN

    config.initial_pn2kc = 4. / config.N_PN  # explicitly set for clarity
    config.kc_prune_weak_weights = True
    config.kc_prune_threshold = 1. / n_pn

    config.N_KC = min(40000, n_pn**2)

    config_ranges = OrderedDict()
    config_ranges['lr'] = [1e-3, 5e-4, 2e-4, 1e-4]
    configs = vary_config(config, config_ranges, mode='combinatorial')
    return configs


def vary_or_prune(n_pn=50):
    """Training networks with different number of PNs and vary hyperparams."""
    config = FullConfig()
    config.max_epoch = 100
    config.save_log_only = True

    config.N_PN = n_pn
    config.data_dir = './datasets/proto/orn'+str(n_pn)

    config.N_ORN_DUPLICATION = 1
    config.skip_orn2pn = True  # Skip ORN-to-PN

    config.initial_pn2kc = 4. / config.N_PN  # explicitly set for clarity
    config.kc_prune_weak_weights = True
    config.kc_prune_threshold = 1./n_pn

    config.N_KC = min(40000, n_pn**2)

    config_ranges = OrderedDict()
    config_ranges['lr'] = [1e-3, 5e-4, 2e-4, 1e-4]
    configs = vary_config(config, config_ranges, mode='combinatorial')
    return configs


def vary_or_prune_fixnkc(n_pn=50):
    new_configs = []
    for config in vary_or_prune(n_pn=n_pn):
        config.N_KC = 2500
        new_configs.append(config)
    return new_configs


def vary_or_prune_relabel(n_pn=50):
    new_configs = []
    for config in vary_or_prune(n_pn=n_pn):
        config.data_dir = './datasets/proto/relabel_orn' + str(n_pn)
        new_configs.append(config)
    return new_configs


def vary_or_prune_relabel_corr(n_pn=50):
    new_configs = []
    for config in vary_or_prune(n_pn=n_pn):
        config.data_dir = './datasets/proto/relabel_corr_orn' + str(n_pn)
        new_configs.append(config)
    return new_configs


def vary_or_analysis(path, acc_min=0.):
    def _vary_or_analysis(path, legend_key):
        modeldirs = tools.get_modeldirs(path)
        sa.plot_progress(modeldirs, ykeys=['val_acc', 'K_smart'],
                         legend_key=legend_key)
        sa.plot_results(modeldirs, xkey=legend_key,
                        ykey=['val_acc', 'K_smart'])
        sa.plot_xy(modeldirs, xkey='lin_bins', ykey='lin_hist',
                   legend_key=legend_key)

    import glob
    _path = path + '_pn'  # folders named XX_pn50, XX_pn100, ..
    folders = glob.glob(_path + '*')
    n_orns = sorted([int(folder.split(_path)[-1]) for folder in folders])
    for n_orn in n_orns:
        _vary_or_analysis(_path + str(n_orn), legend_key='lr')

    analysis_pn2kc_training.plot_all_K(path)


def vary_or_prune_fixnkc_analysis(path, n_pn=None):
    vary_or_analysis(path, n_pn)


def vary_or_prune_relabel_analysis(path, n_pn=None):
    vary_or_analysis(path, n_pn, acc_min=0.5)


def vary_or_prune_relabel_corr_analysis(path, n_pn=None):
    vary_or_analysis(path, n_pn, acc_min=0.5)


def multihead():
    """Multi-task classification."""
    config = FullConfig()
    config.max_epoch = 100
    config.N_ORN_DUPLICATION = 1
    config.data_dir = './datasets/proto/multihead'

    config_ranges = OrderedDict()
    config_ranges['pn_norm_pre'] = [None, 'batch_norm']
    config_ranges['lr'] = [1e-3, 5e-4, 2e-4, 1e-4]
    config_ranges['initial_pn2kc'] = [0.05, 0.1]

    configs = vary_config(config, config_ranges, mode='combinatorial')
    return configs


def multihead_relabel():
    """Multi-task with relabel datset."""
    new_configs = list()
    for cfg in multihead():
        cfg.data_dir = './datasets/proto/multihead_relabel'
        new_configs.append(cfg)
    return new_configs


def multihead_relabel_prune():
    """Multi-task with relabel datset. Latest standard."""
    new_configs = list()
    for config in multihead():
        config.data_dir = './datasets/proto/multihead_relabel'
        n_pn = 50
        config.initial_pn2kc = 4. / config.N_PN  # explicitly set for clarity
        config.kc_prune_weak_weights = True
        config.kc_prune_threshold = 1. / n_pn

        new_configs.append(config)
    return new_configs


def multihead_analysis(path, acc_min=0.85):

    select_dict = {'pn_norm_pre': 'batch_norm', 'initial_pn2kc': 0.1}
    modeldirs = tools.get_modeldirs(path, select_dict=select_dict)
    sa.plot_progress(modeldirs, ykeys=['val_acc', 'glo_score', 'K_smart'],
                     legend_key='lr')
    sa.plot_xy(modeldirs,
               xkey='lin_bins', ykey='lin_hist', legend_key='lr')
    # this acc is average of two heads
    # modeldirs = tools.get_modeldirs(path, acc_min=acc_min)
    # modeldirs = tools.filter_modeldirs(
    #     modeldirs, exclude_badkc=True)
    #
    # # TODO: This no longer works robustly, because there are more than 2
    # #  clusters
    # analysis_multihead.analyze_many_networks_lesion(modeldirs)
    #
    select_dict = {'lr': 5e-4, 'pn_norm_pre': 'batch_norm'}
    modeldirs = tools.get_modeldirs(path, acc_min=acc_min,
                                    select_dict=select_dict)
    modeldirs = tools.filter_modeldirs(
        modeldirs, exclude_badpeak=True)
    dir = modeldirs[0]
    sa.plot_progress(modeldirs, ykeys=['val_acc', 'glo_score'])
    sa.plot_weights(dir)
    analysis_activity.distribution_activity(dir, ['glo', 'kc'])
    analysis_activity.sparseness_activity(dir, ['glo', 'kc'])
    analysis_multihead.analyze_example_network(dir, fix_cluster=3)


def multihead_relabel_analysis(path):
    multihead_analysis(path, acc_min=0.65)


def multihead_relabel_prune_analysis(path):
    acc_min = 0.65
    select_dict = {}
    modeldirs = tools.get_modeldirs(path, select_dict=select_dict)
    sa.plot_progress(modeldirs, ykeys=['val_acc', 'glo_score', 'K_smart'],
                     legend_key='lr')
    sa.plot_xy(modeldirs,
               xkey='lin_bins', ykey='lin_hist', legend_key='lr')

    # this acc is average of two heads
    modeldirs = tools.get_modeldirs(path, acc_min=acc_min)
    modeldirs = tools.filter_modeldirs(
        modeldirs, exclude_badkc=True, exclude_badpeak=True)
    analysis_multihead.analyze_many_networks_lesion(modeldirs)

    select_dict = {'lr': 5e-4, 'pn_norm_pre': 'batch_norm'}
    modeldirs = tools.get_modeldirs(path, acc_min=acc_min,
                                    select_dict=select_dict)
    modeldirs = tools.filter_modeldirs(
        modeldirs, exclude_badkc=True, exclude_badpeak=True)
    dir = modeldirs[0]
    sa.plot_progress(modeldirs, ykeys=['val_acc', 'glo_score'])
    sa.plot_weights(dir)
    analysis_activity.distribution_activity(dir, ['glo', 'kc'])
    analysis_activity.sparseness_activity(dir, ['glo', 'kc'])
    analysis_multihead.analyze_example_network(dir)

