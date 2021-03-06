from skimage.measure import regionprops
import numpy as np
from sklearn.neighbors import NearestNeighbors
from scipy.ndimage import label as bwlabel


def label_broken_lines(lines2split, broken_lines, labeled_lines_num):
    connectivity_struct = np.ones((3,3))
    lines2split, num_of_lines = bwlabel(lines2split,connectivity_struct)
    y = concatenate_pixel_lists(regionprops(lines2split))

    broken_lines, num_of_lines = bwlabel(broken_lines, connectivity_struct)
    x = concatenate_pixel_lists(regionprops(broken_lines))
    one_nn = NearestNeighbors(1).fit(x[:, 0:2])
    dist, indexes_of_neighboors = one_nn.kneighbors(y[:, 0:2])
    res = np.zeros(lines2split.shape)
    for i in range(len(y)):
        res[int(y[i, 0]), int(y[i, 1])] = int(x[indexes_of_neighboors[i], 2] + labeled_lines_num)

    broken_lines_num = int(max(np.amax(res), labeled_lines_num))
    return res, broken_lines_num


def concatenate_pixel_lists(props):
    total_size = 0
    for prop in props:
        total_size = total_size + len(prop.coords)

    res = np.zeros((total_size, 3))
    sz = 0
    for index, prop in enumerate(props):
        temp = prop.coords
        res[sz:sz + len(temp), 0:2] = temp
        res[sz:sz + len(temp), 2] = index+1
        sz = sz + len(temp)
    return res
