#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import sys

# Check command line arguments
if len(sys.argv) < 2:
    print("Usage: python extract_assembly.py <json_file_path> [output_directory]")
    print("Example: python extract_assembly.py untitled.json")
    print("Example: python extract_assembly.py data.json output_folder")
    sys.exit(1)

# Get input file and output directory
json_file = sys.argv[1]
output_dir = sys.argv[2] if len(sys.argv) > 2 else 'assembly_output'

# Check if file exists
if not os.path.exists(json_file):
    print(f"Error: File '{json_file}' does not exist!")
    sys.exit(1)

print(f"Reading file: {json_file}")

# Read JSON file
with open(json_file, 'r') as f:
    data = json.load(f)

# Create output directory
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory: {output_dir}\n")

# Statistics
total_problems = 0
compiled_problems = 0
files_generated = 0

# Iterate through all problems
for key, value in data.items():
    if 'problems' in value:
        problems = value['problems']
        
        for problem_id, problem_data in problems.items():
            total_problems += 1
            
            # Check if compilation failed
            if problem_data.get('compilation_failed') == False:
                compiled_problems += 1
                print(f"Processing problem {problem_id}...")
                
                # Create a separate folder for each problem
                problem_dir = os.path.join(output_dir, f"problem_{problem_id}")
                os.makedirs(problem_dir, exist_ok=True)
                
                # Prepare samples data
                samples_data = {}
                
                # Extract generated_assembly from samples
                if 'samples' in problem_data:
                    for sample_id, sample_data in problem_data['samples'].items():
                        # Save complete sample information (except assembly code, saved separately)
                        sample_info = {}
                        
                        for key, val in sample_data.items():
                            if key != 'generated_assembly':
                                sample_info[key] = val
                        
                        samples_data[sample_id] = sample_info
                        
                        # Extract and save generated_assembly
                        if 'generated_assembly' in sample_data:
                            generated_asm = sample_data['generated_assembly']
                            
                            # Write generated_assembly
                            gen_filename = os.path.join(problem_dir, f"sample_{sample_id}_generated.s")
                            with open(gen_filename, 'w') as f:
                                f.write(generated_asm)
                            print(f"  Generated file: {gen_filename}")
                            files_generated += 1
                            
                            # Record assembly file path in sample_info
                            sample_info['generated_assembly_file'] = f"sample_{sample_id}_generated.s"
                
                # Extract unoptimized_assembly
                if 'unoptimized_assembly' in problem_data:
                    unopt_asm = problem_data['unoptimized_assembly']
                    
                    # Remove possible markdown code block markers
                    if unopt_asm.startswith('```assembly'):
                        unopt_asm = unopt_asm.split('```assembly\n', 1)[1]
                    if unopt_asm.endswith('```'):
                        unopt_asm = unopt_asm.rsplit('```', 1)[0]
                    
                    # Write unoptimized_assembly
                    unopt_filename = os.path.join(problem_dir, "unoptimized.s")
                    with open(unopt_filename, 'w') as f:
                        f.write(unopt_asm)
                    print(f"  Generated file: {unopt_filename}")
                    files_generated += 1
                
                # Save samples information to JSON file
                samples_json = {
                    'problem_id': problem_id,
                    'compilation_failed': problem_data.get('compilation_failed'),
                    'best_sample_id': problem_data.get('best_sample_id'),
                    'overall_correct': problem_data.get('overall_correct'),
                    'best_speedup': problem_data.get('best_speedup'),
                    'unoptimized_assembly_file': 'unoptimized.s',
                    'samples': samples_data
                }
                
                samples_json_file = os.path.join(problem_dir, "samples.json")
                with open(samples_json_file, 'w', encoding='utf-8') as f:
                    json.dump(samples_json, f, indent=2, ensure_ascii=False)
                print(f"  Generated file: {samples_json_file}")
                files_generated += 1
                
                print()

print(f"{'='*60}")
print(f"Complete!")
print(f"Total problems: {total_problems}")
print(f"Successfully compiled problems: {compiled_problems}")
print(f"Total files generated: {files_generated}")
print(f"All files saved to directory: '{output_dir}'")
print(f"{'='*60}")