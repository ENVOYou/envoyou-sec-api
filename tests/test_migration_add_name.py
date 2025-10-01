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

    # Create table as pre-migration state
    meta = MetaData()
    sa.Table('emissions_calculations', meta,
             sa.Column('id', sa.Text, primary_key=True),
             sa.Column('user_id', sa.Text),
             sa.Column('company', sa.Text),
             sa.Column('calculation_data', sa.Text),
             sa.Column('result', sa.Text),
             sa.Column('version', sa.Text),
             sa.Column('created_at', sa.Text),
             )
    meta.create_all(engine)

    # Import the migration module by file path and run its upgrade() against this connection
    import importlib.util
    import pathlib
    mig_path = pathlib.Path(__file__).parent.parent / 'alembic' / 'versions' / '0001_add_name_to_emissions.py'
    spec = importlib.util.spec_from_file_location('migration_mod', str(mig_path))
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    # Bind op to the connection
    ctx = MigrationContext.configure(conn)
    op_obj = Operations(ctx)

    # Bind the alembic op proxy to our Operations instance so migration.upgrade()
    # can call op.add_column() etc.
    import alembic.op as alembic_op
    alembic_op._proxy = op_obj

    # Run upgrade (it will use alembic.op which is now proxied to our connection)
    migration.upgrade()

    # Reflect table and assert column exists
    insp = sa.inspect(conn)
    cols = [c['name'] for c in insp.get_columns('emissions_calculations')]
    assert 'name' in cols
