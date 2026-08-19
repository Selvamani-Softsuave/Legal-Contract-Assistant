"""Initial schema migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-19 01:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'Contracts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('contract_number', sa.String(100), nullable=True, unique=True),
        sa.Column('contract_type', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='Draft'),
        sa.Column('effective_date', sa.DateTime(), nullable=True),
        sa.Column('expiration_date', sa.DateTime(), nullable=True),
        sa.Column('governing_law', sa.String(150), nullable=True),
        sa.Column('jurisdiction', sa.String(150), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'Documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('contract_id', sa.String(36), sa.ForeignKey('Contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('blob_path', sa.String(1000), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='Uploaded'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'DocumentChunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('Documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contract_id', sa.String(36), sa.ForeignKey('Contracts.id', ondelete='NO ACTION'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('article', sa.String(100), nullable=True),
        sa.Column('section', sa.String(100), nullable=True),
        sa.Column('subsection', sa.String(100), nullable=True),
        sa.Column('clause', sa.String(100), nullable=True),
        sa.Column('heading', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'ProcessingJobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('Documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('operation', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='Queued'),
        sa.Column('correlation_id', sa.String(36), nullable=False),
        sa.Column('requested_by', sa.String(100), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'Conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('scoped_contract_ids', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'Messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('Conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'RAGSources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('message_id', sa.String(36), sa.ForeignKey('Messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', sa.String(36), sa.ForeignKey('DocumentChunks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('document_name', sa.String(255), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(100), nullable=True),
        sa.Column('clause', sa.String(100), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

def downgrade() -> None:
    op.drop_table('RAGSources')
    op.drop_table('Messages')
    op.drop_table('Conversations')
    op.drop_table('ProcessingJobs')
    op.drop_table('DocumentChunks')
    op.drop_table('Documents')
    op.drop_table('Contracts')
