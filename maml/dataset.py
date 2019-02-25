""" Code for loading data. """
import numpy as np

import task


class DataGenerator(object):
    def __init__(self, batch_size, meta_batch_size):
        train_x, train_y, val_x, val_y = task.load_data(
            'proto', './datasets/proto/standard')

        self.meta_bs = meta_batch_size
        self.batch_size = batch_size

        self.train_x = train_x
        self.train_y = train_y

        # dictionary mapping class to odor indices
        unique_y = np.unique(train_y)
        self.ind_dict = {y: np.where(train_y==y)[0] for y in unique_y}
        self.unique_y = unique_y

    def generate(self):
        """Generate one meta-batch.

        Returns:
            inputs: array, (meta_batch_size, n_samples_per_class, dim_input)
            outputs: array, (meta_batch_size, n_samples_per_class, dim_output)
        """
        # TODO: don't manually set here
        n_sample_per_class = 5
        n_class_per_batch = 5
        n_valence = 3
        assert n_sample_per_class * n_class_per_batch * 2 == self.batch_size

        inputs = np.zeros([self.meta_bs, self.batch_size, self.train_x.shape[-1]])
        outputs = np.zeros([self.meta_bs, self.batch_size, n_valence])

        for i in range(self.meta_bs):
            # randomly select several classes to train on
            classes = np.random.choice(
                self.unique_y, size=n_class_per_batch, replace=False)
            # relabel them
            new_labels = np.random.randint(0, n_valence, len(classes))

            # for each class, sample some odors
            j = 0
            for _ in range(2):  # repeat twice for lossa and lossb
                for c, l in zip(classes, new_labels):
                    ind = np.random.choice(
                        self.ind_dict[c], n_sample_per_class, replace=False)
                    inputs[i, j:j+n_sample_per_class, :] = self.train_x[ind, :]
                    outputs[i, j:j+n_sample_per_class, l] = 1.0  # one-hot
                    j += n_sample_per_class

        return inputs, outputs


import os
import shutil

import tools
from configs import input_ProtoConfig


def _generate_meta_proto():
    num_samples_per_class = 5
    num_class = 5
    data_generator = DataGenerator(
        batch_size=num_samples_per_class * num_class * 2,  # 5 is # classes
        meta_batch_size=1000*32)
    inputs, outputs = data_generator.generate()
    return inputs, outputs


def save_proto(config=None, seed=0, folder_name=None):
    """Save dataset in numpy format."""

    if config is None:
        config = input_ProtoConfig()

    # make and save data
    train_x, train_y = _generate_meta_proto()

    folder_path = os.path.join(config.path, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    else:
        shutil.rmtree(folder_path)
        os.makedirs(folder_path)

    vars = [train_x.astype(np.float32), train_y.astype(np.int32)]
    varnames = ['train_x', 'train_y']
    for result, name in zip(vars, varnames):
        np.save(os.path.join(folder_path, name), result)

    #save parameters
    tools.save_config(config, folder_path)
    return folder_path


def load_data(dataset, data_dir):
    """Load dataset."""
    names = ['train_x', 'train_y']
    return [np.load(os.path.join(data_dir, name + '.npy')) for name in names]


if __name__ == '__main__':
    save_proto(folder_name='meta_proto')