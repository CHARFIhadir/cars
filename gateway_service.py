from fastapi import FastAPI, HTTPException
import httpx
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL des services backend
USERS_SERVICE_URL = "http://users_service:8000"
CARS_SERVICE_URL = "http://cars_service:8000"
RENTALS_SERVICE_URL = "http://rentals_service:8000"

@app.get("/api/users/")
async def get_users():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{USERS_SERVICE_URL}/users/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Erreur de connexion au service utilisateurs")

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{USERS_SERVICE_URL}/users/{user_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Erreur de connexion au service utilisateurs")

@app.get("/api/cars/")
async def get_cars():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CARS_SERVICE_URL}/cars/")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Erreur de connexion au service voitures")

@app.get("/api/cars/{car_id}")
async def get_car(car_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{CARS_SERVICE_URL}/cars/{car_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Erreur de connexion au service voitures")

class RentalRequest(BaseModel):
    user_id: int
    car_id: int
    start_date: str
    end_date: str

@app.post("/api/rentals/")
async def create_rental(rental: RentalRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{RENTALS_SERVICE_URL}/rentals/", json=rental.dict())
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Erreur de connexion au service des locations")