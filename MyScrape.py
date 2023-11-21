
from requests_html import HTMLSession   as HTMLSession
from bs4           import BeautifulSoup as BeautifulSoup
from datetime      import datetime
import re            as re
import sys           as sys

def getLinks(
    url,

    debug      = 0,
    javascript = 0,

    # Regular expression that lets us know
    # this is a news article
    news_link_regex = ".*",
    ):
    session  = HTMLSession()

    executeJavaScript = javascript

    debug and print("Get " + url)
    pageResponse = session.get(url)

    if executeJavaScript:
        # execute Java-script
        debug and print("Execute JavaScript")
        pageResponse.html.render()
    else:
        debug and print("Skip JavaScript execution")

    debug and print("Parse beautiful soup")
    pageSoup = BeautifulSoup(pageResponse.html.html, "html.parser")

    links = []
    for link in pageSoup.find_all('a'):
        href = link.get('href')

        # Stupid None type, not true not false. Just bogus stupid. 
        if href:
            pass
        else:
            # Link is None value, whatever that means
            continue

        # Ignore stupid places
        if re.search("hulu\.com",url):
            debug and print("Ignoring hulu link: " + href)
            continue

        # As it happens we should only get self referential link
        if re.search("yahoo\.com",url)   and not re.search("yahoo\.com",href):   continue
        if re.search("cnn\.com",url)     and not re.search("cnn\.com",href):     continue
        if re.search("cnbc\.com",url)    and not re.search("cnbc\.com",href):    continue
        if re.search("insider\.com",url) and not re.search("insider\.com",href): continue

        # Yahoo specific
        if re.search("yahoo\.com",url) and not re.search("yahoo.*news\/.*\w+.*",href):
            debug and print("Ignoring yahoo link: " + href)
            continue

        # BBC specific
        if re.search("bbc\.co",url) and not re.search("bbc.*article\/.*\w+.*",href):
            debug and print("Ignoring BBC link: " + href)
            continue

        # MarketWatch specific
        if re.search("marketwatch\.com",url) and not re.search("marketwatch.*story\/.*\w+.*",href):
            debug and print("Ignoring BBC link: " + href)
            continue

        # Seeking alpha specific
        if re.search("seekingalpha\.com",url) and not re.search("(news|article)\/.*\w+.*",href):
            debug and print("Ignoring Seeking Alpha link: " + href)
            continue

        # CNN specific
        if re.search("cnn\.com",url) and not re.search("cnn.*index.html$",href):
            debug and print("Ignoring directory CNN link: " + href)
            continue

        # Aljazeera specific
        if re.search("aljazeera\.com",url) and not re.search("aljazeera\.com\/news$",href):
            debug and print("Ignoring non news Aljazeera link: " + href)
            continue

        # CNN specific
        if re.search("cnn\.com",url) and re.search("live-news",href):
            debug and print("Ignoring live news CNN link: " + href)
            continue

        # CNBC specific
        if re.search("cnbc\.com",url) and re.search("live-updates",href):
            debug and print("Ignoring live updates CNBC link: " + href)
            continue

        # BusinessInsider specific
        if re.search("businessinsider\.com",url) and not re.search("\d+-\d+$",href):
            debug and print("Ignoring BisinessInsider non-article link: " + href)
            continue
        if re.search("insider\.com",url) and not re.search("\d+-\d+$",href):
            debug and print("Ignoring Insider non-article link: " + href)
            continue
        if re.search("insider\.com\/personal-finance",url):
            debug and print("Ignoring Insider personal-finance link: " + href)
            continue

        # CNBC specific
        if re.search("cnbc\.com",url) and not re.search("cnbc.*\.html$",href):
            debug and print("Ignoring CNBC non-article link: " + href)
            continue

        # TKer specific, not used or useful, delete this
        if re.search("tker\.co",url) and not re.search("tker\.co\/p\/",href):
            debug and print("Ignoring TKer non-article link: " + href)
            continue
        if re.search("tker\.co",url) and     re.search("comments$",href):
            debug and print("Ignoring TKer comments link: " + href)
            continue

      # newsLink = re.search(news_link_regex,href)
      # if not newsLink:
      #     debug and print("Ignoring: " + href)
      #     continue

        newsLink = href
 
        # If we get here, we have a news link
        # Make relative links absolute
        if not re.search("^http", newsLink):
            # Remove the last / from source
            # Does not work for http://server/document.html
            # but I just found out Python does not support full regex
            # newsLink = url[0:-1] + newsLink
            # print(newsLink)
            # print(re.search("http.*?\:\/\/.*?\/",url))
            exp = "http.*?\:\/\/.*?\/"

            # newsLink = str(re.search("http.*?\:\/\/.*?\/",url).group()) + newsLink[1:]
            if re.search(exp,url):
                newsLink = str(re.search(exp,url).group()) + newsLink[1:]
            # print(newsLink)
            # print()

            # Python regex sucks ass, it is so much less than Perl >:{
            # newsLink = re.sub("\/\/","/",newsLink)

            debug and print("News link absolute: " + newsLink)
 
        # Looking for a thumbnail of this link
        img = link.find("img")
        imgSrc = None
        if img:
            debug and print("img link: " + str(img))
            imgSrc = img.get("src")
            # Image exists and the link is not bogus
            if imgSrc and re.search("^http",imgSrc) and not re.search("\s+",imgSrc):
                debug and print(f"img src link: {imgSrc}")
            else:
                # Ignore a bogus image link found
                imgSrc = None

        debug and print("Link: " + newsLink)
        links.append({"url":newsLink,"thumbnail":imgSrc})

    # Old way, returning just a URL, delete this
    # return map(lambda x: x["url"],links)
    return links

def getArticle(
    url,

    # html tag and class that will
    # match human readable content
  # content_tag     , # e.g. "div"       for YahooFinance
  # content_class   , # e.g. "caas-body" for YahooFinance

    debug      = 0,
    javascript = 0,

    # Stop reading after this junk
    terminators = [
        'Read Next .*'               ,              # Business Insider
        'Read next .*'               ,              # Business Insider
        'In other news:.*'           ,              # Business Insider
      # 'Read more:.*'               ,              # Yahoo
        'Advertisement.*'            ,
        'Read the latest financial.*',
        'Click here for.*'  ,                       # Yahoo
        'Read Next:.*'               ,              # Yahoo
        'Most stock quote data provided by BATS.*', # CNN
        '\d+ Cable News Network.*',                 # CNN
        'Sign up for free newsletters and get .*',  # CNBC
      # "^Don't miss:.*",                           # CNBC
        '\d+ CNBC LLC.*All Rights Reserved.*',      # CNBC
        '^— \w+ \w+$',                              # CNBC
        'Related from TKer:',                       # TKer
        'Subscribe to TKer',                        # TKer
        'Ready for more\?',                         # TKer
        ],
    ):

    # Sanity check
    if not re.search(r"^http.*\:.*\/",url):
        print(f"Unexpected URL: {url}")
        return

    session  = HTMLSession()

    executeJavaScript = javascript

    # Fetch the news link
    newsLinkResponse = session.get(url)
 
    # News pages javascript execution
    if executeJavaScript:
        newsLinkResponse.html.render()
 
    newsSoup = BeautifulSoup(newsLinkResponse.html.html, "html.parser")

    if not newsSoup:
        print(f"Failed to parse content for {url}")
        return
 
    if not newsSoup.html:
        print(f"Failed to parse html for {url}")
        return
 
    title = newsSoup.html.find("title")
    if not title:
        debug and print("No title found in: " + url)
        return

    title = title.get_text()

    if title == "Error":
        debug and print("Error title in: " + url)
        return

    if title == "Access Denied":
        debug and print("Access Denied title in: " + url)
        return

    # Just keep the text part of the object
    debug and print("Title: " + title)
 
    # Elements that may contain something interesting
    elements = []

    if re.search("yahoo\.com\/",url):
        debug and print(f"Fetching div class_=caas-body elements for Yahoo url {url}")
        elements = newsSoup.find_all("div", class_="caas-body")
    elif re.search("cnbc\.com\/",url):
        debug and print(f"Fetching div class_=group elements for CNBC url {url}")
        elements = newsSoup.find_all("div", class_="group")
    elif re.search("bloomberg",url):
        debug and print(f"Fetching P elements for Bloomberg url {url}")
        elements = newsSoup.find_all("P")
    else:
        debug and print(f"Fetching ALL elements for url {url}")
        elements = newsSoup.find_all()
 
    if not elements:
        debug and print("Nothing useful found in " + url)
        return
 
    # Content is an array of paragraphs found
    # We could have used just a string with double
    # newline but this may be cleaner later.
    content = []
    images  = []

    stopReading = False
    for element in elements:
        debug and print("Element: " + str(element))

        for image in element.find_all('img'):
            imgSrc = image.get("src")
            if imgSrc:
                if re.search("c_thumb",imgSrc):   continue # CNN
                if re.search("avatars",imgSrc):   continue # Yahoo
                if re.search(".png$",imgSrc):     continue # Yahoo logo
                if not re.search("\w+",imgSrc):   continue # empty
                if not re.search("^http",imgSrc): continue # relative links

                debug and print(f"image src link: {imgSrc}")
                images.append(imgSrc)

        for paragraph in element.find_all('p'):
            # If this paragraph has links, ignore it.
            # Usually it is a link to another article.
            # Danger is if it just links to a ticker info. 
            if paragraph.find_all("a"):
                debug and print("Paragraph containing links, skipping.")
                debug and print(paragraph)
                continue

            paragraphText = paragraph.get_text()

            debug and print("Paragraph: " + paragraphText)

            # Skip empty paragraphs
            if not re.search("\w+",paragraphText):
                continue

            # Remove some whitespace
            paragraphText = re.sub("^\s+","" ,paragraphText)
            paragraphText = re.sub("\n"  ," ",paragraphText)
            paragraphText = re.sub("\s+" ," ",paragraphText)

            # Skip boilerplate paragraphs
            paragraphText = re.sub("^Fear \S+ Greed Index\s*"  ,"",paragraphText)
            paragraphText = re.sub("^Markets\s*$"              ,"",paragraphText)
            paragraphText = re.sub("^Latest\s+Market\s+News\s*","",paragraphText)
            paragraphText = re.sub("^Jump to\s*","",paragraphText)
            paragraphText = re.sub("^Read more\s*","",paragraphText)

            for terminator in terminators:
                if re.search(terminator,paragraphText):
                    paragraphText = re.sub(terminator,'',paragraphText)
                    debug and print("Terminated reading at: " + terminator)
                    stopReading = True

            # If there is still content before terminator, write it
            if re.search("\w+",paragraphText):
                content.append(paragraphText)

            # Python does not have labels or
            # goto to break the outer loop
            if stopReading:
                break
        if stopReading:
            break

    # If images were not found in the content, find them in the outer page.
    # This is done for CNBC, and still the image search is imperfect.
    if len(images)==0:
        for image in newsSoup.find_all('img'):
            imgSrc = image.get("src")
            if not imgSrc:                            continue
            if not re.search("\w+"          ,imgSrc): continue 
            if not re.search("^http"        ,imgSrc): continue 
            if re.search("c_thumb"          ,imgSrc): continue # Yahoo
            if re.search("avatars"          ,imgSrc): continue # Yahoo
            if re.search(".png$"            ,imgSrc): continue # Yahoo logo
            if re.search("\.svg$"           ,imgSrc): continue # CNBC
            if re.search("w\=60"            ,imgSrc): continue # CNBC
            if re.search("scorecardresearch",imgSrc): continue # CNBC

            if imgSrc:
                debug and print(f"Outer page image src link: {imgSrc}")
                images.append(imgSrc)

    # Find article date
    articleDate = None

    for div in newsSoup.find_all('div', class_="byline-timestamp"):  # Business Insider
        date = div.get_text()
        if not re.search("\w+", date): continue

        # 2023-10-28T13:30:11Z
        date = re.sub("\s+$"  ,"",date)
        date = re.sub("^\s+"  ,"",date)
        date = re.sub("\n+"   ,"",date)
        date = re.sub("[A-Z]$","",date)

        # Add error check here.
        articleDate = datetime.strptime(date,"%Y-%m-%dT%H:%M:%S")

        debug and print(f"Datetime found: {articleDate}")
        break

    for date in newsSoup.find_all('time'):                         # YahooFinance, CNN
        debug and print(f"Date found: {date}")
        if date.has_attr("datetime"):
            # String value
            strDate = date["datetime"]

            strDate = re.sub("\.\d{3}\w$","",strDate) # YahooFinance
            strDate = re.sub("\+\d{3}\w$","",strDate) # CNN
            strDate = re.sub("[A-Z]$"    ,"",strDate) # Business Insider

            # Convert to datetime type
            if re.search("^\d{4}-\d+-\d+T\d{2}:\d{2}:\d{2}$",strDate):
                articleDate = datetime.strptime(strDate,"%Y-%m-%dT%H:%M:%S")
            else:
                print(f"Unexpected date format: {strDate}")

            debug and print(f"Datetime found: {articleDate}")
            break

    for div in newsSoup.find_all('div', class_="timestamp"): # CNN
        date = div.get_text()
        if not re.search("\w+", date): continue
        date = re.sub("Updated\s+","",date)
        date = re.sub("Published\s+","",date)

        # 9:56 AM EDT, Thu November 2, 2023
        timeDateYear = date.split(",")
        timeDateYear = list(map(lambda x: re.sub("^\s+","",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("\s+$","",x), timeDateYear))

        timeDateYear = list(map(lambda x: re.sub("Jan\w*\s+","01-",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("Feb\w*\s+","02-",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("Mar\w*\s+","03-",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("Apr\w*\s+","04-",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("May\w*\s+","05-",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("Jun\w*\s+","06-",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("Jul\w*\s+","07-",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("Aug\w*\s+","08-",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("Sep\w*\s+","09-",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("Oct\w*\s+","10-",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("Nov\w*\s+","11-",x), timeDateYear))
        timeDateYear = list(map(lambda x: re.sub("Dec\w*\s+","12-",x), timeDateYear))

        # debug and print(timeDateYear[0])
        # debug and print(timeDateYear[1])
        # debug and print(timeDateYear[2])

        # Remove day (Mon, Tue...)
        timeDateYear[1] = re.sub("^\w+\s+","",timeDateYear[1])
        # debug and print(timeDateYear[1])

        # Put back the date 
        date = timeDateYear[2] + "-" + timeDateYear[1] + " " + timeDateYear[0]

        # 2023-11-2 11:11 AM EDT
        date = re.sub("\s+\w+$","",date)

        # Add error check here
        articleDate = datetime.strptime(date,"%Y-%m-%d %H:%M %p")
        debug and print(f"Datetime found: {articleDate}")
        break

    return {
      # "url"    : url,     # redundant
        "title"  : title,
        "date"   : articleDate,
        "content": content, # Array of text paragraphs
        "images" : images,  # Array of img links
        }

