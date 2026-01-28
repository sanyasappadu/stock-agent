import os
import json
import requests
import feedparser
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client       = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_news_headlines(company_name: str) -> list:
    # Try NewsAPI first
    if NEWS_API_KEY:
        try:
            url  = (
                f"https://newsapi.org/v2/everything"
                f"?q={company_name}+stock+India"
                f"&sortBy=publishedAt&pageSize=5"
                f"&language=en"
                f"&apiKey={NEWS_API_KEY}"
            )
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data.get("status") == "ok":
                return [a["title"] for a in data.get("articles", [])
                        if a.get("title")]
        except Exception as e:
            print(f"  NewsAPI error: {e}, falling back to RSS")

    # Fallback: Google News RSS (no key needed)
    try:
        query = company_name.replace(" ", "+")
        feed  = feedparser.parse(
            f"https://news.google.com/rss/search"
            f"?q={query}+NSE+India&hl=en-IN&gl=IN&ceid=IN:en"
        )
        return [e.title for e in feed.entries[:5]]
    except Exception as e:
        print(f"  RSS error: {e}")
        return []

def analyze_sentiment(headlines: list, symbol: str) -> dict:
    if not headlines:
        return {
            "symbol":    symbol,
            "sentiment": "neutral",
            "score":     50,
            "reason":    "No news found",
            "headlines": []
        }

    headlines_text = "\n".join(f"- {h}" for h in headlines)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial news sentiment analyzer for Indian stocks. "
                    "Analyze the given headlines and return ONLY a JSON object with: "
                    "sentiment (bullish / bearish / neutral), "
                    "score (integer 0-100, where 100=very bullish, 0=very bearish, 50=neutral), "
                    "reason (one short sentence explaining the score)."
                )
            },
            {
                "role": "user",
                "content": f"Stock: {symbol}\nHeadlines:\n{headlines_text}"
            }
        ]
    )

    result = json.loads(response.choices[0].message.content)
    return {
        "symbol":    symbol,
        "sentiment": result.get("sentiment", "neutral"),
        "score":     int(result.get("score", 50)),
        "reason":    result.get("reason", ""),
        "headlines": headlines
    }

def get_sentiment_score(symbol: str, company_name: str) -> dict:
    print(f"  Getting news for {company_name}...")
    headlines = get_news_headlines(company_name)
    return analyze_sentiment(headlines, symbol)

if __name__ == "__main__":
    result = get_sentiment_score("TCS", "Tata Consultancy Services")
    print(f"\nSymbol:    {result['symbol']}")
    print(f"Sentiment: {result['sentiment']}")
    print(f"Score:     {result['score']}/100")
    print(f"Reason:    {result['reason']}")
    print(f"Headlines: {len(result['headlines'])} found")