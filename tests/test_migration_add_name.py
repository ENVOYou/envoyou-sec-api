import sqlalchemy as sa
from sqlalchemy import MetaData, Table, Column, Integer, Text
from sqlalchemy import create_engine

from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations

from alembic import op

import importlib


def create_initial_table(engine):
    # create a minimal emissions_calculations table without the `name` column
    meta = MetaData()
    Table(
        'emissions_calculations',
        meta,
        Column('id', TextPrimaryKey := sa.Text, primary_key=True),
        Column('user_id', sa.Text),
        Column('company', sa.Text),
        Column('calculation_data', sa.Text),
        Column('result', sa.Text),
        Column('version', sa.Text),
        Column('created_at', sa.Text),
    )
    meta.create_all(engine)


def test_migration_adds_name_column():
    engine = create_engine('sqlite:///:memory:')
    conn = engine.connect()

    # Import the initial migration and run it
    import importlib.util
    import pathlib
    mig_path = pathlib.Path(__file__).parent.parent / 'alembic' / 'versions' / '0001_initial_tables.py'
    spec = importlib.util.spec_from_file_location('migration_mod', str(mig_path))
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    # Bind op to the connection
    ctx = MigrationContext.configure(conn)
    op_obj = Operations(ctx)

    # Bind the alembic op proxy to our Operations instance
    import alembic.op as alembic_op
    alembic_op._proxy = op_obj

    # Run upgrade (creates all tables including emissions_calculations with name column)
    migration.upgrade()

    # Reflect table and assert name column exists
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('emissions_calculations')]
    assert 'name' in cols, f"Expected 'name' column in emissions_calculations, got columns: {cols}"
