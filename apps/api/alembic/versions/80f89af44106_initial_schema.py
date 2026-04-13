"""initial_schema

Revision ID: 80f89af44106
Revises:
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '80f89af44106'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    # Sources
    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('base_url', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Products
    op.create_table(
        'products',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('sources.id'), nullable=False),
        sa.Column('external_id', sa.String(255)),
        sa.Column('slug', sa.String(512), unique=True, nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('brand', sa.String(255)),
        sa.Column('price_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(3), server_default='EUR'),
        sa.Column('original_url', sa.Text(), nullable=False),
        sa.Column('affiliate_url', sa.Text()),
        sa.Column('image_urls', sa.dialects.postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('category', sa.String(255)),
        sa.Column('subcategory', sa.String(255)),
        sa.Column('gender', sa.String(20)),
        sa.Column('sizes', sa.dialects.postgresql.JSONB(), server_default='[]'),
        sa.Column('colors', sa.dialects.postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('material', sa.Text()),
        sa.Column('tags', sa.dialects.postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('country_availability', sa.dialects.postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('embedding', Vector(768)),
        sa.Column('scraped_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('is_available', sa.Boolean(), server_default='true'),
        sa.Column('language', sa.String(5), server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_products_source', 'products', ['source_id'])
    op.create_index('idx_products_category', 'products', ['category'])
    op.create_index('idx_products_gender', 'products', ['gender'])
    op.create_index('idx_products_brand', 'products', ['brand'])
    op.create_index('idx_products_price', 'products', ['price_cents'])
    op.create_index('idx_products_tags', 'products', ['tags'], postgresql_using='gin')
    op.create_index('idx_products_colors', 'products', ['colors'], postgresql_using='gin')
    op.create_index('idx_products_country', 'products', ['country_availability'], postgresql_using='gin')

    # Product translations
    op.create_table(
        'product_translations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('product_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('locale', sa.String(5), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('slug', sa.String(512), nullable=False),
        sa.Column('meta_title', sa.String(255)),
        sa.Column('meta_description', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('product_id', 'locale'),
    )
    op.create_index('idx_product_translations_locale', 'product_translations', ['locale'])
    op.create_index('idx_product_translations_slug', 'product_translations', ['slug'])

    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True),
        sa.Column('display_name', sa.String(255)),
        sa.Column('avatar_url', sa.Text()),
        sa.Column('locale', sa.String(5), server_default='en'),
        sa.Column('country', sa.String(2)),
        sa.Column('timezone', sa.String(50)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # User profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('gender', sa.String(20)),
        sa.Column('age_range', sa.String(20)),
        sa.Column('body_type', sa.String(50)),
        sa.Column('height_cm', sa.Integer()),
        sa.Column('weight_kg', sa.Integer()),
        sa.Column('preferred_sizes', sa.dialects.postgresql.JSONB(), server_default='{}'),
        sa.Column('style_tags', sa.dialects.postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('favorite_brands', sa.dialects.postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('favorite_colors', sa.dialects.postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('budget_min_cents', sa.Integer()),
        sa.Column('budget_max_cents', sa.Integer()),
        sa.Column('currency', sa.String(3), server_default='EUR'),
        sa.Column('onboarding_completed', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # User events
    op.create_table(
        'user_events',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('session_id', sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('product_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='SET NULL')),
        sa.Column('metadata', sa.dialects.postgresql.JSONB(), server_default='{}'),
        sa.Column('duration_ms', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_user_events_user', 'user_events', ['user_id'])
    op.create_index('idx_user_events_product', 'user_events', ['product_id'])
    op.create_index('idx_user_events_type', 'user_events', ['event_type'])
    op.create_index('idx_user_events_created', 'user_events', ['created_at'])

    # Wishlists
    op.create_table(
        'wishlists',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'product_id'),
    )

    # Recommendations
    op.create_table(
        'recommendations',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('reason', sa.Text()),
        sa.Column('context', sa.dialects.postgresql.JSONB(), server_default='{}'),
        sa.Column('agent_run_id', sa.String(255)),
        sa.Column('is_dismissed', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_recommendations_user', 'recommendations', ['user_id'])
    op.create_index('idx_recommendations_user_date', 'recommendations', ['user_id', 'created_at'])

    # Fashion trends
    op.create_table(
        'fashion_trends',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('season', sa.String(20)),
        sa.Column('region', sa.String(50)),
        sa.Column('gender', sa.String(20)),
        sa.Column('age_range', sa.String(20)),
        sa.Column('trend_tags', sa.dialects.postgresql.ARRAY(sa.Text()), server_default='{}'),
        sa.Column('description', sa.Text()),
        sa.Column('source', sa.String(255)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Seed sources
    op.execute("""
        INSERT INTO sources (name, base_url) VALUES
        ('zalando', 'https://www.zalando.fr'),
        ('asos', 'https://www.asos.com'),
        ('zara', 'https://www.zara.com'),
        ('hm', 'https://www.hm.com')
    """)


def downgrade() -> None:
    op.drop_table('fashion_trends')
    op.drop_table('recommendations')
    op.drop_table('wishlists')
    op.drop_table('user_events')
    op.drop_table('user_profiles')
    op.drop_table('users')
    op.drop_table('product_translations')
    op.drop_table('products')
    op.drop_table('sources')
