import os

import weaviate
from dotenv import load_dotenv
from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEAVIATE_HOST = os.getenv("WEAVIATE_HOST")
WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT"))
WEAVIATE_SECURE = bool(os.getenv("WEAVIATE_SECURE"))
WEAVIATE_GRPC_HOST = os.getenv("WEAVIATE_GRPC_HOST")
WEAVIATE_GRPC_PORT = int(os.getenv("WEAVIATE_GRPC_PORT"))
WEAVIATE_GRPC_SECURE = bool(os.getenv("WEAVIATE_GRPC_SECURE"))
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", None)
WEAVIATE_BEARER_TOKEN = os.getenv("WEAVIATE_BEARER_TOKEN", None)

auth_credentials = None

if WEAVIATE_API_KEY:
    auth_credentials = weaviate.auth.Auth.api_key(WEAVIATE_API_KEY)
elif WEAVIATE_BEARER_TOKEN:
    auth_credentials = weaviate.auth.Auth.bearer_token(WEAVIATE_BEARER_TOKEN)

client = weaviate.connect_to_custom(
    http_host=WEAVIATE_HOST,
    http_port=WEAVIATE_PORT,
    http_secure=WEAVIATE_SECURE,
    grpc_host=WEAVIATE_GRPC_HOST,
    grpc_port=WEAVIATE_GRPC_PORT,
    grpc_secure=WEAVIATE_GRPC_SECURE,
    auth_credentials=auth_credentials,
)


@app.get("/schema")
def schema():
    return client.collections.list_all()


@app.post("/class/{class_name}")
def class0(
    class_name: str,
    offset: int = 0,
    limit: int = 20,
    keyword: str = "",
    certainty: float = 0.65,
    properties: list[str] | None = None,
):
    logger.info(f"{keyword=}, {certainty=}")

    collection = client.collections.get(class_name)
    paginate = {"limit": limit, "offset": offset}

    if keyword:
        query = {"query": keyword, "certainty": certainty}
        metadata = {"return_metadata": ["certainty", "distance"]}
        response = collection.query.near_text(**query, **metadata, **paginate)
        count_response = collection.aggregate.near_text(total_count=True, **query)
    else:
        response = collection.query.fetch_objects(**paginate)
        count_response = collection.aggregate.over_all(total_count=True)

    return {"data": response.objects, "count": count_response.total_count}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
