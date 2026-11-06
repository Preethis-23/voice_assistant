import json
import time
import csv
import sys
import uuid
from pathlib import Path

# Ensure UTF-8 output encoding for Windows shell
sys.stdout.reconfigure(encoding='utf-8')

CASES_FILE = Path("tests/benchmark_cases.json")
RESULTS_CSV = Path("tests/benchmark_results.csv")

def run_harness():
    if not CASES_FILE.exists():
        print(f"Error: {CASES_FILE} not found!")
        return

    with open(CASES_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)

    from app.agent.graph import run_agent_goal

    print(f"Starting KIRA Benchmark Suite across {len(cases)} test cases...\n")
    print(f"{'ID':<4} | {'Category':<24} | {'Status':<10} | {'Latency (s)':<11} | {'Tools Called':<25}")
    print("-" * 80)

    results = []
    
    cat_stats = {}

    for item in cases:
        cid = item["id"]
        cat = item["category"]
        query = item["query"]
        expected_tool = item["expected_tool"]
        auto_verifiable = item["auto_verifiable"]

        if cat not in cat_stats:
            cat_stats[cat] = {"total": 0, "passed": 0, "latencies": []}

        session_id = f"bench_{cid}_{uuid.uuid4().hex[:4]}"
        
        start_t = time.time()
        try:
            state = run_agent_goal(query, session_id=session_id)
            elapsed = time.time() - start_t
        except Exception as e:
            elapsed = time.time() - start_t
            status = "ERROR"
            tools_used = []
            obs_err = str(e)
            results.append({
                "id": cid, "category": cat, "query": query, "expected_tool": expected_tool,
                "status": status, "latency": round(elapsed, 2), "tools_used": "", "error": obs_err
            })
            cat_stats[cat]["total"] += 1
            cat_stats[cat]["latencies"].append(elapsed)
            print(f"{cid:<4} | {cat:<24} | {status:<10} | {elapsed:<11.2f} | Exception: {obs_err[:20]}")
            continue

        # Extract tools called from plan or observations
        tools_called = [s.tool_name for s in state.plan if s.tool_name]
        
        # Verify pass/fail logic
        # 1. Conversational / expected_tool is None
        if expected_tool is None:
            # Pass if no tools called or executed cleanly without errors
            passed = len(tools_called) == 0 or state.error_count == 0
        else:
            # Tool expected: Pass if expected_tool was called OR at least 1 valid tool called and error recovered
            passed = (expected_tool in tools_called) or (len(tools_called) > 0 and state.is_complete)

        status = "PASS" if passed else "FAIL"
        
        cat_stats[cat]["total"] += 1
        if passed:
            cat_stats[cat]["passed"] += 1
        cat_stats[cat]["latencies"].append(elapsed)

        tools_str = ", ".join(tools_called) if tools_called else "None (Direct Answer)"
        print(f"{cid:<4} | {cat:<24} | {status:<10} | {elapsed:<11.2f} | {tools_str[:25]}")

        results.append({
            "id": cid,
            "category": cat,
            "query": query,
            "expected_tool": expected_tool or "None",
            "tools_called": tools_str,
            "status": status,
            "latency": round(elapsed, 2),
            "auto_verifiable": auto_verifiable,
            "final_response": (state.final_response or "")[:150].replace("\n", " ")
        })

    # Save to CSV
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "category", "query", "expected_tool", "tools_called", "status", "latency", "auto_verifiable", "final_response"])
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    
    total_cases = len(cases)
    total_passed = sum(c["passed"] for c in cat_stats.values())
    all_latencies = [r["latency"] for r in results]
    
    avg_lat = sum(all_latencies) / len(all_latencies) if all_latencies else 0
    min_lat = min(all_latencies) if all_latencies else 0
    max_lat = max(all_latencies) if all_latencies else 0

    print(f"Total Test Cases      : {total_cases}")
    print(f"Overall Pass Rate     : {total_passed}/{total_cases} ({total_passed/total_cases*100:.1f}%)")
    print(f"Latency (Min/Max/Avg) : {min_lat:.2f}s / {max_lat:.2f}s / {avg_lat:.2f}s\n")

    print("CATEGORY BREAKDOWN:")
    print(f"{'Category':<26} | {'Passed':<8} | {'Pass Rate':<10} | {'Avg Latency (s)':<15}")
    print("-" * 65)
    for cat, data in cat_stats.items():
        tot = data["total"]
        pas = data["passed"]
        rate = (pas / tot * 100) if tot > 0 else 0
        lats = data["latencies"]
        c_avg_lat = sum(lats)/len(lats) if lats else 0
        print(f"{cat:<26} | {pas}/{tot:<5} | {rate:<9.1f}% | {c_avg_lat:<15.2f}")

    print("=" * 80)
    print(f"Full results output saved to: {RESULTS_CSV}")

if __name__ == "__main__":
    run_harness()
