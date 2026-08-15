from django.db import migrations


def create_postgres_search_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    statements = (
        "CREATE EXTENSION IF NOT EXISTS pg_trgm",
        "CREATE INDEX IF NOT EXISTS cat_product_name_trgm_idx ON catalog_product USING gin (name gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS cat_product_code_trgm_idx ON catalog_product USING gin (code gin_trgm_ops)",
        "CREATE INDEX IF NOT EXISTS cat_product_search_fts_idx ON catalog_product USING gin (to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(description, '')))",
        "CREATE INDEX IF NOT EXISTS cat_identifier_value_trgm_idx ON catalog_productidentifier USING gin (normalized_value gin_trgm_ops)",
    )
    with schema_editor.connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def drop_postgres_search_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        for name in ("cat_identifier_value_trgm_idx", "cat_product_search_fts_idx", "cat_product_code_trgm_idx", "cat_product_name_trgm_idx"):
            cursor.execute(f"DROP INDEX IF EXISTS {name}")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0009_attributedefinition_productbrand_and_more")]
    operations = [migrations.RunPython(create_postgres_search_indexes, drop_postgres_search_indexes)]
