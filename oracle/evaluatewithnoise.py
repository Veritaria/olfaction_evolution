"""Evaluate a trained network with different amount of noise."""

import sys
import os
import pickle

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import tensorflow as tf

rootpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(rootpath)  # This is hacky, should be fixed

import task
from model import FullModel
import tools

mpl.rcParams['font.size'] = 7


foldername = 'standard_net'
# foldername = 'standard_oracle'

path = os.path.join(rootpath, 'files', foldername)
figpath = os.path.join(rootpath, 'figures', foldername)

# TODO: clean up these paths
path = os.path.join(path, '0')
config = tools.load_config(path)
config.data_dir = rootpath + config.data_dir[1:]
config.save_path = rootpath + config.save_path[1:]

# Load dataset
train_x, train_y, val_x, val_y = task.load_data(
        config.dataset, config.data_dir)

def _evaluate(name, value, model='full'):
    tf.reset_default_graph()
    # Build validation model
    val_x_ph = tf.placeholder(val_x.dtype, val_x.shape)
    val_y_ph = tf.placeholder(val_y.dtype, val_y.shape)
    if name == 'orn_noise_std':
        config.ORN_NOISE_STD = value
    elif name == 'orn_dropout_rate':
        config.orn_dropout = True
        config.orn_dropout_rate = value
    elif name == 'alpha':
        config.oracle_scale = value
    else:
        raise ValueError('Unknown name', str(name))
    if model == 'oracle':
        config.skip_orn2pn = True
        config.skip_pn2kc = True
        config.kc_dropout = False
        config.set_oracle = True
        # Helper model for oracle
        oracle_x_ph = tf.placeholder(val_x.dtype, [config.N_CLASS, val_x.shape[1]])
        oracle_y_ph = tf.placeholder(val_y.dtype, [config.N_CLASS])
        oracle = FullModel(oracle_x_ph, oracle_y_ph, config=config, training=False)
    
    val_model = FullModel(val_x_ph, val_y_ph, config=config, training=False)
    
    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True
    with tf.Session(config=tf_config) as sess:
        sess.run(tf.global_variables_initializer())
        if model == 'oracle':
            oracle.set_oracle_weights()
        else:
            val_model.load()
    
        # Validation
        val_loss, val_acc = sess.run(
            [val_model.loss, val_model.acc],
            {val_x_ph: val_x, val_y_ph: val_y})
    
    return val_loss, val_acc


def evaluate(name, values, model='full'):
    losses = list()
    accs = list()
    for value in values:
        val_loss, val_acc = _evaluate(name, value, model)
        losses.append(val_loss)
        accs.append(val_acc)
    return losses, accs


def evaluate_plot(name):
    if name == 'orn_dropout_rate':
        values = np.linspace(0, 0.3, 10)
    elif name == 'orn_noise_std':
        values = np.linspace(0, 0.3, 10)
    elif name == 'alpha':
        values = np.linspace(0.2, 8, 10)
    losses, accs = evaluate(name, values)
    losses_oracle, accs_oracle = evaluate(name, values, model='oracle')
    
    fig = plt.figure(figsize=(2,2))
    ax = fig.add_axes([0.3, 0.3, 0.6, 0.6])
    ax.plot(values, accs_oracle, '-', color='black', label='oracle')
    ax.plot(values, accs, '-', color='red', label='standard')
    plt.xlabel(name)
    plt.ylabel('Acc')
    plt.legend()
    # plt.savefig('evaluateacc_'+name+'.png', dpi=500)
    
    fig = plt.figure(figsize=(2,2))
    ax = fig.add_axes([0.3, 0.3, 0.6, 0.6])
    ax.plot(values, losses_oracle, '-', color='black', label='oracle')
    ax.plot(values, losses, '-', color='red', label='standard')
    plt.xlabel(name)
    plt.ylabel('Loss')
    plt.legend()
    # plt.savefig('evaluateloss_'+name+'.png', dpi=500)
    

if __name__ == '__main__':
    # evaluate_withnoise()
    # evaluate_plot('orn_dropout_rate')
    # evaluate_plot('orn_noise_std')
    evaluate_plot('alpha')