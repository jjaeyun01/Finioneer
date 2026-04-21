#!/bin/bash
echo "=== 데이터 수집 시작 ==="
python scripts/collect_data.py
echo "=== API 서버 시작 ==="
python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}