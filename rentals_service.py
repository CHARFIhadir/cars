from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import httpx
import os
import time

app = FastAPI()

# Lire les variables d'environnement
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "rentals_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "29032002")
CARS_SERVICE_URL = "http://cars_service:8000"

print(f"Configuration PostgreSQL : host={DB_HOST}, port={DB_PORT}, dbname={DB_NAME}, user={DB_USER}")
print(f"Configuration Cars Service : url={CARS_SERVICE_URL}")

# Connexion PostgreSQL avec retry
def connect_db():
    retries = 15
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                dbname=DB_NAME,
                password=DB_PASS
            )
            print("Connexion à PostgreSQL réussie")
            return conn
        except psycopg2.OperationalError as e:
            print(f"Échec de la connexion à PostgreSQL : {e}. Tentative {16-retries}/15 dans 15s...")
            retries -= 1
            time.sleep(15)
    raise Exception("Impossible de se connecter à PostgreSQL après 15 tentatives")

conn = connect_db()
cursor = conn.cursor()

# Pydantic model
class RentalRequest(BaseModel):
    user_id: int
    car_id: int
    start_date: str
    end_date: str

@app.post("/rentals/")
def create_rental(rental: RentalRequest):
    # Vérifier la voiture via appel API
    try:
        response = httpx.get(f"{CARS_SERVICE_URL}/cars/{rental.car_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Voiture introuvable")
        
        car_data = response.json()
        if not car_data.get("available", False):
            raise HTTPException(status_code=400, detail="Voiture non disponible")
    except httpx.RequestError:
        raise HTTPException(status_code=500, detail="Erreur de communication avec le service des voitures")

    # Insérer la location
    cursor.execute(
        "INSERT INTO rentals (user_id, car_id, start_date, end_date) VALUES (%s, %s, %s, %s) RETURNING id",
        (rental.user_id, rental.car_id, rental.start_date, rental.end_date)
    )
    rental_id = cursor.fetchone()[0]
    conn.commit()

    # Retourner la location avec toutes les informations nécessaires
    return {
        "rental_id": rental_id,
        "user_id": rental.user_id,
        "car_id": rental.car_id,
        "start_date": rental.start_date,
        "end_date": rental.end_date,
        "message": "Location créée avec succès"
    }

@app.get("/rentals/")
def list_rentals():
    cursor.execute("SELECT id, user_id, car_id, start_date, end_date FROM rentals ORDER BY id DESC")
    rows = cursor.fetchall()
    return [{"rental_id": r[0], "user_id": r[1], "car_id": r[2], "start_date": r[3], "end_date": r[4]} for r in rows]