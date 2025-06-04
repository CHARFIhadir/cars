from fastapi import FastAPI, HTTPException
import psycopg2
import redis
import json
import os
import time

app = FastAPI()

# Lire les variables d'environnement
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "cars_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "29032002")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

print(f"Configuration PostgreSQL : host={DB_HOST}, port={DB_PORT}, dbname={DB_NAME}, user={DB_USER}")
print(f"Configuration Redis : host={REDIS_HOST}, port=6379")

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

# Connexion Redis avec retry
def connect_redis():
    retries = 15
    while retries > 0:
        try:
            client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
            client.ping()
            print("Connexion à Redis réussie")
            return client
        except redis.RedisError as e:
            print(f"Échec de la connexion à Redis : {e}. Tentative {16-retries}/15 dans 15s...")
            retries -= 1
            time.sleep(15)
    raise Exception("Impossible de se connecter à Redis après 15 tentatives")

redis_client = connect_redis()

@app.get("/cars/")
def list_cars():
    cursor.execute("SELECT id, brand, model, available FROM cars")
    rows = cursor.fetchall()
    return [{"id": r[0], "brand": r[1], "model": r[2], "available": r[3]} for r in rows]

@app.get("/cars/{car_id}")
def get_car(car_id: int):
    cached_car = redis_client.get(f"car:{car_id}")
    if cached_car:
        return json.loads(cached_car)

    cursor.execute("SELECT id, brand, model, available FROM cars WHERE id = %s", (car_id,))
    car = cursor.fetchone()
    
    if not car:
        raise HTTPException(status_code=404, detail="Voiture introuvable")

    car_data = {"id": car[0], "brand": car[1], "model": car[2], "available": car[3]}
    redis_client.setex(f"car:{car_id}", 3600, json.dumps(car_data))
    return car_data