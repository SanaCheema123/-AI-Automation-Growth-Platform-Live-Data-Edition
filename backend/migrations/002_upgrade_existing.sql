-- Upgrade helper for repositories created from the original starter migration.
-- PostgreSQL/Supabase only. Back up the database first.

alter table contacts add column if not exists source varchar(100);
alter table contacts add column if not exists status varchar(50) not null default 'new';
alter table contacts add column if not exists qualification_reason text;
alter table contacts add column if not exists engagement_score double precision;
alter table contacts add column if not exists last_activity_at timestamp;
alter table contacts add column if not exists converted_at timestamp;

alter table events add column if not exists updated_at timestamp not null default now();
alter table workflows add column if not exists updated_at timestamp not null default now();

alter table workflow_runs add column if not exists idempotency_key varchar(128);
alter table workflow_runs add column if not exists trigger_type varchar(100) not null default 'manual';
alter table workflow_runs add column if not exists current_step integer not null default 0;
alter table workflow_runs add column if not exists current_node varchar(100);
alter table workflow_runs add column if not exists updated_at timestamp not null default now();
alter table workflow_runs add column if not exists cancelled_at timestamp;
update workflow_runs set idempotency_key=id where idempotency_key is null;
alter table workflow_runs alter column idempotency_key set not null;
create unique index if not exists uq_workflow_run_idempotency on workflow_runs(organization_id, workflow_id, idempotency_key);

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

alter table approvals add column if not exists step_index integer not null default 0;
alter table approvals add column if not exists risk_level varchar(30) not null default 'medium';
alter table approvals add column if not exists editable_context_key varchar(100);
create unique index if not exists uq_approval_run_step on approvals(workflow_run_id, step_index);

create index if not exists ix_contacts_org_status on contacts(organization_id, status);
create index if not exists ix_contacts_org_score on contacts(organization_id, score);
create index if not exists ix_workflow_runs_org_status on workflow_runs(organization_id, status);
create index if not exists ix_approvals_org_status on approvals(organization_id, status);
create index if not exists ix_ai_requests_org_created on ai_requests(organization_id, created_at desc);
