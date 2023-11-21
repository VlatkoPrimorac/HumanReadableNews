#!/usr/bin/python3

import argparse      as argparse
import sqlite3
import datetime
import re

# Our module with scrape function
import MyScrape

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose',
        default=False,
        help='Verbose output',
        action=argparse.BooleanOptionalAction)

parser.add_argument('-J', '--JavaScript',
        default=False,
        help='Execute JavaScript',
        action=argparse.BooleanOptionalAction)

parser.add_argument('-S', '--GetSecondaryLinks',
        default=False,
        help='Get news links from each article.',
        action=argparse.BooleanOptionalAction)

parser.add_argument('-n', '--news_source',
        action='append',
        default=[],
        help='News source file(s)')

parser.add_argument('-d', '--database_file',
        default="articles.db",
        help='Sqlite 3 DB file, articles.db by default')

args = parser.parse_args()
verbose            = args.verbose
executeJavaScript  = args.JavaScript
getSecondaryLinks  = args.GetSecondaryLinks
dbFileName         = args.database_file

verbose and print("Using verbose output...")

# Open or create DB file
dbConnection = sqlite3.connect(dbFileName)

# A civilized way to read DB rows, by column names
dbConnection.row_factory = sqlite3.Row

if not dbConnection:
    print ("Failed to open DB file " + dbFileName)
    exit()

# DB "cursor" or handle
db = dbConnection.cursor()

if not db:
    print ("Cannot obtain DB handle for " + dbFileName)
    exit()

verbose and print("Using DB file " + dbFileName)

# "articles" will be the DB table where we store articles
results = db.execute("select * from sqlite_master where name='articles'")
if results.fetchone() is None:
    # Create table
    verbose and print("Creating articles DB table.")

    # date            is date found in the article
    # date_downloaded is date we downloaded the page
    db.execute("create table articles(url, thumbnail, title, content, image, date, date_downloaded)")

newsSources = args.news_source 
if (not newsSources) or len(newsSources)==0:
    newsSources = [
        "https://news.yahoo.com/",
        "https://cnbc.com/",
        "https://businessinsider.com/",
      # "https://money.cnn.com/", # 404 results only
        "https://edition.cnn.com/business/",
        "https://edition.cnn.com/business/tech/",
        "https://edition.cnn.com/markets/",
        "https://finance.yahoo.com/",
        "https://finance.yahoo.com/topic/stock-market-news/",
        "https://finance.yahoo.com/topic/economic-news/",
        "https://finance.yahoo.com/topic/crypto/",
        "https://finance.yahoo.com/topic/earnings/",
        # To do: 
        # "https://apnews.com/business",
        # "https://apnews.com/business",
        # "https://www.aljazeera.com/economy/",
        # "",
        ]

verbose and print(f"News sources: {newsSources}")

# Use the same download date for all articles
# downloaded in this run. That way we can sort
# them later by other criteria.
downloadDate = datetime.datetime.now()

for url in newsSources:
    verbose and print(f"Fetching links for {url}")

    if not re.search("^http",url):
        url = "http://" + url + "/"

    # array of {url: thumbnail:} dictionaries
    links = MyScrape.getLinks(
        url        = url,
        javascript = executeJavaScript,
      # debug = verbose,
        )

    # Go one deeper and follow the links from each linked article itself
    if getSecondaryLinks:
        for link in links:
            newsLinkUrl = link["url"]
            verbose and print(f"Fetching secondary links for {newsLinkUrl}")
            articleLinks = MyScrape.getLinks(
                url   = newsLinkUrl,
              # debug = verbose,
                )

            links = links + articleLinks

    numberOfArticlesFound = len(links)
    verbose and print(f"{numberOfArticlesFound} articles found")

    for link in links:
        newsLinkUrl = link["url"]

        # Sanity check
        if re.search("\'",newsLinkUrl):
            print(f"Single quote found in url, skipping: {newsLinkUrl}")
            continue
        if re.search("\s+",newsLinkUrl):
            print(f"Whitespace found in url, skipping: {newsLinkUrl}")
            continue

        # Avoid sites that behave badly
        if re.search("governor.virginia\.gov",newsLinkUrl):
            print(f"governor.virginia.gov found in url, skipping: {newsLinkUrl}")
            continue
        if re.search("census\.gov",newsLinkUrl):
            print(f"census.gov found in url, skipping: {newsLinkUrl}")
            continue

        # If link is already downloaded, skip it
        results = db.execute(f"select * from articles where url='{newsLinkUrl}'")
        if results.fetchone() is not None:
          # verbose and print(f"Already processed: {newsLinkUrl}")
            continue
        else:
            verbose and print(f"Reading article: {newsLinkUrl}")

        # { title=..., content=..., }
        article = MyScrape.getArticle(
            url             = newsLinkUrl,
          # debug           = verbose,
            )


        if not article:
            # Save bogus entry so we don't download it again
            db.execute(
                """insert into articles(
                    url,
                    thumbnail,
                    title,
                    content,
                    image,
                    date,
                    date_downloaded) values(?,?,?,?,?,?,?)""",
                (
                    newsLinkUrl,
                    link["thumbnail"],
                    None,
                    None,
                    None,
                    None,
                    downloadDate,
                ),
            )
        else:
            # getArticle will return an array of images. Ignore those
            # images we have alredy used. This will be useful to
            # eliminate common thumbnails form each website, as it
            # will appear only once. 
            results = db.execute(f"select image from articles where image like 'http%'")
            seen = {}
            for row in results:
                seen[row["image"]] = True
            newImages = list(filter(lambda x: not x in seen,article["images"]))

            db.execute(
                """insert into articles(
                    url,
                    thumbnail,
                    title,
                    content,
                    image,
                    date,
                    date_downloaded) values(?,?,?,?,?,?,?)""",
                (
                    newsLinkUrl,
                    link["thumbnail"],
                    article["title"],
                    "\n\n".join(article["content"]),
                    newImages[0] if len(newImages)>0 else None,
                    article["date"],
                    downloadDate,
                ),
            )

        dbConnection.commit()

