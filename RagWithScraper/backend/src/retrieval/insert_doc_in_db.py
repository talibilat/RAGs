import os
import pandas as pd
import sys
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Add the src directory to the Python path to enable imports
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, src_dir)

# Import the logger and mongo client
from utils.logger import setup_logger
from utils.mongo_client import get_collection
from utils.openai_embeddings import generate_openai_embedding
from utils.hf_embeddings import generate_hf_embedding

# Set up logger and paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
csv_path = os.path.join(
    project_root,
    os.getenv('DATA_DIR', 'data'),
    os.getenv('FAQS_DIR', 'faqs'),
    os.getenv('CSV_FILENAME', 'faqs_regex.csv')
)
logger = setup_logger(name="Insert Data to MongoDB", log_to_file=True)

# Get MongoDB collection
faqs_collection = get_collection(
    os.getenv('MONGODB_DATABASE', 'manual'),
    os.getenv('MONGODB_COLLECTION_FAQS', 'faqs_regex')
)

# Clear existing data from the collection
logger.info("Clearing existing data from MongoDB collection...")
faqs_collection.delete_many({})
logger.info("Collection cleared successfully")

# Read the CSV file
df = pd.read_csv(csv_path)
logger.info(f"CSV loaded with {len(df)} rows and {len(df.columns)} columns")

# Data processing
logger.info("Processing data...")
# Combine question and answer into a new 'content' column
df['content'] = "Question: " + df['question'] + "\nAnswer: " + df['answer']

# Drop the confidence column if it exists
if 'confidence' in df.columns:
    df = df.drop(columns=['confidence'])
    logger.info("Dropped 'confidence' column")

logger.info(f"Data processed. Final columns: {', '.join(df.columns)}")

# Convert DataFrame to list of dictionaries (JSON-like)
records = df.to_dict(orient='records')
logger.info(f"Converting {len(records)} records to MongoDB documents")

# Generate embeddings for each record
logger.info("Generating embeddings for documents...")
for record in records:
    try:
        # Generate OpenAI embeddings
        record['content_embedding_openai'] = generate_openai_embedding(record['content'])
        logger.debug(f"Generated OpenAI embedding for: {record['question'][:50]}...")
        
        # Generate HuggingFace embeddings
        record['content_embedding_hf'] = generate_hf_embedding(record['content'])
        logger.debug(f"Generated HF embedding for: {record['question'][:50]}...")
    except Exception as e:
        logger.error(f"Error generating embeddings for document: {str(e)}")

# Insert the records into MongoDB
logger.info("Inserting records with embeddings into MongoDB...")
result = faqs_collection.insert_many(records)
logger.info(f"Successfully inserted {len(result.inserted_ids)} documents into MongoDB")
logger.info("Data import complete!")

if __name__ == "__main__":
    logger.info("Starting data insertion process...")