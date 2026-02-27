import asyncio
import asyncpg

async def create_db():
    print("Connecting to default postgres database...")
    # Connect to the default 'postgres' database
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/postgres')
    try:
        # Create database (must be outside of a transaction block in postgres)
        print("Creating credit_network database...")
        await conn.execute('CREATE DATABASE credit_network')
        print("Database created successfully!")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print("Database 'credit_network' already exists!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_db())
