import os
from collections import defaultdict
import pickle
import json
import time

import numpy as np
import tensorflow as tf

import task
from model import SingleLayerModel, FullModel, NormalizedMLP
from configs import FullConfig, SingleLayerConfig
import tools


def make_input(x, y, batch_size):
    data = tf.data.Dataset.from_tensor_slices((x, y))
    data = data.shuffle(int(1E6))
    # Making sure the shape is fully defined
    try:
        data = data.batch(tf.cast(batch_size, tf.int64), drop_remainder=True)
    except TypeError:
        data = data.apply(tf.contrib.data.batch_and_drop_remainder(batch_size))
    # data = data.batch(tf.cast(batch_size, tf.int64))
    data = data.repeat()
    train_iter = data.make_initializable_iterator()
    next_element = train_iter.get_next()
    return train_iter, next_element


def train(config, reload=False, verbose=False):
    tf.reset_default_graph()

    # Merge model config with config from dataset
    dataset_config = tools.load_config(config.data_dir)
    dataset_config.update(config)
    config = dataset_config
    print(config)

    if not os.path.exists(config.save_path):
        os.makedirs(config.save_path)
    # Save config
    tools.save_config(config, save_path=config.save_path)

    # Load dataset
    train_x, train_y, val_x, val_y = task.load_data(config.dataset, config.data_dir)

    batch_size = config.batch_size
    n_batch = train_x.shape[0] // batch_size

    if config.model == 'full':
        CurrentModel = FullModel
    elif config.model == 'singlelayer':
        CurrentModel = SingleLayerModel
    elif config.model == 'normmlp':
        CurrentModel = NormalizedMLP
    else:
        raise ValueError('Unknown model type ' + str(config.model))

    # Build train model
    train_x_ph = tf.placeholder(train_x.dtype, train_x.shape)
    train_y_ph = tf.placeholder(train_y.dtype, train_y.shape)
    train_iter, next_element = make_input(train_x_ph, train_y_ph, batch_size)
    model = CurrentModel(next_element[0], next_element[1], config=config)

    # Build validation model
    val_x_ph = tf.placeholder(val_x.dtype, val_x.shape)
    val_y_ph = tf.placeholder(val_y.dtype, val_y.shape)
    val_model = CurrentModel(val_x_ph, val_y_ph, config=config, training=False)

    # Make custom logger
    log = defaultdict(list)
    log_name = os.path.join(config.save_path, 'log.pkl')  # Consider json instead of pickle

    glo_score_mode = 'tile' if config.replicate_orn_with_tiling else 'repeat'

    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True
    with tf.Session(config=tf_config) as sess:
        sess.run(tf.global_variables_initializer())
        sess.run(tf.local_variables_initializer())
        sess.run(train_iter.initializer, feed_dict={train_x_ph: train_x,
                                                    train_y_ph: train_y})
        if reload:
            model.load()
            with open(log_name, 'rb') as f:
                log = pickle.load(f)

        loss = 0
        acc = 0
        total_time, start_time = 0, time.time()
        # weight_over_time = []
        for ep in range(config.max_epoch):
            if verbose:
                # Validation
                val_loss, val_acc, val_acc2, glo_in_pre_mean, glo_in_mean = sess.run(
                    [val_model.loss, val_model.acc, val_model.acc2,
                     val_model.glo_in_pre_mean, val_model.glo_in_mean],
                    {val_x_ph: val_x, val_y_ph: val_y})
            else:
                # Validation
                val_loss, val_acc, val_acc2 = sess.run(
                    [val_model.loss, val_model.acc, val_model.acc2],
                    {val_x_ph: val_x, val_y_ph: val_y})
            val_acc = val_acc[1]
            val_acc2 = val_acc2[1]
            print('[*] Epoch {:d}'.format(ep))
            print('Train/Validation loss {:0.2f}/{:0.2f}'.format(loss, val_loss))
            print('Train/Validation accuracy {:0.2f}/{:0.2f}'.format(acc, val_acc))
            if verbose:
                print('GLO_IN_PRE_MEAN ' + str(np.mean(glo_in_pre_mean)))
                print('GLO_IN_MEAN ' + str(np.mean(glo_in_mean)))

            log['epoch'].append(ep)
            log['train_loss'].append(loss)
            log['train_acc'].append(acc)
            log['val_loss'].append(val_loss)
            log['val_acc'].append(val_acc)

            if config.label_type == 'multi_head_sparse':
                print('Validation accuracy head 2 {:0.2f}'.format(val_acc2))
                log['val_acc2'].append(val_acc2)

            if config.model == 'full':
                if config.receptor_layer:
                    w_or = sess.run(model.w_or)
                    or_glo_score, _ = tools.compute_glo_score(
                        w_or, config.N_ORN, glo_score_mode)
                    print('OR receptor glo score ' + str(or_glo_score))
                    log['or_glo_score'].append(or_glo_score)

                    w_orn = sess.run(model.w_orn)
                    glo_score, _ = tools.compute_glo_score(
                        w_orn, config.N_ORN, 'matrix', w_or)
                    print('Glo score ' + str(glo_score))
                    log['glo_score'].append(glo_score)

                    w_combined = np.matmul(w_or, w_orn)
                    combined_glo_score, _ = tools.compute_glo_score(
                        w_combined, config.N_ORN, glo_score_mode)
                    print('Combined glo score ' + str(combined_glo_score))
                    log['combined_glo_score'].append(combined_glo_score)

                else:
                    w_orn = sess.run(model.w_orn)
                    glo_score, _ = tools.compute_glo_score(
                        w_orn, config.N_ORN, glo_score_mode)
                    log['glo_score'].append(glo_score)
                    print('Glo score ' + str(glo_score))

                    sim_score, _ = tools.compute_sim_score(
                        w_orn, config.N_ORN, glo_score_mode)
                    log['sim_score'].append(sim_score)
                    print('Sim score ' + str(sim_score))

                    # w_glo = sess.run(model.w_glo)
                    # glo_score_w_glo, _ = tools.compute_glo_score(w_glo)
                    # log['glo_score_w_glo'].append(glo_score_w_glo, config.N_ORN)

            # Compute condition number
            # w_glo = sess.run(model.w_glo)
            # w_orn2kc = np.dot(w_orn, w_glo)
            # cond = np.linalg.cond(w_orn2kc)
            # log['cond'].append(cond)
            # print('Condition number '+ str(cond))

            if ep > 0:
                time_spent = time.time() - start_time
                total_time += time_spent
                print('Time taken {:0.1f}s'.format(total_time))
                print('Examples/second {:d}'.format(int(train_x.shape[0]/time_spent)))
            start_time = time.time()

            with open(log_name, 'wb') as f:
                pickle.dump(log, f, protocol=pickle.HIGHEST_PROTOCOL)

            if 'target_acc' in dir(config) and config.target_acc is not None:
                if val_acc > config.target_acc:
                    print('Training reached target accuracy {:0.2f}>{:0.2f}'.format(
                        val_acc, config.target_acc
                    ))
                    break

            try:
                if config.save_every_epoch:
                    model.save_pickle(ep)
                # Train
                for b in range(n_batch-1):
                    _ = sess.run(model.train_op)
                # Compute training loss and accuracy using last batch
                # loss, acc, _ = sess.run([model.loss, model.acc, model.train_op])
                loss, acc, _, gnorm, glo_in_mean = sess.run(
                    [model.loss, model.acc, model.train_op,
                     model.gradient_norm, model.glo_in_mean])
                if verbose:
                    print('GRADIENT NORM')
                    print(model.var_names)
                    print(gnorm)
                    # print('GLO_IN_MEAN')
                    # print(glo_in_mean)
                acc = acc[1]


            except KeyboardInterrupt:
                print('Training interrupted by users')
                break

            # for b in range(n_batch):
            #     w_orn = sess.run(model.w_orn)
            #     weight_over_time.append(w_orn)
            #     with open('./weight_over_time.pickle', 'wb') as handle:
            #         pickle.dump(weight_over_time, handle,
            #                     protocol=pickle.HIGHEST_PROTOCOL)
        print('Training finished')
        model.save_pickle()
        model.save()


if __name__ == '__main__':
    experiment = 'robert'
    # experiment = 'peter'
    if experiment == 'peter':
        config = SingleLayerConfig()

    elif experiment == 'robert':
        config = FullConfig()
        config.dataset = 'proto'
        config.data_dir = './datasets/proto/_50_generalization_onehot'
        config.model = 'full'
        config.save_path = './files/peter'
    else:
        raise NotImplementedError

    train(config)


