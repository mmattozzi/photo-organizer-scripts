import os
import subprocess
import sys
import shutil
import argparse
import hashlib
import re
import cv2

FILE_TYPES = [ "jpg", "JPG", "jpeg", "JPEG", "mp4", "MP4", "mov", "MOV" ]

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1073741824), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def detect_faces(image_path):
    global face_cascade

    try:
        face_cascade
    except NameError:
        # Load the Haar Cascade model
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read image.")
        return

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Return true if faces are detected
    return len(faces) > 0


def verify_directory_contents(source_dir, dest_dir, ignore_pattern, faces_only):
    print(f"Verifying files in {source_dir} are present in {dest_dir}")

    source_files = dict()
    dest_file = dict()
    not_found = []
    files_verified = 0

    ignore_regex = None
    if ignore_pattern:
        ignore_regex = re.compile(ignore_pattern)

    print(f"Scanning source directory: {source_dir}")
    files_processed = 0
    files_with_faces = 0
    for root, dirs, files in os.walk(source_dir):
        for file in files:            
            if file.startswith('.'):
                continue
            source_file_path = os.path.join(root, file)
            if any(file.endswith(file_type) for file_type in FILE_TYPES):
                if ignore_pattern and ignore_regex.search(source_file_path):
                    continue
                if faces_only and detect_faces(source_file_path):
                    file_md5 = calculate_md5(source_file_path)
                    source_files[file_md5] = source_file_path
                    files_with_faces += 1
            
            files_processed += 1
            if faces_only:
                print(f"\rFiles scanned: {files_processed} - Found {files_with_faces} files with faces", end="")
            else:
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
            for dest_md5, dest_file_path in dest_file.items():
                dest_file_name = os.path.basename(dest_file_path)
                if dest_file_name == os.path.basename(source_file_path):
                    print(f"File {source_file_path} not found in destination directory, but a file with the same name was found: {dest_file_path}")
                    break

    print(f"Files not found: {len(not_found)}")
    for file in not_found:
        print(f"File not found: {file}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recursively verify that every photo in source_dir is present somewhere in dest_dir.")
    parser.add_argument('-s', '--source_dir', required=True, help="Source directory containing photos")
    parser.add_argument('-d', '--dest_dir', required=True, help="Destination directory to copy organized photos")
    parser.add_argument("-i", "--ignore", help="Ignore source files matching the given pattern")
    parser.add_argument("--faces-only", action="store_true", help="Only check for files that are likely to contain faces")
    
    args = parser.parse_args()
    verify_directory_contents(args.source_dir, args.dest_dir, args.ignore, args.faces_only)
