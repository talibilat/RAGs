import asyncio
from arq import create_pool
from arq.connections import RedisSettings
import os

async def main():
    redis_settings = RedisSettings(host=os.getenv('REDIS_HOST', 'localhost'), port=int(os.getenv('REDIS_PORT', 6379)))
    redis = await create_pool(redis_settings)
    job = await redis.enqueue_job('process_document', 'test_doc_123')
    print(f"Enqueued job {job.job_id}")

if __name__ == '__main__':
    asyncio.run(main())
