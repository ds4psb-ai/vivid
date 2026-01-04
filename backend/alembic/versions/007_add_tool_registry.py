"""Add tool registry tables for scalable workflow planner

Revision ID: 007_add_tool_registry
Revises: 006_add_humancloud
Create Date: 2026-01-04

Tables:
- tools: Core tool definitions with i18n support
- tool_schemas: Versioned JSON schemas per tool
- tool_dependencies: Tool chaining relationships
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '007_add_tool_registry'
down_revision = '006_add_humancloud'
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================================
    # tools - Core tool definitions
    # =========================================================================
    op.create_table(
        'tools',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tool_key', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('dimension', sa.String(10), nullable=False),  # '1D', '2D', '3D', '4D'
        sa.Column('category', sa.String(50), nullable=False, index=True),  # 'generation', 'analysis', 'editing'
        
        # i18n metadata
        sa.Column('name_ko', sa.String(100), nullable=False),
        sa.Column('name_en', sa.String(100), nullable=False),
        sa.Column('description_ko', sa.Text, nullable=True),
        sa.Column('description_en', sa.Text, nullable=True),
        
        # Execution info
        sa.Column('endpoint', sa.String(200), nullable=False),
        sa.Column('executor_type', sa.String(20), nullable=False, server_default='http'),  # 'http', 'grpc', 'serverless'
        sa.Column('timeout_seconds', sa.Integer, nullable=False, server_default='60'),
        
        # Cost & billing
        sa.Column('credit_cost', sa.Integer, nullable=False, server_default='5'),
        sa.Column('billing_type', sa.String(20), nullable=False, server_default='per_run'),  # 'per_run', 'per_minute', 'per_token'
        
        # UI
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        
        # Status flags
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_beta', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_system', sa.Boolean, nullable=False, server_default='false'),  # System tools can't be deleted
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Index for common queries
    op.create_index('ix_tools_dimension', 'tools', ['dimension'])
    op.create_index('ix_tools_is_active', 'tools', ['is_active'])
    
    # =========================================================================
    # tool_schemas - Versioned input/output schemas
    # =========================================================================
    op.create_table(
        'tool_schemas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tool_id', UUID(as_uuid=True), sa.ForeignKey('tools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),  # 'v1.0.0'
        sa.Column('input_schema', JSONB, nullable=False),
        sa.Column('output_schema', JSONB, nullable=False),
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        sa.UniqueConstraint('tool_id', 'version', name='uq_tool_schema_version'),
    )
    
    op.create_index('ix_tool_schemas_tool_current', 'tool_schemas', ['tool_id', 'is_current'])
    
    # =========================================================================
    # tool_dependencies - Tool chaining relationships
    # =========================================================================
    op.create_table(
        'tool_dependencies',
        sa.Column('from_tool_id', UUID(as_uuid=True), sa.ForeignKey('tools.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('to_tool_id', UUID(as_uuid=True), sa.ForeignKey('tools.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('output_to_input_mapping', JSONB, nullable=True),  # {"prompt": "input_text"}
        sa.Column('is_recommended', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # =========================================================================
    # Seed initial 4 tools
    # =========================================================================
    tools_data = [
        {
            'tool_key': 'prompt_generator',
            'dimension': '1D',
            'category': 'generation',
            'name_ko': 'Veo 프롬프트 생성기',
            'name_en': 'Veo Prompt Generator',
            'description_ko': '주제와 스타일을 기반으로 Veo 영상 생성 프롬프트를 만듭니다',
            'description_en': 'Generate Veo video prompts based on topic and style',
            'endpoint': '/api/teaching/prompt/generate',
            'executor_type': 'http',
            'credit_cost': 5,
            'color': 'violet',
            'icon': 'wand-2',
            'is_system': True,
        },
        {
            'tool_key': 'storyboard_generator',
            'dimension': '2D',
            'category': 'generation',
            'name_ko': '스토리보드 아키텍트',
            'name_en': 'Storyboard Architect',
            'description_ko': '스크립트나 개념을 시각적 스토리보드로 변환합니다',
            'description_en': 'Transform scripts or concepts into visual storyboards',
            'endpoint': '/api/teaching/storyboard/create',
            'executor_type': 'http',
            'credit_cost': 10,
            'color': 'emerald',
            'icon': 'layout-grid',
            'is_system': True,
        },
        {
            'tool_key': 'image_generator',
            'dimension': '3D',
            'category': 'generation',
            'name_ko': '이미지 도구',
            'name_en': 'Image Tool',
            'description_ko': 'AI를 활용해 이미지를 생성하고 편집합니다',
            'description_en': 'Generate and edit images using AI',
            'endpoint': '/api/teaching/image/generate',
            'executor_type': 'http',
            'credit_cost': 15,
            'color': 'amber',
            'icon': 'image',
            'is_system': True,
        },
        {
            'tool_key': 'reference_analyzer',
            'dimension': '4D',
            'category': 'analysis',
            'name_ko': '레퍼런스 분석기',
            'name_en': 'Reference Analyzer',
            'description_ko': '레퍼런스 영상이나 이미지를 분석합니다',
            'description_en': 'Analyze reference videos or images',
            'endpoint': '/api/teaching/reference/analyze',
            'executor_type': 'http',
            'credit_cost': 8,
            'color': 'cyan',
            'icon': 'scan',
            'is_system': True,
        },
    ]
    
    # Insert tools
    tools_table = sa.table(
        'tools',
        sa.column('tool_key', sa.String),
        sa.column('dimension', sa.String),
        sa.column('category', sa.String),
        sa.column('name_ko', sa.String),
        sa.column('name_en', sa.String),
        sa.column('description_ko', sa.Text),
        sa.column('description_en', sa.Text),
        sa.column('endpoint', sa.String),
        sa.column('executor_type', sa.String),
        sa.column('credit_cost', sa.Integer),
        sa.column('color', sa.String),
        sa.column('icon', sa.String),
        sa.column('is_system', sa.Boolean),
    )
    op.bulk_insert(tools_table, tools_data)
    
    # Insert schemas for each tool (v1.0.0)
    op.execute("""
        INSERT INTO tool_schemas (tool_id, version, input_schema, output_schema, is_current)
        SELECT id, 'v1.0.0', 
            '{"type": "object", "properties": {"topic": {"type": "string"}, "style": {"type": "string"}, "mood": {"type": "string"}, "duration": {"type": "string"}}, "required": ["topic"]}'::jsonb,
            '{"type": "object", "properties": {"prompt": {"type": "string"}, "negative_prompt": {"type": "string"}}}'::jsonb,
            true
        FROM tools WHERE tool_key = 'prompt_generator';
        
        INSERT INTO tool_schemas (tool_id, version, input_schema, output_schema, is_current)
        SELECT id, 'v1.0.0',
            '{"type": "object", "properties": {"script": {"type": "string"}, "scene_count": {"type": "integer", "default": 5}}, "required": ["script"]}'::jsonb,
            '{"type": "object", "properties": {"scenes": {"type": "array"}}}'::jsonb,
            true
        FROM tools WHERE tool_key = 'storyboard_generator';
        
        INSERT INTO tool_schemas (tool_id, version, input_schema, output_schema, is_current)
        SELECT id, 'v1.0.0',
            '{"type": "object", "properties": {"prompt": {"type": "string"}, "style": {"type": "string"}}, "required": ["prompt"]}'::jsonb,
            '{"type": "object", "properties": {"image_url": {"type": "string"}}}'::jsonb,
            true
        FROM tools WHERE tool_key = 'image_generator';
        
        INSERT INTO tool_schemas (tool_id, version, input_schema, output_schema, is_current)
        SELECT id, 'v1.0.0',
            '{"type": "object", "properties": {"url": {"type": "string"}, "focus": {"type": "array"}}, "required": ["url"]}'::jsonb,
            '{"type": "object", "properties": {"analysis": {"type": "object"}}}'::jsonb,
            true
        FROM tools WHERE tool_key = 'reference_analyzer';
    """)
    
    # Insert recommended tool chains
    op.execute("""
        -- prompt_generator -> storyboard_generator (recommended)
        INSERT INTO tool_dependencies (from_tool_id, to_tool_id, output_to_input_mapping, is_recommended)
        SELECT t1.id, t2.id, '{"prompt": "script"}'::jsonb, true
        FROM tools t1, tools t2
        WHERE t1.tool_key = 'prompt_generator' AND t2.tool_key = 'storyboard_generator';
        
        -- storyboard_generator -> image_generator
        INSERT INTO tool_dependencies (from_tool_id, to_tool_id, output_to_input_mapping, is_recommended)
        SELECT t1.id, t2.id, '{"scene_description": "prompt"}'::jsonb, true
        FROM tools t1, tools t2
        WHERE t1.tool_key = 'storyboard_generator' AND t2.tool_key = 'image_generator';
        
        -- reference_analyzer -> prompt_generator
        INSERT INTO tool_dependencies (from_tool_id, to_tool_id, output_to_input_mapping, is_recommended)
        SELECT t1.id, t2.id, '{"analysis.style": "style"}'::jsonb, false
        FROM tools t1, tools t2
        WHERE t1.tool_key = 'reference_analyzer' AND t2.tool_key = 'prompt_generator';
    """)


def downgrade():
    op.drop_table('tool_dependencies')
    op.drop_table('tool_schemas')
    op.drop_table('tools')
