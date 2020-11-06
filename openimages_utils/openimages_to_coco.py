#!/usr/bin/env python3

'''
This script will generate a COCO json annotation file for a subset
of Google Open Image classes, including segmentation masks!

The images and masks need to be downloaded separately.
I used oi_download_dataset with instructions from
https://towardsdatascience.com/how-to-easily-download-googles-open-images-dataset-for-your-ai-apps-db552a82fc6

Then I manually downloaded the masks from
https://storage.googleapis.com/openimages/web/download.html

And pre-sorted them using my custom python script in this repo:
sort_openimages_annotations.py

Without pre-sorting, this script would take hours to try and match
all of the images to their masks by filename.
As such, arguments image_dir and mask_dir are expected to have
sub directories for each class.

Note that you do need to manually update the CATEGORIES in this file.
I started at 92 because COCO defines up to 91.
'''

import sys
import datetime
import json
import os
import re
import fnmatch
import argparse
import random
from PIL import Image
import numpy as np
from pycococreatortools import pycococreatortools
from copy import deepcopy

# Train, val, test split
DATA_SPLIT = (85,5,10)

INFO = {
    "description": "boxes and chickens",
    "url": "",
    "version": "0.1.0",
    "year": 2020,
    "contributor": "Alex Avery",
    "date_created": datetime.datetime.utcnow().isoformat(' ')
}

LICENSES = [
    {
        "id": 1,
        "name": "Attribution-NonCommercial-ShareAlike License",
        "url": "http://creativecommons.org/licenses/by-nc-sa/2.0/"
    }
]

CATEGORIES = [
    {
        'id': 92,
        'name': 'box',
        'supercategory': 'furniture',
    },
    {
        'id': 93,
        'name': 'chicken',
        'supercategory': 'animal',
    },
]

def filter_for_jpeg(root, files):
    file_types = ['*.jpeg', '*.jpg']
    file_types = r'|'.join([fnmatch.translate(x) for x in file_types])
    files = [os.path.join(root, f) for f in files]
    files = [f for f in files if re.match(file_types, f)]
    
    return files

def filter_for_annotations(root, files, image_filename):
    file_types = ['*.png']
    file_types = r'|'.join([fnmatch.translate(x) for x in file_types])
    basename_no_extension = os.path.splitext(os.path.basename(image_filename))[0]
    file_name_prefix = basename_no_extension + '.*'
    files = [os.path.join(root, f) for f in files]
    files = [f for f in files if re.match(file_types, f)]
    files = [f for f in files if re.match(file_name_prefix, os.path.splitext(os.path.basename(f))[0])]

    return files

# Split the list of files into train, val, test with DATA_SPLIT percentages
def train_val_test_split(file_list):
    num_files = len(file_list)
    random.shuffle(file_list)
    train_split = num_files * DATA_SPLIT[0] // 100
    val_split = train_split + (num_files * DATA_SPLIT[1] // 100)
    train_imgs, val_imgs, test_imgs = np.split(file_list, (train_split, val_split))
    return (train_imgs, val_imgs, test_imgs)

def oi_to_coco(args):
    image_dir = args.image_dir
    mask_dir = args.mask_dir
    out_json_filename = args.out_json_filename

    coco_output_common = {
        "info": INFO,
        "licenses": LICENSES,
        "categories": CATEGORIES,
        "images": [],
        "annotations": []
    }

    # Initialize train, val, test outputs
    coco_outputs = (deepcopy(coco_output_common), deepcopy(coco_output_common), deepcopy(coco_output_common))

    # Each 'dataset' has it's own counter
    image_ids = [1, 1, 1]
    segmentation_ids = [1, 1, 1]

    # Keep track of files with missing annotations
    missing_annotation_files = []

    # Process each category/class
    for category in CATEGORIES:
        class_id = category['id']
        class_name = category['name']

        # Only walk categories of interest (this saves a ton of time)
        current_cat_path = os.path.join(image_dir, class_name, 'images')

        # filter for jpeg images
        for root, _, files in os.walk(current_cat_path):
            image_files = filter_for_jpeg(root, files)

            # Generate the random splits
            train_imgs, val_imgs, test_imgs = train_val_test_split(image_files)

            # For each subset of images
            for i, image_files in enumerate([train_imgs, val_imgs, test_imgs]):
                coco_output = coco_outputs[i]

                # For each jpg image
                for image_filename in image_files:
                    print("Processing %s" % image_filename)
                    image = Image.open(image_filename)

                    # Filter for associated png annotations
                    for root, _, files in os.walk(os.path.join(mask_dir, class_name)):
                        annotation_files = filter_for_annotations(root, files, image_filename)
                        if len(annotation_files) == 0:
                            #print("Missing annotation for %s" % image_filename)
                            missing_annotation_files.append(image_filename)

                        # For each associated annotation
                        for annotation_filename in annotation_files:
                            #print(annotation_filename)

                            category_info = {'id': class_id, 'is_crowd': 'crowd' in image_filename}
                            binary_mask = np.asarray(Image.open(annotation_filename)
                                .convert('1')).astype(np.uint8)

                            # 0 tolerance for maximum accuracy
                            annotation_info = pycococreatortools.create_annotation_info(
                                segmentation_ids[i], image_ids[i], category_info, binary_mask,
                                image.size, tolerance=0)

                            if annotation_info is not None:
                                coco_output["annotations"].append(annotation_info)

                            segmentation_ids[i] += 1

                    '''
                    Quirk here - Using oi_download_dataset to download images puts them in
                    a sub dir called images. This is because there's another one next to
                    it with the pascal or darknet annotations (which we're not using)
                    '''
                    image_path = os.path.join(class_name, 'images', os.path.basename(image_filename))
                    image_info = pycococreatortools.create_image_info(image_ids[i], image_path, image.size)
                    coco_output["images"].append(image_info)

                    image_ids[i] += 1

    if len(missing_annotation_files) != 0:
        print("Warning. Missing annotations for %i files: " % len(missing_annotation_files))
        for f in missing_annotation_files:
            print(f)
        print("Warning. This may skew results\n")

    # Remove '.json' if it exists in the output json filename
    out_json_base = out_json_filename.replace('.json', "")
    # Create our file names for each of our sets
    out_jsons = (out_json_base+'_train.json', out_json_base+'_val.json', out_json_base+'_test.json')

    # Write out the json files
    for i, coco_output in enumerate(coco_outputs):
        with open(out_jsons[i], 'w') as output_json_file:
            print("Writing COCO json file: %s" % out_jsons[i])
            json.dump(coco_output, output_json_file)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('image_dir', metavar='image_dir', type=str, help='Images directory')
    parser.add_argument('mask_dir', metavar='mask_dir', type=str, help='Masks directory')
    parser.add_argument('out_json_filename', metavar='out_json_filename', type=str, \
        help='output json filename (with or without .json)')
    parser.set_defaults(func=oi_to_coco)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
