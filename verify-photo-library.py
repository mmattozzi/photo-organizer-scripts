import os
import subprocess
import sys
import shutil
import argparse
import hashlib
import re

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1073741824), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_directory_contents(source_dir, dest_dir, ignore_pattern):
    print(f"Verifying files in {source_dir} are present in {dest_dir}")

    source_files = dict()
    dest_file = dict()
    not_found = []
    files_verified = 0

    ignore_regex = re.compile(ignore_pattern)

    print(f"Scanning source directory: {source_dir}")
    files_processed = 0
    for root, dirs, files in os.walk(source_dir):
        for file in files:            
            if file.startswith('.') or ignore_regex.match(file):
                continue
            source_file_path = os.path.join(root, file)
            file_md5 = calculate_md5(source_file_path)
            source_files[file_md5] = source_file_path
            files_processed += 1
            print(f"\rFiles scanned: {files_processed}", end="")

    print();
    print(f"Found {len(source_files)} unique files in source directory")

    print(f"Scanning destination directory: {dest_dir}")
    files_processed = 0
    for root, dirs, files in os.walk(dest_dir):
        for file in files:
            dest_file_path = os.path.join(root, file)
            file_md5 = calculate_md5(dest_file_path)
            dest_file[file_md5] = dest_file_path
            files_processed += 1
            print(f"\rFiles scanned: {files_processed}", end="")
    
    print();
    print(f"Found {len(dest_file)} unique files in destination directory")

    for file_md5, source_file_path in source_files.items():
        if file_md5 in dest_file:
            files_verified += 1
        else:
            not_found.append(source_file_path)

    print(f"Files not found: {len(not_found)}")
    for file in not_found:
        print(f"File not found: {file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recursively verify that every photo in source_dir is present somewhere in dest_dir.")
    parser.add_argument('-s', '--source_dir', required=True, help="Source directory containing photos")
    parser.add_argument('-d', '--dest_dir', required=True, help="Destination directory to copy organized photos")
    parser.add_argument("-i", "--ignore", help="Ignore source files matching the given pattern")
    
    args = parser.parse_args()
    verify_directory_contents(args.source_dir, args.dest_dir, args.ignore)
