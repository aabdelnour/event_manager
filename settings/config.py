from pydantic_settings import BaseSettings
from pydantic import Field, AnyUrl

class Settings(BaseSettings):
    database_url: AnyUrl = Field(..., description="URL for connecting to the database")
    max_login_attempts: int = Field(default=3, description="Maximum login attempts before lockout")
    server_base_url: AnyUrl = Field(default='http://localhost', description="Base URL of the server")
    server_download_folder: str = Field(default='downloads', description="Folder for storing downloaded files")
    secret_key: str = Field(default="secret-key", description="Secret key for encryption")
    algorithm: str = Field(default="HS256", description="Algorithm used for encryption")
    access_token_expire_minutes: int = Field(default=30, description="Expiration time for access tokens in minutes")
    refresh_token_expire_minutes: int = Field(default=1440, description="24 hours for refresh token")
    database_min_size: int = Field(default=5, description="Minimum size of the database connection pool")
    database_max_size: int = Field(default=20, description="Maximum size of the database connection pool")
    postgres_user: str = Field(default='user', description="PostgreSQL username")
    postgres_password: str = Field(default='password', description="PostgreSQL password")
    postgres_server: str = Field(default='localhost', description="PostgreSQL server address")
    postgres_port: str = Field(default='5432', description="PostgreSQL port")
    postgres_db: str = Field(default='myappdb', description="PostgreSQL database name")
    discord_bot_token: str = Field(default='NONE', description="Discord bot token")
    discord_channel_id: int = Field(default=1234567890, description="Default Discord channel ID for the bot to interact")
    openai_api_key: str = Field(default='NONE', description="OpenAI API Key")
    send_real_mail: bool = Field(default=False, description="Use mock")
    smtp_server: str = Field(default='smtp.mailtrap.io', description="SMTP server for sending emails")
    smtp_port: int = Field(default=2525, description="SMTP port for sending emails")
    smtp_username: str = Field(default='your-mailtrap-username', description="Username for SMTP server")
    smtp_password: str = Field(default='your-mailtrap-password', description="Password for SMTP server")
    debug: bool = Field(default=False, description="Debug mode outputs errors and sqlalchemy queries")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

def get_settings() -> Settings:
    return settings
