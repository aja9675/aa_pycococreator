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
from PIL import Image
import numpy as np
from pycococreatortools import pycococreatortools


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

def oi_to_coco(image_dir, mask_dir, out_json_filename):

    coco_output = {
        "info": INFO,
        "licenses": LICENSES,
        "categories": CATEGORIES,
        "images": [],
        "annotations": []
    }

    image_id = 1
    segmentation_id = 1
    
    # Process each category/class
    for category in CATEGORIES:
        class_id = category['id']
        class_name = category['name']

        # Only walk categories of interest (this saves a ton of time)
        current_cat_path = os.path.join(image_dir, class_name, 'images')

        # filter for jpeg images
        for root, _, files in os.walk(current_cat_path):
            image_files = filter_for_jpeg(root, files)

            # go through each image
            for image_filename in image_files:
                print("Processing %s" % image_filename)
                image = Image.open(image_filename)

                # filter for associated png annotations
                # Note that this is SLOW if you don't remove unused annotations
                for root, _, files in os.walk(os.path.join(mask_dir, class_name)):
                    annotation_files = filter_for_annotations(root, files, image_filename)

                    # go through each associated annotation
                    for annotation_filename in annotation_files:
                        #print(annotation_filename)

                        category_info = {'id': class_id, 'is_crowd': 'crowd' in image_filename}
                        binary_mask = np.asarray(Image.open(annotation_filename)
                            .convert('1')).astype(np.uint8)
                        
                        annotation_info = pycococreatortools.create_annotation_info(
                            segmentation_id, image_id, category_info, binary_mask,
                            image.size, tolerance=2)

                        if annotation_info is not None:
                            coco_output["annotations"].append(annotation_info)

                        segmentation_id = segmentation_id + 1

                '''
                Quirk here - Using oi_download_dataset to download images puts them in
                a sub dir called images. This is because there's another one next to
                it with the pascal or darknet annotations (which we're not using)
                '''
                image_path = os.path.join(class_name, 'images', os.path.basename(image_filename))
                image_info = pycococreatortools.create_image_info(image_id, image_path, image.size)
                coco_output["images"].append(image_info)

                image_id = image_id + 1

    with open(out_json_filename, 'w') as output_json_file:
        print("Writing COCO json file: %s" % output_json_file)
        json.dump(coco_output, output_json_file)


def main():
    if len(sys.argv) != 4:
        sys.exit("Usage: openimages_to_coco.py <image_dir> <mask_dir> <output_json_filename>")

    image_dir = sys.argv[1]
    mask_dir = sys.argv[2]
    out_json_filename = sys.argv[3]

    oi_to_coco(image_dir, mask_dir, out_json_filename)


if __name__ == "__main__":
    main()
