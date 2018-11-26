import os
import csv
import tensorflow as tf
import numpy as np
from mgc.audioset import (
    ontology,
    load_music_genre_subset_as_numpy,
    load_music_genre_subset_as_tensor,
)


DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), './data/'))
TF_RECORDS_DIR = os.path.join(DATA_DIR, 'bal_train')
MUSIC_GENRE_CLASSES = ontology.find_children('Music genre')
MUSIC_GENRE_CLASSES_BY_ID = {}
for c in MUSIC_GENRE_CLASSES:
    MUSIC_GENRE_CLASSES_BY_ID[c['id']] = c


def test_load_music_genre_subset_as_numpy_match_csv_samples():
    '''
    This test check if we are reading tfrecords correctly
    in numpy format
    by comparing the read data with the Audioset's csv format.
    This test uses the balanced dataset
    '''
    read_audioset_balanced_csv()
    csv_samples = read_audioset_balanced_csv()
    ids, X, y = load_music_genre_subset_as_numpy(TF_RECORDS_DIR)

    for i in range(len(ids)):
        video_id = ids[i].decode('utf-8')
        csv_sample = csv_samples[video_id]
        csv_label_ids = csv_sample['positive_labels']
        assert_classes_in_csv_sample_match_tf_sample(csv_label_ids, y[i])


def test_load_music_genre_subset_as_tensor_match_csv_samples():
    '''
    This test check if we are reading tfrecords correctly
    in TF tensor format
    by comparing the read data with the Audioset's csv format.
    This test uses the balanced dataset
    '''
    read_audioset_balanced_csv()
    csv_samples = read_audioset_balanced_csv()
    ids, X, y = load_music_genre_subset_as_tensor(TF_RECORDS_DIR, repeat=False)
    ids, X, y = tensor_to_numpy(ids, X, y)

    for i in range(len(ids)):
        video_id = ids[i].decode('utf-8')
        csv_sample = csv_samples[video_id]
        csv_label_ids = csv_sample['positive_labels']
        assert_classes_in_csv_sample_match_tf_sample(csv_label_ids, y[i])


def tensor_to_numpy(ids_tensor, X_tensor, y_tensor):
    with tf.Session() as sess:
        ids = np.array([])
        X = np.ndarray((0, 10, 128))
        # there are 53 music genre classes
        y = np.ndarray((0, 53))
        while True:
            try:
                (ids_batch, features_batch, labels_batch) = sess.run(
                    (ids_tensor, X_tensor, y_tensor)
                )
                ids = np.concatenate([ids, ids_batch])
                X = np.concatenate([X, features_batch], axis=0)
                y = np.concatenate([y, labels_batch], axis=0)
            except tf.errors.OutOfRangeError:
                break

    return ids, X, y


def assert_classes_in_csv_sample_match_tf_sample(csv_label_ids, y_row):
    # Find active classes: Get ids of columns containing 1's
    classes_indexes = np.argwhere(y_row)[0].tolist()
    classes_ids = [MUSIC_GENRE_CLASSES[i]['id'] for i in classes_indexes]
    assert set(classes_ids).issubset(csv_label_ids)


def read_audioset_balanced_csv():
    filepath = os.path.join(DATA_DIR, 'balanced_train_segments.csv')
    dataset = {}
    with open(filepath) as csvfile:
        reader = csv.reader(csvfile, skipinitialspace=True)
        # skip first 3 lines
        next(reader)
        next(reader)
        next(reader)
        for row in reader:
            sample = {
                'YTID': row[0],
                'start_seconds': row[1],
                'end_seconds': row[2],
                'positive_labels': row[3].split(',')
            }
            dataset[sample['YTID']] = sample

        return dataset
