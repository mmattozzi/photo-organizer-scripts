import os
import subprocess
import sys
import shutil
import argparse

def process_directory_contents(source_dir, dest_dir):
    print(f"Copying files from {source_dir} to {dest_dir}")

    not_copied_no_date = []
    not_copied_exists = []
    files_copied = 0

    for file in os.listdir(source_dir):
        file_path = os.path.join(source_dir, file)
        if os.path.isfile(file_path):
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
                dest_year_month_day_dir = os.path.join(dest_year_month_dir, day)
                if not os.path.exists(dest_year_month_day_dir):
                    os.makedirs(dest_year_month_day_dir)
                    print(f"Created directory: {dest_year_month_day_dir}")
                
                dest_file_path = os.path.join(dest_year_month_day_dir, file)
                print(f"Copying {file_path} to {dest_file_path}")

                if not os.path.exists(dest_file_path):
                    shutil.copy2(file_path, dest_file_path)
                    files_copied += 1
                else:
                    print(f"File already exists: {dest_file_path}")
                    not_copied_exists.append(file_path)
            else:
                print(f"Could not determine date for {file_path}")
                not_copied_no_date.append(file_path)

    print(f"Files copied: {files_copied}")

    if len(not_copied_no_date) > 0:
        print("Files that could not be copied due to unknown date:")
        for file_path in not_copied_no_date:
            print(file_path)
        
    if len(not_copied_exists) > 0:
        print("Files that could not be copied due to existing file of the same name:")
        for file_path in not_copied_exists:
            print(file_path)

def process_subdirs(source_dir, dest_dir, level):
    level -= 1
    for file in os.listdir(source_dir):
        full_path = os.path.join(source_dir, file)
        if level == 0 and os.path.isdir(full_path):
            print(f"Processing directory: {full_path}")
            process_directory_contents(full_path, dest_dir)
        elif os.path.isdir(full_path):
            level -= 1
            process_subdirs(full_path, dest_dir, level)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize photos by date.")
    parser.add_argument('-s', '--source_dir', required=True, help="Source directory containing photos")
    parser.add_argument('-d', '--dest_dir', required=True, help="Destination directory to copy organized photos")
    parser.add_argument('-l', '--level', type=int, default=0, help="Depth of directory structure to organize photos, 0 to process contents of given directory")

    args = parser.parse_args()
    if (args.level == 0):
        process_directory_contents(args.source_dir, args.dest_dir)
    else:
        process_subdirs(args.source_dir, args.dest_dir, args.level)