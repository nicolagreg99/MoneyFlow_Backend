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


# -----------------------------------------------------
# CREATE TABLES
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

    print("Creazione tabella cache tassi di cambio...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exchange_rates_cache (
            id SERIAL PRIMARY KEY,
            base_currency VARCHAR(3) NOT NULL,
            target_currency VARCHAR(3) NOT NULL,
            rate_date DATE NOT NULL,
            exchange_rate NUMERIC(12,6) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(base_currency, target_currency, rate_date)
        );
    """)

    conn.commit()

# -----------------------------------------------------
# UPDATE COLUMNS

    # Verify user
    print("Verifica ed eventuale aggiunta colonne 'verified' e 'verification_token'...")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE;")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255);")

    # EXCHANGE RATES - COLONNE PER SPESE
    print("Creazione colonne echange rates spese...")
    cur.execute("ALTER TABLE spese ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'EUR';")
    cur.execute("ALTER TABLE spese ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(12,6) DEFAULT 1.0;")
    
    # EXCHANGE RATES - COLONNE PER ENTRATE
    print("Creazione colonne echange rates entrate...")
    cur.execute("ALTER TABLE entrate ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'EUR';")
    cur.execute("ALTER TABLE entrate ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(12,6) DEFAULT 1.0;")
    
    # VALUTA DEFAULT UTENTE
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS default_currency VARCHAR(3) DEFAULT 'EUR';")

    # AGGIORNA I DATI ESISTENTI
    print("Aggiornamento dati esistenti...")
    cur.execute("UPDATE spese SET exchange_rate = 1.0 WHERE exchange_rate IS NULL;")
    cur.execute("UPDATE spese SET currency = 'EUR' WHERE currency IS NULL;")
    cur.execute("UPDATE entrate SET exchange_rate = 1.0 WHERE exchange_rate IS NULL;")
    cur.execute("UPDATE entrate SET currency = 'EUR' WHERE currency IS NULL;")

    conn.commit()
    cur.close()
    conn.close()
    print("Migrazione completata.")

if __name__ == "__main__":
    migrate()