"""Widen chunk_id column in RAGSources table

Revision ID: 002_widen_chunk_id
Revises: 001_initial_schema
Create Date: 2026-08-20 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '002_widen_chunk_id'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
    DECLARE @fk_name NVARCHAR(256);
    SELECT @fk_name = fk.name
    FROM sys.foreign_keys fk
    JOIN sys.tables t ON fk.parent_object_id = t.object_id
    WHERE t.name = 'RAGSources' AND fk.referenced_object_id = OBJECT_ID('DocumentChunks');
    IF @fk_name IS NOT NULL
        EXEC('ALTER TABLE [RAGSources] DROP CONSTRAINT [' + @fk_name + ']');
    
    ALTER TABLE [RAGSources] ALTER COLUMN [chunk_id] VARCHAR(255) NULL;
    """)

def downgrade() -> None:
    op.alter_column(
        'RAGSources',
        'chunk_id',
        existing_type=sa.String(255),
        type_=sa.String(36),
        existing_nullable=True,
        nullable=True
    )
