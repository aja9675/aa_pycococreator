#!/usr/bin/env python3

'''
This script will sort Google Open Images segmentation masks (.pngs)
into directories by class name

Segmentation masks can be downloaded here:
https://storage.googleapis.com/openimages/web/download.html
They come in sets, which you have to download all of. But then
this script will walk all of these and pull out each class.

Note that 'class-descriptions.csv' is required to map the
class ids to class names
'''

import sys
import os
import csv
from glob import glob
from shutil import move

def parse_class_descriptions(file_path):
	reader = csv.reader(open(file_path, 'r'))
	d = {}
	for row in reader:
		k, v = row
		# Format class id as it is in the annotation file names
		k = k.replace('/', '', 2)
		# Convert to lowercase for consistency with other tools
		v = v.lower()
		d[k] = v

	return d

def sort_classes(class_descriptions_fn, input_dir, out_dir_base):
	class_dict = parse_class_descriptions(class_descriptions_fn)

	mask_file_paths = [y for x in os.walk(input_dir) for y in glob(os.path.join(x[0], '*.png'))]

	# For every annotation, move it to it's class dir
	for mask_file_path in mask_file_paths:
		file_name = os.path.basename(mask_file_path)

		# Careful when splitting, some class id's contain underscores
		class_id = file_name.split('_', 1)[1].rsplit('_', 1)[0]

		# Get actual class name from class id (ex. /m/025dyy -> Box)
		class_name = class_dict[class_id]

		# Create class directory if it doesn't exist
		output_dir = os.path.join(out_dir_base, class_name)
		if not os.path.exists(output_dir):
			print("Creating %s" % output_dir)
			os.makedirs(output_dir)

		# Move the file to it's new class directory
		move(mask_file_path, output_dir)


def main():

	if len(sys.argv) != 4:
		sys.exit("Usage: sort_openimages_annotations.py <class-descriptions.csv> <input_dir> <output_dir>")

	class_descriptions_fn = sys.argv[1]
	input_dir = sys.argv[2]
	output_dir = sys.argv[3]

	sort_classes(class_descriptions_fn, input_dir, output_dir)

if __name__ == "__main__":
	main()
