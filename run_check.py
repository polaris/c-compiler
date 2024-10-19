import json
import os
import subprocess

def print_filenames_without_extension(directory, data):
    for root, dirs, files in os.walk(directory):
        for file in files:
            filename_without_extension = os.path.splitext(file)[0]
            if filename_without_extension not in data:
                if filename_without_extension == 'expected_results':
                    continue
                subprocess.run(f'gcc {directory}/{filename_without_extension}.c -o {filename_without_extension}', shell=True, check=True)
                result = subprocess.run(f'./{filename_without_extension}', shell=True)
                actual_return_code = result.returncode

                print(f'  "{filename_without_extension}": {{ "return_code": {actual_return_code} }},')
                
                subprocess.run(f'rm -f {filename_without_extension}', shell=True, check=True)


with open('tests/valid/expected_results.json', 'r') as file:
    data = json.load(file)
    directory_path = 'tests/valid'
    print_filenames_without_extension(directory_path, data)
