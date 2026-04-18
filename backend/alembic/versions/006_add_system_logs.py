"""Add system_logs table

Revision ID: 006
Revises: 005_add_calendar_tables
Create Date: 2024-04-19

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create system_logs table
    op.create_table(
        'system_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('severity', sa.String(10), nullable=False, index=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('source', sa.String(100), nullable=False, server_default='system'),
        sa.Column('extra_data', postgresql.JSONB(), nullable=True),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('modules.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), index=True),
    )
    
    # Create index on severity for faster filtering
    op.create_index('ix_system_logs_severity', 'system_logs', ['severity'])
    
    # Create index on created_at for reverse chronological ordering
    op.create_index('ix_system_logs_created_at', 'system_logs', ['created_at'])
    
    # Create composite index for common query patterns
    op.create_index(
        'ix_system_logs_severity_created_at',
        'system_logs',
        ['severity', 'created_at']
    )
    
    # Create index on source for filtering
    op.create_index('ix_system_logs_source', 'system_logs', ['source'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_system_logs_source', table_name='system_logs')
    op.drop_index('ix_system_logs_severity_created_at', table_name='system_logs')
    op.drop_index('ix_system_logs_created_at', table_name='system_logs')
    op.drop_index('ix_system_logs_severity', table_name='system_logs')
    
    # Drop table
    op.drop_table('system_logs')
