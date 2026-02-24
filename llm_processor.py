import ollama
import json

def process_content_with_llm(text, model_name="llama3", ollama_host="http://localhost:11434"):
    """
    Sends the extracted text to a local Ollama instance and asks it to 
    summarize and categorize the content. Returns a dictionary with 
    'summary' and 'category'.
    """
    if not text:
        return {"summary": "No text content found to summarize.", "category": "Uncategorized"}

    prompt = f"""
You are an expert content analyzer. I will provide you with the text content of a webpage.
Your task is to analyze it and provide a JSON response with exactly two keys:
1. "summary": A concise, 1-3 sentence summary of the main topic or purpose of the page.
2. "category": A single, broad category describing the content (e.g., Technology, News, Programming, Shopping, Entertainment, Productivity, Reference, etc.). Choose the single best fit.

The response MUST be valid JSON only, without any markdown formatting or extra text.

Webpage Text:
{text[:4000]} # Limit text length to avoid token limits for standard models

JSON Response format:
{{
  "summary": "...",
  "category": "..."
}}
"""

    try:
        # Use the ollama python client which supports format="json" 
        # to enforce json output in newer versions
        client = ollama.Client(host=ollama_host)
        
        response = client.chat(
            model=model_name,
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            format='json'
        )
        
        result_content = response['message']['content']
        
        # Parse the JSON string from the response
        try:
            data = json.loads(result_content)
            return {
                "summary": data.get("summary", "Summary not generated"),
                "category": data.get("category", "Uncategorized")
            }
        except json.JSONDecodeError:
            print("Failed to parse JSON from LLM response:", result_content)
            return {"summary": "Error parsing summary", "category": "Uncategorized"}
            
    except Exception as e:
        print(f"Error calling Ollama API: {e}")
        return {"summary": f"Error: {str(e)}", "category": "Error"}
