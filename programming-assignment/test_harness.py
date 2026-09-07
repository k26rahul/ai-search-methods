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


def resolve_student_script(base_dir: Path, roll_number: str) -> Path | None:
    """Find the runnable python script for a given roll number."""
    folder = base_dir / roll_number
    if not folder.exists() or not folder.is_dir():
        return None

    standard_script = folder / f"{roll_number}.py"
    if standard_script.exists():
        return standard_script

    py_files = list(folder.glob("*.py"))
    if py_files:
        return py_files[0]

    return None


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
    """Format seconds into MM:SS.cc format."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:05.2f}"


def run_solution(script_path: Path, test_case_path: Path, timeout: float):
    """Execute solution script with streaming I/O, validation, and timeout."""
    test_meta = parse_test_case(test_case_path)
    n = test_meta["n"]
    dist = test_meta["dist"]
    raw_input = test_meta["content"]

    print("\n" + "=" * 60)
    print(f"Executing: {script_path.relative_to(script_path.parents[1])}")
    print(f"Test Case: {test_case_path.name} ({test_meta['kind']}, N={n})")
    print(f"Timeout:   {timeout} seconds")
    print("=" * 60 + "\n")

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
    timed_out = False
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

            if process.poll() is not None and output_queue.empty():
                break

            try:
                stream_name, line = output_queue.get(timeout=0.05)
            except queue.Empty:
                continue

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
                    print(f"         {cleaned}")
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
                        print(f"        {cleaned}")
            except queue.Empty:
                break

    total_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Script:           {script_path.name}")
    print(f"Test Case:        {test_case_path.name} ({test_meta['kind']}, N={n})")
    print(f"Elapsed Time:     {total_time:.2f}s (Limit: {timeout}s)")

    if interrupted:
        print("Exit Reason:      INTERRUPTED BY USER")
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
    print("=" * 60 + "\n")


def main():
    """Main CLI entrypoint for interactive and argument-based testing."""
    base_dir = Path(__file__).resolve().parent
    validator_tc_dir = base_dir / "validator-tc"

    parser = argparse.ArgumentParser(description="TSP Test Harness")
    parser.add_argument("--roll", type=str, help="Roll number to execute")
    parser.add_argument("--type", choices=["euclidean", "non-euclidean"], help="Problem metric type")
    parser.add_argument("--size", choices=["10", "25", "50", "100"], help="Problem size")
    parser.add_argument("--timeout", type=float, default=300.0, help="Timeout in seconds (default: 300)")

    args = parser.parse_args()

    roll = args.roll
    if not roll:
        discovered_rolls = discover_roll_numbers(base_dir)
        if not discovered_rolls:
            print("[ERROR] No roll number directories found in assignment folder.", file=sys.stderr)
            sys.exit(1)

        choices = []
        for r in discovered_rolls:
            script_exists = resolve_student_script(base_dir, r) is not None
            status_text = "ready" if script_exists else "no script found"
            choices.append({"name": f"{r} ({status_text})", "value": r})

        roll = inquirer.select(
            message="Select roll number to execute:",
            choices=choices,
        ).execute()

    script_path = resolve_student_script(base_dir, roll)
    if not script_path:
        print(f"\n[ERROR] Runnable script not found for roll number '{roll}'.", file=sys.stderr)
        print(f"Expected location: {base_dir / roll / f'{roll}.py'}\n", file=sys.stderr)
        sys.exit(1)

    prob_type = args.type
    if not prob_type:
        prob_type = inquirer.select(
            message="Select problem type:",
            choices=[
                {"name": "Euclidean", "value": "euclidean"},
                {"name": "Non-Euclidean", "value": "non-euclidean"},
            ],
        ).execute()

    size = args.size
    if not size:
        size = inquirer.select(
            message="Select problem size (number of cities):",
            choices=["10", "25", "50", "100"],
        ).execute()

    prefix = "reuc" if prob_type.lower() == "euclidean" else "rnoneuc"
    test_case_file = validator_tc_dir / f"{prefix}_{size}"

    if not test_case_file.exists():
        print(f"\n[ERROR] Test case file not found: {test_case_file}\n", file=sys.stderr)
        sys.exit(1)

    run_solution(script_path, test_case_file, args.timeout)


if __name__ == "__main__":
    main()
