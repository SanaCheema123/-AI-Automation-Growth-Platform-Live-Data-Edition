-- AI Automation Growth Platform - clean PostgreSQL/Supabase schema.
-- For production, set AUTO_CREATE_TABLES=false and apply migrations explicitly.

create table if not exists organizations (
    id varchar(36) primary key,
    name varchar(200) not null,
    created_at timestamp not null default now()
);

create table if not exists users (
    id varchar(36) primary key,
    organization_id varchar(36) not null references organizations(id) on delete cascade,
    email varchar(255) not null unique,
    password_hash varchar(255) not null,
    name varchar(150) not null,
    role varchar(50) not null default 'member',
    created_at timestamp not null default now()
);
create index if not exists ix_users_organization_id on users(organization_id);
create index if not exists ix_users_email on users(email);

create table if not exists contacts (
    id varchar(36) primary key,
    organization_id varchar(36) not null references organizations(id) on delete cascade,
    external_id varchar(255),
    name varchar(200) not null,
    email varchar(255),
    company varchar(255),
    role varchar(255),
    persona varchar(255),
    industry varchar(255),
    source varchar(100),
    status varchar(50) not null default 'new',
    notes text,
    qualification_reason text,
    score double precision,
    engagement_score double precision,
    buying_signal_score double precision,
    workflow_status varchar(50),
    next_action text,
    follow_up_date timestamp,
    last_activity_at timestamp,
    converted_at timestamp,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now()
);
create index if not exists ix_contacts_organization_id on contacts(organization_id);
create index if not exists ix_contacts_external_id on contacts(external_id);
create index if not exists ix_contacts_org_status on contacts(organization_id, status);
create index if not exists ix_contacts_org_score on contacts(organization_id, score);

create table if not exists events (
    id varchar(36) primary key,
    organization_id varchar(36) not null references organizations(id) on delete cascade,
    name varchar(255) not null,
    target_persona varchar(255),
    offer text,
    objective text,
    event_date timestamp,
    status varchar(50) not null default 'draft',
    created_at timestamp not null default now(),
    updated_at timestamp not null default now()
);
create index if not exists ix_events_organization_id on events(organization_id);

create table if not exists workflows (
    id varchar(36) primary key,
    organization_id varchar(36) not null references organizations(id) on delete cascade,
    name varchar(255) not null,
    description text,
    definition_json text not null,
    active boolean not null default false,
    version integer not null default 1,
    created_at timestamp not null default now(),
    updated_at timestamp not null default now()
);
create index if not exists ix_workflows_organization_id on workflows(organization_id);

create table if not exists workflow_runs (
    id varchar(36) primary key,
    workflow_id varchar(36) not null references workflows(id) on delete cascade,
    organization_id varchar(36) not null references organizations(id) on delete cascade,
    idempotency_key varchar(128) not null,
    status varchar(50) not null default 'pending',
    trigger_type varchar(100) not null default 'manual',
    current_step integer not null default 0,
    current_node varchar(100),
    context_json text not null default '{}',
    error text,
    started_at timestamp not null default now(),
    updated_at timestamp not null default now(),
    completed_at timestamp,
    cancelled_at timestamp,
    constraint uq_workflow_run_idempotency unique (organization_id, workflow_id, idempotency_key)
);
create index if not exists ix_workflow_runs_workflow_id on workflow_runs(workflow_id);
create index if not exists ix_workflow_runs_org_status on workflow_runs(organization_id, status);

create table if not exists workflow_step_runs (
    id varchar(36) primary key,
    organization_id varchar(36) not null references organizations(id) on delete cascade,
    workflow_run_id varchar(36) not null references workflow_runs(id) on delete cascade,
    step_index integer not null,
    node_type varchar(100) not null,
    status varchar(50) not null default 'running',
    input_json text not null default '{}',
    output_json text not null default '{}',
    error text,
    started_at timestamp not null default now(),
    completed_at timestamp,
    constraint uq_workflow_step_run_index unique (workflow_run_id, step_index)
);
create index if not exists ix_workflow_step_runs_org on workflow_step_runs(organization_id);
create index if not exists ix_workflow_step_runs_run on workflow_step_runs(workflow_run_id);

create table if not exists approvals (
    id varchar(36) primary key,
    organization_id varchar(36) not null references organizations(id) on delete cascade,
    workflow_run_id varchar(36) not null references workflow_runs(id) on delete cascade,
    step_index integer not null,
    action_type varchar(100) not null,
    risk_level varchar(30) not null default 'medium',
    payload_json text not null,
    editable_context_key varchar(100),
    status varchar(50) not null default 'pending',
    reviewer_id varchar(36),
    review_comment text,
    created_at timestamp not null default now(),
    reviewed_at timestamp,
    constraint uq_approval_run_step unique (workflow_run_id, step_index)
);
create index if not exists ix_approvals_org_status on approvals(organization_id, status);
create index if not exists ix_approvals_workflow_run_id on approvals(workflow_run_id);

create table if not exists ai_requests (
    id varchar(36) primary key,
    organization_id varchar(36) not null references organizations(id) on delete cascade,
    provider varchar(50) not null,
    model varchar(100) not null,
    operation varchar(100) not null,
    prompt_version varchar(100),
    input_text text,
    output_text text,
    latency_ms double precision,
    success boolean not null default true,
    created_at timestamp not null default now()
);
create index if not exists ix_ai_requests_organization_id on ai_requests(organization_id);
create index if not exists ix_ai_requests_org_created on ai_requests(organization_id, created_at desc);

create table if not exists audit_logs (
    id varchar(36) primary key,
    organization_id varchar(36) not null references organizations(id) on delete cascade,
    user_id varchar(36),
    action varchar(150) not null,
    resource_type varchar(100) not null,
    resource_id varchar(36),
    metadata_json text not null default '{}',
    created_at timestamp not null default now()
);
create index if not exists ix_audit_logs_organization_id on audit_logs(organization_id);
