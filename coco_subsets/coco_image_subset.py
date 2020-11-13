#!/usr/bin/env python3

'''
This script will read a COCO json file containing a subset of classes and do 1 of
2 things: copy them if you already have them on disk, or download them to a new
directory.
This is useful if you only want to move around or download small amounts of data.

usage: coco_image_subset.py copy <input COCO json> <image dir in> <image dir out>
usage: coco_image_subset.py download <input COCO json> <image dir out>

'''

import sys
import os
import argparse
import json
from shutil import copyfile
import urllib.request

def coco_image_copy(args):
	src_img_dir = args.image_in_dir
	dst_img_dir = args.image_out_dir

	if not os.path.exists(dst_img_dir):
		os.makedirs(dst_img_dir)

	# Parse json file
	with open(args.in_json_filename, "r") as infile:
		json_data = json.load(infile)

	# Get the list of images
	images = json_data['images']

	# Copy them to the specified output directory
	print("Copying...")
	for img in images:
		src_img_fname = os.path.join(src_img_dir, img['file_name'])
		dst_img_fname = os.path.join(dst_img_dir, img['file_name'])
		#print("Copying %s -> %s" % (src_img_fname, dst_img_fname))
		copyfile(src_img_fname, dst_img_fname)


def coco_image_download(args):
	dst_img_dir = args.image_out_dir

	if not os.path.exists(dst_img_dir):
		os.makedirs(dst_img_dir)

	# Parse json file
	with open(args.in_json_filename, "r") as infile:
		json_data = json.load(infile)

	# Get the list of images
	images = json_data['images']

	# Probably not the fastest way to do this, but simple
	print("Downloading... (this will take a while)")
	for img in images:
		dst_img_fname = os.path.join(dst_img_dir, img['file_name'])
		#print("Downloading %s to %s" % (img['coco_url'], dst_img_fname))
		urllib.request.urlretrieve(img['coco_url'], dst_img_fname)


def main():
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers()
	
	parser_copy = subparsers.add_parser('copy')
	parser_copy.add_argument('in_json_filename', type=str, help='Input COCO json file')
	parser_copy.add_argument('image_in_dir', type=str, help='Input image directory')
	parser_copy.add_argument('image_out_dir', type=str, help='Output image directory')
	parser_copy.set_defaults(func=coco_image_copy)
	
	parser_download = subparsers.add_parser('download')
	parser_download.add_argument('in_json_filename', type=str, help='Input COCO json file')
	parser_download.add_argument('image_out_dir', type=str, help='Output image directory')
	parser_download.set_defaults(func=coco_image_download)

	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()

__author__ = "Alex Avery"
__license__ = "Beerware"
__email__ = "aja9675@rit.edu"
