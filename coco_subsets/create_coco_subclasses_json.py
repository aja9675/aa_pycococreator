#!/usr/bin/env python3

'''
This script will read a COCO json file (such as instances_val2017.json)
and create a new json file that contains a subset of the original classes.

usage: create_coco_subclasses_json.py <input COCO json> <output COCO json> [classes]
ex: create_coco_subclasses_json.py instances_val2017.json person_car_subset_val2017.json person car

'''

import sys
import argparse
import json


def create_coco_subset_json(args):
	category_subset_names = args.classes
	# subset of categorys
	category_subset = [] # json objects
	# ids for each category
	category_ids = [] # list of integers
	# subset of annotations
	annotation_subset = [] # json objects
	# subset of image ids found in annotation_subset
	# Note we don't need multiple instances of the same image
	img_ids = set() # set of integers
	# subset of images
	images_subset = [] # json objects

	# Parse json file
	with open(args.in_json_filename, "r") as infile:
		json_data = json.load(infile)

	images = json_data['images']
	annotations = json_data['annotations']
	categories = json_data['categories']

	# First check that all class parameters are valid
	category_subset_names = [cat.lower() for cat in category_subset_names]
	for cat_name in category_subset_names:
		found_match = False
		for cat in categories:
			if cat['name'] == cat_name:
				found_match = True
		if not found_match:
			sys.exit("Error. '%s' class not found" % cat_name)

	# First get the subset of categories that we want
	for cat in categories:
		if cat['name'] in category_subset_names:
			category_subset.append(cat)
			category_ids.append(cat['id'])

	# Now find the annotations that are associated with those classes
	for ann in annotations:
		if ann['category_id'] in category_ids:
			annotation_subset.append(ann)
			img_ids.add(ann['image_id'])

	# Now find each image that had a matching annotation
	for img in images:
		if img['id'] in img_ids:
			images_subset.append(img)

	# Re-use our existing json object and just replace with our subsets
	json_data['images'] = images_subset
	json_data['annotations'] = annotation_subset
	json_data['categories'] = category_subset

	with open(args.out_json_filename, 'w') as outfile:
		# Add separators if you want to actually look at the file
		#json.dump(json_data, outfile, indent=2, separators=(',', ': '))
		json.dump(json_data, outfile)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('in_json_filename', type=str, help='Input COCO json file')
	parser.add_argument('out_json_filename', type=str, help='Output COCO json file')
	parser.add_argument('classes', nargs='+', type=str, help='List of COCO classes you want to extract')

	parser.set_defaults(func=create_coco_subset_json)
	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()

__author__ = "Alex Avery"
__license__ = "Beerware"
__email__ = "aja9675@rit.edu"
