-- W2026-64: S3ロケーション詳細設定カラム追加
-- 対応alembicマイグレーション: modules/invenio-files-rest/invenio_files_rest/alembic/8644b32a3eec_add_column_files_location.py
ALTER TABLE files_location ADD COLUMN IF NOT EXISTS s3_default_block_size BIGINT;
ALTER TABLE files_location ADD COLUMN IF NOT EXISTS s3_maximum_number_of_parts BIGINT;
ALTER TABLE files_location ADD COLUMN IF NOT EXISTS s3_region_name CHARACTER VARYING(128);
ALTER TABLE files_location ADD COLUMN IF NOT EXISTS s3_signature_version CHARACTER VARYING(20);
ALTER TABLE files_location ADD COLUMN IF NOT EXISTS s3_url_expiration BIGINT;
-- Apply s3v4 to all existing data
UPDATE files_location SET s3_signature_version = 's3v4';