import ollama
import json
import google.generativeai as genai
from security import validate_llm_input

def process_with_ollama(prompt, model_name, host):
    """Internal helper for Ollama processing. Returns (content, tokens)."""
    client = ollama.Client(host=host)
    response = client.chat(
        model=model_name,
        messages=[{'role': 'user', 'content': prompt}],
        format='json'
    )
    content = response['message']['content']
    # For Ollama, total tokens = prompt_eval_count + eval_count
    tokens = response.get('prompt_eval_count', 0) + response.get('eval_count', 0)
    return content, tokens

def process_with_gemini(prompt, api_key):
    """Internal helper for Gemini processing. Returns (content, tokens)."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # Using flash for speed and cost-effectiveness
    
    # Gemini might need a nudge to return clean JSON
    response = model.generate_content(prompt + "\nIMPORTANT: Return ONLY valid JSON.")
    
    # Extract tokens from usage_metadata if available
    tokens = getattr(response.usage_metadata, 'total_token_count', 0) if hasattr(response, 'usage_metadata') else 0
    return response.text, tokens

def process_content_with_llm(text, provider="ollama", model_name="llama3", ollama_host="http://localhost:11434", gemini_api_key=None):
    """
    Analyzes content using the specified LLM provider (ollama or gemini).
    Returns a dictionary with 'summary', 'category', and 'tokens'.
    """
    if not text:
        return {"summary": "No text content found to summarize.", "category": "Uncategorized", "tokens": 0}

    # Security Layer: Sanitize and validate input
    validation = validate_llm_input(text)
    if validation["is_risk"]:
        return {
            "summary": "Summarization blocked for security reasons (potentially malicious content).",
            "category": "Security Blocked",
            "tokens": 0
        }
    
    # Use sanitized text for the prompt
    clean_text = validation["safe_text"]

    prompt = f"""
You are an expert content analyzer. I will provide you with the text content of a webpage.
Your task is to analyze it and provide a JSON response with exactly two keys:
1. "summary": A concise, 1-3 sentence summary of the main topic or purpose of the page.
2. "category": A single, broad category describing the content (e.g., Technology, News, Programming, Shopping, Entertainment, Productivity, Reference, etc.). Choose the single best fit.

The response MUST be valid JSON only, without any markdown formatting or extra text.

Webpage Text:
{clean_text[:4000]}

JSON Response format:
{{
  "summary": "...",
  "category": "..."
}}
"""

    try:
        if provider == "gemini":
            if not gemini_api_key:
                return {"summary": "Gemini API key missing", "category": "Config Error", "tokens": 0}
            result_content, tokens = process_with_gemini(prompt, gemini_api_key)
        else: # Default to ollama
            result_content, tokens = process_with_ollama(prompt, model_name, ollama_host)
        
        # Parse the JSON string from the response
        # Sometimes LLMs wrap JSON in code blocks
        if "```json" in result_content:
            result_content = result_content.split("```json")[1].split("```")[0].strip()
        elif "```" in result_content:
            result_content = result_content.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(result_content)
            return {
                "summary": data.get("summary", "Summary not generated"),
                "category": data.get("category", "Uncategorized"),
                "tokens": tokens
            }
        except json.JSONDecodeError:
            print("Failed to parse JSON from LLM response:", result_content)
            return {"summary": "Error parsing summary", "category": "Uncategorized", "tokens": tokens}
            
    except Exception as e:
        print(f"Error calling {provider} API: {e}")
        return {"summary": f"Error: {str(e)}", "category": "Error", "tokens": 0}
