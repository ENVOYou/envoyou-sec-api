#!/usr/bin/env python3
"""MCP Server for Supabase operations"""
import os
import json
from typing import Any
from datetime import datetime, date
import psycopg2
from psycopg2.extras import RealDictCursor

class SupabaseMCP:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
    
    def query(self, table: str, filters: dict = None, select: str = "*") -> dict:
        """Query table via PostgreSQL"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            sql = f"SELECT {select} FROM {table}"
            if filters:
                where = " AND ".join([f"{k} = %s" for k in filters.keys()])
                sql += f" WHERE {where}"
                cur.execute(sql, tuple(filters.values()))
            else:
                cur.execute(sql)
            
            rows = cur.fetchall()
            data = []
            for row in rows:
                row_dict = dict(row)
                # Convert datetime to string
                for k, v in row_dict.items():
                    if isinstance(v, (datetime, date)):
                        row_dict[k] = v.isoformat()
                data.append(row_dict)
            cur.close()
            conn.close()
            return {"success": True, "data": data, "count": len(data)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def insert(self, table: str, data: dict) -> dict:
        """Insert into table"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cols = ", ".join(data.keys())
            vals = ", ".join(["%s"] * len(data))
            sql = f"INSERT INTO {table} ({cols}) VALUES ({vals}) RETURNING *"
            cur.execute(sql, tuple(data.values()))
            conn.commit()
            cur.close()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update(self, table: str, filters: dict, data: dict) -> dict:
        """Update table"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
            where = " AND ".join([f"{k} = %s" for k in filters.keys()])
            sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
            cur.execute(sql, tuple(data.values()) + tuple(filters.values()))
            conn.commit()
            cur.close()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete(self, table: str, filters: dict) -> dict:
        """Delete from table"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            where = " AND ".join([f"{k} = %s" for k in filters.keys()])
            sql = f"DELETE FROM {table} WHERE {where}"
            cur.execute(sql, tuple(filters.values()))
            conn.commit()
            cur.close()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    import sys
    mcp = SupabaseMCP()
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: supabase_mcp.py <command> [args]"}))
        sys.exit(1)
    
    command = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    
    commands = {
        "query": lambda: mcp.query(**args),
        "insert": lambda: mcp.insert(**args),
        "update": lambda: mcp.update(**args),
        "delete": lambda: mcp.delete(**args),
    }
    
    result = commands.get(command, lambda: {"error": "Unknown command"})()
    print(json.dumps(result))

if __name__ == "__main__":
    main()
