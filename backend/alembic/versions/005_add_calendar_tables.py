"""Add calendar events and keyword filters

Revision ID: 005
Revises: 004_add_portfolio_tables
Create Date: 2024-01-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_add_calendar_tables'
down_revision: Union[str, None] = '004_add_portfolio_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create calendar_events table
    op.create_table(
        'calendar_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('modules.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_all_day', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('event_type', sa.String(20), nullable=False, server_default='personal'),
        sa.Column('source', sa.String(50), nullable=False, server_default='manual'),
        sa.Column('external_id', sa.String(100), nullable=True, index=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('impact', sa.String(10), nullable=True),
        sa.Column('currency', sa.String(3), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('actual_value', sa.String(50), nullable=True),
        sa.Column('forecast_value', sa.String(50), nullable=True),
        sa.Column('previous_value', sa.String(50), nullable=True),
        sa.Column('recurrence_rule', sa.String(500), nullable=True),
        sa.Column('parent_event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('calendar_events.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create calendar_keyword_filters table
    op.create_table(
        'calendar_keyword_filters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('modules.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('keyword', sa.String(100), nullable=False),
        sa.Column('is_include', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('calendar_keyword_filters')
    op.drop_table('calendar_events')
