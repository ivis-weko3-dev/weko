-- =============================================================================
-- scripts/migration.sql（広場用 / W2026-64 ミドルウェアアップデート）
--
-- 用途:
--   移行手順「pgアップグレード手順」⑦マイグレーション実行で、PostgreSQL の
--   リストア後に実行する DB スキーマ変更。
--     docker cp scripts/migration.sql $(docker compose ps -q postgresql):/tmp/migration.sql
--     docker compose exec -T postgresql psql -v ON_ERROR_STOP=1 -U invenio -d invenio -f /tmp/migration.sql
--
-- 内容:
--   課題 No.3: stats_events / stats_aggregation / stats_bookmark の type 列の
--   NOT NULL 制約を外す（OpenSearch では _doc_type が無く type が None になるため）。
--   invenio-stats の alembic リビジョン 0109e99b50da（make_type_nullable）と同じ変更。
--   stats_events はパーティションテーブルで、親に対する ALTER は全パーティションに適用される。
--
-- 冪等性 / alembic との関係:
--   ALTER COLUMN ... DROP NOT NULL は、すでに NULL 可の列に実行してもエラーにならず何もしない。
--   alembic_version がある環境で `invenio alembic upgrade heads`（0109e99b50da を含む）と
--   前後どちらの順で二重に適用しても結果は同じで、無害。
--   alembic_version がない環境では、このファイルで No.3 を適用する（upgrade heads は実行しない）。
--
-- JC（ivis/feature/W2026-31）版との違い:
--   JC 版の pidrelations_pidrelation 主キー変更 (parent_id, child_id, relation_type) は、
--   広場では実行しない。広場は invenio-pidrelations 1.0.0a4 のままで、モデルの主キーは
--   (parent_id, child_id) のため、JC 版を実行するとモデルと DB がずれる。
--   （広場は invenio-search 以外のモジュールをアップデートしない方針）
--
-- 対象外（参考）:
--   files_location の s3_* 列（invenio_files_rest 8644b32a3eec）はここでは追加しない。
--   alembic_version がある環境では alembic upgrade heads が追加し、先に SQL で追加すると
--   その後の alembic upgrade が「column already exists」で失敗するため。
--   alembic_version がない環境で必要な場合は、移行手順書の記載に従って個別に実行する。
-- =============================================================================

BEGIN;

ALTER TABLE stats_events      ALTER COLUMN type DROP NOT NULL;
ALTER TABLE stats_aggregation ALTER COLUMN type DROP NOT NULL;
ALTER TABLE stats_bookmark    ALTER COLUMN type DROP NOT NULL;

COMMIT;

-- 確認（すべて YES になること）
SELECT table_name, is_nullable
  FROM information_schema.columns
 WHERE table_schema = 'public'
   AND column_name = 'type'
   AND table_name IN ('stats_events', 'stats_aggregation', 'stats_bookmark')
 ORDER BY table_name;
