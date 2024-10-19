import json
import os
import subprocess

def run_invalid_tests(type):
    directory = f'tests/invalid_{type}'
    for root, dirs, files in os.walk(directory):
        for file in files:
            filename = os.path.splitext(file)[0]
            success = False
            try:
                subprocess.run(f'./compiler.py tests/valid/{filename}.c --{type}', shell=True, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                success = True
            except Exception as e:
                print(f"{filename}: Unexpected error occurred: {e}")
            
            if success:
                print(f"Success {filename}: failed {type}")
            else:
                print(f"Failure {filename}: did not fail {type}")

run_invalid_tests('lex')
run_invalid_tests('parse')
run_invalid_tests('validation')

with open('tests/valid/expected_results.json', 'r') as file:
    data = json.load(file)
    for filename, attributes in data.items():
        expected_return_code = attributes['return_code']
        try:
            subprocess.run(f'./compiler.py tests/valid/{filename}.c > {filename}.s', shell=True, check=True)
            subprocess.run(f'gcc {filename}.s -o {filename}', shell=True, check=True)
            result = subprocess.run(f'./{filename}', shell=True)
            actual_return_code = result.returncode
            if actual_return_code == expected_return_code:
                print(f"Success {filename}: return code {actual_return_code}")
            else:
                print(f"Failure {filename}: expected {expected_return_code}, got {actual_return_code}) <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
            subprocess.run(f'rm -f {filename}.s {filename}', shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"{filename}: Command failed with error: {e}")
        except Exception as e:
            print(f"{filename}: Unexpected error occurred: {e}")
