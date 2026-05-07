from arq.connections import RedisSettings
from src.worker.tasks import process_document, embed_chunks, sync_to_search_engines
import os

class WorkerSettings:
    functions = [process_document, embed_chunks, sync_to_search_engines]
    redis_settings = RedisSettings(host=os.getenv('REDIS_HOST', 'localhost'), port=int(os.getenv('REDIS_PORT', 6379)))
