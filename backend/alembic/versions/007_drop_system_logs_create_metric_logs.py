"""Drop system_logs table, create metric_logs table

Revision ID: 007
Revises: 006_add_system_logs
Create Date: 2026-04-22

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the orphaned system_logs table (file-based logging replaced DB logging)
    # Note: auto-created indexes are dropped with the table
    op.drop_index('ix_system_logs_source', table_name='system_logs')
    op.drop_index('ix_system_logs_severity_created_at', table_name='system_logs')
    op.drop_table('system_logs')
    
    # Create new metric_logs table for the MetricLog model (renamed from SystemLog in metrics.py)
    op.create_table(
        'metric_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('level', sa.String(20), nullable=False, index=True),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), default=dict, nullable=False),
    )


def downgrade() -> None:
    # Drop metric_logs table
    op.drop_table('metric_logs')
    
    # Recreate system_logs table (from migration 006)
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
    
    op.create_index(
        'ix_system_logs_severity_created_at',
        'system_logs',
        ['severity', 'created_at']
    )
    op.create_index('ix_system_logs_source', 'system_logs', ['source'])
