import json
import os
import subprocess

def run_invalid_tests(test_type):
    directory = f'tests/invalid_{test_type}'
    success_count = 0
    failure_count = 0
    total_count = 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            total_count += 1
            filename = os.path.splitext(file)[0]
            success = False
            try:
                subprocess.run(
                    f'./compiler.py tests/valid/{filename}.c --{test_type}',
                    shell=True,
                    check=True,
                    stderr=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError:
                success = True
            except Exception as e:
                print(f"{filename}: Unexpected error occurred: {e}")
            
            if success:
                print(f"Success {filename}: failed {test_type}")
                success_count += 1
            else:
                print(f"Failure {filename}: did not fail {test_type}")
                failure_count += 1

    print(f"\nInvalid {test_type} tests summary:")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    print(f"Total: {total_count}\n")
    return success_count, failure_count, total_count

def run_valid_tests():
    with open('tests/valid/expected_results.json', 'r') as file:
        data = json.load(file)
        success_count = 0
        failure_count = 0
        total_count = 0

        for filename, attributes in data.items():
            total_count += 1
            expected_return_code = attributes['return_code']

            try:
                subprocess.run(f'./compiler.py tests/valid/{filename}.c > {filename}.s', shell=True, check=True)
                subprocess.run(f'gcc {filename}.s -o {filename}', shell=True, check=True)
                result = subprocess.run(f'./{filename}', shell=True)
                actual_return_code = result.returncode
                if actual_return_code == expected_return_code:
                    print(f"Success {filename}: return code {actual_return_code}")
                    success_count += 1
                else:
                    print(f"Failure {filename}: expected {expected_return_code}, got {actual_return_code} <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
                    failure_count += 1
            except subprocess.CalledProcessError as e:
                print(f"{filename}: Command failed with error: {e}")
                failure_count += 1
            except Exception as e:
                print(f"{filename}: Unexpected error occurred: {e}")
                failure_count += 1
            finally:
                subprocess.run(f'rm -f {filename}.s {filename}', shell=True, check=True)

        print(f"\nValid tests summary:")
        print(f"Successful: {success_count}")
        print(f"Failed: {failure_count}")
        print(f"Total: {total_count}\n")
        return success_count, failure_count, total_count

if __name__ == "__main__":
    total_success = 0
    total_failure = 0
    total_tests = 0

    for test_type in ['lex', 'parse', 'validation']:
        success, failure, total = run_invalid_tests(test_type)
        total_success += success
        total_failure += failure
        total_tests += total

    success, failure, total = run_valid_tests()
    total_success += success
    total_failure += failure
    total_tests += total

    print("\nOverall Test Summary:")
    print(f"Successful: {total_success}")
    print(f"Failed: {total_failure}")
    print(f"Total: {total_tests}")
