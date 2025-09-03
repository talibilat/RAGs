
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder


sql_query_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                """You are a PostgreSQL expert. Analyse what the user is asking and what information is needed to answer the question.
                Then generate ONE runnable PostgreSQL SQL query using ONLY the provided schema. Do not include markdown fences or commentary.
                
                IMPORTANT: If the question seems too broad (asking for "all" data), automatically add a LIMIT clause to prevent large result sets. Focus on the most relevant/recent data.
                
                Requirements for every query:
                - Only include source_url columns when the corresponding table is selected AND when NOT using aggregate functions:
                  - If selecting from financial_metrics_normalized, include f.source_url AS source_url_f.
                  - If selecting from cap_table_normalized, include cm.source_url AS source_url_cm.
                  - company_financials has no source_url column; NEVER reference c.source_url.
                  - If a table isn't joined/used, omit its source column.
                  - IMPORTANT: When using aggregate functions (COUNT, SUM, MAX, MIN, AVG), do NOT include source_url columns as they would require GROUP BY clauses.
                - Always include a column named "unit" in the SELECT list:
                  - If selecting from financial_metrics_normalized, use f.unit AS unit when relevant.
                  - If selecting monetary amounts from cm.amount_usdm, return 'USDm' AS unit.
                  - If selecting percentages from cm.percent_cap, return '%' AS unit.
                  - If selecting ratios from cm.x_ebitda, return 'x' AS unit.
                  - Otherwise return NULL AS unit.
                - CRITICAL: When using aggregate functions (COUNT, SUM, MAX, MIN, AVG), do NOT include f.unit in SELECT as it would require GROUP BY f.unit. Instead, use a literal string like 'USDm' AS unit or NULL AS unit.
                - Select only columns necessary to answer the question plus allowed source_url columns and unit.Hello

                  - For aggregate questions (e.g., COUNT, SUM, MAX, MIN, AVG), do NOT include identifier columns such as c.company_id unless explicitly requested by the question.
                  - For aggregate questions, do NOT include source_url columns as they would require GROUP BY clauses.
                  - Avoid selecting large JSON columns like c.periods, c.key_financials, c.cash_flow_and_leverage, c.cap_table unless explicitly requested.
                - Use table and column names exactly as they appear in the schema.
                - Prefer relevant filters and ordering when appropriate.
                """
            ),
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        (
            "human",
            (
                "Schema:\n{schema}\n\n"
                "Question: {question}\n\n"
                "Return only the SQL in the `sql` field."
            ),
        ),
    ]
)


generation_answer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                """You are given:
                        - A user question
                        - A SQL query
                        - A SQL result
                        
                        Your task is to **answer the user's question** using only the SQL result.  
                        Each sentence in your answer that is based on the result must include a **source reference** in the form [1][2][3] etc.  
                        You may reuse the same reference number if the same source supports multiple sentences.  
                        At the end of the answer, explicitly state which number corresponds to which source.  
                        
                        IMPORTANT: If the SQL result is very large (more than 20 rows) or the question seems too broad, provide a summary/gist instead of all details. Mention that this is a summary because the full dataset is large, and ask the user to be more specific for detailed information.
                        
                        Format strictly as shown in the examples.
                        
                        ---
                        
                        ## Few-Shot Examples
                        
                        ### Example 1
                        **Question:** What is the total revenue of Tronox in 2024?  
                        **SQL Query:**  
                        ```sql
                        SELECT Sales FROM key_financials 
                        WHERE company='Tronox' AND period_date='2024-12-31';
                        
                        SQL Result: 3074
                        
                        Answer:
                        The total revenue of Tronox in 2024 was USD 3,074 million [1].
                        
                        Sources:
                        [1] → /company_id/1/key_financials
                        
                        ⸻
                        
                        Example 2
                        
                        Question: What was Chemco Holdings’ operating profit margin in LTM 2025?
                        SQL Query:
                        
                        SELECT Operating_profit_margin FROM key_financials 
                        WHERE company='Chemco Holdings' AND period_date='2025-06-30';
                        
                        SQL Result: 9.0
                        
                        Answer:
                        Chemco Holdings reported an operating profit margin of 9.0% in the LTM ending June 2025 [2].
                        
                        Sources:
                        [2] → /company_id/2/key_financials
                        
                        ⸻
                        
                        Example 3
                        
                        Question: What was MineralsCo International’s net debt position as of 2025-06-30?
                        SQL Query:
                        
                        SELECT Net_debt FROM cash_flow_and_leverage 
                        WHERE company='MineralsCo International' AND period_date='2025-06-30';
                        
                        SQL Result: 760
                        
                        Answer:
                        As of 30 June 2025, MineralsCo International had a net debt of USD 760 million [3][2].
                        
                        Sources:
                        [3] → /company_id/3/cash_flow_and_leverage
                        [2] → /company_id/2/cap_table_normalized"""
            ),
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        (
            "human",
            (
                "Question: {question}\n"
                "SQL Query: {query}\n"
                "SQL Result: {result}\n"
                "Answer: "
            ),
        ),
    ]
)

