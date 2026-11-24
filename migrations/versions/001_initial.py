"""Initial migration: users, devices, device_credentials, device_status, audit_logs, activity_logs

Revision ID: 001_initial
Revises:
Create Date: 2026-11-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('hashed_password', sa.String(length=1024), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # 2. devices table
    op.create_table(
        'devices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('model', sa.String(length=128), nullable=True),
        sa.Column('manufacturer', sa.String(length=128), nullable=True),
        sa.Column('android_version', sa.String(length=32), nullable=True),
        sa.Column('app_version', sa.String(length=32), nullable=True),
        sa.Column('install_id', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('install_id')
    )
    op.create_index(op.f('ix_devices_owner_id'), 'devices', ['owner_id'], unique=False)

    # 3. device_credentials table
    op.create_table(
        'device_credentials',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('device_id', sa.String(length=36), nullable=False),
        sa.Column('api_key', sa.String(length=1024), nullable=False),
        sa.Column('pairing_code', sa.String(length=16), nullable=True),
        sa.Column('pairing_code_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paired_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id')
    )

    # 4. device_status table
    op.create_table(
        'device_status',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('device_id', sa.String(length=36), nullable=False),
        sa.Column('battery_level', sa.Integer(), nullable=True),
        sa.Column('is_charging', sa.Boolean(), nullable=True),
        sa.Column('network_type', sa.String(length=32), nullable=True),
        sa.Column('wifi_ssid', sa.String(length=128), nullable=True),
        sa.Column('storage_available_gb', sa.Float(), nullable=True),
        sa.Column('uptime_seconds', sa.Integer(), nullable=True),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_online', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id')
    )

    # 5. audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('device_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_device_id'), 'audit_logs', ['device_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)

    # 6. activity_logs table
    op.create_table(
        'activity_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('device_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_logs_device_id'), 'activity_logs', ['device_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_activity_logs_device_id'), table_name='activity_logs')
    op.drop_table('activity_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_device_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_table('device_status')
    op.drop_table('device_credentials')
    op.drop_index(op.f('ix_devices_owner_id'), table_name='devices')
    op.drop_table('devices')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
