# modules/query_processing.py

import openai
import os 
from modules.hallucination_mitigation import (
    generate_system_prompt,
    extract_information_from_context
)

def answer_query(query, relevant_chunks, config):
    """
    Answer the user's query using the language model and function calling.
    """    
    # Hallucination Mitigation Technique 1: System prompt
    system_prompt = generate_system_prompt()
    
    # User prompt including context and question
    messages = [
        {"role": "system", "content": "You are a helpful assistant that answers questions about legal contracts based on the provided context. Always strive for accuracy and only use information from the given context."},
        {"role": "user", "content": f"Context: {relevant_chunks}\n\nQuestion: {query}"}
    ]


    # Define functions for function calling
    functions = [
        {
            "name": "extract_effective_date",
            "description": "Extract the effective date from the contract text",
            "parameters": {
                "type": "object",
                "properties": {
                    "effective_date": {
                        "type": "string",
                        "description": "The effective date of the contract"
                    }
                },
                "required": ["effective_date"]
            }
        }
    ]
    
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # Initial API call
    response = openai.ChatCompletion.create(
        model=config['model'],
        messages=messages,
        functions=functions,
        function_call="auto"  # Let the model decide
    )
    # print(response.choices[0].message.content)
    message = response['choices'][0]['message']
    # print(message)
    
    # Check if the model wants to call a function
    if message.get('function_call'):
        function_call = message['function_call']
        if function_call['name'] == 'extract_effective_date':
            # Hallucination Mitigation Technique 2: Function calling
            effective_date = extract_information_from_context(relevant_chunks, query)
            # Append function response to messages
            messages.append(message)
            messages.append({
                "role": "function",
                "name": "extract_effective_date",
                "content": effective_date
            })
            # Final response
            final_response = openai.ChatCompletion.create(
                model=config['model'],
                messages=messages
            )
            final_message = final_response['choices'][0]['message']
            answer = final_message['content']
        else:
            answer = "The assistant tried to call an unknown function."
    else:
        # Direct answer without function call
        answer = message['content']
    
    return answer
