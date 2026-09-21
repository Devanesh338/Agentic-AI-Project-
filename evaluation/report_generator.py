import sqlite3
import csv
import json
import os
from .config import DB_PATH

def export_to_csv(run_id: int, output_file: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM evaluation_results WHERE run_id = ?", (run_id,))
    rows = cursor.fetchall()
    
    if not rows:
        print(f"No results found for run {run_id}")
        return
        
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(rows[0].keys())
        for row in rows:
            writer.writerow(row)
            
    print(f"Exported run {run_id} to {output_file}")
    conn.close()

def export_to_json(run_id: int, output_file: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM evaluation_results WHERE run_id = ?", (run_id,))
    rows = cursor.fetchall()
    
    data = [dict(row) for row in rows]
    
    # Parse json fields
    for item in data:
        for key in ["plan_quality_scores", "raw_trace"]:
            if item.get(key):
                try:
                    item[key] = json.loads(item[key])
                except:
                    pass
                    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    print(f"Exported run {run_id} to {output_file}")
    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m evaluation.report_generator <run_id> <json|csv> [output_file]")
        sys.exit(1)
        
    run_id = int(sys.argv[1])
    format_type = sys.argv[2].lower()
    out_file = sys.argv[3] if len(sys.argv) > 3 else f"evaluation_run_{run_id}.{format_type}"
    
    if format_type == "csv":
        export_to_csv(run_id, out_file)
    elif format_type == "json":
        export_to_json(run_id, out_file)
    else:
        print("Invalid format. Use json or csv.")
