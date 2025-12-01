#!/usr/bin/env python3
"""
Calculate similarity between sample_0_generated.s and unoptimized.s for each problem
and update samples.json files

Usage:
    python calculate_similarity.py [options]

Examples:
    # Use default settings (current directory, problem_ prefix)
    python calculate_similarity.py
    
    # Specify directory
    python calculate_similarity.py --base-dir /path/to/projects
    
    # Custom directory prefix and filenames
    python calculate_similarity.py --prefix task_ --generated optimized.s --unoptimized original.s
    
    # Calculate similarity only, don't update JSON
    python calculate_similarity.py --no-update
"""

import os
import json
import re
import argparse
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Tuple, Optional

def normalize_assembly_line(line: str) -> str:
    """Normalize assembly code line by removing comments and extra whitespace"""
    # Remove trailing comments
    if '#' in line:
        line = line[:line.index('#')]
    if ';' in line:
        line = line[:line.index(';')]
    # Strip leading/trailing whitespace
    line = line.strip()
    return line

def extract_instructions(lines: List[str]) -> List[str]:
    """Extract instruction sequence (removing labels, comments, empty lines)"""
    instructions = []
    for line in lines:
        normalized = normalize_assembly_line(line)
        if not normalized:
            continue
        # Skip label lines (starting with . or letter, ending with :)
        if re.match(r'^[.a-zA-Z_][a-zA-Z0-9_.]*:\s*$', normalized):
            continue
        # Skip directives (starting with . but not a label)
        if normalized.startswith('.'):
            continue
        # Extract instruction (first word)
        parts = normalized.split()
        if parts:
            instructions.append(parts[0])
    return instructions

def calculate_similarity(file1_path: str, file2_path: str) -> Dict[str, float]:
    """Calculate similarity between two assembly files"""
    try:
        with open(file1_path, 'r', encoding='utf-8') as f:
            lines1 = f.readlines()
        with open(file2_path, 'r', encoding='utf-8') as f:
            lines2 = f.readlines()
    except FileNotFoundError:
        return {
            'line_similarity': 0.0,
            'instruction_similarity': 0.0,
            'overall_similarity': 0.0
        }
    
    # 1. Line-level similarity (after removing empty lines and comments)
    normalized_lines1 = [normalize_assembly_line(line) for line in lines1]
    normalized_lines2 = [normalize_assembly_line(line) for line in lines2]
    normalized_lines1 = [line for line in normalized_lines1 if line]
    normalized_lines2 = [line for line in normalized_lines2 if line]
    
    line_similarity = SequenceMatcher(None, normalized_lines1, normalized_lines2).ratio()
    
    # 2. Instruction sequence similarity
    instructions1 = extract_instructions(lines1)
    instructions2 = extract_instructions(lines2)
    instruction_similarity = SequenceMatcher(None, instructions1, instructions2).ratio() if instructions1 or instructions2 else 0.0
    
    # 3. Overall similarity (weighted average)
    overall_similarity = (line_similarity * 0.6 + instruction_similarity * 0.4)
    
    return {
        'line_similarity': round(line_similarity, 4),
        'instruction_similarity': round(instruction_similarity, 4),
        'overall_similarity': round(overall_similarity, 4)
    }

def process_all_problems(
    base_dir: str,
    dir_prefix: str = 'problem_',
    generated_file: str = 'sample_0_generated.s',
    unoptimized_file: str = 'unoptimized.s',
    samples_json: str = 'samples.json',
    sample_key: str = '0',
    update_json: bool = True
) -> List[Dict]:
    """
    Process all problem directories
    
    Parameters:
        base_dir: Base directory path
        dir_prefix: Directory name prefix (default: 'problem_')
        generated_file: Generated assembly filename (default: 'sample_0_generated.s')
        unoptimized_file: Unoptimized assembly filename (default: 'unoptimized.s')
        samples_json: JSON filename (default: 'samples.json')
        sample_key: Sample key in JSON (default: '0')
        update_json: Whether to update JSON file (default: True)
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        print(f"Error: Directory does not exist: {base_dir}")
        return []
    
    results = []
    
    # Find all directories matching the prefix
    problem_dirs = sorted([d for d in base_path.iterdir() 
                          if d.is_dir() and d.name.startswith(dir_prefix)])
    
    if not problem_dirs:
        print(f"Warning: No directories starting with '{dir_prefix}' found in {base_dir}")
        return []
    
    print(f"Found {len(problem_dirs)} directories\n")
    
    for problem_dir in problem_dirs:
        problem_id = problem_dir.name
        gen_file_path = problem_dir / generated_file
        unopt_file_path = problem_dir / unoptimized_file
        json_file_path = problem_dir / samples_json
        
        if not gen_file_path.exists() or not unopt_file_path.exists():
            print(f"Skipping {problem_id}: Missing required files ({generated_file} or {unoptimized_file})")
            continue
        
        # Calculate similarity
        similarity = calculate_similarity(str(gen_file_path), str(unopt_file_path))
        
        # Read JSON (if exists and update is needed)
        correct = False
        if json_file_path.exists() and update_json:
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Update sample similarity information
                if 'samples' in data and sample_key in data['samples']:
                    data['samples'][sample_key]['similarity'] = similarity
                    correct = data.get('samples', {}).get(sample_key, {}).get('correct', False)
                
                # Save updated JSON
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
            except Exception as e:
                print(f"✗ {problem_id}: JSON processing failed - {e}")
        elif json_file_path.exists():
            # Read only, don't update
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                correct = data.get('samples', {}).get(sample_key, {}).get('correct', False)
            except:
                pass
        
        results.append({
            'problem_id': problem_id,
            'similarity': similarity,
            'correct': correct
        })
        
        print(f"✓ {problem_id}: Similarity = {similarity['overall_similarity']:.4f}")
    
    return results

def generate_report(results: List[Dict], output_file: str = None):
    """Generate similarity report"""
    if not results:
        print("No results available")
        return
    
    # Sort by instruction similarity in ascending order
    sorted_results = sorted(results, key=lambda x: x['similarity']['instruction_similarity'], reverse=False)
    
    # Generate report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("Assembly Code Similarity Report")
    report_lines.append("=" * 80)
    report_lines.append(f"\nTotal: {len(results)} problems\n")
    report_lines.append(f"{'Problem ID':<15} {'Overall Sim':<12} {'Line Similar':<12} {'Inst Similar':<12} {'Correct':<8}")
    report_lines.append("-" * 80)
    
    for result in sorted_results:
        problem_id = result['problem_id']
        sim = result['similarity']
        correct = "✓" if result['correct'] else "✗"
        report_lines.append(
            f"{problem_id:<15} {sim['overall_similarity']:<12.4f} {sim['line_similarity']:<12.4f} "
            f"{sim['instruction_similarity']:<12.4f} {correct:<8}"
        )
    
    # Statistics
    overall_sims = [r['similarity']['overall_similarity'] for r in results]
    line_sims = [r['similarity']['line_similarity'] for r in results]
    inst_sims = [r['similarity']['instruction_similarity'] for r in results]
    
    report_lines.append("-" * 80)
    report_lines.append(f"\nStatistics:")
    report_lines.append(f"  Overall Similarity - Average: {sum(overall_sims)/len(overall_sims):.4f}, "
                       f"Max: {max(overall_sims):.4f}, Min: {min(overall_sims):.4f}")
    report_lines.append(f"  Line Similarity - Average: {sum(line_sims)/len(line_sims):.4f}, "
                       f"Max: {max(line_sims):.4f}, Min: {min(line_sims):.4f}")
    report_lines.append(f"  Instruction Similarity - Average: {sum(inst_sims)/len(inst_sims):.4f}, "
                       f"Max: {max(inst_sims):.4f}, Min: {min(inst_sims):.4f}")
    
    # Count problems with instruction similarity < 1.0
    inst_less_than_one = sum(1 for sim in inst_sims if sim < 1.0)
    report_lines.append(f"  Number of problems with instruction similarity < 1.0: {inst_less_than_one}")
    
    correct_count = sum(1 for r in results if r['correct'])
    report_lines.append(f"\nCorrectness Statistics: {correct_count}/{len(results)} problems passed tests")
    
    report_lines.append("=" * 80)
    
    report_text = "\n".join(report_lines)
    print("\n" + report_text)
    
    # Save to file
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"\nReport saved to: {output_file}")

def main():
    """Main function, parse command line arguments and execute"""
    parser = argparse.ArgumentParser(
        description='Calculate assembly code similarity and update JSON files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Use default settings
  %(prog)s --base-dir /path/to/projects       # Specify directory
  %(prog)s --prefix task_ --generated opt.s   # Custom prefix and filenames
  %(prog)s --no-update                       # Calculate only, don't update JSON
        """
    )
    
    parser.add_argument(
        '--base-dir',
        type=str,
        default='.',
        help='Base directory path (default: current directory)'
    )
    
    parser.add_argument(
        '--prefix',
        type=str,
        default='problem_',
        help='Directory name prefix (default: problem_)'
    )
    
    parser.add_argument(
        '--generated',
        type=str,
        default='sample_0_generated.s',
        help='Generated assembly filename (default: sample_0_generated.s)'
    )
    
    parser.add_argument(
        '--unoptimized',
        type=str,
        default='unoptimized.s',
        help='Unoptimized assembly filename (default: unoptimized.s)'
    )
    
    parser.add_argument(
        '--samples-json',
        type=str,
        default='samples.json',
        help='JSON filename (default: samples.json)'
    )
    
    parser.add_argument(
        '--sample-key',
        type=str,
        default='0',
        help='Sample key in JSON (default: 0)'
    )
    
    parser.add_argument(
        '--no-update',
        action='store_true',
        help='Calculate similarity only, don\'t update JSON files'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Report output file path (default: base_dir/similarity_report.txt)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Quiet mode, only show final report'
    )
    
    args = parser.parse_args()
    
    # Determine output file path
    if args.output is None:
        base_path = Path(args.base_dir).resolve()
        output_file = base_path / 'similarity_report.txt'
    else:
        output_file = args.output
    
    # Execute processing
    if not args.quiet:
        print(f"Processing directory: {os.path.abspath(args.base_dir)}")
        print(f"Directory prefix: {args.prefix}")
        print(f"Generated file: {args.generated}")
        print(f"Unoptimized file: {args.unoptimized}\n")
    
    results = process_all_problems(
        base_dir=args.base_dir,
        dir_prefix=args.prefix,
        generated_file=args.generated,
        unoptimized_file=args.unoptimized,
        samples_json=args.samples_json,
        sample_key=args.sample_key,
        update_json=not args.no_update
    )
    
    if results:
        generate_report(results, str(output_file))
    else:
        print("No processable results found")

if __name__ == '__main__':
    main()

