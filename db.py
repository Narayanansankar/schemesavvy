import psycopg2
import pandas as pd

DB_NAME = "scheme_savvy_db"
DB_USER = "postgres"
DB_PASSWORD = "sankar0711"
DB_HOST = "localhost"
DB_PORT = "5432"

csv_file_path = 'regulated_quotes_schemes.csv'

try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    print("Connected to the database!")

    data = pd.read_csv(csv_file_path)

    for index, row in data.iterrows():
        cur.execute("""
            INSERT INTO schemes (scheme_name, scheme_link, details, benefits, eligibility, application_process, documents_required, Category, State) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['scheme_name'],
            row['scheme_link'],
            row['details'],
            row['benefits'],
            row['eligibility'],
            row['application_process'],
            row['documents_required'],
            row['Category'],
            row['State']
        ))

    conn.commit()
    print("Data inserted successfully!")

except Exception as e:
    print(f"Error: {e}")

finally:
    cur.close()
    conn.close()
    print("Database connection closed.")
