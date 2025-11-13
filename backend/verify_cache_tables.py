"""Script pour vérifier la création des tables cache"""
from sqlalchemy import create_engine, inspect, text

DATABASE_URL = "postgresql+psycopg2://neondb_owner:npg_wnWutsPQ5vN0@ep-damp-thunder-ado6n9o2-pooler.c-2.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require"

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

print("Verification des tables cache creees...")
print("-" * 60)

# Liste de toutes les tables
all_tables = inspector.get_table_names()

# Tables cache attendues
expected_cache_tables = [
    'product_discovery_cache',
    'product_scoring_cache',
    'search_history'
]

# Vérification
for table in expected_cache_tables:
    if table in all_tables:
        print(f"OK {table}")

        # Afficher les colonnes
        columns = inspector.get_columns(table)
        print(f"   Colonnes ({len(columns)}):")
        for col in columns[:5]:  # Afficher les 5 premières
            print(f"     - {col['name']}: {col['type']}")
        if len(columns) > 5:
            print(f"     ... et {len(columns) - 5} autres colonnes")

        # Afficher les indexes
        indexes = inspector.get_indexes(table)
        if indexes:
            print(f"   Indexes ({len(indexes)}):")
            for idx in indexes:
                print(f"     - {idx['name']}")
        print()
    else:
        print(f"FAIL {table} - MANQUANTE")
        print()

# Compter les enregistrements
print("Comptage des enregistrements:")
with engine.connect() as conn:
    for table in expected_cache_tables:
        if table in all_tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"   {table}: {count} enregistrements")

print("-" * 60)
print("Verification terminee!")
