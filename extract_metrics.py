import sqlite3
import json
from pathlib import Path

# Portable path relative to repository root
DB_PATH = Path(__file__).resolve().parent / "data" / "assistant.db"

def extract_metrics():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print("KIRA PROJECT METRICS EXTRACTOR")
    print("==================================\n")

    # 1. Volume / Scale Metrics
    cursor.execute("SELECT COUNT(*) FROM conversations")
    total_goals = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT session_id) FROM conversations")
    total_sessions = cursor.fetchone()[0]

    print("--- SCALE & VOLUME ---")
    print(f"Total Goals/Tasks Processed : {total_goals}")
    print(f"Total Unique Sessions       : {total_sessions}\n")

    # 2. Tool Reliability Metrics
    cursor.execute("SELECT COUNT(*) FROM tool_logs")
    total_tools = cursor.fetchone()[0]

    if total_tools > 0:
        cursor.execute("SELECT COUNT(*) FROM tool_logs WHERE success = 1")
        successful_tools = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tool_logs WHERE success = 0")
        failed_tools = cursor.fetchone()[0]
        
        success_rate = (successful_tools / total_tools) * 100
        
        print("--- TOOL RELIABILITY ---")
        print(f"Total Tool Executions       : {total_tools}")
        print(f"Successful Executions       : {successful_tools}")
        print(f"Failed Executions           : {failed_tools}")
        print(f"Base Tool Success Rate      : {success_rate:.1f}%\n")
        
        # Most used tools
        cursor.execute("""
            SELECT tool_name, COUNT(*) as count 
            FROM tool_logs 
            GROUP BY tool_name 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_tools = cursor.fetchall()
        print("Top Tools Used:")
        for t in top_tools:
            print(f" - {t[0]}: {t[1]} times")
    else:
        print("No tool logs found yet.")

    conn.close()

if __name__ == "__main__":
    extract_metrics()
