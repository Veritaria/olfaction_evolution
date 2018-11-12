import os
import pickle

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import tools
import tensorflow as tf
from model import SingleLayerModel, FullModel
import task

# mpl.rcParams['font.size'] = 7
dir = os.path.join(os.getcwd(), 'vary_claws')
dirs = [os.path.join(dir, n) for n in os.listdir(dir) if n[:1] == '0']
dirs = dirs[:1]
fig_dir = os.path.join(dir, 'figures')
list_of_legends = list(range(0,15,2)) + [15, 20, 25, 35, 50, 100, 200]
list_of_legends = list_of_legends[:1]
glo_score, val_acc, val_loss, train_loss = \
    tools.plot_summary(dirs, fig_dir, list_of_legends,
                       'nORN = 50, nORN dup = 10, vary nPN per ORN')

# titles = ['glomerular score', 'validation accuracy', 'validation loss', 'training loss']
# data = [glo_score, val_acc, val_loss, train_loss]
# mpl.rcParams['font.size'] = 10
# rc = (2,2)
# fig, ax = plt.subplots(nrows=rc[0], ncols=rc[1], figsize=(10,10))
# fig.suptitle('nORN = 50, nORN dup = 10, vary nPN per ORN')
# for i, (d, t) in enumerate(zip(data, titles)):
#     ax_i = np.unravel_index(i, dims=rc)
#     cur_ax = ax[ax_i]
#     x = parameters
#     y = [x[-1] for x in d]
#     cur_ax.semilogx(parameters, y,  marker='o')
#     cur_ax.set_xlabel('nPN dup')
#     cur_ax.set_ylabel(t)
#     cur_ax.grid(True)
#     cur_ax.spines["right"].set_visible(False)
#     cur_ax.spines["top"].set_visible(False)
#     cur_ax.xaxis.set_ticks_position('bottom')
#     cur_ax.yaxis.set_ticks_position('left')
# plt.savefig(os.path.join(fig_dir, 'summary_last_epoch.pdf'))

worn, born, wpn, bpn = [], [], [], []
for i, d in enumerate(dirs):
    model_dir = os.path.join(d, 'model.pkl')
    with open(model_dir, 'rb') as f:
        var_dict = pickle.load(f)
        w_orn = var_dict['w_orn']
        worn.append(w_orn)
        born.append(var_dict['model/layer1/bias:0'])
        wpn.append(var_dict['model/layer2/kernel:0'])
        bpn.append(var_dict['model/layer2/bias:0'])
        print(tools.compute_glo_score(w_orn)[0])

r,c=2,2
fig, ax = plt.subplots(r,c, figsize=(10,10))
for i, w in enumerate(bpn):
    p_i= np.unravel_index(i, (r,c))
    cur_ax = ax[p_i]
    cur_ax.hist(w.flatten(), bins=50)
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, 'weight_distr.png'))

def helper(ax):
    plt.sca(ax)
    plt.axis('tight', ax= ax)
    for loc in ['bottom', 'top', 'left', 'right']:
        ax.spines[loc].set_visible(False)
    ax.tick_params('both', length=0)
    ax.set_xlabel('To PNs')
    ax.set_ylabel('From ORNs')
    # cb = plt.colorbar()
    # cb.outline.set_linewidth(0.5)
    # cb.set_label('Weight', fontsize=7, labelpad=-10)
    plt.tick_params(axis='both', which='major', labelsize=7)

vlim = .5
fig, ax = plt.subplots(nrows=5, ncols = 2, figsize=(10,10))
for i, cur_w in enumerate(worn):
    ind_max = np.argmax(cur_w, axis=0)
    ind_sort = np.argsort(ind_max)
    cur_w_sorted = cur_w[:, ind_sort]


    ax[i,0].imshow(cur_w, cmap='RdBu_r', vmin = -vlim, vmax=vlim)
    helper(ax[i,0])
    plt.title(str(list_of_legends[i]))
    ax[i,1].imshow(cur_w_sorted, cmap='RdBu_r', vmin=-vlim, vmax=vlim)
    helper(ax[i,1])
    plt.title('Sorted')
plt.tight_layout()
plt.savefig(os.path.join(fig_dir, 'weights.png'))



# # Reload the network and analyze activity
fig, ax = plt.subplots(nrows=3, ncols=2)
for i, d in enumerate(dirs):
    config = tools.load_config(d)

    tf.reset_default_graph()
    CurrentModel = FullModel

    # Build validation model
    train_x, train_y, val_x, val_y = task.load_data(config.dataset, config.data_dir)
    val_x_ph = tf.placeholder(val_x.dtype, val_x.shape)
    val_y_ph = tf.placeholder(val_y.dtype, val_y.shape)
    model = CurrentModel(val_x_ph, val_y_ph, config=config, training=False)

    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True
    with tf.Session(config=tf_config) as sess:
        sess.run(tf.global_variables_initializer())
        sess.run(tf.local_variables_initializer())
        model.load()

        # Validation
        val_loss, val_acc, glo_act, glo_in, glo_in_pre, kc = sess.run(
            [model.loss, model.acc, model.glo, model.glo_in, model.glo_in_pre, model.kc],
            {val_x_ph: val_x, val_y_ph: val_y})

        results = sess.run(tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES))

    ax[i,0].hist(kc.flatten(), bins=100, range =(0, 5))
    ax[i,0].set_title('Activity: ' + str(list_of_legends[i]))
    sparsity = np.count_nonzero(kc >0, axis= 1) / kc.shape[1]
    ax[i,1].hist(sparsity, bins=20, range=(0,1))
    ax[i,1].set_title('Sparseness')

ax[2,0].hist(val_x.flatten(), bins=20, range= (0,5))
ax[2,0].set_title('OR activation')

plt.savefig(os.path.join(fig_dir, 'activity.png'))