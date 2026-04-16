"""
Database Manager - Gerenciamento de conexões PostgreSQL/SQLite
Sistema de banco de dados profissional com SQLAlchemy
"""

import logging
from contextlib import contextmanager
from typing import Optional, Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import NullPool, StaticPool

from app.config import config

logger = logging.getLogger(__name__)

# Base declarativa para modelos
Base = declarative_base()


class Database:
    """Gerenciador de banco de dados com suporte a PostgreSQL e SQLite"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._init_engine()
    
    def _init_engine(self):
        """Inicializa a engine do SQLAlchemy com configurações otimizadas"""
        try:
            if config.IS_POSTGRESQL:
                # PostgreSQL - Railway production
                self.engine = create_engine(
                    config.DATABASE_URL,
                    pool_size=10,
                    max_overflow=20,
                    pool_timeout=30,
                    pool_recycle=1800,
                    pool_pre_ping=True,
                    echo=config.DEBUG
                )
                logger.info("🐘 PostgreSQL engine inicializada")
            else:
                # SQLite - Development/local
                self.engine = create_engine(
                    config.DATABASE_URL,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=config.DEBUG
                )
                logger.info("🗄️ SQLite engine inicializada")
            
            # Criar session maker
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Configurar eventos
            self._setup_events()
            
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar engine: {e}")
            raise
    
    def _setup_events(self):
        """Configura eventos do SQLAlchemy"""
        
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Configura pragmas do SQLite para melhor performance"""
            if not config.IS_POSTGRESQL:
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
    
    def create_tables(self):
        """Cria todas as tabelas definidas nos modelos"""
        try:
            # Importar modelos para registro
            from app import models
            
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Tabelas criadas com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas: {e}")
            raise
    
    def drop_tables(self):
        """Remove todas as tabelas (cuidado!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("⚠️ Todas as tabelas foram removidas")
        except Exception as e:
            logger.error(f"❌ Erro ao remover tabelas: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager para sessões de banco de dados
        Garante commit/rollback automático e fechamento da sessão
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Erro na transação: {e}")
            raise
        finally:
            session.close()
    
    def get_db(self) -> Session:
        """
        Retorna uma nova sessão de banco de dados
        ATENÇÃO: Use get_session() para transações automáticas
        """
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """Testa a conexão com o banco de dados"""
        try:
            with self.get_session() as session:
                if config.IS_POSTGRESQL:
                    session.execute(text("SELECT version()"))
                else:
                    session.execute(text("SELECT 1"))
                logger.info("✅ Conexão com banco de dados OK")
                return True
        except Exception as e:
            logger.error(f"❌ Falha na conexão com banco de dados: {e}")
            return False
    
    def execute_raw(self, query: str, params: Optional[dict] = None):
        """Executa uma query SQL raw"""
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            return result
    
    def backup(self, backup_path: str):
        """Cria backup do banco de dados (SQLite apenas)"""
        if config.IS_POSTGRESQL:
            logger.warning("Backup manual via PostgreSQL dump recomendado")
            return False
        
        import shutil
        import os
        
        db_path = config.DATABASE_URL.replace('sqlite:///', '')
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            logger.info(f"💾 Backup criado: {backup_path}")
            return True
        return False


# Instância global do banco de dados
db = Database()


# Função utilitária para obter sessão rapidamente
def get_db_session() -> Generator[Session, None, None]:
    """Função utilitária para obter sessão via dependência"""
    with db.get_session() as session:
        yield session
