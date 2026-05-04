"""
config.py — Configuração centralizada da aplicação.

Lê variáveis do .env e disponibiliza como um objeto Settings.
Qualquer arquivo do projeto que precise de configuração importa daqui.
Isso evita ter strings de conexão espalhadas pelo código.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Cada atributo aqui mapeia para uma variável de ambiente.
    Ex: DATABASE_URL no .env → settings.database_url no Python.
    O Pydantic valida automaticamente — se faltar uma variável obrigatória,
    a aplicação nem inicia (fail fast).
    """

    # Conexão com o banco
    database_url: str = "postgresql://nexas:nexas@localhost:5432/nexas"

    # Aplicação
    app_env: str = "development"
    app_port: int = 8000
    app_host: str = "0.0.0.0"

    # CORS
    cors_origins: str = "http://localhost:8000,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Converte a string de origens em lista."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância única — importada por todo o projeto
# Uso: from backend.config import settings
settings = Settings()
