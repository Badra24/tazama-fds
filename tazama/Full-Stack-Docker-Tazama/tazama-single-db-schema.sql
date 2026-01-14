-- Tazama Schema Setup - Single Database Version
-- Database: badraaji
-- Schema: tazama
--
-- Run this as: psql -U badraaji -d badraaji -f tazama-single-db-schema.sql

-- Connect to badraaji database and use tazama schema
\c badraaji

-- Set search path to tazama schema
SET search_path TO tazama, public;

-- ============================================================================
-- CONFIGURATION TABLES (originally from 'configuration' database)
-- ============================================================================

DROP TABLE IF EXISTS tazama.network_map CASCADE;
CREATE TABLE tazama.network_map (
    configuration jsonb not null,
    tenantId text generated always as (configuration ->> 'tenantId') stored
);

DROP TABLE IF EXISTS tazama.typology CASCADE;
CREATE TABLE tazama.typology (
    configuration jsonb not null,
    typologyId text generated always as (configuration ->> 'id') stored,
    typologyCfg text generated always as (configuration ->> 'cfg') stored,
    tenantId text generated always as (configuration ->> 'tenantId') stored,
    primary key (typologyId, typologyCfg, tenantId)
);

DROP TABLE IF EXISTS tazama.rule CASCADE;
CREATE TABLE tazama.rule (
    configuration jsonb not null,
    ruleId text generated always as (configuration ->> 'id') stored,
    ruleCfg text generated always as (configuration ->> 'cfg') stored,
    tenantId text generated always as (configuration ->> 'tenantId') stored,
    primary key (ruleId, ruleCfg, tenantId)
);

-- ============================================================================
-- EVALUATION TABLES (originally from 'evaluation' database)
-- ============================================================================

DROP TABLE IF EXISTS tazama.evaluation CASCADE;
CREATE TABLE tazama.evaluation (
    evaluation jsonb not null,
    messageId text generated always as (
        evaluation -> 'transaction' -> 'FIToFIPmtSts' -> 'GrpHdr' ->> 'MsgId'
    ) stored,
    tenantId text generated always as (evaluation -> 'transaction' ->> 'TenantId') stored,
    constraint unique_msgid_evaluation unique (messageId, tenantId)
);

-- ============================================================================
-- EVENT HISTORY TABLES (originally from 'event_history' database)
-- ============================================================================

DROP TABLE IF EXISTS tazama.account CASCADE;
CREATE TABLE tazama.account (
    id varchar not null,
    tenantId text not null,
    primary key (id, tenantId)
);

DROP TABLE IF EXISTS tazama.entity CASCADE;
CREATE TABLE tazama.entity (
    id varchar not null,
    tenantId text not null,
    creDtTm timestamptz not null,
    primary key (id, tenantId)
);

DROP TABLE IF EXISTS tazama.account_holder CASCADE;
CREATE TABLE tazama.account_holder (
    source varchar not null,
    destination varchar not null,
    tenantId text not null,
    creDtTm timestamptz not null,
    foreign key (source, tenantId) references tazama.entity (id, tenantId),
    foreign key (destination, tenantId) references tazama.account (id, tenantId),
    primary key (source, destination, tenantId)
);

DROP TABLE IF EXISTS tazama.condition CASCADE;
CREATE TABLE tazama.condition (
    id varchar generated always as (condition ->> 'condId') stored,
    tenantId text generated always as (condition ->> 'tenantId') stored,
    condition jsonb not null,
    primary key (id, tenantId)
);

DROP TABLE IF EXISTS tazama.governed_as_creditor_account_by CASCADE;
CREATE TABLE tazama.governed_as_creditor_account_by (
    source varchar not null,
    destination varchar not null,
    evtTp text [] not null,
    incptnDtTm timestamptz not null,
    xprtnDtTm timestamptz,
    tenantId text not null,
    foreign key (source, tenantId) references tazama.account (id, tenantId),
    foreign key (destination, tenantId) references tazama.condition (id, tenantId),
    primary key (source, destination, tenantId)
);

DROP TABLE IF EXISTS tazama.governed_as_creditor_by CASCADE;
CREATE TABLE tazama.governed_as_creditor_by (
    source varchar not null,
    destination varchar not null,
    evtTp TEXT [] not null,
    incptnDtTm timestamptz not null,
    xprtnDtTm timestamptz,
    tenantId text not null,
    foreign key (source, tenantId) references tazama.entity (id, tenantId),
    foreign key (destination, tenantId) references tazama.condition (id, tenantId),
    primary key (source, destination, tenantId)
);

DROP TABLE IF EXISTS tazama.governed_as_debtor_account_by CASCADE;
CREATE TABLE tazama.governed_as_debtor_account_by (
    source varchar not null,
    destination varchar not null,
    evtTp TEXT [] not null,
    incptnDtTm timestamptz not null,
    xprtnDtTm timestamptz,
    tenantId text not null,
    foreign key (source, tenantId) references tazama.account (id, tenantId),
    foreign key (destination, tenantId) references tazama.condition (id, tenantId),
    primary key (source, destination, tenantId)
);

DROP TABLE IF EXISTS tazama.governed_as_debtor_by CASCADE;
CREATE TABLE tazama.governed_as_debtor_by (
    source varchar not null,
    destination varchar not null,
    evtTp TEXT [] not null,
    incptnDtTm timestamptz not null,
    xprtnDtTm timestamptz,
    tenantId text not null,
    foreign key (source, tenantId) references tazama.entity (id, tenantId),
    foreign key (destination, tenantId) references tazama.condition (id, tenantId),
    primary key (source, destination, tenantId)
);

DROP TABLE IF EXISTS tazama.transaction CASCADE;
CREATE TABLE tazama.transaction (
    source varchar not null,
    destination varchar not null,
    transaction jsonb not null,
    endToEndId text generated always as (transaction->>'EndToEndId') stored,
    amt numeric(18, 2) generated always as (
        (transaction->>'Amt')::numeric(18, 2)
    ) stored,
    ccy varchar generated always as (transaction->>'Ccy') stored,
    msgId varchar generated always as (transaction->>'MsgId') stored,
    creDtTm text generated always as (transaction->>'CreDtTm') stored,
    txTp varchar generated always as (transaction->>'TxTp') stored,
    txSts varchar generated always as (transaction->>'TxSts') stored,
    tenantId text generated always as (transaction->>'TenantId') stored,
    constraint unique_msgid unique (msgId, tenantId),
    foreign key (source, tenantId) references tazama.account (id, tenantId),
    foreign key (destination, tenantId) references tazama.account (id, tenantId),
    primary key (endToEndId, txTp, tenantId)
);

CREATE INDEX idx_tr_cre_dt_tm ON tazama.transaction (creDtTm, tenantId);
CREATE INDEX idx_tr_source_txtp_credttm ON tazama.transaction (source, txtp, creDtTm, tenantId);
CREATE INDEX idx_tr_pacs002_accc ON tazama.transaction (endtoendid, creDtTm, tenantId)
WHERE txtp = 'pacs.002.001.12' AND txsts = 'ACCC';
CREATE INDEX idx_tr_dest_txtp_txsts_credttm ON tazama.transaction (
    destination, txtp, txsts, creDtTm desc
) include (source);

-- ============================================================================
-- RAW HISTORY TABLES (originally from 'raw_history' database)
-- ============================================================================

DROP TABLE IF EXISTS tazama.pacs002 CASCADE;
CREATE TABLE tazama.pacs002 (
    document jsonb not null,
    creDtTm text generated always as (
        document -> 'FIToFIPmtSts' -> 'GrpHdr' ->> 'CreDtTm'
    ) stored,
    messageId text generated always as (
        document -> 'FIToFIPmtSts' -> 'GrpHdr' ->> 'MsgId'
    ) stored,
    endToEndId text generated always as (
        document -> 'FIToFIPmtSts' -> 'TxInfAndSts' ->> 'OrgnlEndToEndId'
    ) stored,
    tenantId text generated always as (
        document ->> 'TenantId' ) stored,
    constraint unique_msgid_pacs002 unique (messageId, tenantId),
    constraint message_id_not_null check (messageId is not null),
    constraint cre_dt_tm check (creDtTm is not null),
    primary key (endToEndId, tenantId)
);

DROP TABLE IF EXISTS tazama.pacs008 CASCADE;
CREATE TABLE tazama.pacs008 (
    document jsonb not null,
    creDtTm text generated always as (
        document -> 'FIToFICstmrCdtTrf' -> 'GrpHdr' ->> 'CreDtTm'
    ) stored,
    messageId text generated always as (
        document -> 'FIToFICstmrCdtTrf' -> 'GrpHdr' ->> 'MsgId'
    ) stored,
    endToEndId text generated always as (
        document -> 'FIToFICstmrCdtTrf' -> 'CdtTrfTxInf' -> 'PmtId' ->> 'EndToEndId'
    ) stored,
    debtorAccountId text generated always as (
        document -> 'FIToFICstmrCdtTrf' -> 'CdtTrfTxInf' -> 'DbtrAcct' -> 'Id' -> 'Othr' -> 0 ->> 'Id'
    ) stored,
    creditorAccountId text generated always as (
        document -> 'FIToFICstmrCdtTrf' -> 'CdtTrfTxInf' -> 'CdtrAcct' -> 'Id' -> 'Othr' -> 0 ->> 'Id'
    ) stored,
    tenantId text generated always as (
        document ->> 'TenantId' ) stored,
    constraint unique_msgid_e2eid_pacs008 unique (messageId, tenantId),
    constraint message_id_not_null check (messageId is not null),
    constraint cre_dt_tm check (creDtTm is not null),
    constraint dbtr_acct_id_not_null check (debtorAccountId is not null),
    constraint cdtr_acct_id_not_null check (creditorAccountId is not null),
    primary key (endToEndId, tenantId)
);

CREATE INDEX idx_pacs008_dbtr_acct_id ON tazama.pacs008 (debtorAccountId, tenantId);
CREATE INDEX idx_pacs008_cdtr_acct_id ON tazama.pacs008 (creditorAccountId, tenantId);
CREATE INDEX idx_pacs008_credttm ON tazama.pacs008 (creDtTm, tenantId);

DROP TABLE IF EXISTS tazama.pain001 CASCADE;
CREATE TABLE tazama.pain001 (
    document jsonb not null,
    creDtTm text generated always as (
        document -> 'CstmrCdtTrfInitn' -> 'GrpHdr' ->> 'CreDtTm'
    ) stored,
    messageId text generated always as (
        document -> 'CstmrCdtTrfInitn' -> 'GrpHdr' ->> 'MsgId'
    ) stored,
    endToEndId text generated always as (
        document -> 'CstmrCdtTrfInitn' -> 'PmtInf' -> 'CdtTrfTxInf' -> 'PmtId' ->> 'EndToEndId'
    ) stored,
    debtorAccountId text generated always as (
        document -> 'CstmrCdtTrfInitn' -> 'PmtInf' -> 'DbtrAcct' -> 'Id' -> 'Othr' -> 0 ->> 'Id'
    ) stored,
    creditorAccountId text generated always as (
        document -> 'CstmrCdtTrfInitn' -> 'PmtInf' -> 'CdtTrfTxInf' -> 'CdtrAcct' -> 'Id' -> 'Othr' -> 0 ->> 'Id'
    ) stored,
    tenantId text generated always as (
        document ->> 'TenantId' ) stored,
    constraint unique_msgid_e2eid_pain001 unique (messageId, tenantId),
    constraint message_id_not_null check (messageId is not null),
    constraint cre_dt_tm check (creDtTm is not null),
    constraint dbtr_acct_id_not_null check (debtorAccountId is not null),
    constraint cdtr_acct_id_not_null check (creditorAccountId is not null),
    primary key (endToEndId, tenantId)
);

CREATE INDEX idx_pain001_dbtr_acct_id ON tazama.pain001 (debtorAccountId, tenantId);
CREATE INDEX idx_pain001_cdtr_acct_id ON tazama.pain001 (creditorAccountId, tenantId);
CREATE INDEX idx_pain001_credttm ON tazama.pain001 (creDtTm, tenantId);

DROP TABLE IF EXISTS tazama.pain013 CASCADE;
CREATE TABLE tazama.pain013 (
    document jsonb not null,
    creDtTm text generated always as (
        document -> 'CdtrPmtActvtnReq' -> 'GrpHdr' ->> 'CreDtTm'
    ) stored,
    messageId text generated always as (
        document -> 'CdtrPmtActvtnReq' -> 'GrpHdr' ->> 'MsgId'
    ) stored,
    endToEndId text generated always as (
        document -> 'CdtrPmtActvtnReq' -> 'PmtInf' -> 'CdtTrfTxInf' -> 'PmtId' ->> 'EndToEndId'
    ) stored,
    debtorAccountId text generated always as (
        document -> 'CdtrPmtActvtnReq' -> 'PmtInf' -> 'DbtrAcct' -> 'Id' -> 'Othr' -> 0 ->> 'Id'
    ) stored,
    creditorAccountId text generated always as (
        document -> 'CdtrPmtActvtnReq' -> 'PmtInf' -> 'CdtTrfTxInf' -> 'CdtrAcct' -> 'Id' -> 'Othr' -> 0 ->> 'Id'
    ) stored,
    tenantId text generated always as (
        document ->> 'TenantId' ) stored,
    constraint unique_msgid_e2eid_pain013 unique (messageId, tenantId),
    constraint message_id_not_null check (messageId is not null),
    constraint cre_dt_tm check (creDtTm is not null),
    constraint dbtr_acct_id_not_null check (debtorAccountId is not null),
    constraint cdtr_acct_id_not_null check (creditorAccountId is not null),
    primary key (endToEndId, tenantId)
);

CREATE INDEX idx_pain013_dbtr_acct_id ON tazama.pain013 (debtorAccountId, tenantId);
CREATE INDEX idx_pain013_cdtr_acct_id ON tazama.pain013 (creditorAccountId, tenantId);
CREATE INDEX idx_pain013_credttm ON tazama.pain013 (creDtTm, tenantId);

-- Done!
\echo '✅ Tazama schema setup complete!'
\echo ''
\echo 'Tables created in schema: tazama'
\dt tazama.*
