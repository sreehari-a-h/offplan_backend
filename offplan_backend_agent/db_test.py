import psycopg2

try:
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='your-db-password',
        host='db.xtzdmalumstpitlmiscl.supabase.co',
        # host='aws-0-ap-south-1.pooler.supabase.com',
        port='5432',
        sslmode='require'
    )
    print("✅ Connected successfully!")
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
