"""
RAG Response Generation Module.

This module implements the core Retrieval-Augmented Generation (RAG) functionality
for generating answers to user questions. It creates a pipeline that:

1. Retrieves relevant documents from a vector database
2. Formats the retrieved documents into a prompt context
3. Generates a response using an LLM (OpenAI)
4. Returns the generated answer along with reference source URLs

The module uses LangChain to build the RAG pipeline, making it easy to customize
and extend the generation process.
"""
import os
import sys
import dotenv
from typing import Dict, List, Tuple
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

# Add the src directory to the Python path to enable imports
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, src_dir)

# Import local utilities
from utils.logger import setup_logger
from utils.retriever_client import retrieve_similar_documents

# Load environment variables
dotenv.load_dotenv()

# Set up logger
logger = setup_logger(name="RAG Generation", log_to_file=True)

def get_rag_chain(model: str = None) -> RunnablePassthrough:
    """
    Create a complete RAG chain for generating answers to questions.
    
    This function builds a LangChain pipeline that:
    1. Takes a user question as input
    2. Retrieves relevant documents using vector similarity search
    3. Formats the question and retrieved documents into a prompt
    4. Sends the prompt to the LLM
    5. Returns the generated response
    
    The chain follows this structure:
    retrieve → prompt → llm → output_parser
    
    Args:
        model (str, optional): The OpenAI model name to use. If not provided,
                              defaults to the OPENAI_MODEL env variable or "gpt-4o"
        
    Returns:
        RunnablePassthrough: A fully configured RAG chain that can be invoked with a question
    """
    try:
        # Use environment variable if model not specified
        model = model or os.getenv('OPENAI_MODEL', 'gpt-4o')
        logger.info(f"Creating RAG chain with model: {model}")
        
        # Generate context using the retriever
        # This step creates a dictionary with the original question and retrieved context
        retrieve = {
            "context": lambda x: "\n\n".join([doc['content'] for doc in retrieve_similar_documents(x, "openai", 3)]),
            "question": RunnablePassthrough()
        }

        # Define the prompt template with detailed instructions for the LLM
        template = """You have to reply in markdown format. You are an empathetic Voy Health customer agent. Address the question first and then Answer the question based only on the following context. 
        If the person is having a normal conversation then go ahead; however, if the user is asking any question
        and If there is no relevant content in the context to answer the question, respond that you don't have enough information to answer accurately.
        
        And guife them to talk to the customer care using below information:
        Live Chat: Contact us via chat from your account (Mon-Fri - 09:00am - 17:00pm). Response Time: 2 minutes
        Email: Contact us at help@joinvoy.com. Response Time: 24 hours
        Phone: Call us at 020 3912 9885 (Mo-Fr 09:00-17:00). Response times may vary, press 2 if you'd like us to call you back once you're at the front of the queue
        If you have any questions during this process or need additional support, please don't hesitate to reach out. We're here to ensure you have everything you need to continue your weight loss journey successfully.



        Context:
        {context}

        Question: {question}

        Provide a clear, direct answer based solely on the context provided. Do not make assumptions or add information not present in the context.
        """
        
        # Create the prompt template for formatting retrieved contexts with the question
        prompt = ChatPromptTemplate.from_template(template)
        logger.debug("Created prompt template")
        
        # Initialize the language model with specified parameters
        llm = ChatOpenAI(temperature=0, model=model)
        logger.debug(f"Initialized ChatOpenAI with model: {model}")
        
        # Create output parser to extract the text response
        output_parser = StrOutputParser()

        # Create and return the complete RAG chain
        rag_chain = (
            retrieve  # Get question and retrieved documents
            | prompt  # Format into prompt template
            | llm     # Send to LLM
            | output_parser  # Parse response
        )
        
        logger.info("Successfully created RAG chain")
        return rag_chain
    
    except Exception as e:
        logger.error(f"Error creating RAG chain: {str(e)}")
        raise

def generate_answer(question: str) -> Tuple[str, List[str]]:
    """
    Generate an answer for a given question using the RAG pipeline.
    
    This function:
    1. Retrieves relevant documents from the vector database
    2. Extracts reference URLs from the documents
    3. Creates and executes the RAG pipeline to generate an answer
    4. Returns both the generated answer and reference sources
    
    Args:
        question (str): The user's question to be answered
        
    Returns:
        Tuple[str, List[str]]: A tuple containing:
            - The generated answer text (str)
            - A list of reference URLs from the source documents (List[str])
            
    Raises:
        Exception: If an error occurs during the generation process
    """
    try:
        logger.info(f"Generating answer for question: '{question}'")
        
        # First, retrieve the most relevant documents from the database
        docs = retrieve_similar_documents(question, "openai", 3)
        
        # Extract reference URLs from the retrieved documents for citation
        reference_urls = [doc['page_url'] for doc in docs]
        logger.info(f"Found {len(reference_urls)} reference documents")
        
        # If no relevant documents found, return a default response
        if not docs:
            logger.warning("No relevant documents found")
            return "I apologize, but I couldn't find any relevant information to answer your question accurately.", []
        
        # Get the configured RAG chain
        rag_chain = get_rag_chain()
        
        # Generate the answer by invoking the chain with the question
        answer = rag_chain.invoke(question)
        logger.info("Successfully generated answer")
        
        return answer, reference_urls
        
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        return f"I apologize, but I encountered an error while generating the answer: {str(e)}", []

# if __name__ == "__main__":
#     # Example usage
#     question = "Where is my order?"
#     answer, urls = generate_answer(question)
#     print("\nQuestion:", question)
#     print("\nAnswer:", answer)
#     print("\nReferences:")
#     for url in urls:
#         print(f"- {url}")
