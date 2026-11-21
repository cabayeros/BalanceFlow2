from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import get_settings

settings = get_settings()

# Render/PostgreSQL supplies `postgresql://...`; use the psycopg v3 driver
# installed by requirements.txt instead of SQLAlchemy's default psycopg2.
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

# SQLite necesita un argumento especial; PostgreSQL no
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    database_url,
    connect_args=connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base de la que heredan todos los modelos
Base = declarative_base()


def get_db():
    """
    Dependency para FastAPI: entrega una sesión de BD y la cierra al terminar.
    Úsalo así en tus endpoints: def mi_endpoint(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
