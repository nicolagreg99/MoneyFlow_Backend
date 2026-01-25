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
            CONSTRAINT entrate_user_id_fkey
                FOREIGN KEY(user_id) REFERENCES users(id)
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

    # USER CATEGORIES
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_categories (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            expenses_categories JSONB DEFAULT '[]',
            incomes_categories JSONB DEFAULT '[]',
            CONSTRAINT user_categories_user_id_fkey
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # EXCHANGE RATES CACHE
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
    print("Aggiornamento colonne...")

    # USERS
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE;")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255);")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS default_currency VARCHAR(3) DEFAULT 'EUR';")

    # SPESE - currency
    cur.execute("ALTER TABLE spese ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'EUR';")
    cur.execute("ALTER TABLE spese ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(12,6) DEFAULT 1.0;")

    # ENTRATE - currency
    cur.execute("ALTER TABLE entrate ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'EUR';")
    cur.execute("ALTER TABLE entrate ADD COLUMN IF NOT EXISTS exchange_rate NUMERIC(12,6) DEFAULT 1.0;")

    # NORMALIZE EXISTING DATA
    print("Normalizzazione dati esistenti...")
    cur.execute("UPDATE spese SET currency = 'EUR' WHERE currency IS NULL;")
    cur.execute("UPDATE spese SET exchange_rate = 1.0 WHERE exchange_rate IS NULL;")
    cur.execute("UPDATE entrate SET currency = 'EUR' WHERE currency IS NULL;")
    cur.execute("UPDATE entrate SET exchange_rate = 1.0 WHERE exchange_rate IS NULL;")

    conn.commit()

    # -----------------------------------------------------
    # ASSETS
    print("Creazione tabella assets...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            bank VARCHAR(255) NOT NULL,
            asset_type VARCHAR(255) NOT NULL,
            amount NUMERIC NOT NULL,
            currency VARCHAR(3) NOT NULL,
            exchange_rate NUMERIC DEFAULT 1.0,
            is_payable BOOLEAN NOT NULL DEFAULT FALSE,
            last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT unique_user_bank_asset_currency
                UNIQUE (user_id, bank, asset_type, currency),

            CONSTRAINT assets_user_id_fkey
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );
    """)

    # ASSET TRANSACTIONS
    print("Creazione tabella asset_transactions...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS asset_transactions (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,

            from_asset_id INTEGER,
            to_asset_id INTEGER,

            amount NUMERIC NOT NULL,
            converted_amount NUMERIC,
            from_currency VARCHAR(3) NOT NULL,
            to_currency VARCHAR(3) NOT NULL,

            transaction_type VARCHAR(50) NOT NULL,
            exchange_rate NUMERIC(12,6),

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT asset_transactions_user_id_fkey
                FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            CONSTRAINT asset_transactions_from_asset_fkey
                FOREIGN KEY (from_asset_id)
                REFERENCES assets(id),

            CONSTRAINT asset_transactions_to_asset_fkey
                FOREIGN KEY (to_asset_id)
                REFERENCES assets(id)
        );
    """)

    conn.commit()

    # -----------------------------------------------------
    # LINK SPESE ↔ ASSETS
    print("Update spese con payment_asset_id...")
    cur.execute("ALTER TABLE spese ADD COLUMN IF NOT EXISTS payment_asset_id INTEGER;")

    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'expenses_payment_asset_fkey'
            ) THEN
                ALTER TABLE spese
                ADD CONSTRAINT expenses_payment_asset_fkey
                FOREIGN KEY (payment_asset_id)
                REFERENCES assets(id)
                ON DELETE RESTRICT;
            END IF;
        END $$;
    """)

    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'chk_spese_positive_amount'
            ) THEN
                ALTER TABLE spese
                ADD CONSTRAINT chk_spese_positive_amount
                CHECK (valore > 0);
            END IF;
        END $$;
    """)

    # -----------------------------------------------------
    # LINK ENTRATE ↔ ASSETS
    print("Update entrate con payment_asset_id...")
    cur.execute("ALTER TABLE entrate ADD COLUMN IF NOT EXISTS payment_asset_id INTEGER;")

    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'incomes_payment_asset_fkey'
            ) THEN
                ALTER TABLE entrate
                ADD CONSTRAINT incomes_payment_asset_fkey
                FOREIGN KEY (payment_asset_id)
                REFERENCES assets(id)
                ON DELETE RESTRICT;
            END IF;
        END $$;
    """)

    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'chk_entrate_positive_amount'
            ) THEN
                ALTER TABLE entrate
                ADD CONSTRAINT chk_entrate_positive_amount
                CHECK (valore > 0);
            END IF;
        END $$;
    """)

    conn.commit()

    cur.close()
    conn.close()
    print("Migration completed!")


if __name__ == "__main__":
    migrate()
