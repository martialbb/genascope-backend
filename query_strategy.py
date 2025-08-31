#!/usr/bin/env python3
"""
Query the chat strategy name by ID
"""
import os
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def query_strategy():
    """Query the strategy name by ID"""
    # Get database URI from environment
    database_uri = os.getenv("DATABASE_URI")
    if not database_uri:
        print("❌ DATABASE_URI not found in environment variables")
        return
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_uri)
        print("✅ Connected to database")
        
        # Query for the strategy
        strategy_id = "e6a59eea-906f-43af-9ce1-c33b1e3f3a6e"
        
        # First, let's see what tables might contain strategies
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%strategy%' OR table_name LIKE '%chat%'
        ORDER BY table_name;
        """
        
        tables = await conn.fetch(tables_query)
        print("\n📋 Tables containing 'strategy' or 'chat':")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # Try to find the strategy in potential tables
        potential_tables = ['chat_strategies', 'strategies', 'chat_strategy_configs']
        
        for table_name in potential_tables:
            try:
                query = f"""
                SELECT * FROM {table_name} 
                WHERE id = $1;
                """
                result = await conn.fetch(query, strategy_id)
                if result:
                    print(f"\n✅ Found strategy in table '{table_name}':")
                    for row in result:
                        print(f"   {dict(row)}")
                    break
            except Exception as e:
                print(f"   Table '{table_name}' not found or error: {str(e)}")
        else:
            print(f"\n❌ Strategy with ID {strategy_id} not found in common tables")
            
            # Let's try a broader search
            print("\n🔍 Searching all tables for this ID...")
            all_tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """
            all_tables = await conn.fetch(all_tables_query)
            
            for table in all_tables:
                table_name = table['table_name']
                try:
                    # Check if table has an 'id' column
                    columns_query = f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND column_name = 'id';
                    """
                    has_id = await conn.fetch(columns_query)
                    
                    if has_id:
                        search_query = f"SELECT * FROM {table_name} WHERE id = $1;"
                        result = await conn.fetch(search_query, strategy_id)
                        if result:
                            print(f"\n✅ Found in table '{table_name}':")
                            for row in result:
                                print(f"   {dict(row)}")
                            break
                except Exception:
                    continue
        
        await conn.close()
        print("\n🔌 Database connection closed")
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(query_strategy())
