import pymongo
import os
import dotenv
import certifi
from utils.logger import setup_logger

# Set up minimal logger
logger = setup_logger(name="MongoDB_Client", log_to_file=True)

# Load environment variables
dotenv.load_dotenv()

# MongoDB connection variables
mongodb_uri = os.getenv("MONGODB_URI")

# Initialize MongoDB client once
try:
    client = pymongo.MongoClient(mongodb_uri, tlsCAFile=certifi.where())
    # Ping the server to check connection
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

def get_collection(db_name, collection_name):
    """Get a MongoDB collection from the specified database
    
    Args:
        db_name (str): Name of the database
        collection_name (str): Name of the collection
        
    Returns:
        Collection: MongoDB collection object
    """
    try:
        db = client[db_name]
        collection = db[collection_name]
        return collection
    except Exception as e:
        logger.error(f"Error accessing collection {collection_name} in database {db_name}: {str(e)}")
        raise 