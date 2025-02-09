import os
import subprocess
import sys
import shutil
import argparse
import hashlib

FILE_TYPES = [ "jpg", "JPG", "jpeg", "JPEG", "mp4", "MP4", "mov", "MOV" ]

def calculate_64bit_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    full_digest = sha256_hash.digest()
    lower_64_bits = int.from_bytes(full_digest[-8:], byteorder='big')
    return f"{lower_64_bits:016x}"

def process_directory_contents(source_dir, dest_dir, move):
    print(f"Copying files from {source_dir} to {dest_dir}")

    not_copied_no_date = []
    not_copied_exists = []
    files_copied = 0

    for file in os.listdir(source_dir):
        file_path = os.path.join(source_dir, file)
        if os.path.isfile(file_path):
            
            if file.startswith('.'):
                continue
            if not any(file.endswith(file_type) for file_type in FILE_TYPES):
                continue

            print(f"Found file: {file_path}")
            exiftool_result = subprocess.run(['exiftool', '-CreateDate', '-FileModifyDate', file_path], capture_output=True, text=True)
            
            # Extract the date from the output
            exif_create_date = None
            file_modify_date = None
            for line in exiftool_result.stdout.split("\n"):
                if "Create Date" in line:
                    exif_create_date = line.split(": ")[1]
                if "File Modification Date/Time" in line:
                    file_modify_date = line.split(": ")[1]

            best_date = exif_create_date or file_modify_date
            print(f"Best date: {best_date}")

            if best_date:
                date_parts = best_date.split()[0].split(':')
                year, month, day = date_parts[0], date_parts[1], date_parts[2]
                print(f"Year: {year}, Month: {month}, Day: {day}")

                dest_year_dir = os.path.join(dest_dir, year)
                if not os.path.exists(dest_year_dir):
                    os.makedirs(dest_year_dir)
                    print(f"Created directory: {dest_year_dir}")
                dest_year_month_dir = os.path.join(dest_year_dir, month)
                if not os.path.exists(dest_year_month_dir):
                    os.makedirs(dest_year_month_dir)
                    print(f"Created directory: {dest_year_month_dir}")
                
                dest_file_path = os.path.join(dest_year_month_dir, file)
                action = "Moving" if move else "Copying"
                print(f"{action} {file_path} to {dest_file_path}")

                if not os.path.exists(dest_file_path):
                    if move:
                        shutil.move(file_path, dest_file_path)
                    else:
                        shutil.copy(file_path, dest_file_path)
                    files_copied += 1
                else:
                    print(f"File already exists: {dest_file_path}")
                    hash64 = calculate_64bit_hash(file_path)
                    dest_hash64 = calculate_64bit_hash(dest_file_path)
                    if not hash64 == dest_hash64:
                        print(f"File already exists but is different: {dest_file_path}")
                        file_name, file_ext = os.path.splitext(file)
                        dest_file_path = os.path.join(dest_year_month_dir, f"{file_name}_{hash64}{file_ext}")
                        print(f"Saving to: {dest_file_path}")
                        if move:
                            shutil.move(file_path, dest_file_path)
                        else:
                            shutil.copy(file_path, dest_file_path)
                        files_copied += 1

                    not_copied_exists.append(file_path)
            else:
                print(f"Could not determine date for {file_path}")
                not_copied_no_date.append(file_path)

    print(f"Files created: {files_copied}")

    if len(not_copied_no_date) > 0:
        print("Files that could not be copied due to unknown date:")
        for file_path in not_copied_no_date:
            print(file_path)
        
    if len(not_copied_exists) > 0:
        print("Files that were not copied due to existing file of the same name with same hash:")
        for file_path in not_copied_exists:
            print(file_path)

    return files_copied

def process_subdirs(source_dir, dest_dir, move=False):
    process_directory_contents(source_dir, dest_dir, move)

    files_copied = 0

    for file in os.listdir(source_dir):
        if file.startswith('.') or "Thumbs" == file:
            continue
        full_path = os.path.join(source_dir, file)
        if os.path.isdir(full_path):
            print(f"Processing directory: {full_path}")
            files_copied += process_directory_contents(full_path, dest_dir, move)        
            process_subdirs(full_path, dest_dir, move)

    return files_copied

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize photos by date.")
    parser.add_argument('-s', '--source_dir', required=True, help="Source directory containing photos")
    parser.add_argument('-d', '--dest_dir', required=True, help="Destination directory to copy organized photos")
    parser.add_argument('-r', '--recurse', action='store_true', help="Recurse into subdirectories")
    parser.add_argument('-m', '--move', action='store_true', help="Move files instead of copying them")

    args = parser.parse_args()
    files_copied = 0
    if not args.recurse:
        files_copied = process_directory_contents(args.source_dir, args.dest_dir, args.move)
    else:
        files_copied = process_subdirs(args.source_dir, args.dest_dir, args.move)

    print(f"Total files copied: {files_copied}")