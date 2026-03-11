from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from psycopg2 import pool
from pydantic import BaseModel
from contextlib  import contextmanager
from dotenv import load_dotenv
import os


load_dotenv()

app = FastAPI(title="API Système Bancaire - Projet 12")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

try: 
    db_pool = pool.SimpleConnectionPool(
        1,10,
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "ma_banque"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "ton_pass")
    )
except Exception as e:
    print(f"Tsy adaka nifanandray amin ny database: {e}")
    exit(-1)


@contextmanager
def get_db_connection():
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)

class VirementSchema(BaseModel):
    source_id: int
    dest_id: int
    montant: float

@app.get("/")
def read_root():
    return {"message": "Serveur Bancaire Opérationnel"}


@app.get("/api/comptes", status_code=status.HTTP_200_OK)
def list_accounts():
    """Récupère la liste des comptes avec gestion de pool."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id_compte, titulaire, solde FROM comptes ORDER BY id_compte;")
            rows = cur.fetchall()
            return [{"id": r[0], "titulaire": r[1], "solde": float(r[2])} for r in rows]

@app.post("/api/virement", status_code=status.HTTP_201_CREATED)
def execute_transfer(virement: VirementSchema):
    """Exécute un virement en utilisant la procédure stockée PostgreSQL."""
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                # Appel de la procédure stockée
                cur.execute("CALL p_virement(%s, %s, %s)", 
                           (virement.source_id, virement.dest_id, virement.montant))
                conn.commit()
                return {"status": "success", "detail": "Transfer completed successfully"}
        except Exception as e:
            conn.rollback()
            # On remonte l'erreur précise du Trigger SQL (ex: solde insuffisant)
            error_msg = str(e).split('\n')[0]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Transaction failed: {error_msg}"
            )