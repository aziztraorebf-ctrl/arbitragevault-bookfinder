#!/usr/bin/env python3
"""
Export Render Database - Migration vers Neon
Script d'extraction des données depuis Render PostgreSQL via SQLAlchemy app existante

Pattern: Utilise la connexion app existante pour contourner les problèmes MCP/SSL
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.core.db import DatabaseManagerManager
from app.core.settings import get_settings
from sqlalchemy import text


async def export_table_structure():
    """Export structure des tables pour recreation sur Neon."""
    
    print("📋 Exporting table structure from Render...")
    
    db = DatabaseManager()
    await db.initialize()
    
    structure_queries = [
        # Tables info
        """
        SELECT table_name, column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        ORDER BY table_name, ordinal_position;
        """,
        
        # Indexes info
        """
        SELECT schemaname, tablename, indexname, indexdef
        FROM pg_indexes 
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname;
        """,
        
        # Constraints info
        """
        SELECT tc.table_name, tc.constraint_name, tc.constraint_type,
               kcu.column_name, ccu.table_name AS foreign_table_name,
               ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        LEFT JOIN information_schema.constraint_column_usage ccu 
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_schema = 'public'
        ORDER BY tc.table_name, tc.constraint_name;
        """
    ]
    
    results = {}
    
    try:
        async with db.get_session() as session:
            if not session.is_active:
                print("❌ Database session not active")
                return None
                
            for i, query in enumerate(structure_queries):
                query_name = ["columns", "indexes", "constraints"][i]
                print(f"  Executing {query_name} query...")
                
                result = await session.execute(text(query))
                rows = result.fetchall()
                
                results[query_name] = [
                    {column: value for column, value in zip(result.keys(), row)}
                    for row in rows
                ]
                
                print(f"  ✅ Found {len(rows)} {query_name}")
                
    except Exception as e:
        print(f"❌ Error exporting structure: {e}")
        return None
    finally:
        await db.close()
    
    return results


async def export_table_data():
    """Export data des tables pour migration."""
    
    print("📊 Exporting table data from Render...")
    
    db = DatabaseManager()
    await db.initialize()
    
    try:
        async with db.get_session() as session:
            if not session.is_active:
                print("❌ Database session not active")
                return None
                
            # Get list of tables
            tables_result = await session.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in tables_result.fetchall()]
            print(f"  Found {len(tables)} tables: {tables}")
            
            table_data = {}
            
            for table_name in tables:
                print(f"  Exporting {table_name}...")
                
                # Get row count first
                count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
                row_count = count_result.scalar()
                print(f"    {row_count} rows")
                
                if row_count > 0:
                    # Export data (limit for safety)
                    limit = 1000  # Adjust as needed
                    data_result = await session.execute(text(f"SELECT * FROM {table_name} LIMIT {limit};"))
                    rows = data_result.fetchall()
                    
                    table_data[table_name] = {
                        "columns": list(data_result.keys()),
                        "rows": [[str(col) if col is not None else None for col in row] for row in rows],
                        "total_count": row_count,
                        "exported_count": len(rows)
                    }
                else:
                    table_data[table_name] = {
                        "columns": [],
                        "rows": [],
                        "total_count": 0,
                        "exported_count": 0
                    }
            
            return table_data
            
    except Exception as e:
        print(f"❌ Error exporting data: {e}")
        return None
    finally:
        await db.close()


async def main():
    """Export principal Render -> Neon migration."""
    
    print("🚀 RENDER TO NEON MIGRATION - Data Export")
    print("=" * 60)
    
    # Export structure
    structure = await export_table_structure()
    if structure:
        with open("render_structure.json", "w") as f:
            json.dump(structure, f, indent=2, default=str)
        print("✅ Structure exported to render_structure.json")
    else:
        print("❌ Failed to export structure")
        return False
    
    # Export data
    data = await export_table_data()
    if data:
        with open("render_data.json", "w") as f:
            json.dump(data, f, indent=2, default=str)
        print("✅ Data exported to render_data.json")
        
        # Summary
        total_tables = len(data)
        total_rows = sum(table["total_count"] for table in data.values())
        print(f"📊 Export Summary: {total_tables} tables, {total_rows} total rows")
        
    else:
        print("❌ Failed to export data")
        return False
    
    print("\n✅ Export completed successfully!")
    print("Next: Import to Neon using MCP tools")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)