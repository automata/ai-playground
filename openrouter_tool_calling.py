import os
import json, requests
from openai import OpenAI
from dotenv import load_dotenv
from pprint import pprint as pp

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# You can use any model that supports tool calling
MODEL = "deepseek/deepseek-chat-v3-0324:free"
# MODEL = "google/gemini-2.0-flash-001"

openai_client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENROUTER_API_KEY,
)

task = "What are the titles of some James Joyce books?"

messages = [
  {
    "role": "system",
    "content": "You are a helpful assistant."
  },
  {
    "role": "user",
    "content": task,
  }
]

def search_gutenberg_books(search_terms):
    search_query = " ".join(search_terms)
    url = "https://gutendex.com/books"
    response = requests.get(url, params={"search": search_query})

    simplified_results = []
    for book in response.json().get("results", []):
        simplified_results.append({
            "id": book.get("id"),
            "title": book.get("title"),
            "authors": book.get("authors")
        })

    return simplified_results

tools = [
  {
    "type": "function",
    "function": {
      "name": "search_gutenberg_books",
      "description": "Search for books in the Project Gutenberg library based on specified search terms",
      "parameters": {
        "type": "object",
        "properties": {
          "search_terms": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "List of search terms to find books in the Gutenberg library (e.g. ['dickens', 'great'] to search for books by Dickens with 'great' in the title)"
          }
        },
        "required": ["search_terms"]
      }
    }
  }
]

TOOL_MAPPING = {
    "search_gutenberg_books": search_gutenberg_books
}

request_1 = {
    "model": MODEL,
    "tools": tools,
    "messages": messages
}

response_1 = openai_client.chat.completions.create(**request_1).choices[0].message

pp(response_1)
