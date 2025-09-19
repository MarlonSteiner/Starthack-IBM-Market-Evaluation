import requests
import json
import os

# --- Configuration ---

# IMPORTANT: Paste your webz.io API key here.
# It's better to use an environment variable, but pasting it here works for the hackathon.
API_KEY = "47dc1680-bbf1-4cef-a6e1-724f247f5ae9" 

def get_news_from_api():
    """Fetches recent news articles from the webz.io News API Lite."""

    # The API endpoint for the Lite version
    url = "https://api.webz.io/newsApiLite"

    # Define the parameters for your API request
    # 'q' is your query. You can use boolean operators like OR/AND.
    # 'sort=crawled' gets the most recently discovered articles.
    params = {
        "token": API_KEY,
        "q": '"financial markets" OR "earnings surprise" OR "CEO exit" OR "interest rates" OR "stock market"',
        "sort": "crawled" 
    }

    print("Fetching recent news from webz.io API...")

    try:
        response = requests.get(url, params=params)
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status() 
        
        data = response.json()
        
        # The articles are in the 'posts' list of the response
        api_articles = data.get('posts', [])
        
        formatted_articles = []
        for article in api_articles:
            # Reformat the API response to match the structure your project expects
            formatted_articles.append({
                'source': article.get('thread', {}).get('site', 'Unknown Source'),
                'title': article.get('title', 'No Title'),
                'url': article.get('url', '#'),
                'article_text': article.get('text', '')
            })
            
        return formatted_articles

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        # Try to print the API's error message if available
        try:
            print("API Response:", response.text)
        except:
            pass
        return []
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from API response.")
        print("API Response:", response.text)
        return []


# --- Execution ---

if __name__ == "__main__":
    print("Starting news fetcher using webz.io API...\n")
    
    scraped_data = get_news_from_api()
    
    if scraped_data:
        print(f"\n✅ Successfully fetched {len(scraped_data)} articles from the API.")
        # Pretty print the output using json module
        print(json.dumps(scraped_data, indent=2))
        
        # Optionally, save to a file
        with open('api_articles.json', 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, ensure_ascii=False, indent=4)
        print("\nData saved to api_articles.json")
    else:
        print("\n❌ No articles were fetched. Check your API key and the query parameters.")