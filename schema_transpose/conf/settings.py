from pydantic import BaseSettings


class Settings(BaseSettings):
    project_name: str = "schema_transpose"
    debug: bool = False
