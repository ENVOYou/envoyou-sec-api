#!/usr/bin/env python3
"""MCP Server for Supabase operations"""
import os
import json
from typing import Any
from supabase import create_client, Client

class SupabaseMCP:
    def __init__(self):
        self.client: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
    
    def query(self, table: str, filters: dict = None, select: str = "*") -> dict:
        """Query Supabase table"""
        query = self.client.table(table).select(select)
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        return {"data": query.execute().data}
    
    def insert(self, table: str, data: dict) -> dict:
        """Insert into Supabase table"""
        result = self.client.table(table).insert(data).execute()
        return {"data": result.data}
    
    def update(self, table: str, filters: dict, data: dict) -> dict:
        """Update Supabase table"""
        query = self.client.table(table).update(data)
        for key, value in filters.items():
            query = query.eq(key, value)
        return {"data": query.execute().data}
    
    def delete(self, table: str, filters: dict) -> dict:
        """Delete from Supabase table"""
        query = self.client.table(table).delete()
        for key, value in filters.items():
            query = query.eq(key, value)
        return {"data": query.execute().data}

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
