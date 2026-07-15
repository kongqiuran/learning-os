import os

import uvicorn

from src.api.factory import create_app
from src.database import create_database_tables


app = create_app()


def main():
    create_database_tables()
    uvicorn.run(
        "api_server:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "false").lower() == "true",
    )


if __name__ == "__main__":
    main()
