import argparse
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from InquirerPy import inquirer


def discover_roll_numbers(base_dir: Path) -> list[str]:
    """Find student roll number directories in the assignment folder."""
    excluded = {"validator-tc", "__pycache__", ".git", ".agents", ".vscode"}
    candidates = []

    for item in base_dir.iterdir():
        if item.is_dir() and item.name not in excluded and not item.name.startswith("."):
            candidates.append(item.name)

    candidates.sort()
    return candidates


def get_student_scripts(base_dir: Path, roll_number: str) -> list[Path]:
    """Find all python scripts for a given roll number, prioritizing <roll>.py."""
    folder = base_dir / roll_number
    if not folder.exists() or not folder.is_dir():
        return []

    py_files = sorted(folder.glob("*.py"), key=lambda p: p.name)
    standard_script = folder / f"{roll_number}.py"

    if standard_script in py_files:
        py_files.remove(standard_script)
        py_files.insert(0, standard_script)

    return py_files


def parse_test_case(file_path: Path):
    """Load test case contents and parse problem metadata for validation."""
    content = file_path.read_text(encoding="utf-8")
    lines = content.strip().split("\n")

    kind = lines[0].strip()
    n = int(lines[1].strip())

    coords = []
    idx = 2
    for _ in range(n):
        parts = lines[idx].split()
        coords.append((float(parts[0]), float(parts[1])))
        idx += 1

    dist = []
    for _ in range(n):
        parts = lines[idx].split()
        dist.append([float(x) for x in parts])
        idx += 1

    return {
        "content": content,
        "kind": kind,
        "n": n,
        "coords": coords,
        "dist": dist,
    }


def validate_and_score_tour(line: str, n: int, dist: list[list[float]]):
    """Validate a tour line and calculate its path cost if valid."""
    try:
        tour = [int(x) for x in line.strip().split()]
    except ValueError:
        return False, None, None

    if len(tour) != n:
        return False, None, tour

    if len(set(tour)) != n or min(tour) < 0 or max(tour) >= n:
        return False, None, tour

    total_cost = 0.0
    for i in range(n):
        a = tour[i]
        b = tour[(i + 1) % n]
        total_cost += dist[a][b]

    return True, total_cost, tour


def format_duration(seconds: float) -> str:
    """Format seconds into MM:SS.mmm format."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:06.3f}"


def format_tour_path(line: str, max_cities: int = 10) -> str:
    """Format tour path string, displaying at most max_cities followed by ellipsis."""
    cities = line.split()
    if len(cities) > max_cities:
        return " ".join(cities[:max_cities]) + " ..."
    return " ".join(cities)


def run_solution(
    script_path: Path,
    test_case_path: Path,
    timeout: float,
    patience: float | None = None,
    case_info: tuple[int, int] | None = None,
    show_script_in_header: bool = False,
):
    """Execute solution script with streaming I/O, validation, and timeout."""
    test_meta = parse_test_case(test_case_path)
    n = test_meta["n"]
    dist = test_meta["dist"]
    raw_input = test_meta["content"]

    patience_str = f"{patience:.1f}s" if patience is not None else "disabled"
    print("\n" + "#" * 60)
    if case_info:
        print(f"# Test Case [{case_info[0]}/{case_info[1]}]: {test_case_path.name} ({test_meta['kind']}, N={n})")
    else:
        print(f"# Test Case: {test_case_path.name} ({test_meta['kind']}, N={n})")
    if show_script_in_header:
        print(f"# Script:    {script_path.name}")
    print(f"# Config:    Timeout = {timeout:.1f}s | Patience = {patience_str}")
    print("#" * 60 + "\n")

    process = subprocess.Popen(
        [sys.executable, "-u", str(script_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def feed_input():
        try:
            if process.stdin:
                process.stdin.write(raw_input)
                process.stdin.flush()
                process.stdin.close()
        except (BrokenPipeError, OSError):
            pass

    stdin_thread = threading.Thread(target=feed_input, daemon=True)
    stdin_thread.start()

    output_queue = queue.Queue()

    def stream_reader(pipe, stream_name):
        try:
            for line in iter(pipe.readline, ""):
                output_queue.put((stream_name, line))
            pipe.close()
        except (ValueError, OSError):
            pass

    stdout_thread = threading.Thread(target=stream_reader, args=(process.stdout, "stdout"), daemon=True)
    stderr_thread = threading.Thread(target=stream_reader, args=(process.stderr, "stderr"), daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    start_time = time.time()
    last_output_time = start_time
    timed_out = False
    patience_timed_out = False
    interrupted = False

    tours_emitted = 0
    valid_tours = 0
    first_cost = None
    best_cost = None
    last_valid_tour = None
    last_valid_cost = None

    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                timed_out = True
                break

            if patience is not None and (time.time() - last_output_time) >= patience:
                patience_timed_out = True
                break

            if process.poll() is not None and output_queue.empty():
                break

            try:
                stream_name, line = output_queue.get(timeout=0.05)
            except queue.Empty:
                continue

            last_output_time = time.time()

            current_elapsed = time.time() - start_time
            timestamp = format_duration(current_elapsed)

            if stream_name == "stdout":
                cleaned = line.strip()
                if not cleaned:
                    continue

                is_valid, cost, tour = validate_and_score_tour(cleaned, n, dist)
                tours_emitted += 1

                if is_valid:
                    valid_tours += 1
                    if first_cost is None:
                        first_cost = cost

                    improvement_str = ""
                    if best_cost is None or cost < best_cost - 1e-9:
                        delta = (best_cost - cost) if best_cost is not None else 0.0
                        best_cost = cost
                        improvement_str = f" [NEW BEST -{delta:.2f}]" if delta > 0 else " [INITIAL]"

                    last_valid_tour = tour
                    last_valid_cost = cost

                    print(f"[{timestamp}] Tour #{tours_emitted} | Cost: {cost:.4f}{improvement_str}")
                    print(f"         {format_tour_path(cleaned)}")
                else:
                    print(f"[{timestamp}] [NON-TOUR/DEBUG] {cleaned}")

            elif stream_name == "stderr":
                print(f"[{timestamp}] [STDERR] {line.rstrip()}", file=sys.stderr)

    except KeyboardInterrupt:
        interrupted = True
        print("\n\n[INFO] Execution interrupted by user. Terminating process...")

    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()

        while not output_queue.empty():
            try:
                stream_name, line = output_queue.get_nowait()
                if stream_name == "stdout" and line.strip():
                    cleaned = line.strip()
                    is_valid, cost, tour = validate_and_score_tour(cleaned, n, dist)
                    tours_emitted += 1
                    if is_valid:
                        valid_tours += 1
                        if first_cost is None:
                            first_cost = cost
                        if best_cost is None or cost < best_cost:
                            best_cost = cost
                        last_valid_tour = tour
                        last_valid_cost = cost
                        print(f"[DRAIN] Tour #{tours_emitted} | Cost: {cost:.4f}")
                        print(f"        {format_tour_path(cleaned)}")
            except queue.Empty:
                break

    total_time = time.time() - start_time

    print("\n" + "=" * 10)
    print("EVALUATION SUMMARY")
    print("=" * 10)
    print(f"Elapsed Time:     {total_time:.2f}s (Limit: {timeout}s)")

    if interrupted:
        print("Exit Reason:      INTERRUPTED BY USER")
    elif patience_timed_out:
        print(f"Exit Reason:      PATIENCE TIMEOUT (No output for {patience}s)")
    elif timed_out:
        print("Exit Reason:      TIMED OUT (Reached cutoff)")
    else:
        print(f"Exit Reason:      COMPLETED NORMALLY (Exit code: {process.returncode})")

    print(f"Tours Printed:    {tours_emitted} (Valid: {valid_tours})")

    if valid_tours > 0:
        print(f"Initial Cost:     {first_cost:.4f}")
        print(f"Best Cost:        {best_cost:.4f}")
        print(f"Evaluated Cost:   {last_valid_cost:.4f} (from last valid tour)")
        improvement = ((first_cost - last_valid_cost) / first_cost * 100) if first_cost > 0 else 0.0
        print(f"Improvement:      {first_cost - last_valid_cost:.4f} ({improvement:.2f}%)")
        print("Result:           PASS")
    else:
        print("Result:           FAIL (No valid tour produced)")
    print("=" * 10 + "\n")

    return {
        "script": script_path.name,
        "test_case": test_case_path.name,
        "kind": test_meta["kind"],
        "n": n,
        "elapsed": total_time,
        "timeout": timeout,
        "patience": patience,
        "interrupted": interrupted,
        "timed_out": timed_out,
        "patience_timed_out": patience_timed_out,
        "tours_emitted": tours_emitted,
        "valid_tours": valid_tours,
        "first_cost": first_cost,
        "best_cost": best_cost,
        "last_cost": last_valid_cost,
        "passed": valid_tours > 0,
    }


DEFAULT_TIMEOUT_MAP = {
    "10": 5.0,
    "25": 10.0,
    "50": 20.0,
    "100": 40.0,
}

DEFAULT_PATIENCE_MAP = {
    "10": 1.0,
    "25": 2.0,
    "50": 5.0,
    "100": 10.0,
}


def main():
    """Main CLI entrypoint for interactive and argument-based testing."""
    base_dir = Path(__file__).resolve().parent
    validator_tc_dir = base_dir / "validator-tc"

    parser = argparse.ArgumentParser(description="TSP Test Harness")
    parser.add_argument("--roll", type=str, help="Roll number to execute")
    parser.add_argument("--script", type=str, help="Specific solution script to run within the roll folder")
    parser.add_argument("--type", choices=["euclidean", "non-euclidean", "both"], help="Problem metric type")
    parser.add_argument("--size", choices=["10", "25", "50", "100", "all"], help="Problem size")
    parser.add_argument("--timeout", type=float, default=None, help="Timeout in seconds")
    parser.add_argument("--patience", type=float, default=None, help="Patience timeout in seconds (early exit if no output)")
    parser.add_argument("--multiplier", type=float, default=None, choices=[1.0, 2.0, 4.0], help="Timeout and patience multiplier when running all sizes")

    args = parser.parse_args()

    roll = args.roll
    if not roll:
        discovered_rolls = discover_roll_numbers(base_dir)
        if not discovered_rolls:
            print("[ERROR] No roll number directories found in assignment folder.", file=sys.stderr)
            sys.exit(1)

        choices = []
        for r in discovered_rolls:
            scripts = get_student_scripts(base_dir, r)
            if scripts:
                status_text = f"{len(scripts)} script{'s' if len(scripts) > 1 else ''}"
            else:
                status_text = "no script found"
            choices.append({"name": f"{r} ({status_text})", "value": r})

        roll = inquirer.select(
            message="Select roll number to execute:",
            choices=choices,
        ).execute()

    available_scripts = get_student_scripts(base_dir, roll)
    if not available_scripts:
        print(f"\n[ERROR] No Python scripts found in folder '{roll}'.", file=sys.stderr)
        print(f"Expected location: {base_dir / roll}\n", file=sys.stderr)
        sys.exit(1)

    selected_scripts = []
    if args.script:
        if args.script.lower() in ("all", "both"):
            selected_scripts = available_scripts
        else:
            for p in available_scripts:
                if p.name == args.script or p.stem == args.script:
                    selected_scripts = [p]
                    break
            if not selected_scripts:
                print(f"\n[ERROR] Script '{args.script}' not found in folder '{roll}'.", file=sys.stderr)
                sys.exit(1)

    if not selected_scripts:
        script_choices = []
        if len(available_scripts) > 1:
            script_choices.append({
                "name": f"All ({len(available_scripts)} scripts)",
                "value": "all",
            })
        for p in available_scripts:
            script_choices.append({"name": p.name, "value": p})

        chosen = inquirer.select(
            message="Select solution file to run:",
            choices=script_choices,
        ).execute()

        if chosen == "all":
            selected_scripts = available_scripts
        else:
            selected_scripts = [chosen]

    prob_type = args.type
    if not prob_type:
        prob_type = inquirer.select(
            message="Select problem type:",
            choices=[
                {"name": "Euclidean", "value": "euclidean"},
                {"name": "Non-Euclidean", "value": "non-euclidean"},
                {"name": "Both (Euclidean & Non-Euclidean)", "value": "both"},
            ],
        ).execute()

    size = args.size
    if not size:
        size = inquirer.select(
            message="Select problem size (number of cities):",
            choices=[
                {"name": "10", "value": "10"},
                {"name": "25", "value": "25"},
                {"name": "50", "value": "50"},
                {"name": "100", "value": "100"},
                {"name": "All (10, 25, 50, 100)", "value": "all"},
            ],
        ).execute()

    if size == "all":
        multiplier = args.multiplier
        if multiplier is None:
            multiplier_choice = inquirer.select(
                message="Use default timeout and patience, or scale them?",
                choices=[
                    {"name": "1x (Default: 10->5s/1s, 25->10s/2s, 50->20s/5s, 100->40s/10s)", "value": 1.0},
                    {"name": "2x (Double: 10->10s/2s, 25->20s/4s, 50->40s/10s, 100->80s/20s)", "value": 2.0},
                    {"name": "4x (Quadruple: 10->20s/4s, 25->40s/8s, 50->80s/20s, 100->160s/40s)", "value": 4.0},
                ],
                default=1.0,
            ).execute()
            multiplier = float(multiplier_choice)
    else:
        multiplier = 1.0
        default_timeout = str(int(DEFAULT_TIMEOUT_MAP.get(str(size), 300)))
        timeout = args.timeout
        if timeout is None:
            timeout_choice = inquirer.select(
                message="Select timeout in seconds:",
                choices=["5", "10", "20", "40", "100", "150", "200", "250", "300"],
                default=default_timeout,
            ).execute()
            timeout = float(timeout_choice)

        default_patience = str(int(DEFAULT_PATIENCE_MAP.get(str(size), 5)))
        patience = args.patience
        if patience is None and not (args.roll and args.size and args.type and args.timeout is not None):
            patience_choice = inquirer.select(
                message="Select patience in seconds (timeout if no output):",
                choices=["1", "2", "5", "10", "50", "100", "None"],
                default=default_patience,
            ).execute()
            patience = float(patience_choice) if patience_choice != "None" else None

    type_prefixes = []
    if prob_type.lower() in ("euclidean", "reuc"):
        type_prefixes = ["reuc"]
    elif prob_type.lower() in ("non-euclidean", "rnoneuc"):
        type_prefixes = ["rnoneuc"]
    else:
        type_prefixes = ["reuc", "rnoneuc"]

    sizes = ["10", "25", "50", "100"] if size == "all" else [str(size)]

    run_tasks = []
    for s in sizes:
        for prefix in type_prefixes:
            tc_file = validator_tc_dir / f"{prefix}_{s}"
            if not tc_file.exists():
                print(f"[ERROR] Test case file not found: {tc_file}", file=sys.stderr)
                sys.exit(1)

            if size == "all":
                t = DEFAULT_TIMEOUT_MAP[s] * multiplier
                p = DEFAULT_PATIENCE_MAP[s] * multiplier
            else:
                t = timeout
                p = patience

            for sc in selected_scripts:
                run_tasks.append((tc_file, sc, t, p))

    if len(selected_scripts) == 1:
        print(f"\nExecuting: {selected_scripts[0].relative_to(base_dir)}")
    else:
        print(f"\nExecuting: {len(selected_scripts)} scripts across {len(sizes) * len(type_prefixes)} test case(s) ({len(run_tasks)} runs total)")

    results = []
    show_script_in_hdr = len(selected_scripts) > 1

    for idx, (tc_file, sc, t, p) in enumerate(run_tasks, 1):
        case_info = (idx, len(run_tasks)) if len(run_tasks) > 1 else None
        result = run_solution(
            sc,
            tc_file,
            t,
            p,
            case_info=case_info,
            show_script_in_header=show_script_in_hdr,
        )
        results.append(result)

        if result["interrupted"]:
            print("\n[INFO] User interrupted. Stopping remaining test cases.")
            break

    if len(run_tasks) > 1:
        if len(selected_scripts) > 1:
            best_costs = {}
            for r in results:
                tc = r["test_case"]
                if r["passed"] and r["last_cost"] is not None:
                    if tc not in best_costs or r["last_cost"] < best_costs[tc]:
                        best_costs[tc] = r["last_cost"]

            max_script_len = max(len(s.name) for s in selected_scripts)
            script_col_w = max(max_script_len + 2, 24)

            total_width = 14 + script_col_w + 16 + 6 + 13 + 14 + 9 + 8
            print("\n" + "=" * total_width)
            print(f"BATCH EVALUATION SUMMARY ({len(results)} of {len(run_tasks)} runs completed)")
            print("=" * total_width)
            header = f"{'Test Case':<14} {'Script':<{script_col_w}} {'Kind':<16} {'N':<6} {'Best Cost':<13} {'Eval Cost':<14} {'Time':<9} {'Status'}"
            print(header)
            print("-" * total_width)

            prev_tc = None
            for r in results:
                curr_tc = r["test_case"]
                if prev_tc is not None and curr_tc != prev_tc:
                    print("-" * total_width)
                prev_tc = curr_tc

                kind_str = "Euclidean" if "NON" not in r["kind"].upper() else "Non-Euclidean"
                best_s = f"{r['best_cost']:.2f}" if r["best_cost"] is not None else "N/A"

                is_best_for_tc = False
                if r["passed"] and r["last_cost"] is not None and curr_tc in best_costs:
                    if abs(r["last_cost"] - best_costs[curr_tc]) < 1e-6:
                        is_best_for_tc = True

                if r["last_cost"] is not None:
                    eval_s = f"{r['last_cost']:.2f}{' *' if is_best_for_tc else ''}"
                else:
                    eval_s = "N/A"

                time_s = f"{r['elapsed']:.2f}s"
                status_s = "PASS" if r["passed"] else "FAIL"
                if r["interrupted"]:
                    status_s = "ABORT"

                print(f"{curr_tc:<14} {r['script']:<{script_col_w}} {kind_str:<16} {r['n']:<6} {best_s:<13} {eval_s:<14} {time_s:<9} {status_s}")

            print("=" * total_width)
            print("(* indicates best evaluated cost for that test case)\n")
        else:
            print("\n" + "=" * 78)
            print(f"BATCH EVALUATION SUMMARY ({len(results)} of {len(run_tasks)} completed)")
            print("=" * 78)
            print(f"{'Test Case':<14} {'Kind':<15} {'N':<6} {'Best Cost':<12} {'Eval Cost':<12} {'Time':<8} {'Status'}")
            print("-" * 78)
            for r in results:
                kind_str = "Euclidean" if "NON" not in r["kind"].upper() else "Non-Eucl"
                best_s = f"{r['best_cost']:.2f}" if r["best_cost"] is not None else "N/A"
                eval_s = f"{r['last_cost']:.2f}" if r["last_cost"] is not None else "N/A"
                time_s = f"{r['elapsed']:.2f}s"
                status_s = "PASS" if r["passed"] else "FAIL"
                if r["interrupted"]:
                    status_s = "ABORT"
                print(f"{r['test_case']:<14} {kind_str:<15} {r['n']:<6} {best_s:<12} {eval_s:<12} {time_s:<8} {status_s}")
            print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
