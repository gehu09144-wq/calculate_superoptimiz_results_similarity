# Assembly Code Similarity Calculator

This project provides tools to calculate similarity between optimized and unoptimized assembly code from superoptimizer results. It is designed to analyze how similar generated optimized assembly code is compared to the original unoptimized version.

## Overview

The toolkit consists of two main scripts:

1. **`extract_assembly.py`** - Extracts assembly code from JSON result files and organizes them into a directory structure
2. **`calculate_similarity.py`** - Calculates similarity metrics between optimized and unoptimized assembly files

## Features

- **Multiple Similarity Metrics**:
  - Line-level similarity (normalized, excluding comments and empty lines)
  - Instruction-level similarity (sequence of assembly instructions)
  - Overall similarity (weighted combination of the above)

- **Batch Processing**: Process multiple problems in a single run
- **JSON Integration**: Automatically updates JSON files with similarity results
- **Detailed Reports**: Generates comprehensive similarity reports with statistics

## Installation

### Requirements

- Python 3.6 or higher
- Standard library only (no external dependencies)

No additional packages need to be installed - the scripts use only Python's standard library.

## Usage

### Step 1: Extract Assembly Code

First, extract assembly code from your superoptimizer result JSON files:

```bash
python extract_assembly.py <json_file_path> [output_directory]
```

**Parameters:**

- `json_file_path`: Path to the JSON file containing superoptimizer results
- `output_directory`: (Optional) Output directory name (default: `assembly_output`)

**Example:**

```bash
python extract_assembly.py gpt5-1_problem_results.json assembly_output
```

This script will:

- Create a directory structure: `output_directory/problem_{problem_id}/`
- Extract `generated_assembly` from each sample and save as `sample_{sample_id}_generated.s`
- Extract `unoptimized_assembly` and save as `unoptimized.s`
- Create a `samples.json` file in each problem directory with metadata

**Output Structure:**

```text
assembly_output/
├── problem_0/
│   ├── sample_0_generated.s
│   ├── unoptimized.s
│   └── samples.json
├── problem_1/
│   ├── sample_0_generated.s
│   ├── unoptimized.s
│   └── samples.json
└── ...
```

### Step 2: Calculate Similarity

Calculate similarity between optimized and unoptimized assembly files:

```bash
python calculate_similarity.py [options]
```

**Common Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--base-dir` | Base directory containing problem directories | `.` (current directory) |
| `--prefix` | Directory name prefix | `problem_` |
| `--generated` | Generated assembly filename | `sample_0_generated.s` |
| `--unoptimized` | Unoptimized assembly filename | `unoptimized.s` |
| `--samples-json` | JSON filename in each problem directory | `samples.json` |
| `--sample-key` | Sample key in JSON file | `0` |
| `--no-update` | Calculate similarity without updating JSON files | `False` |
| `--output` | Report output file path | `similarity_report.txt` |
| `--quiet` | Quiet mode (only show final report) | `False` |

**Examples:**

```bash
# Use default settings (current directory, problem_ prefix)
python calculate_similarity.py

# Specify a different directory
python calculate_similarity.py --base-dir assembly_output

# Custom directory prefix and filenames
python calculate_similarity.py --prefix task_ --generated optimized.s --unoptimized original.s

# Calculate similarity without updating JSON files
python calculate_similarity.py --no-update

# Specify custom output file
python calculate_similarity.py --output my_report.txt
```

## How It Works

### Similarity Calculation

The similarity calculation uses a multi-level approach:

1. **Line-Level Similarity** (60% weight):
   - Normalizes assembly lines by removing comments and extra whitespace
   - Uses Python's `difflib.SequenceMatcher` to compare normalized line sequences
   - Filters out empty lines, labels, and directives

2. **Instruction-Level Similarity** (40% weight):
   - Extracts only the instruction opcodes (e.g., `mov`, `add`, `sub`)
   - Compares the sequence of instructions using `SequenceMatcher`
   - Ignores operands, labels, and directives

3. **Overall Similarity**:
   - Weighted average: `overall = 0.6 * line_similarity + 0.4 * instruction_similarity`

### Normalization Process

The script normalizes assembly code by:

- Removing comments (lines starting with `#` or `;`)
- Stripping leading/trailing whitespace
- Filtering out:
  - Empty lines
  - Labels (e.g., `.L1:`, `main:`)
  - Directives (lines starting with `.`)

### Output Format

The script generates a similarity report with:

- Similarity metrics for each problem
- Statistics (average, min, max for each metric)
- Correctness information (if available in JSON)
- Sorted results by instruction similarity

**Report Example:**

```text
================================================================================
Assembly Code Similarity Report
================================================================================

Total: 200 problems

Problem ID       Overall Sim  Line Similar  Inst Similar  Correct
--------------------------------------------------------------------------------
problem_0        0.8234       0.8500        0.7800        ✗
problem_1        0.9123       0.9200        0.9000        ✓
...
--------------------------------------------------------------------------------

Statistics:
  Overall Similarity - Average: 0.7234, Max: 1.0000, Min: 0.1234
  Line Similarity - Average: 0.7500, Max: 1.0000, Min: 0.2000
  Instruction Similarity - Average: 0.6800, Max: 1.0000, Min: 0.1000
  Number of problems with instruction similarity < 1.0: 150

Correctness Statistics: 13/200 problems passed tests
================================================================================
```

### JSON Update Format

When similarity is calculated, the script updates the `samples.json` file:

```json
{
  "problem_id": "0",
  "samples": {
    "0": {
      "similarity": {
        "line_similarity": 0.8500,
        "instruction_similarity": 0.7800,
        "overall_similarity": 0.8234
      },
      "correct": false,
      ...
    }
  },
  ...
}
```

## File Structure

```text
calculate_superoptimiz_results_similarity/
├── calculate_similarity.py          # Main similarity calculation script
├── extract_assembly.py              # Assembly extraction script
├── README.md                        # This file
├── *.json                           # Superoptimizer result files
└── [output_directory]/              # Generated by extract_assembly.py
    └── problem_*/
        ├── sample_*_generated.s     # Optimized assembly
        ├── unoptimized.s            # Original assembly
        └── samples.json             # Problem metadata
```

## Workflow Example

Complete workflow for analyzing superoptimizer results:

```bash
# 1. Extract assembly from JSON results
python extract_assembly.py gpt5-1_problem_results.json gpt5-1_output

# 2. Calculate similarity metrics
python calculate_similarity.py --base-dir gpt5-1_output --output gpt5-1_similarity_report.txt

# 3. View the report
cat gpt5-1_similarity_report.txt
```

## Understanding Similarity Scores

- **1.0000**: Identical assembly code
- **0.7000 - 0.9999**: Very similar (minor differences in operands or formatting)
- **0.4000 - 0.6999**: Moderately similar (some instruction differences)
- **0.0000 - 0.3999**: Significantly different (major structural changes)

A lower similarity score may indicate:

- More aggressive optimizations
- Different instruction sequences
- Structural code reorganization
- Potential optimization opportunities

## Limitations

1. **Assembly Format**: The scripts are designed for standard assembly syntax. Custom assembly dialects may require modifications.

2. **Comment Handling**: Comments are stripped before comparison. Assembly code with embedded documentation may show lower line-level similarity.

3. **Instruction Semantics**: The tool compares instruction sequences, not semantic equivalence. Two functionally identical but differently structured code blocks may show lower similarity.

4. **Normalization**: The normalization process may not handle all edge cases for different assembly dialects.

## Troubleshooting

### No directories found

```text
Warning: No directories starting with 'problem_' found in /path/to/dir
```

- Check that you've run `extract_assembly.py` first
- Verify the `--prefix` option matches your directory naming

### Missing files

```text
Skipping problem_X: Missing required files (sample_0_generated.s or unoptimized.s)
```

- Ensure both generated and unoptimized assembly files exist
- Check file permissions

### JSON update failures

- Verify JSON file format is valid
- Check that the sample key exists in the JSON structure
- Review error messages for specific issues

## License

This project is provided as-is for research and analysis purposes.

## Contributing

When contributing to this project:

1. Follow the existing code style
2. Add comments for complex logic
3. Test with various assembly formats
4. Update documentation as needed
