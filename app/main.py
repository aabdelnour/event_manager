from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse
from settings.config import get_settings
from app.database import Database
from app.routers import user_routes
from app.services.jwt_service import create_access_token
from app.utils.api_description import getDescription
from app.utils.auth import authenticate_user

app = FastAPI(
    title="User Management",
    description=getDescription(),
    version="0.0.1",
    contact={
        "name": "API Support",
        "url": "http://www.example.com/support",
        "email": "support@example.com",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

@app.get("/")
def read_root():
    return {"message": "Welcome to my FastAPI application!"}

@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    Database.initialize(database_url=str(settings.database_url), echo=settings.debug)
    await Database.create_tables()
    print("Database initialized with URL:", settings.database_url)
    print("Debug mode:", settings.debug)

@app.exception_handler(Exception)
async def exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"message": "An unexpected error occurred."})

app.include_router(user_routes.router)

import logging
logger = logging.getLogger(__name__)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect email or password.")
        access_token = create_access_token(data={"sub": user.email, "role": str(user.role)})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logging.exception("Error during login")
        raise HTTPException(status_code=500, detail="Internal Server Error")
