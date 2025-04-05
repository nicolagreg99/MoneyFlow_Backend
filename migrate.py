import psycopg2
from config import DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST

def migrate():
    conn = psycopg2.connect(
        dbname=DATABASE_NAME,
        user=DATABASE_USER,
        password=DATABASE_PASSWORD,
        host=DATABASE_HOST
    )
    cur = conn.cursor()

    print("Creazione tabelle...")

    # USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reset_token VARCHAR(255),
            reset_token_expiry TIMESTAMP,
            last_name VARCHAR(255),
            first_name VARCHAR(255),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ENTRATE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entrate (
            id SERIAL PRIMARY KEY,
            valore NUMERIC(10, 2) NOT NULL,
            tipo VARCHAR(255) NOT NULL,
            giorno DATE NOT NULL,
            inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fields JSONB,
            user_id INTEGER NOT NULL,
            CONSTRAINT idx_entrate_user_id FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)

    # SPESE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS spese (
            id SERIAL PRIMARY KEY,
            valore NUMERIC,
            tipo TEXT,
            giorno DATE,
            inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fields JSON,
            user_id INTEGER
        );
    """)

    # USER_CATEGORIES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_categories (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            expenses_categories JSONB DEFAULT '[]',
            incomes_categories JSONB DEFAULT '[]',
            CONSTRAINT user_categories_user_id_fkey FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Migrazione completata.")

if __name__ == "__main__":
    migrate()
