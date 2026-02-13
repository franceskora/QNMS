import sqlite3
import pandas as pd
import io

DB_FILE = 'factory_data.db'

def export_all_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Get list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"📦 FOUND {len(tables)} TABLES IN DATABASE:")
    
    # 2. Loop through each table and export to CSV
    for table_name in tables:
        table = table_name[0]
        print(f"   └── Exporting '{table}'...", end=" ")
        
        try:
            # Read entire table
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            
            # Save to CSV (e.g., 'dump_device_states.csv')
            filename = f"dump_{table}.csv"
            df.to_csv(filename, index=False)
            
            print(f"✅ Done! ({len(df)} rows saved to {filename})")
        except Exception as e:
            print(f"❌ Error: {e}")

    # 3. Create a Full SQL Dump (Backup)
    print("\n💾 CREATING MASTER SQL DUMP...", end=" ")
    with io.open('full_backup.sql', 'w') as f:
        for line in conn.iterdump():
            f.write('%s\n' % line)
    print("✅ Saved to 'full_backup.sql'")

    conn.close()
    print("\n🎉 EXPORT COMPLETE. You can now download these files.")

if __name__ == "__main__":
    export_all_data()