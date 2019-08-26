import unittest
import numpy as np

from eolearn.core import FeatureType, EOPatch
from eolearn.ml_tools import TrainTestSplitTask


class TestTrainSet(unittest.TestCase):

    def test_train_split(self):
        new_name = 'TEST_TRAIN_MASK'

        input_mask_feature = (FeatureType.MASK_TIMELESS, 'TEST')
        input_label_feature = (FeatureType.LABEL_TIMELESS, 'TEST')
        new_mask_feature = (FeatureType.MASK_TIMELESS, new_name)
        new_label_feature = (FeatureType.LABEL_TIMELESS, new_name)

        self.assertRaises(ValueError, TrainTestSplitTask, input_mask_feature, None)
        self.assertRaises(ValueError, TrainTestSplitTask, input_mask_feature, 1.5)
        self.assertRaises(ValueError, TrainTestSplitTask, input_mask_feature, [0.5, 0.3, 0.7])
        self.assertRaises(ValueError, TrainTestSplitTask, input_mask_feature, [0.5, 0.3, 0.7], split_type=None)
        self.assertRaises(ValueError, TrainTestSplitTask, input_mask_feature, [0.5, 0.3, 0.7], split_type='nonsense')

        shape = (1000, 1000, 3)
        size = np.prod(shape)

        data = np.random.randint(10, size=shape, dtype=np.int)

        indices = [(0, 2, 0, 2), (0, 2, 2, 4), (2, 4, 0, 2), (2, 4, 2, 4), (0, 4, 4, 8), (4, 8, 0, 4), (4, 8, 4, 8)]
        for index, (i_1, i_2, j_1, j_2) in enumerate(indices, 1):
            data[i_1:i_2, j_1:j_2, :] = index * 11

        patch = EOPatch()
        patch[input_mask_feature] = data
        patch[input_label_feature] = data.copy().reshape((size,))

        bins = [0.2, 0.5, 0.8]
        expected_unique = set(range(1, len(bins) + 2))

        patch = TrainTestSplitTask((*input_mask_feature, new_name), bins)(patch, seed=1)
        self.assertTrue(set(np.unique(patch[new_mask_feature])) <= expected_unique)

        result_seed1 = np.copy(patch[new_mask_feature])
        unique = (np.unique(result_seed1[i_1:i_2, j_1:j_2, :], return_counts=True) for i_1, i_2, j_1, j_2 in indices)
        expected = [(i_2 - i_1) * (j_2 - j_1) * shape[-1] for i_1, i_2, j_1, j_2 in indices]

        for (unique_values, unique_counts), expected_count in zip(unique, expected):
            self.assertTrue(len(unique_values) == 1)
            self.assertTrue(len(unique_counts) == 1)
            self.assertTrue(unique_counts[0] == expected_count)

        # seed=2 should produce different result than seed=1
        patch = TrainTestSplitTask((*input_mask_feature, new_name), bins)(patch, seed=2)
        result_seed2 = np.copy(patch[new_mask_feature])
        self.assertTrue(set(np.unique(result_seed2)) <= expected_unique)
        self.assertFalse(np.array_equal(result_seed1, result_seed2))

        # test with seed 1 should produce the same result as before
        patch = TrainTestSplitTask((*input_mask_feature, new_name), bins)(patch, seed=1)
        result_seed_equal = patch[new_mask_feature]
        self.assertTrue(set(np.unique(result_seed2)) <= expected_unique)
        self.assertTrue(np.array_equal(result_seed1, result_seed_equal))

        # test LABEL_TIMELESS
        patch = TrainTestSplitTask((*input_label_feature, new_name), bins)(patch)
        result_label = patch[new_label_feature]
        self.assertTrue(set(np.unique(result_label)) <= expected_unique)

        shape = (10, 100, 100, 3)
        size = np.prod(shape)

        # test FeatureType.DATA and no_data_value=2

        bins = [0.2, 0.5, 0.7, 0.8]
        expected_unique = set(range(0, len(bins) + 2))

        data = np.random.randint(10, size=shape)
        patch[(FeatureType.DATA, 'TEST')] = data

        patch = TrainTestSplitTask((FeatureType.DATA, 'TEST', 'BINS'), bins, no_data_value=2)(patch, seed=542)

        self.assertTrue(set(np.unique(patch[(FeatureType.DATA, 'BINS')])) <= expected_unique)
        self.assertTrue(np.all(patch[(FeatureType.DATA, 'BINS')][data == 2] == 0))

    def test_train_split_random(self):
        new_name = 'TEST_TRAIN_MASK'
        input_mask_feature = (FeatureType.MASK_TIMELESS, 'TEST')

        shape = (1000, 1000, 3)

        input_data = np.random.randint(10, size=shape, dtype=np.int)
        patch = EOPatch()
        patch[input_mask_feature] = input_data

        bins = [0.2, 0.6]
        patch = TrainTestSplitTask((*input_mask_feature, new_name), bins, split_type='random')(patch, seed=1)

        output_data = patch[(FeatureType.MASK_TIMELESS, new_name)]
        unique, counts = np.unique(output_data, return_counts=True)
        class_percentages = np.round(counts / input_data.size, 1)
        expected_unique = list(range(1, len(bins) + 2))

        self.assertTrue(np.array_equal(unique, expected_unique))
        self.assertTrue(np.array_equal(class_percentages, [0.2, 0.4, 0.4]))


if __name__ == '__main__':
    unittest.main()
