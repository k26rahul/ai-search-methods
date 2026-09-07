# TSP Test Harness Documentation

This directory contains the test harness script `test_harness.py` for evaluating Travelling Salesperson Problem (TSP) solver implementations.

## Test Cases Overview

The test cases are located in the `validator-tc/` directory. There are 8 test cases divided equally between Euclidean and Non-Euclidean distance metrics across 4 problem sizes:

| File Name | Metric Type | City Count ($N$) | Description |
| :--- | :--- | :--- | :--- |
| `reuc_10` | EUCLIDEAN | 10 | Small Euclidean TSP |
| `reuc_25` | EUCLIDEAN | 25 | Medium-small Euclidean TSP |
| `reuc_50` | EUCLIDEAN | 50 | Medium Euclidean TSP |
| `reuc_100` | EUCLIDEAN | 100 | Large Euclidean TSP |
| `rnoneuc_10` | NON-EUCLIDEAN | 10 | Small Non-Euclidean TSP |
| `rnoneuc_25` | NON-EUCLIDEAN | 25 | Medium-small Non-Euclidean TSP |
| `rnoneuc_50` | NON-EUCLIDEAN | 50 | Medium Non-Euclidean TSP |
| `rnoneuc_100` | NON-EUCLIDEAN | 100 | Large Non-Euclidean TSP |

### Test Case File Structure

Each test case file conforms to the assignment standard input format:

1. **Line 1**: Metric kind string (`EUCLIDEAN` or `NON-EUCLIDEAN`).
2. **Line 2**: Integer $N$ specifying the total number of cities.
3. **Lines 3 to $N+2$**: $N$ lines with space-separated 2D float coordinates (`x y`).
4. **Lines $N+3$ to $2N+2$**: $N$ lines representing the $N \times N$ distance matrix where each line contains $N$ space-separated float distance values.

## Features

- **Interactive Selection**: Uses `InquirerPy` to prompt for student roll number, solution file, problem metric, size, and timeout settings.
- **Multiple Script Comparison**: Allows running individual scripts or all scripts in a roll number folder sequentially on each test case.
- **Real-Time Streaming**: Runs solver subprocesses in unbuffered mode (`-u`), capturing anytime tour outputs with millisecond timestamps (`[MM:SS.mmm]`).
- **Tour Validation and Scoring**: Verifies valid zero-based permutations ($0$ to $N-1$) and computes path cost using the distance matrix.
- **Path Decluttering**: Displays the first 10 cities of each tour followed by `...` for problem sizes larger than 10.
- **Patience Early Exit**: Terminates execution early if no new tour is emitted within a selected patience window.
- **Assignment Cutoff Alignment**: Evaluates the last valid tour printed before termination, consistent with course evaluation rules.
- **Batch Grouping by Size**: Groups test cases by city size so Euclidean and Non-Euclidean variants appear together.
- **Graceful Interrupt**: Pressing `Ctrl+C` terminates the active child process cleanly and prints the summary for completed runs.

## Default Timeout and Patience Mappings

When testing, the harness provides sensible defaults mapped to problem sizes:

| Problem Size ($N$) | Default Timeout | Default Patience |
| :--- | :--- | :--- |
| 10 | 5 seconds | 1 second |
| 25 | 10 seconds | 2 seconds |
| 50 | 20 seconds | 5 seconds |
| 100 | 40 seconds | 10 seconds |

When selecting **All** sizes, the harness prompts for a multiplier:
- **1x (Default)**: Uses base mapping values above.
- **2x (Double)**: Doubles both timeout and patience (10s/2s, 20s/4s, 40s/10s, 80s/20s).
- **4x (Quadruple)**: Quadruples both timeout and patience (20s/4s, 40s/8s, 80s/20s, 160s/40s).

## Interactive Usage

Run the harness without arguments:

```powershell
python test_harness.py
```

### Prompt Steps

1. **Select Roll Number**: Scans the directory and lists available folders (e.g., `23f1002653`, `23f2000575`).
2. **Select Solution File**: Lists python files inside that folder, plus an option for `All (<N> scripts)`.
3. **Select Problem Type**: Choose `Euclidean`, `Non-Euclidean`, or `Both (Euclidean & Non-Euclidean)`.
4. **Select Problem Size**: Choose `10`, `25`, `50`, `100`, or `All (10, 25, 50, 100)`.
5. **Configure Limits**:
   - If a single size was chosen: prompts for timeout and patience duration.
   - If all sizes were chosen: prompts for the multiplier profile (`1x`, `2x`, `4x`).

## Command-Line Usage

The harness can be run non-interactively via CLI flags:

```powershell
# Run a single script on one test case
python test_harness.py --roll 23f1002653 --script 23f1002653.py --type euclidean --size 10 --timeout 5 --patience 1

# Run a specific solver on both metrics for size 25
python test_harness.py --roll 23f1002653 --script double-bridge-perturbation.py --type both --size 25

# Benchmark all solution scripts on all test cases with 2x timeout/patience
python test_harness.py --roll 23f1002653 --script all --type both --size all --multiplier 2
```

### CLI Flag Reference

- `--roll <str>`: Student roll number directory.
- `--script <str>`: Specific script filename or `all` to run every script.
- `--type <euclidean|non-euclidean|both>`: Problem metric.
- `--size <10|25|50|100|all>`: City count.
- `--timeout <float>`: Hard timeout limit in seconds.
- `--patience <float>`: Inactivity cutoff in seconds.
- `--multiplier <1.0|2.0|4.0>`: Multiplier for timeout and patience when running all sizes.

## Output Structure

### 1. Test Case Header
Before each run, the harness prints a single banner with case and configuration details:

```text
############################################################
# Test Case [1/6]: reuc_10 (EUCLIDEAN, N=10)
# Script:    23f1002653.py
# Config:    Timeout = 5.0s | Patience = 1.0s
############################################################
```

### 2. Anytime Tour Output
Tours emitted by the program stream in real time:

```text
[00:00.038] Tour #1 | Cost: 690.0137 [INITIAL]
         0 2 7 5 8 3 4 9 6 1
[00:00.038] Tour #2 | Cost: 655.6751 [NEW BEST -34.34]
         0 2 8 3 4 9 1 6 5 7
```

### 3. Per-Run Evaluation Summary
```text
==========
EVALUATION SUMMARY
==========
Elapsed Time:     1.10s (Limit: 5.0s)
Exit Reason:      PATIENCE TIMEOUT (No output for 1.0s)
Tours Printed:    3 (Valid: 3)
Initial Cost:     690.0137
Best Cost:        655.6751
Evaluated Cost:   655.6751 (from last valid tour)
Improvement:      34.3385 (4.98%)
Result:           PASS
==========
```

### 4. Batch Comparative Summary Table
When multiple runs occur, a final table groups runs by test case and marks the lowest evaluated cost with an asterisk (`*`):

```text
===================================================================================================================
BATCH EVALUATION SUMMARY (6 of 6 runs completed)
===================================================================================================================
Test Case      Script                              Kind             N      Best Cost     Eval Cost      Time      Status
-------------------------------------------------------------------------------------------------------------------
reuc_10        23f1002653.py                       Euclidean        10     655.68        655.68 *       1.12s     PASS
reuc_10        double-bridge-perturbation.py       Euclidean        10     655.68        655.68 *       1.05s     PASS
reuc_10        neighbor-list-restricted-2-opt.py   Euclidean        10     655.68        655.68 *       1.12s     PASS
-------------------------------------------------------------------------------------------------------------------
rnoneuc_10     23f1002653.py                       Non-Euclidean    10     657.21        657.21 *       1.05s     PASS
rnoneuc_10     double-bridge-perturbation.py       Non-Euclidean    10     657.21        657.21 *       1.06s     PASS
rnoneuc_10     neighbor-list-restricted-2-opt.py   Non-Euclidean    10     657.21        657.21 *       1.06s     PASS
===================================================================================================================
(* indicates best evaluated cost for that test case)
```
