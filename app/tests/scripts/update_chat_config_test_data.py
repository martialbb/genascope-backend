#!/usr/bin/env python3
"""
Update chat configuration test data with new required fields.
This script adds values for account_id, goal, specialty, patient_introduction, and is_active.
"""

import os
import sys
import psycopg2
from datetime import datetime

# Database connection parameters
DB_HOST = os.getenv('POSTGRES_HOST', 'db')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'genascope')
DB_USER = os.getenv('POSTGRES_USER', 'genascope')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'genascope')

def get_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def update_chat_strategies():
    """Update chat_strategies with new required fields."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # First get the current strategies
            cursor.execute("SELECT id, name FROM chat_strategies ORDER BY created_at")
            current_strategies = cursor.fetchall()
            print(f"Found {len(current_strategies)} chat strategies to update")
            
            # Update each strategy with new fields
            for i, (strategy_id, name) in enumerate(current_strategies):
                account_id = '4941a71c-765e-43b9-aaf1-307b9ee1cebd'  # Use existing account_id
                
                if 'genetic' in name.lower() or 'counseling' in name.lower():
                    goal = 'Provide genetic counseling guidance and support'
                    specialty = 'Genetics'
                    patient_introduction = 'Hello! I\'m here to help you understand your genetic test results and provide guidance on next steps.'
                elif 'oncology' in name.lower() or 'screening' in name.lower():
                    goal = 'Support oncology patients with genetic counseling'
                    specialty = 'Oncology'
                    patient_introduction = 'Welcome! I\'m your genetic counselor assistant, ready to help you navigate your genetic health information.'
                elif 'cardiac' in name.lower() or 'cardiology' in name.lower():
                    goal = 'Provide cardiology-focused genetic counseling'
                    specialty = 'Cardiology'
                    patient_introduction = 'Hi there! I\'m here to help you understand genetic factors related to heart health.'
                else:
                    goal = 'Provide personalized genetic counseling and support'
                    specialty = 'Genetics'
                    patient_introduction = 'Hello! I\'m your genetic counselor assistant, here to help with your health questions.'
                
                cursor.execute("""
                    UPDATE chat_strategies 
                    SET account_id = %s, goal = %s, specialty = %s, 
                        patient_introduction = %s, is_active = %s, updated_at = %s
                    WHERE id = %s
                """, (
                    account_id, goal, specialty, patient_introduction, 
                    True, datetime.utcnow(), strategy_id
                ))
                
                print(f"  Updated strategy '{name}' with specialty '{specialty}'")
            
        conn.commit()
        print(f"Successfully updated {len(current_strategies)} chat strategies with new fields")
    except Exception as e:
        conn.rollback()
        print(f"Error updating chat strategies: {e}")
        raise
    finally:
        conn.close()

def update_knowledge_sources():
    """Update knowledge_sources with is_active field (only field added by migration)."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # The migration already added is_active with default true, so just verify
            cursor.execute("SELECT COUNT(*) FROM knowledge_sources WHERE is_active IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                cursor.execute("UPDATE knowledge_sources SET is_active = true WHERE is_active IS NULL")
                print(f"Updated {null_count} knowledge sources to set is_active = true")
            else:
                print("All knowledge sources already have is_active field populated")
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error updating knowledge sources: {e}")
        raise
    finally:
        conn.close()

def verify_updates():
    """Verify that all required fields are now populated."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check chat_strategies
            cursor.execute("""
                SELECT id, name, account_id, goal, specialty, patient_introduction, is_active 
                FROM chat_strategies 
                ORDER BY created_at
            """)
            strategies = cursor.fetchall()
            print(f"\nChat Strategies ({len(strategies)} total):")
            for strategy in strategies:
                print(f"  ID: {strategy[0][:8]}... | Name: {strategy[1]} | Specialty: {strategy[4]} | Active: {strategy[6]}")
            
            # Check knowledge_sources
            cursor.execute("""
                SELECT id, name, account_id, is_active 
                FROM knowledge_sources 
                ORDER BY created_at
            """)
            sources = cursor.fetchall()
            print(f"\nKnowledge Sources ({len(sources)} total):")
            for source in sources:
                print(f"  ID: {source[0][:8]}... | Name: {source[1]} | Account: {source[2]} | Active: {source[3]}")
            
            # Check for any null values in required fields
            cursor.execute("""
                SELECT COUNT(*) FROM chat_strategies 
                WHERE account_id IS NULL OR goal IS NULL OR specialty IS NULL 
                   OR patient_introduction IS NULL OR is_active IS NULL
            """)
            null_strategies = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM knowledge_sources 
                WHERE account_id IS NULL OR is_active IS NULL
            """)
            null_sources = cursor.fetchone()[0]
            
            print(f"\nValidation:")
            print(f"  Chat strategies with null required fields: {null_strategies}")
            print(f"  Knowledge sources with null required fields: {null_sources}")
            
            if null_strategies == 0 and null_sources == 0:
                print("  ✅ All required fields are populated!")
                return True
            else:
                print("  ❌ Some required fields are still null")
                return False
                
    finally:
        conn.close()

def main():
    """Main function to update test data."""
    print("Updating chat configuration test data with new required fields...")
    
    try:
        update_chat_strategies()
        update_knowledge_sources()
        verify_updates()
        print("\n✅ Test data update completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error updating test data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
