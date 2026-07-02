# migrations

스키마 마이그레이션 파일 위치. 스키마 정본은 `shared/db_models.py`(SQLAlchemy)이며,
`db/schema.sql` 은 거기서 생성된 전체 DDL 스냅샷이다.

향후 Alembic 도입 시 이 디렉터리를 버전 저장소로 사용한다.
