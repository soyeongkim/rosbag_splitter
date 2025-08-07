#!/usr/bin/env python

import rosbag
import os
import argparse

def split_bag(input_bag, output_prefix, max_size):
    max_size_bytes = max_size  # max_size in bytes

    bag = rosbag.Bag(input_bag, 'r')
    bag_size = os.path.getsize(input_bag)
    print(f"Original bag size: {bag_size / (1024 * 1024)} MB")

    split_count = 0
    output_bag = None
    output_bag_size = 0

    for topic, msg, t in bag.read_messages():
        if output_bag is None:
            output_bag_path = f"{output_prefix}_{split_count:03d}.bag"
            output_bag = rosbag.Bag(output_bag_path, 'w')
            print(f"Creating new bag: {output_bag_path}")
            output_bag_size = 0

        output_bag.write(topic, msg, t)
        output_bag_size = os.path.getsize(output_bag_path)

        if output_bag_size >= max_size_bytes:
            output_bag.close()
            print(f"Closed bag: {output_bag_path} with size: {output_bag_size / (1024 * 1024)} MB")
            split_count += 1
            output_bag = None

    if output_bag is not None:
        output_bag.close()
        print(f"Closed bag: {output_bag_path} with size: {output_bag_size / (1024 * 1024)} MB")

    bag.close()
    print("Completed splitting bag.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Split a rosbag into multiple smaller bags.")
    parser.add_argument('input_bag', type=str, help='Input rosbag file')
    parser.add_argument('output_prefix', type=str, help='Output prefix for the split bags')
    parser.add_argument('--max_size', type=int, default=1024*1024*500, help='Maximum size for each split bag in bytes (default: 500MB)')

    args = parser.parse_args()
    split_bag(args.input_bag, args.output_prefix, args.max_size)