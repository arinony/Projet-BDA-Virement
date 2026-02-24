from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from pydantic import BaseModel
import os

app = FastAPI(title="API Système Bancaire - Projet 12")

# Configuration CORS pour autoriser React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En prod, remplace par l'URL de ton React
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration de la connexion PostgreSQL
# Conseil : En Master 2, on utilise normalement des variables d'environnement
DB_CONFIG = {
    "host": "localhost",
    "database": "ma_banque",
    "user": "postgres",
    "password": "TON_MOT_DE_PASSE" # <--- METS TON MOT DE PASSE ICI
}

# Modèle de données pour le virement
class Virement(BaseModel):
    source_id: int
    dest_id: int
    montant: float

@app.get("/")
def read_root():
    return {"message": "Serveur Bancaire Opérationnel"}

# 1. Route pour voir tous les comptes
@app.get("/api/comptes")
def get_comptes():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT id_compte, titulaire, solde FROM comptes ORDER BY id_compte;")
        comptes = cur.fetchall()
        cur.close()
        conn.close()
        return [{"id": c[0], "titulaire": c[1], "solde": float(c[2])} for c in comptes]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Route pour effectuer le virement (Appelle la procédure SQL)
@app.post("/api/virement")
def post_virement(virement: Virement):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Appel de la procédure p_virement(src, dst, val)
        cur.execute("CALL p_virement(%s, %s, %s)", 
                    (virement.source_id, virement.dest_id, virement.montant))
        
        conn.commit() # Très important pour valider la transaction
        cur.close()
        return {"status": "success", "message": "Virement validé par la base de données"}
    
    except Exception as e:
        if conn:
            conn.rollback() # Annule tout en cas d'erreur (Principe ACID)
        # On renvoie l'erreur du Trigger (ex: Solde insuffisant) au Front-end
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if conn:
            conn.close()
