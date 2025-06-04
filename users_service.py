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
DB_NAME = os.getenv("DB_NAME", "users_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "29032002")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

print(f"Configuration PostgreSQL : host={DB_HOST}, port={DB_PORT}, dbname={DB_NAME}, user={DB_USER}")
print(f"Configuration Redis : host={REDIS_HOST}, port=6379")

# Connexion PostgreSQL avec retry
def connect_db():
    retries = 15  # Augmenté à 15
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
            time.sleep(15)  # Augmenté à 15s
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

@app.get("/users/")
def list_users():
    cursor.execute("SELECT id, name, email FROM users")
    rows = cursor.fetchall()
    return [{"id": r[0], "name": r[1], "email": r[2]} for r in rows]

@app.get("/users/{user_id}")
def get_user(user_id: int):
    cached_user = redis_client.get(f"user:{user_id}")
    if cached_user:
        return json.loads(cached_user)

    cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user_data = {"id": user[0], "name": user[1], "email": user[2]}
    redis_client.setex(f"user:{user_id}", 3600, json.dumps(user_data))
    return user_data