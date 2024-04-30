DEFAULT_FEEDS = [
    "https://feeds.arstechnica.com/arstechnica/features.xml",
    "https://pluralistic.net/feed/",
    "https://www.theatlantic.com/feed/best-of/",
    "https://www.quantamagazine.org/feed",
    "https://www.reddit.com/r/python/top.rss",
    "https://lobste.rs/top/rss",
    "https://hnrss.org/best",
    "https://en.wikipedia.org/w/api.php?action=featuredfeed&feed=featured&feedformat=atom",
    "https://www.openculture.com/feed/rss2",
    "https://publicdomainreview.org/rss.xml",
    "https://www.eff.org/rss/updates.xml",
    "https://www.theverge.com/features/rss/index.xml",
    "https://www.bbc.com/culture/feed.rss",
    "https://blog.opensource.org/feed/",
    "https://www.technologyreview.com/feed/",
    "https://simonwillison.net/atom/everything/",
]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
LOG_LEVEL = "INFO"
GET_TIMEOUT = 10
FETCH_INTERVAL_SEC = 1800
SKIP_OLDER_THAN_DAYS = 60
PG_URI = "postgresql://pav:password@localhost/rss"
PG_POOL_MIN = 5
PG_POOL_MAX = 50
