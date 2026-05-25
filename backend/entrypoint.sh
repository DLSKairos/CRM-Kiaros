#!/bin/bash
set -e

echo "⏳ Creando tablas en la base de datos..."
python -c "
from app.database import sync_engine
from sqlmodel import SQLModel
import app.models
SQLModel.metadata.create_all(sync_engine)
print('✅ Tablas listas.')
"

echo "🚀 Iniciando servidor..."
exec "$@"
