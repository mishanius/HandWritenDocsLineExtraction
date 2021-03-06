import json
import os

from skimage import measure

from estimateBinaryHeight import *
from LineExtraction import *
from PostProcessByMRF import *
from skimage.color import label2rgb
import argparse

from extractors.MultiSkewExtractor import MultiSkewExtractor
from utils.debugble_decorator import DEFAULT_CACHE_PATH, CacheSwitch, PartialImageSwitch


def extract_lines(image_path, mask_path=None):
    # Load a color image in grayscale
    I = cv2.imread(image_path, 0)
    bin = cv2.bitwise_not(I)
    charRange = estimateBinaryHeight(bin, 0)
    if mask_path is None:
        LineMask = LineExtraction(I, charRange)
        cv2.imwrite("images/mask.png", LineMask * 255)
        LineMask = np.logical_not(LineMask)
        LineMask = LineMask.astype(np.uint)
    else:
        LineMask = cv2.imread(mask_path, 0)
        LineMask = cv2.bitwise_not(LineMask)

    L, num = bwlabel(bin)
    result, Labels, newLines = post_process_by_mfr(L, num, LineMask, charRange)
    r = label2rgb(result, bg_color=(0, 0, 0))
    cv2.imshow('image', r)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    result_dict = {}
    for prop in regionprops(result.astype(np.int32).copy(order='C')):
        contours = measure.find_contours(prop.convex_image * 255, 1)
        result_dict[prop.label] = []
        for n, contour in enumerate(contours):
            contour[:] = contour[:] + prop.bbox[:2]
            result_dict[prop.label].append(contour.tolist())

    json_result = json.dumps(result_dict)
    with open('straight_line_result.json', 'w') as f:
        json.dump(json_result, f)
    print("file straight_line_result.json is ready!")


def multi_skew_line_extraction(image_path, mask_path=None):
    angles = np.arange(0, 155, 25)
    multi_extractor = MultiSkewExtractor(image_path)
    result = multi_extractor.extract_lines(angles)
    with open('multi_skew_result.json', 'w') as f:
        json.dump(result, f)
    print("file multi_skew_result.json is ready!")


def prepare_cache(with_cache=False, reset_cache=False):
    CacheSwitch().value = with_cache
    path_to_cache = DEFAULT_CACHE_PATH
    if reset_cache:
        for filename in os.listdir(path_to_cache):
            file_path = os.path.join(path_to_cache, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))


extractors = {
    "MultiSkew": multi_skew_line_extraction,
    "ExtractLines": extract_lines
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='extract lines from doc')
    parser.add_argument('--image_path', type=str, default='binary_hetero_doc.png', required=True,
                        help='path to the doc image')
    parser.add_argument('--mask_path', type=str, default=None, required=False,
                        help='path for already created mask for example images/image_mask.png')
    parser.add_argument('--extractor', type=str, default=None, required=True,
                        help='name of extraction algorithm MultiSkew or ExtractLines')
    parser.add_argument('--no_cache', action='store_false')
    parser.add_argument('--reset_cache', action='store_true')
    parser.add_argument('--with_partial_images', action='store_true')
    args = parser.parse_args()
    PartialImageSwitch().value = args.with_partial_images
    prepare_cache(args.no_cache, args.reset_cache)
    extractors[args.extractor](args.image_path, args.mask_path)
