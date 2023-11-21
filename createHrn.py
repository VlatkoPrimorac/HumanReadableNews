#!/usr/bin/python3

import yfinance as yahooFinance

import argparse      as argparse
import sqlite3
import sys
import urllib.parse
from datetime import datetime
from datetime import timedelta
import re

import dominate
from dominate.tags import *

# Utility function to pretty format dates
def prettyDateString(
    date,
    today = "Today "
    ):
    dateString = str(date) or ""

    # Remove seconds from 00:00:00
    if re.search("\d{2}:\d{2}:\d{2}$",dateString):
        dateString = re.sub(":\d{2}$","",dateString)

    # Remove today's date part from the article date
    todayString = str(datetime.today().date())
    dateString = re.sub(todayString+"\s*",today,dateString)

    # Remove yesterday's date part from the article date
    yesterdayString = str(datetime.today().date()-timedelta(days=1))
    dateString = re.sub(yesterdayString,"Yesterday",dateString)

    return dateString

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose',
        default=False,
        help='Verbose output',
        action=argparse.BooleanOptionalAction)

parser.add_argument('-o', '--output_file',
        default="",
        help='Output file, stdout by default')

parser.add_argument('-d', '--database_file',
        default="articles.db",
        help='Sqlite 3 DB file, articles.db by default')

parser.add_argument('-t', '--title',
        default="Business News Digest",
        help='Page title, Business New Digest by default')

parser.add_argument('-l', '--limit',
        default="1000",
        help='Limit the number of articles to, 1000 by default')

args = parser.parse_args()
verbose            = args.verbose
dbFileName         = args.database_file

verbose and print("Using verbose output...")

tickerList = [
    {   "category": "Index ETFs",
        "tickers":  [
            "SPY",      # S&P 500 tracking ETF
            "DIA",      # Dow Jones tracking ETF
            "QQQ",      # Nasdaq tracking ETF
            "IWM",      # Russell
        ], },
    {   "category": "Stock Index Futures",
        "tickers":  [
            "ES=F",     # S&P 500 Futures
            "YM=F",     # Dow Jones Futures
            "NQ=F",     # Nasdaq Futures
            "RTY=F",    # Russell Futures
        ], },
    {   "category": "Commodities Futures",
        "tickers":  [
            "GC=F",     # Gold Futures
            "SI=F",     # Silver Futures
            "HG=F",     # Copper Futures
            "CL=F",     # Crude oil Futures
            "BTC=F",    # Bitcoin futures
          # "^VIX",     # VIX - quote not working right either
        ], },
    {   "category": "Commodities Futures",
        "tickers":  [
            "EURUSD=X", # USD / Euro exchange rate
            "GBPUSD=X", # USD / GB exchange rate
            "CHFUSD=X", # USD / Swiss Franc exchange rate
            "CHFEUR=X", # Euro / Swiss Franc exchange rate
            "USDJPY=X", # Yen / USD exchange rate
          # "USDRSD=X", # $    / Srpski dinar
          # "EURRSD=X", # Euro / Srpski dinar
        ], },
    {   "category": "US Treasuries Yield",
        "tickers":  [
            "^TNX",     # 10 yr treasury yield
            "^TYX",     # 30 yr treasury yield
        ], },
    {   "category": "European Stocks",
        "tickers":  [
            "AIR.DE", 
            "ASME.DE", 
            "DB1.DE",
            "MOH.F", 
            "NESN.SW", 
            "SIE.DE", 
            "SLYG.F", 
            "SNW.DE",
        ], },
    {   "category": "US Lrge Cap Stocks",
        "tickers":  [
            "AAPL",
            "MSFT", 
            "AMZN",
            "NVDA",
            "GOOG",
            "META",
            "BRK-B", 
            "TSLA", 
            "UNH", 
            "LLY",
            "JPM",
            "XOM",
            "AVGO",
            "V",
            "JNJ",
            "PG",
            "MA",
        ], },
    ]


# marketIndexETFs = [
    # "SPY",      # S&P 500 tracking ETF
    # "DIA",      # Dow Jones tracking ETF
    # "QQQ",      # Nasdaq tracking ETF

    # These are not provided properly by the yf interface
    # "^GSPC",    # S&P 500
    # "^DJI",     # Dow Jones
    # "^IXIC",    # Nasdaq
    # "^N225",    # Nikkei 225
    # "^FTSE",    # FTSE 100
    # ]
# marketBonds = [
    # ]
# marketUsStocks = [
    # "AAPL", "AMZN","NVDA","GOOG","META","MSFT", "JPM", "LLY", "V", "PG",
    # "PFE", "NKE", "LMT", "MO", "HUM", "F","BRK-B","TSLA","UNH","JPM","XOM",
    # "JNJ","KO","WMT","HD","MRK","BA",
    # "BHP", # my old time favorite
    # "RIO",
    # "PM","DHR","COP","SBUX","T","A","AA","HUM","CSX","TT","AIG","OXY","D","O","B",
    # "C","Z","KR","EBAY","CSCO","INTC","AMD",
    # # ADRs
    # "BABA","NVO","SONY",
    # ]
# marketEurStocks = [
    # "SIE.DE","AIR.DE","NESN.SW","SNW.DE","ASME.DE","MOH.F","SLYG.F","DB1.DE",
    # ]
# marketUsStocks = list(set(marketUsStocks))
# marketUsStocks.sort()
# marketEurStocks = list(set(marketEurStocks))
# marketEurStocks.sort()

numberOfArticlesLimit = args.limit
verbose and print(f"Limiting number of articles to {numberOfArticlesLimit}")

# Open or create DB file
dbConnection = sqlite3.connect(dbFileName)

if not dbConnection:
    print ("Failed to open DB file " + dbFileName)
    exit()

# A civilized way to read DB rows, by column names
dbConnection.row_factory = sqlite3.Row

# DB "cursor" or handle
db = dbConnection.cursor()

if not db:
    print ("Cannot obtain DB handle for " + dbFileName)
    exit()

# Generate human readable html from a given set of articles
# Given all the data is in a DB now, this can be done
# by a completely separate program.
verbose and print(f"Generating html from articles in the database {dbFileName}.")

# verbose and print("Generating output html.")
doc = dominate.document(title=args.title)
doc.add(dominate.tags.comment(f"Generated by " + sys.argv[0]+" on " + str(datetime.today())))
doc.body["text"]    = "White"
doc.body["link"]    = "Green"
doc.body["vlink"]   = "DarkGreen"
doc.body["alink"]   = "DarkOliveGreen"
doc.body["bgcolor"] = "Black"
doc.body["margin"] = "20"
doc.body["padding"] = "20"
# doc.body["leftmargin"] = "20"
# doc.body["rightmargin"] = "20"
doc.add(dominate.tags.meta(charset="UTF-8"))

# Refresh every 30 minutes
doc.add(dominate.tags.meta(http_equiv="refresh", content="1800"))
doc.add(dominate.tags.h1(args.title, id="page_title"))

helpText = """
   Welcome, dear reader! 

   To read the latest business news, well... Just start reading.

   Articles are sorted from newest to oldest, just read, scroll and enjoy. 

   Click on the S&P quote to get detailed (yet delayed) market quotes.

   Click on Table of Contents to get the list of all articles available. 

   To jump to the next article, swipe left.
   To return to the previous article, swipe right.
   To return to the top and reload, (long) swipe down.
   """

# Nice to have, sql from DB printed into comment of the web page we generate
sqlComments = dominate.tags.comment("\n")
for sql in (
    "select count(*) as 'Articles in the database' from articles where title is not null",
    "select count(*) as 'Empty URLs in the database' from articles where title is     null",
    "select count(*) as 'Images in the database'   from articles where image is not null",
    """
    select
        date(date) as date,
        count(*)   as articles,
        count(case when url like '%cnn%'     then 'Something' end) as 'CNN',
        count(case when url like '%cnbc%'    then 'Something' end) as 'CNBC',
        count(case when url like '%yahoo%'   then 'Something' end) as 'Yahoo',
        count(case when url like '%insider%' then 'Something' end) as 'Business Insider'
    from
        articles
    group by
        date(date)
    order by
        date desc
    limit
        20
    """,
  # "select count(*) as 'CNN Articles'              from articles where title is not null and url like '%cnn%'",
  # "select count(*) as 'CNBC Articles'             from articles where title is not null and url like '%cnbc%'",
  # "select count(*) as 'Yahoo Articles'            from articles where title is not null and url like '%yahoo%'",
  # "select count(*) as 'Business Insider Articles' from articles where title is not null and url like '%insider%'",
    ):
    result = list(db.execute(sql))
    # sqlComments.add(sql+"\n")
    for row in result:
        for column in row.keys():
            sqlComments.add(column + ": " + "%4s" % str(row[column]) + "  ")
        sqlComments.add("\n")

quotesButtonText = "" # "Delayed Quotes: "
quotesDiv = dominate.tags.div(id="quotes")
quotesDiv.add(dominate.tags.br())
for tl in tickerList:
# for (category, marketIndices) in (
        # ("Index ETFs",     marketIndexETFs),
        # ("Futures",        marketFutures),
        # ("Currencies",     marketCurrencies),
        # ("US Stocks",      marketUsStocks),
        # ("European Stocks",marketEurStocks),
      # # ("Bonds", marketBonds), # bid/ask/current price not provided
    # ):
    # quotesTable = dominate.tags.table(padding="5px",border="5px",collapse="collapse",id="quotes")

    category      = tl["category"]
    marketIndices = tl["tickers"]

    quotesTable = dominate.tags.table(padding="25px")

    # Header one column for category - we replaced this by using category instead of Symbol in header below
    # tr=dominate.tags.tr(dominate.tags.th(category,colspan="100%",align="left", style="font-family:'Courier New'"))
    # quotesTable.add(tr)

    # Header columns
    tr=dominate.tags.tr()
    for header in ( category, "Ticker", "Bid", "Ask", "Previous Day Close","Pct Change",):
        tr.add(dominate.tags.th(header, align="left", style="font-family:'Courier New'"))
    quotesTable.add(tr)

    for index in marketIndices:
        tr=dominate.tags.tr()
        # I'm actually looking at Yahoo finance and the quotes of previous
        # date close from the website and this API are different. This is
        # to be used for shits and giggles only.
        indexInfo = yahooFinance.Ticker(index)

        for attribute,value in indexInfo.info.items():
            # print(attribute + ": " + str(value))
            pass

        pctChange = "{:+.2%}".format((indexInfo.info["bid"] - indexInfo.info["previousClose"])/indexInfo.info["previousClose"])\
                if "bid" in indexInfo.info and indexInfo.info["bid"] and "previousClose" in indexInfo.info and indexInfo.info["previousClose"] else "-"

        name = indexInfo.info["longName"] if "longName" in indexInfo.info else indexInfo.info["shortName"] if "shortName" in indexInfo.info else ""

        tr.add(
            dominate.tags.td(name                           , align="left", style="font-family:'Courier New'",),
            dominate.tags.td(indexInfo.info["symbol"]       , align="left", style="font-family:'Courier New'",),
            dominate.tags.td("%.2f" % indexInfo.info["bid"] , align="right", style="font-family:'Courier New'",) if "bid"           in indexInfo.info and indexInfo.info["bid"]           else dominate.tags.td(),
            dominate.tags.td("%.2f" % indexInfo.info["ask"] , align="right", style="font-family:'Courier New'",) if "ask"           in indexInfo.info and indexInfo.info["ask"]           else dominate.tags.td(),
            dominate.tags.td("%.2f" % indexInfo.info["previousClose"], align="right", style="font-family:'Courier New'",) if "previousClose" in indexInfo.info and indexInfo.info["previousClose"] else dominate.tags.td(),
            dominate.tags.td(pctChange                      , align="right", style="font-family:'Courier New'",),
            )
        quotesTable.add(tr)

        # Bad programming depending on th eorder but at times I get sloppy
        if(indexInfo.info["symbol"]=="SPY"): quotesButtonText += " S&P500 "  + pctChange
        if(indexInfo.info["symbol"]=="DIA"): quotesButtonText += ", DJIA "   + pctChange
        if(indexInfo.info["symbol"]=="QQQ"): quotesButtonText += ", Nasdaq " + pctChange
        if(re.search("Oil",name)): quotesButtonText += ", Crude Oil " + pctChange
    quotesDiv.add(quotesTable)
    quotesDiv.add(dominate.tags.br())

verbose and print(quotesButtonText)
quotesButton = dominate.tags.a(quotesButtonText, onClick="quotesShowHide()", id="quotes_button", style = "font-family:'Courier New'")

# Javascript code that gives show/hide button the functionality
quotesShowHideScript = dominate.tags.script("""
    // Show quotes by default
    var quotesDiv    = document.getElementById('quotes');
    var quotesButton = document.getElementById('quotes_button');
    quotesDiv.style.display = 'none';
    // quotesButton.innerHTML = 'Show Delayed Market Quotes';

    // Show or hide table of contents
    function quotesShowHide() {
       var quotesDiv    = document.getElementById('quotes');
       var quotesButton = document.getElementById('quotes_button');
       if (quotesDiv.style.display === 'none') {
           quotesDiv.style.display = 'block';
           quotesButton.innerHTML  = 'Hide Delayed Market Quotes';
       } else {
           quotesDiv.style.display = 'none';
           quotesButton.innerHTML  = '""" + quotesButtonText + """';
       }
    }
    """
    )


doc.add(sqlComments)

# Table of contents
toc = list(db.execute(f"""
    select
        title,
        date,
        url
    from
        articles
    where
        title is not null
    order by
        date            desc,
        date_downloaded desc
    limit
        {numberOfArticlesLimit}
    """))

# Open output file or stdout
if args.output_file:
    outputFH = open(args.output_file, "w", encoding="utf-8")
    if not outputFH:
        exit
    verbose and print("Output file: " + args.output_file)
else:
    verbose and print("Using stdout.")
    outputFH = sys.stdout

numberOfArticles      = len(toc)

# And they say Perl is unreadable. Doing this in Python was a learning experience, I learned to appreciate the beauty of Perl even more. 
numberOfArticlesToday     = len(list(filter(lambda x: datetime.strptime(x["date"],"%Y-%m-%d %H:%M:%S").date()>=datetime.now().date() if x["date"] else False, toc)))
numberOfArticlesYesterday = len(list(filter(
    lambda x:
        datetime.strptime(x["date"],"%Y-%m-%d %H:%M:%S").date()>=(datetime.now().date()-timedelta(days=1)) and
        datetime.strptime(x["date"],"%Y-%m-%d %H:%M:%S").date()< (datetime.now().date()                  )
    if x["date"] else False, toc)))


# Page <div> introduction
headerDiv = dominate.tags.div()
headerDiv.add(dominate.tags.comment(f"""
    Publically available business news presented in an easy to read format.

    Script: {sys.argv[0]}
    Args:   {sys.argv}

    {numberOfArticlesToday} articles found today,
    {numberOfArticlesYesterday} yesterday,
    page limited to {numberOfArticles} articles.
    """))
# headerDiv.add(dominate.tags.p("", id="demo"))

# Page <div> footer
footerDiv = dominate.tags.div()

jsFunctionsComment = dominate.tags.comment("""
    Python dominate library for html generation is escaping < and >
    characters, so the javascript code ends up being wrong in the
    browser. I'm glad I did this in Python so I can appreciate Perl 
    more and more each day. 

    dominate.tags.script
        ...
        if(1<0) { // stupid dominate library will translate this into &lt and make javascript not work
            ...
        }

    """)

# Javascript function definitions <script>
jsFunctionsScript = dominate.tags.script("""
    var xOrigin    =   0;
    var yOrigin    =   0;
    var xMargin    = 300;
    var yMargin    = 700;
    var resolution =  30;

    function touchStartHandler(event) {
        xOrigin = event.touches[0].clientX;
        yOrigin = event.touches[0].clientY;
    }
    function touchMoveHandler(
        event,
        linkToPreviousArticle,
        linkToNextArticle,
    ) {
        var x = event.touches[0].clientX;
        var y = event.touches[0].clientY;

        // These conditions should never be true
        if (xOrigin==0) { xOrigin = x; }
        if (yOrigin==0) { yOrigin = y; }

        var type = event.type

        // A good way to debug, turn this on when needed
        // document.getElementById('demo').innerHTML = x + ', ' + y + ', ' + xOrigin + ', ' + yOrigin;

        // Detect swipe right
        // trying to use more than without using the > character 
        if( parseInt((x-xOrigin-xMargin)/resolution) ==0 ) {
            // document.getElementById('demo').innerHTML = 'Swipe Right!';
            if(linkToPreviousArticle) {
                // alert(linkToPreviousArticle);
                // window.scrollTo(linkToPreviousArticle)
                window.location.href = linkToPreviousArticle;
            }
        }

        // Detect swipe left
        if( parseInt((x-xOrigin+xMargin)/resolution) ==0 ) {
            // document.getElementById('demo').innerHTML = 'Swipe Left!';
            if(linkToNextArticle) {
                // window.scrollTo(linkToNextArticle)
                window.location.href = linkToNextArticle;
            }
        }

        // Detect swipe up
        if( parseInt((y-yOrigin+yMargin)/resolution) ==0 ) {
            // document.getElementById('demo').innerHTML = 'Swipe Up!';
            // alert('Swipe Up!');
            // $('html, body').animate({ scrollTop: 0 }, 'fast');
            // window.scrollTo({top: 0})
            ;
        }

        // Detect swipe down
        if( parseInt((y-yOrigin-yMargin)/resolution) ==0 ) {
            // document.getElementById('demo').innerHTML = 'Swipe Down!';
            // alert('Swipe Down!');
            // location.replace('#')
            // $('html, body').animate({ scrollTop: 0 }, 'fast');
            // window.scrollTo({top: 0})
            window.location.href = '#';
            window.location.reload();
        }
    }
    """)

# Add header first, we shall add footer last,
# together with javascript code
doc.add(headerDiv)

# Table of contents
# TOC has her own <div> and #tag
tocDiv = dominate.tags.div(
    ontouchstart = "touchStartHandler(event)",
    ontouchmove  = "touchMoveHandler (event)",
    )
# tocDiv = dominate.tags.div(style="font-family:'Courier New'")
tocDiv["id"] = f"table_of_contents"

# Skip TOC and go to the first article
# tocDiv.add(
    # dominate.tags.a("Start reading the latest news", href="#first_article"),
    # " or pick from the articles below."
    # )
# tocDiv.add(dominate.tags.br())
# tocDiv.add(dominate.tags.br())

# for row in toc:
for articleNumber in range(len(toc)):
    row = toc[articleNumber]

    source = ""

    if   re.search(r"^http.*\:\/\/.*cnn\.com\/",row["url"]): source = "CNN"
    elif re.search(r"^http.*\:\/\/.*cnbc\.com\/",row["url"]): source = "CNBC"
    elif re.search(r"^http.*\:\/\/.*yahoo\.com\/",row["url"]): source = "Yahoo"
    elif re.search(r"^http.*\:\/\/.*insider\.com\/",row["url"]): source = "Business Insider"

    # No need vor <a> except I need to let api accept style part
    tocDiv.add(dominate.tags.a(prettyDateString(row["date"],today=""), style="font-family:'Courier New'"))
  # tocDiv.add(dominate.tags.a(re.sub("\s","_","%16s" % source), style="font-family:'Courier New'"))
    tocDiv.add(dominate.tags.a(row["title"], href="#" + re.sub("\W+","_",row["url"])))
    tocDiv.add(dominate.tags.br())

# Extra space after TOC
# tocDiv.add(dominate.tags.br())
tocDiv.add(dominate.tags.br())

# Table of Contents show/hide button
tocButton = dominate.tags.a("Show Table of Contents", onClick="tocShowHide()", id="toc_button", style = "font-family:'Courier New'")

# Javascript code that gives show/hide button the functionality
tocShowHideScript = dominate.tags.script("""
    // Hide table of contents by default
    var tocDiv    = document.getElementById('table_of_contents');
    var tocButton = document.getElementById('toc_button');
    tocDiv.style.display = 'none';
    tocButton.innerHTML = 'Show Table of Contents';

    // Show or hide table of contents
    function tocShowHide() {
       var tocDiv    = document.getElementById('table_of_contents');
       var tocButton = document.getElementById('toc_button');
       if (tocDiv.style.display === 'none') {
           tocDiv.style.display = 'block';
           tocButton.innerHTML  = 'Hide Table of Contents';
       } else {
           tocDiv.style.display = 'none';
           tocButton.innerHTML  = 'Show Table of Contents';
       }
    }
    """
    )

# Add market quotes to the document
doc.add(quotesButton)
doc.add(quotesDiv)
doc.add(quotesShowHideScript)
doc.add(dominate.tags.br())

# Add table of contents to the document
doc.add(tocButton)
doc.add(tocDiv)
doc.add(tocShowHideScript)
doc.add(dominate.tags.br())
doc.add(dominate.tags.br())

# "articles" will be the DB table where we store articles
# We will be a memory hog here but if the structure gets
# to be too large the web page will be too large anyway
articles = list(db.execute(f"""
    select
        * 
    from
        articles
    where
        title is not null
    order by
        date            desc,
        date_downloaded desc
    limit
        {numberOfArticlesLimit}
    """))

for articleNumber in range(len(articles)):
    row = articles[articleNumber]
    articleDiv = dominate.tags.div(
        # ontouchstart = "touchStartHandler(event)",
        # ontouchmove  = "touchMoveHandler (event)",
    )
    # articleDiv.add(dominate.tags.br())
    articleId = re.sub("\W+","_",row["url"])

    articleDiv["id"] = articleId
    articleDiv["margin"] = f"20%"
    articleDiv["border"] = f"20%"

    titleDiv = dominate.tags.div()

    titleLink = dominate.tags.b(dominate.tags.a(row["title"], target="_blank", href=row["url"]))

    # Reload when user wants top page, that way we pick whatever is new
    topAndReloadLink            = dominate.tags.a("latest", href="#")
    topAndReloadLink["onClick"] = "window.location.reload();"

    # We will have an extra ID tag for the first article that will
    # work after reload, no matter which article comes first
    topOfPageLink       = dominate.tags.a("Back to: ", style = "font-family:'Courier New'")
    topOfPageLink.add(    dominate.tags.a(
        "The Top and Reload",
        href  = "#",
        style = "font-family:'Courier New'",
        ))
    # topOfPageLink.add(dominate.tags.comment("""
        # Table of Contents is common usage yet just because veryone is wrong it does not mean I have to do the same.
        # Plus,, without the 's' it fits neatly under the number of letters above. 
        # """))
    # topOfPageLink.add(dominate.tags.a(" and reload.", style = "font-family:'Courier New'"))
    # firstArticleLink    = dominate.tags.a("first", href="#first_article")

    # Reload when user wants first article too
    topOfPageLink   ["onClick"] = "window.location.reload();"
    # firstArticleLink["onClick"] = "window.location.reload();"

    lastArticleLink     = dominate.tags.a("last",     href="#" + re.sub("\W+","_",articles[len(articles)-1]["url"]))
    previousArticleLink = dominate.tags.a("previous", href="#" + re.sub("\W+","_",articles[articleNumber-1]["url"])) if articleNumber>0                 else ""
    thisArticleTag      =                                        re.sub("\W+","_",articles[articleNumber]  ["url"]) 
    thisArticleLink     = dominate.tags.a("this",     href="#" + re.sub("\W+","_",articles[articleNumber]  ["url"])) 
    nextArticleLink     = dominate.tags.a("next"    , href="#" + re.sub("\W+","_",articles[articleNumber+1]["url"])) if articleNumber<(len(articles)-1) else ""

    previousArticleUrl = "#" + re.sub("\W+","_",articles[articleNumber-1]["url"]) if articleNumber>0                 else ""
    nextArticleUrl     = "#" + re.sub("\W+","_",articles[articleNumber+1]["url"]) if articleNumber<(len(articles)-1) else ""

    articleDiv["ontouchstart"] = f"touchStartHandler(event, '{previousArticleUrl}', '{nextArticleUrl}')"
    articleDiv["ontouchmove"]  = f"touchMoveHandler (event, '{previousArticleUrl}', '{nextArticleUrl}')"

    titleDiv.add(titleLink,dominate.tags.br())

    if row["date"]:
        titleDiv.add(dominate.tags.a(prettyDateString(row["date"]), style="font-family:'Courier New'"))
    else:
        articleAge  = datetime.now()        - datetime.strptime(row["date_downloaded"],"%Y-%m-%d %H:%M:%S.%f")
        articleDays = datetime.now().date() - datetime.strptime(row["date_downloaded"],"%Y-%m-%d %H:%M:%S.%f").date()
        if articleAge.days > 0:
            # 24h+ old download
            titleDiv.add(dominate.tags.a("Downloaded on " + re.sub("\s.*","",row["date_downloaded"])))
        elif articleDays.days > 0:
            # Yesterday's download, given we did not pick it up above
            # titleDiv.add(dominate.tags.a("Downloaded yesterday"))
            pass
        elif articleAge.seconds > 60*60:
            # hours = int(articleAge.seconds/(60*60))
            # titleDiv.add(dominate.tags.a(f"Downloaded {hours} hours ago."))
            pass
        elif articleAge.seconds > 60:
            # minutes = int(articleAge.seconds/(60))
            # titleDiv.add(dominate.tags.a(f"Downloaded {minutes} minutes ago."))
            pass
        else:
            # titleDiv.add(dominate.tags.a(f"Downloaded just now."))
            pass

    # The target audience is mobile first. Swipe right and left now work,
    # so does the good old scrolling, thus we no longer need these links.
    # titleDiv.add(dominate.tags.p(previousArticleLink, nextArticleLink))

    articleDiv.add(titleDiv)

    if row["image"]:
        articleDiv.add(dominate.tags.img(src=row["image"],width="100%",align="center"))

    # Content <div>
    contentDiv = dominate.tags.div()
    for paragraph in row["content"].split("\n\n"):
        # If there are no words in the paragraph, skip it
        if re.search("^W+$",paragraph):
            debug and print(f"No words in paragraph: {paragraph}, skipping")
            continue

        # Change space to newline after 80 or so characters
        # It looks nicer when reading the page html source
        paragraph = re.sub(r"(.{80}.*?)\s+",r"\1\n           ",paragraph)

        # Replace ======= with =
        paragraph = re.sub(r"\={5,}",r"=====",paragraph)
        paragraph = re.sub(r"\-{5,}",r"-----",paragraph)

        contentDiv.add(dominate.tags.p(paragraph),)
    articleDiv.add(contentDiv)

    # Share this article on usual platforms
    shareDiv = dominate.tags.div(dominate.tags.a("Share in: ",style="font-family:'Courier New'"))
    mailSubject = row["title"]
    mailContent = row["content"][:1000]
    mailContent = re.sub(r"(.{80}.*?)\s+",r"\1\n           ",mailContent)
    shareInEmail = dominate.tags.a(
               "email",
        href  = f"mailto:?subject='{mailSubject}'&body={mailContent}",
        style = "font-family:'Courier New'",
        )

    paramsFacebook = {
        "u": f"http://18.205.182.137/HumanReadableNewsDev.html#{articleId}",
        "t": row["title"],
        }
    shareToFb = dominate.tags.a(
                 "Facebook",
        target = "_blank",
        href   = "https://www.facebook.com/sharer/sharer.php?" + urllib.parse.urlencode(paramsFacebook),
        style = "font-family:'Courier New'",
        )

    shareToTwitter = dominate.tags.a(
                 "Twitter",
      # target  = "_blank",
      # href    = "https://twitter.com/intent/tweet?" + urllib.parse.urlencode(paramsTwitter),
      # href    = "https://twitter.com/twitterdev?" + urllib.parse.urlencode(paramsTwitter),
        style   = "font-family:'Courier New'",
        # Twitter won't recognice IP address as a web page link
        onClick = f"sharePage('http://HumanReadableNews.com/HumanReadableNewsDev.html#{thisArticleTag}','{row['title']}\\n\\n')"
        )

    # ASCII 38 is '&'
    jsTwitterShare = dominate.tags.script("""
    function sharePage(url,text) {
        window.open('https://twitter.com/intent/tweet?url=' + encodeURIComponent(url) + String.fromCharCode(38) + 'text=' + encodeURIComponent(text), '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=350,width=600');
        return false;
    };
    """)

    shareDiv.add(
        shareInEmail,  dominate.tags.a(",",style="font-family:'Courier New'"),
        shareToFb,     dominate.tags.a(",",style="font-family:'Courier New'"),
        shareToTwitter,
        )

    articleDiv.add(dominate.tags.br())
    articleDiv.add(
      # shareDiv,
      # dominate.tags.br(),
      # firstArticleLink,
      # topOfPageLink,
      # topAndReloadLink, previousArticleLink, nextArticleLink,
      # lastArticleLink,
        )
    articleDiv.add(dominate.tags.br())
    articleDiv.add(dominate.tags.br())
    articleDiv.add(dominate.tags.br())
    articleDiv.add(dominate.tags.br())

    # Add this <div> element to the page
    doc.add(articleDiv)

# In the end, add page footer <div> here
doc.add(footerDiv)

# Not necessary but it makes me feel better
doc.add(jsFunctionsComment)

doc.add(jsFunctionsScript)

# Twitter share button functionality
doc.add(jsTwitterShare)

# At long last print the document to the file
print(doc, file=outputFH)

