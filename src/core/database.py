from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# configuración de la base de datos SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/messages.db"
# motor de la base de datos
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
# sesión de la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# clase base para los modelos
Base = declarative_base()

def get_db():
    """Obtiene una sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()