#!/usr/bin/python3

import requests, json, os, sqlite3, argparse, random
from sys import argv, stdout
from collections import OrderedDict
from bs4 import BeautifulSoup
from langdetect import detect_langs, DetectorFactory

# DetectorFactory.seed = 0 # SEED FOR CONSISTENCY
# database_name = 'plugin_telemetry.db'
# verbose = False
# jdump = False

# MARKETPLACE URLS
WP_MARKETPLACE = 'https://wordpress.org/plugins/{}'
DRUPAL_MARKETPLACE = 'https://www.drupal.org/project/{}'
JOOMLA_MARKETPLACE = 'https://extensions.joomla.org/extensions/extension/{}'
JEXTENSIONS = 'https://storejextensions.org/extensions/{}.html'
CODECANYON_SEARCH = 'https://codecanyon.net/search/{}'
EDD = 'https://easydigitaldownloads.com/downloads/{}'
WPMUDEV = 'https://premium.wpmudev.org/project/{}'
GITHUB = 'https://github.com{}'
THEMEFOREST_SEARCH = 'https://themeforest.net/search/{}'

# OTHER URLS
WP_DOWNLOADS_API = 'https://api.wordpress.org/stats/plugin/1.0/downloads.php'
WP_DEVLOG_URL = 'https://plugins.trac.wordpress.org/log/{}'
WP_PROFILE_URL = 'https://profiles.wordpress.org/{}'
DRUPAL_PROFILE_URL = 'https://www.drupal.org{}'
CC_DORK = 'https://www.google.com/search?q=inurl:{} site:codecanyon.net'
GITSEARCH = 'https://github.com/search?q={}'

UA_LIST = user_agent_list = [
   #Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    #Firefox
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
]

class TelemetryScanner():
  def __init__(self):
    self.database_name   = 'plugin_telemetry.db'
    self.verbose         = False
    self.jdump           = False
    DetectorFactory.seed = 0

# GENERIC TELEMETRY
  def initTelemetryData(self):
    d = OrderedDict()
    d.update({'Plugin Name':'name'})
    d.update({'Author':OrderedDict()})
    d.update({'Latest Version':'ver'})
    d.update({'Date Modified':'date'})
    d.update({'Downloads':'downloads'})
    d.update({'Ratings':'ratings'})
    d.update({'Sales':'sales'})
    return d

  def initTelemetryDB(self, database):
    try:  # CONNECT TO DB
      db = sqlite3.connect(database)
    except Exception as e:  # SOMETHING WENT WRONG
      print('There was a problem connecting to the database: {}'.format(database))
      print(e)
    c = db.cursor()

    # SET UP TABLES
    c.execute('CREATE TABLE IF NOT EXISTS wp_mkt (name, author, version, date, downloads, rating, price)')
    c.execute('CREATE TABLE IF NOT EXISTS joomla_mkt (name, author, version, date, rating, price)')
    c.execute('CREATE TABLE IF NOT EXISTS drupal_mkt (name, author, version, date, downloads, rating, price)')
    c.execute('CREATE TABLE IF NOT EXISTS jext (name, version, rating, price)')
    c.execute('CREATE TABLE IF NOT EXISTS codecanyon (name, author, date, downloads, rating, price)')
    c.execute('CREATE TABLE IF NOT EXISTS edd (name, date, version, price)')
    c.execute('CREATE TABLE IF NOT EXISTS wpmudev (name, version, downloads, price)')
    c.execute('CREATE TABLE IF NOT EXISTS github (name, author, date, version, rating, price)')
    c.execute('CREATE TABLE IF NOT EXISTS themeforest (name, author, date, downloads, rating, price)')

    # SAVE AND QUIT
    db.commit()
    db.close()

  def get_soup(self, mkt, slug):
    if mkt is 'wp_mkt':
      URL = WP_MARKETPLACE.format(slug)
    elif mkt is 'joomla_mkt':
      URL = JOOMLA_MARKETPLACE.format(slug)
    elif mkt is 'drupal_mkt':
      URL = DRUPAL_MARKETPLACE.format(slug)
    elif mkt is 'jext':
      URL = JEXTENSIONS.format(slug)
    elif mkt is 'codecanyon':
      URL = self.codecanyon_search(slug)
    elif mkt is 'themeforest':
      URL = self.themeforest_search(slug)
    elif mkt is 'edd':
      _slug = slug.lower()
      if 'edd-' in _slug: # Trim slug first, then try request
        _slug = _slug[4:]
      if '-master' in _slug:
        _slug = _slug[:-7]
      URL = EDD.format(_slug)
    elif mkt is 'wpmudev':
      URL = WPMUDEV.format(slug)

    # ADD A UA HEADER TO THE REQUEST, HELPS WITH SOME MARKETS

    try:  # GET REQUEST
      ua = random.choice(UA_LIST)
      source = requests.get(URL, headers={'User-Agent':ua})
    except requests.exceptions.RequestException as e:
      if mkt not in ['codecanyon', 'themeforest']:
        print("Handled Exception => {}".format(e))
    
    return BeautifulSoup(source.content, 'html.parser')

  def get_author_language(self, info):
    author = info['Author']
    author_url_source = None
    try:  # SCRAPE AUTHOR'S WEBSITE
      author_url_source = requests.get(author['URL'])
    except requests.exceptions.RequestException: # NOPE :(
      # print("Encountered RequestException when scraping --> {}".format(author['URL']))
      # print("Trying internet search instead...\n")
      self.get_author_info(author['Name'], info)
    
    if author_url_source is not None: # LANGUAGE DETECTION ON AUTHORS SITE
      author_url_source = BeautifulSoup(author_url_source.content, 'html.parser')
      langs = detect_langs(author_url_source.text)
      languages = OrderedDict()
      for l in langs:
        languages.update({l.lang:(round(l.prob, 4) * 100)})
      author.update({'Languages':languages})
    else: # NO LANGUAGES FOUND
      pass

  def get_author_info(self, name, info):
    author = info['Author']
    site_dork = "github.com"
    google_query = 'https://google.com/search?q='
    url = google_query + name + " site:" + site_dork
    source = requests.get(url)
    soup = BeautifulSoup(source.content, "html.parser")
    websites = []
    try:
      websites = soup.find_all('div', {'class':'kCrYT'})
    except:
      print("Error: Could not search " + name + " with parameter: " + site_dork)
    for website in websites:
      try:
        website = website.find('a')['href'].split("&")[0].split("=")[-1]
      except:
        continue
      if site_dork in website:
        website = "/".join(website.split("/")[:4])
        author.update({'Github':website})
        break

    source = requests.get(website)
    soup = BeautifulSoup(source.content, "html.parser")
    try:
      location = soup.find(attrs={'itemprop':'homeLocation'}).text.strip("\n")
      author.update({'Location':location})
    except:
      pass
    try:
      email = soup.find(attrs={'itemprop':'email'}).text.strip("\n")
      author.update({'Email':email})
    except:
      pass
    try:
      url = soup.find(attrs={'itemprop':'url'}).text.strip("\n")
      author.update({'Other URL':url})
    except:
      pass

# WP MARKETPLACE
  def wp_mkt_get_plugin_info(self, info, source):
    self.wp_get_plugin_info(info, source)
    self.wp_get_author_info(info, source)
    self.wp_get_download_stats(info, self.plugin_slug)
    self.wp_get_dev_log(info, self.plugin_slug)

  def wp_get_plugin_info(self, info, source):
    name = source.find('h1', {'class':'plugin-title'}).text

    table = source.find('div', {'class':'widget plugin-meta'})
    line = [t for t in table.find_all('li')]
    version = line[0].strong.text
    updated = line[1].strong.text

    info.update({'Plugin Name':name})
    info.update({'Latest Version':version})
    info.update({'Date Modified':updated})

    try:
      table = source.find('script', {'type':'application/ld+json'})
      table = json.loads(table.text)[0]

      info.update({'Ratings': self.wp_get_rating_info(table)})
      info.update({'Sales': self.wp_get_sales_info(table)})
    except:
      info.update({'Ratings':'not found'})
      info.update({'Sales':'not found'})
    
  def wp_get_rating_info(self, table):
    ratings = table['aggregateRating']
    avg = ratings['ratingValue']
    count = ratings['ratingCount']
    return '{}/5 {} ratings'.format(avg, count)

  def wp_get_sales_info(self, table):
    sales = table['offers']
    price = sales['price']
    currency = sales['priceCurrency']
    return '{} {}'.format(price, currency)

  def wp_get_author_info(self, info, source):
    author_info = source.find('span', {'class':'author vcard'})
    author = OrderedDict()
    author.update({'Name':author_info.text})
    try:
      author.update({'URL':author_info.a.attrs['href']})
    except:
      author.update({'URL':'not found'})
    info.update({'Author':{'Main':author}})
    try:
      self.get_author_language(info)
    except:
      pass

  def wp_scrape_profile(self, user_name):
    url = WP_PROFILE_URL.format(user_name)
    
    
    try:  # GET PROFILE
      source = requests.get(url)
    except requests.exceptions.RequestException:
      pass
    source = BeautifulSoup(source.content, 'html.parser')
    profile = {'Profile URL':url}
    profile_header = source.find('header', {'class':'site-header clear'})
    user_meta = source.find('ul',{'id':'user-meta'})

    try:  # NAME
      name = profile_header.h2.text
      profile['Name'] = name
    except:
      pass

    try:  # SLACK
      handle = profile_header.p.text.strip()
      e = handle.find(' on Slack')
      if e == -1:
        e = handle.find(' on WordPress.org and Slack')
      if e != -1:
        b = handle.rfind('@', 0, e)
        profile['Slack'] = handle[b:e]
      else:
        pass
    except:
      pass

    try:  # Member Since
      profile['Member Since'] = user_meta.find(
                                                'li',
                                                {'id':'user-member-since'}
                                              ).find('strong').text.strip()
      pass
    except:
      pass

    try:  # Location
      profile['Location'] = user_meta.find(
                                            'li',
                                            {'id':'user-location'}
                                          ).find('strong').text.strip()
    except:
      pass

    try:  # Website
      profile['URL'] = user_meta.find(
                                        'li',
                                        {'id':'user-website'}
                                     ).find('strong').text.strip()
    except:
      pass

    try:  # GitHub
      profile['GitHub'] = user_meta.find(
                                          'li',
                                          {'id':'user-github'}
                                        ).find('strong').a['href']
    except:
      pass

    try:  # Company
      profile['Company'] = user_meta.find(
                                            'li',
                                            {'id':'user-company'}
                                         ).find('strong').text.strip()
    except:
      pass

    return profile

  def wp_get_download_stats(self, info, slug):
    statsURL = WP_DOWNLOADS_API +'?slug={}&historical_summary=1'.format(slug)
    download_stats = BeautifulSoup(requests.get(statsURL).content, 'html.parser')
    info.update({'Downloads': json.loads(download_stats.text)['all_time']})

  def wp_get_dev_log(self, info, slug):
    try:
      ua = random.choice(UA_LIST)
      source = requests.get(WP_DEVLOG_URL.format(slug), headers={'User-Agent':ua})
    except requests.exceptions.RequestException:
      pass
    source = BeautifulSoup(source.content, 'html.parser')

    authors = []
    authors = self.wp_track_author_changes(source, authors)
    
    info['Author']['History'] = OrderedDict()
    for author in authors:
      try:
        author_profile = self.wp_scrape_profile(author)
        info['Author']['History'].update({author:author_profile})
      except:
        info['Author']['History'].update({author:'not found'})

  def wp_track_author_changes(self, source, authors):
    table = source.find('table', {'class':'listing chglist'})
    a_list = table.find_all('td', {'class':'author'})
    for a in a_list:
      a = a.text.strip()
      if a not in authors:
        authors.append(a)

    next_revs_button = None
    try:
      nav = source.find('div', {'id':'ctxtnav'})
      next_revs_button = nav.find('li', {'class':'last'}).find('span').a['href']
    except:
      pass

    if next_revs_button is not None:
      next_revs_button = 'https://plugins.trac.wordpress.org' + next_revs_button
      try:
        ua = random.choice(UA_LIST)
        source = requests.get(next_revs_button, headers={'User-Agent':ua})
      except requests.exceptions.RequestException:
        pass
      source = BeautifulSoup(source.content, 'html.parser')

      authors = self.wp_track_author_changes(source, authors)

    return authors

# DRUPAL MARKETPLACE
  def drupal_mkt_get_plugin_info(self, info, soup):
    info.update({'Plugin Name':soup.find('h1', {'id':'page-subtitle'}).text})
    byline = soup.find('div', {'class':'submitted'})
    c_url = soup.find('div', {'id':'project-committers'})
    date = byline.find_all('time')[1]

    info.update({'Author':self.drupal_mkt_get_authors(c_url.a['href'])})
    info.update({'Date Modified':date.text})

    project_info = soup.find('ul', {'class':'project-info'})
    download_count = project_info.find('small')
    info.update({'Downloads':download_count.text})
    
    try:
      version_info = soup.find('div', {'class':'release recommended-Yes security-covered'})
      latest = version_info.a.text
      info.update({'Latest Version':latest})
    except:
      try:
        warning = soup.find('div', {'class':'note-warning'}).text
        info.update({'Latest Version':warning})
      except:
        pass

    try:
      rating_info = soup.find('a', {'class':'log-in-to-star'})
      info.update({'Ratings':rating_info.text})
    except:
      info.update({'Ratings':'not found'})
    info.update({'Sales':'0.00 USD'})

  def drupal_mkt_get_authors(self, c_url):
    c_url = 'https://www.drupal.org' + c_url
    try:
      source = requests.get(c_url)
    except requests.exceptions.RequestException:
      return 'not found'
    source = BeautifulSoup(source.content, 'html.parser')
    

    c_table = source.find('table', {'class':'sticky-enabled'})
    commits = c_table.find_all('tr')

    authors = {}
    for commit in commits:
      c_data = commit.find_all('td')
      try:
        profile       = c_data[0].a['href']
        c_auth        = c_data[0].find('a').text
        last_commit   = c_data[1].text
        first_commit  = c_data[2].text
        total_commits = c_data[3].text
      except:
        continue
      
      if c_auth not in authors:
        authors[c_auth] = {
                            'Profile':self.drupal_mkt_scrape_profile(profile),
                            'Commit Info':{
                                            'First' : first_commit,
                                            'Last'  : last_commit,
                                            'Total' : total_commits
                                          }
                          }
    
    return authors

  def drupal_mkt_scrape_profile(self, author):
    profile_url = DRUPAL_PROFILE_URL.format(author)

    profile = {}
    
    try:
      source = requests.get(profile_url)
    except requests.exceptions.RequestException:
      pass
    source = BeautifulSoup(source.content, 'html.parser')

    profile['Profile URL'] = profile_url

    try:
      name = source.find('h1', {'id':'page-title', 'class':'title'}).text
    except:
      name = 'not found'

    try:
      location = source.find('div', {'class':'field field-name-field-country field-type-list-text field-label-hidden'})
      location = location.text.strip()
    except:
      try:
        location = source.find('div', {'class':'field field-name-field-user-location field-type-text field-label-hidden'})
        location = location.text.strip()
      except:
        location = 'not found'

    try:
      websites = source.find('div', {'class':'field field-name-field-websites field-type-link-field field-label-hidden'})
      websites = [w['href'] for w in websites.find_all('a')]
      if len(websites) == 0:
        website = 'not found'
      elif len(websites) == 1:
        website = websites[0]
      elif len(websites) > 1:
        website = websites
    except:
      website = 'not found'

    try:
      language_list = source.find('div', {'class':'field field-name-field-languages field-type-list-text field-label-inline clearfix'})
      language_list = language_list.find('div', {'class':'field-items'})
      languages = [l.text.strip() for l in language_list.find_all('div')]
    except:
      languages = 'not found'

    try:
      main_profile = source.find('div', {'class':'main'})
      history = main_profile.find('dl').p.text
    except:
      history = 'not found'

    profile['Name'] = name
    profile['Location'] = location
    profile['Webiste'] = website
    profile['Languages'] = languages
    profile['History'] = history

    return json.dumps(profile)

# JOOMLA MARKETPLACE
  def joomla_mkt_get_plugin_info(self, info, source):
    meta = source.find('div', {'id':'extension-meta'})

    info.update({'Plugin Name':meta.h2.text})
    info.update({'Latest Version':meta.dl.find_all('dd')[0].text})
    info.update({'Date Modified':meta.dl.find_all('dd')[2].text})
    author = OrderedDict()
    author.update({'Name':meta.dl.find_all('dd')[1].text.strip('\n')})
    
    download_link = source.find('a', {'title':'download'}).attrs['href']
    author.update({'URL':os.path.dirname(download_link)})
    info.update({'Author':author})
    self.get_author_language(info)

    if 'Paid' in meta.dl.find_all('dd')[5].text:
      # print('Paid Plugin --> Searching for pricing information')
      try:
        self.joomla_mkt_find_price(info, download_link)
      except:
        # print('Sorry, can\'t find prices')
        pass  
    elif 'Free' in meta.dl.find_all('dd')[5].text:
      info.update({'Sales':'FREE'})
    
    self.joomla_mkt_get_ratings(info, source)

  def joomla_mkt_find_price(self, info, download_url):
    prices = OrderedDict()
    dSource = requests.get(download_url)
    dSoup = BeautifulSoup(dSource.content, 'html.parser')
    jstr = dSoup.find('script', {'type':'application/ld+json'}).text
    jdata = json.loads(jstr)

    for offer in jdata['itemListElement']:
      offer_type = offer['item']['name']
      price = offer['item']['offers']['price'] + ' ' + offer['item']['offers']['priceCurrency']
      prices.update({offer_type:price})
    info.update({'Sales':prices})

  def joomla_mkt_get_ratings(self, info, source):
    ratingInfo = source.find('div', {'itemprop':'aggregateRating'})
    ratingValue = ratingInfo.find('meta', {'itemprop':'ratingValue'}).attrs['content']
    ratingValue = ratingValue + ' out of 5 Stars'
    numRatings = ratingInfo.find('meta', {'itemprop':'reviewCount'}).attrs['content']
    info.update(
                 {
                    'Ratings': {
                                'Number of Ratings': numRatings, 
                                'Average Rating': ratingValue
                               } 
                 }
               )

# JEXTENSIONS MARKETPLACE
  def jext_get_plugin_info(self, info, source):
    error404 = '404 - The requested page cannot be found.'
    if error404 in source.text:
      raise Exception(error404)

    titles = source.find_all('span', {'class':'scheda_title'})
    r = None
    v = None
    for title in titles:
      if title.text == 'Version':
        info.update({'Latest Version':title.parent.find('span', {'class':'scheda_desc'}).text})
      if title.text == 'Votes:':
        v = title.parent.text.replace('Votes:','')
      if title.text == '5/5' or title.text == '4/5' or title.text == '3/5' or title.text == '2/5' or title.text == '1/5' or title.text == '0/5':
        r = title.text
      
      ratings = None
      if r and v:
        ratings = '{} ({} Votes)'.format(r, v)
      elif r and not v:
        ratings = r
      elif v and not r:
        ratings = '{} Votes'.format(v)
      info.update({'Ratings':ratings})
      
    try:
      info.update({'Sales':source.find('span', {'class':'price'}).text})
    except:
      pass
    try:
      info.update({'Plugin Name':source.find('h1', {'class':'main_article_title'}).text})
    except:
      pass

# CODE CANYON
  def codecanyon_search(self, plugin_slug):
    source = requests.get(CODECANYON_SEARCH.format(plugin_slug))
    search_soup = BeautifulSoup(source.content, 'html.parser')
    results = search_soup.find('div', {'data-test-selector':'search-results'})

    try:
      url = results.a['href']
    except:
      url = None

    if plugin_slug in url:
      return url
    
  def codecanyon_scrape_listing(self, soup, info):
    try:
      results = self.cc_get_name_and_ratings(soup)
    except:
      pass
    
    info.update({'Plugin Name':results['name']})
    info.update({'Ratings':results['ratings']})
    info.update({'Downloads':results['sales']})

    try:
      info.update({'Author':self.cc_get_author_info(soup)})
    except:
      info.update({'Author':'not found'})

    try:
      info.update({'Date Modified':self.cc_get_date_updated(soup)})
    except:
      info.update({'Date Modified':'not found'})

    try:
      info.update({'Sales':self.cc_get_sales_info(soup)})
    except:
      info.update({'Sales':'not found'})
    
    try:
      del info['Latest Version']
    except:
      pass

  def cc_get_name_and_ratings(self, soup):
    results = {}
    try: # GET NAME
      header = soup.find('div', {'class':'item-header'}, {'data-view':'itemHeader'})
      name = header.find('div', {'class':'item-header__title'}).h1.text.strip()
    except:
      # print('Could not retrieve Plugin Name')
      name = 'not found'

    try:  # GET RATINGS
      rating_info = soup.find('span', {'class':'rating-detailed__average'}).text.strip()
      ratings = rating_info[:rating_info.find('\n')]
    except:
      # print('Could not retrieve Plugin Ratings')
      ratings = 'not found'

    try:  # GET SALES INFO
      sales_count = header.find('span', {'class':'item-header__sales-count'}).text
    except:
      # print('Could not retrieve Plugin Sales')
      sales_count = 'not found'

    results.update({'name':name})
    results.update({'ratings':ratings})
    results.update({'sales':sales_count})

    return results

  def cc_get_author_info(self, soup):
    author_info = OrderedDict()
    author = soup.find('a', {'rel':'author'})
    author_info.update({'Name':author.text})

    author_profile = 'https://codecanyon.net{}'.format(author['href'])
    try:  # GET REQUEST FOR AUTHORS PROFILE
      author_source = requests.get(author_profile)
    except:
      # print('Could not retrieve author\'s profile')
      pass
    author_soup = BeautifulSoup(author_source.content, 'html.parser')
    
    try:  # RETRIEVE BASIC INFO
      location_and_date = author_soup.find('div', {'class':'user-info-header__user-details'})
      location_and_date = location_and_date.p.text.strip()
      author_info.update({'Info':location_and_date})
    except:
      # print('Could not retieve author\'s header info')
      pass
    
    try:  # RETRIEVE AUTHOR RATINGS
      rating_info = author_soup.find('div', {'class':'rating-detailed'})
      rating_info = rating_info.find_all('meta')
      ratings = '{}/5, {} ratings'.format(rating_info[0]['content'], rating_info[1]['content'])
      author_info.update({'Ratings':ratings})
    except:
      # print('Could not retieve author\'s rating info')
      pass

    try:  # RETRIEVE SOCIAL NETWORK
      social_net = author_soup.find('div', {'class':'social-networks'})
      networks = social_net.find_all('a')
      net = {}
      for n in networks:
        net.update({n['title']:n['href']})
      
      author_info.update({'Social Network':net})
    except:
      # print('Could not retieve author\'s social networks')
      pass

    return author_info

  def cc_get_date_updated(self, soup):
    date = soup.find('time', {'class':'updated'})
    return date.text.strip()

  def cc_get_sales_info(self, soup):
    sales = {}

    # GET LICENSE OPTIONS
    licenses = []
    for d in soup.find('div', {'data-view':'itemVariantSelector'}).find_all('div'):
      if 'purchase-form__license' in d['class']:
        licenses.append(d)
    
    for l in licenses:
      license_type = l.price['data-license']
      license_price = l.price['data-price-prepaid']
      sales.update({license_type:license_price})

    return sales

# EASY DIGTAL DOWNLOADS
  def edd_scrape_listing(self, soup, info):
    self.edd_get_name(info, soup)
    self.edd_get_version(info, soup)
    self.edd_get_pricing(info, soup)

    info.pop('Author', None)
    info.pop('Downloads', None)
    info.pop('Ratings', None)

  def edd_get_name(self, info, soup):
    name = soup.find('head').find('title').text
    info.update({'Plugin Name':name})

  def edd_get_version(self, info, soup):
    id = soup.find('input', {'name':'download_id'})['value']
    changelog = soup.find('div', {'id':'show-changelog-{}'.format(id)})
    latest = changelog.strong.text.split(',')

    info.update({'Latest Version':latest[0]})
    info.update({'Date Modified':'{}, {}'.format(latest[1], latest[2])})

  def edd_get_pricing(self, info, soup):
    options = soup.find('div', {'class':'edd_price_options edd_single_mode'})
    opts = options.find_all('label')

    prices = OrderedDict()
    for option in opts:
      name = option.find('span', {'class':'edd_price_option_name'}).text
      price = option.find('span', {'class':'edd_price_option_price'}).text
      prices.update({name:price})
    info.update({'Sales':prices})

# WPMU-DEV
  def wpmudev_get_plugin_info(self, info, soup):
    title = soup.find('div', {'class':'wpmud-hg-hero__title'}).h1
    info.update({'Plugin Name':title.text})

    i = soup.find_all('div', {'class':'wpmud-hg-project-info__item'})
    downloads = i[0].strong.text
    installs = i[1].strong.text
    info.update({'Downloads':'{} ({} Active Installs)'.format(downloads, installs)})
    
    version = i[3].strong.text
    info.update({'Latest Version':version})

    info.update({'Sales':'WPMU DEV Subscription - $49/month'})
    
    info.pop('Author', None)
    info.pop('Date Modified', None)
    info.pop('Ratings', None)

# GITHUB
  def github_search(self, slug):
    git_query = GITSEARCH.format(slug)
    source = requests.get(git_query)
    soup = BeautifulSoup(source.content, 'html.parser')
    repo_list = soup.find('ul', {'class':'repo-list'})
    if (repo_list is None) and ('-master' in slug):
      git_query = GITSEARCH.format(slug[:-7]) # Remove branch label and try again
      source = requests.get(git_query)
      soup = BeautifulSoup(source.content, 'html.parser')
      repo_list = soup.find('ul', {'class':'repo-list'})
      slug = slug[:-7]
    repos = [r['href'] for r in repo_list.find_all('a', {'class':'v-align-middle'})]

    plugin_repo = None
    for repo in repos:
      if os.path.basename(os.path.normpath(repo)).lower() == slug.lower():
        plugin_repo = repo
        break
    return plugin_repo

  def scrape_git_repo(self, repo, info):
    URL = GITHUB.format(repo)
    source = requests.get(URL)
    soup = BeautifulSoup(source.content, 'html.parser')
    info.update({'Plugin Name':os.path.basename(os.path.normpath(repo))})
    info.update({'Author':self.git_get_author_info(URL, soup)})
    info.update({'Latest Version':self.git_get_version_info(URL)})
    info.update({'Date Modified':self.git_get_date(soup)})
    info.update({'Ratings':self.git_get_star_info(soup)})
    info.update({'Sales':'0.00 USD'})

    info.pop('Downloads', None)

  def git_get_author_info(self, repo, soup):
    owner = self.git_get_owner_info(soup)
    URL = repo + '/commits/master'
    source = requests.get(URL)
    try:
      soup = BeautifulSoup(source.content, 'html.parser')
    except:
      return 'not found'
    
    devs = []
    contributors = [c.text for c in soup.find_all('a', {'class':'commit-author'})]
    # ^ Only returns first page :/
    for dev in contributors:
      if dev not in devs:
        devs.append(dev)

    authors = []
    for dev in devs:
      try:
        authors.append({dev:git_scrape_profile(dev)})
      except:
        authors.append({dev:'profile not found'})

    author = OrderedDict()
    author.update({'Owner':owner})
    author.update({'Contributors':authors})
    return author

  def git_get_owner_info(self, soup):
    details = OrderedDict()
    owner = soup.find('span', {'class':'author'})
    try:
      owner_url = GITHUB.format(owner.a['href'])
      user_type = owner.a['data-hovercard-type']
      source = requests.get(owner_url)
      profile = BeautifulSoup(source.content, 'html.parser')
    except:
      return 'not found'
    
    if user_type == 'organization':
      card = profile.find('div', {'class':'TableObject-item TableObject-item--primary '})
      name = card.h1.text.strip()

      try:
        location = profile.find('span', {'itemprop':'location'}).text.strip()
      except:
        location = 'not found'
      
      try:
        site = profile.find('a', {'itemprop':'url'}).text.strip()
      except:
        site = 'not found'

      try:
        email = profile.find('a', {'itemprop':'email'}).text.strip()
      except:
        email = 'not found'

      details.update({'Name':name})
      details.update({'Location':location})
      details.update({'URL':site})
      details.update({'Email':email})

    elif user_type == 'user':
      details = self.git_scrape_profile(owner.a.text.strip())

    return details

  def git_get_version_info(self, repo):
    URL = repo + '/releases'
    source = requests.get(URL)
    try:
      soup = BeautifulSoup(source.content, 'html.parser')
      latest = soup.find('div', {'class':'release-entry'})
      return latest.a.text.strip()
    except:
      return 'not found'

  def git_get_date(self, soup):
    line = soup.find('span', {'itemprop':'dateModified'})
    try:
      date = line.find('relative-time').text
    except:
      date = 'not found'
    
    return date

  def git_get_star_info(self, soup):
    stars = soup.find('ul', {'class':'pagehead-actions'}).find_all('li')[1].find_all('a')[1]['aria-label']
    if stars:
      return stars
    else:
      return 'not found'

  def git_scrape_profile(self, author):
    author_profile = OrderedDict()
    try:
      source = requests.get(GITHUB.format('/'+author))
      soup = BeautifulSoup(source.content, 'html.parser')
    except:
      return 'profile not found'

    profile = soup.find('div', {'class':'js-profile-editable-area'})
    try:
      name = soup.find('span', {'itemprop':'name'}).text
    except:
      name = 'not found'
    
    try:
      org = profile.find('li', {'itemprop':'worksFor'}).text.strip()
    except:
      org = 'not found'
    
    try:
      loc = profile.find('li', {'itemprop':'homeLocation'}).text.strip()
    except:
      loc = 'not found'
    
    try:
      url = profile.find('li', {'itemprop':'url'}).text.strip()
    except:
      url = 'not found'
    
    author_profile.update({'Name':name})
    author_profile.update({'Location':loc})
    author_profile.update({'Organization':org})
    author_profile.update({'URL':url})

    return author_profile

# THEMEFOREST
  def themeforest_search(self, plugin_slug):
    source = requests.get(THEMEFOREST_SEARCH.format(plugin_slug))
    search_soup = BeautifulSoup(source.content, 'html.parser')
    results = search_soup.find('div', {'data-test-selector':'search-results'})

    try:
      url = results.a['href']
    except:
      url = None

    if plugin_slug in url:
      return url

  def themeforest_scrape_listing(self, source, info):
    try:
      results = self.cc_get_name_and_ratings(source)
    except:
      pass
    
    info.update({'Plugin Name':results['name']})
    info.update({'Ratings':results['ratings']})
    info.update({'Downloads':results['sales']})

    try:
      info.update({'Author':self.cc_get_author_info(source)})
    except:
      info.update({'Author':'not found'})

    try:
      info.update({'Date Modified':self.cc_get_date_updated(source)})
    except:
      info.update({'Date Modified':'not found'})

    try:
      info.update({'Sales':self.cc_get_sales_info(source)})
    except:
      info.update({'Sales':'not found'})
    
    try:
      del info['Latest Version']
    except:
      pass

# PROCESS RESULTS
  def dump_telemetry(self, mkt, info, database):
    print()
    if self.jdump:
      if not os.path.exists('telemetry_reports/{}/'.format(mkt)):
        os.makedirs('telemetry_reports/{}/'.format(mkt))
      with open('telemetry_reports/{}/{}.json'.format(mkt, self.plugin_slug), 'w') as outfile:
        json.dump(info, outfile)
      print('Telemetry Report written to telemetry_reports/{}/{}.json'.format(mkt, self.plugin_slug))

    # switch(mkt) --> CONSTRUCT ENTRY
    if mkt is 'wp_mkt':
      n = info['Plugin Name']
      a = json.dumps(info['Author'])
      v = info['Latest Version']
      m = info['Date Modified']
      d = info['Downloads']
      r = info['Ratings']
      p = info['Sales']

      entry = '(\'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\')' .format(n, a, v, m, d, r, p)

      # CONSTRUCT SQL COMMANDS
      select_cmd = 'SELECT * FROM {} WHERE name=\'{}\''.format(mkt, n)
      delete_cmd = 'DELETE FROM {} WHERE name=\'{}\''.format(mkt, n)
      insert_cmd = 'INSERT INTO {} VALUES (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\')'.format(mkt, n, a, v, m, d, r, p)

    elif mkt is 'joomla_mkt':
      n = info['Plugin Name']
      a = json.dumps(info['Author'])
      v = info['Latest Version']
      m = info['Date Modified']
      r = json.dumps(info['Ratings'])
      p = json.dumps(info['Sales'])

      entry = '(\'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\')' .format(n, a, v, m, r, p)

      # CONSTRUCT SQL COMMANDS
      select_cmd = 'SELECT * FROM {} WHERE name=\'{}\''.format(mkt, n)
      delete_cmd = 'DELETE FROM {} WHERE name=\'{}\''.format(mkt, n)
      insert_cmd = 'INSERT INTO {} VALUES (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\')'.format(mkt, n, a, v, m, r, p)

    elif mkt is 'drupal_mkt':
      n = info['Plugin Name']
      a = json.dumps(info['Author'])
      v = info['Latest Version']
      m = info['Date Modified']
      d = info['Downloads']
      r = info['Ratings']
      p = info['Sales']

      entry = '(\'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\')' .format(n, a, v, m, d, r, p)

      # CONSTRUCT SQL COMMANDS
      select_cmd = 'SELECT * FROM {} WHERE name=\'{}\''.format(mkt, n)
      delete_cmd = 'DELETE FROM {} WHERE name=\'{}\''.format(mkt, n)
      insert_cmd = 'INSERT INTO {} VALUES (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\')'.format(mkt, n, a, v, m, d, r, p)

    elif mkt is 'jext':
      n = info['Plugin Name']
      v = info['Latest Version']
      r = info['Ratings']
      p = info['Sales']

      entry = '(\'{}\', \'{}\', \'{}\', \'{}\')' .format(n, v, r, p)

      # CONSTRUCT SQL COMMANDS
      select_cmd = 'SELECT * FROM {} WHERE name=\'{}\''.format(mkt, n)
      delete_cmd = 'DELETE FROM {} WHERE name=\'{}\''.format(mkt, n)
      insert_cmd = 'INSERT INTO {} VALUES (\'{}\',\'{}\',\'{}\',\'{}\')'.format(mkt, n, v, r, p)

    elif mkt is 'codecanyon':
      n = info['Plugin Name']
      a = json.dumps(info['Author'])
      m = info['Date Modified']
      d = info['Downloads']
      r = info['Ratings']
      p = json.dumps(info['Sales'])

      entry = '(\'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\')' .format(n, a, m, d, r, p)

      # CONSTRUCT SQL COMMANDS
      select_cmd = 'SELECT * FROM {} WHERE name=\'{}\''.format(mkt, n)
      delete_cmd = 'DELETE FROM {} WHERE name=\'{}\''.format(mkt, n)
      insert_cmd = 'INSERT INTO {} VALUES (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\')'.format(mkt, n, a, m, d, r, p)

    elif mkt is 'edd':
      n = info['Plugin Name']
      v = info['Latest Version']
      m = info['Date Modified']
      p = json.dumps(info['Sales'])
      
      entry = '(\'{}\', \'{}\', \'{}\', \'{}\')' .format(n, v, m, p)

      # CONSTRUCT SQL COMMANDS
      select_cmd = 'SELECT * FROM {} WHERE name=\'{}\''.format(mkt, n)
      delete_cmd = 'DELETE FROM {} WHERE name=\'{}\''.format(mkt, n)
      insert_cmd = 'INSERT INTO {} VALUES (\'{}\',\'{}\',\'{}\',\'{}\')'.format(mkt, n, v, m, p)

    elif mkt is 'wpmudev':
      n = info['Plugin Name']
      d = info['Downloads']
      v = info['Latest Version']
      p = json.dumps(info['Sales'])
      
      entry = '(\'{}\', \'{}\', \'{}\', \'{}\')' .format(n, d, v, p)

      # CONSTRUCT SQL COMMANDS
      select_cmd = 'SELECT * FROM {} WHERE name=\'{}\''.format(mkt, n)
      delete_cmd = 'DELETE FROM {} WHERE name=\'{}\''.format(mkt, n)
      insert_cmd = 'INSERT INTO {} VALUES (\'{}\',\'{}\',\'{}\',\'{}\')'.format(mkt, n, d, v, p)

    elif mkt is 'github':
      n = info['Plugin Name']
      a = json.dumps(info['Author'])
      v = info['Latest Version']
      m = json.dumps(info['Date Modified'])
      r = info['Ratings']
      p = info['Sales']

      entry = '(\'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\')' .format(n, a, v, m, r, p)

      # CONSTRUCT SQL COMMANDS
      select_cmd = 'SELECT * FROM {} WHERE name=\'{}\''.format(mkt, n)
      delete_cmd = 'DELETE FROM {} WHERE name=\'{}\''.format(mkt, n)
      insert_cmd = 'INSERT INTO {} VALUES (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\')'.format(mkt, n, a, v, m, r, p)

    elif mkt is 'themeforest':
      n = info['Plugin Name']
      a = json.dumps(info['Author'])
      m = info['Date Modified']
      d = info['Downloads']
      r = info['Ratings']
      p = json.dumps(info['Sales'])

      entry = '(\'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\')' .format(n, a, m, d, r, p)

      # CONSTRUCT SQL COMMANDS
      select_cmd = 'SELECT * FROM {} WHERE name=\'{}\''.format(mkt, n)
      delete_cmd = 'DELETE FROM {} WHERE name=\'{}\''.format(mkt, n)
      insert_cmd = 'INSERT INTO {} VALUES (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\')'.format(mkt, n, a, m, d, r, p)

    else:
      print("no mkt specified")

    try:  # CONNECT TO DB
        db = sqlite3.connect(database)
    except Exception as e:
      print('There was a problem connecting to the database: {}'.format(database))
      print(e)
    c = db.cursor()

    c.execute(select_cmd)
    current_entry = c.fetchone()

    if not (current_entry == entry): # UPDATE ENTRY
      try:
        print('Updating table {} in {} with Telemetry Data'.format(mkt, database), end='... ')
        c.execute(delete_cmd)
        c.execute(insert_cmd)
        print('Done!')
      except Exception as e:
        print('Something went wrong:')
        print(e)
        print()

    else: # NO UPDATING NEEDED
      print('No Updating needed')

    # SAVE AND CLOSE
    db.commit()
    db.close()
      
  def run(self, plugin_slug, verbose=None, jdump=None):
    self.plugin_slug = plugin_slug
    self.initTelemetryDB(self.database_name)
    tData = {}

    self.jdump = jdump
    
    print('Telemetry Analysis for {}:'.format(self.plugin_slug))
    print('  +----------------------------------------+')

    info = self.initTelemetryData()
    print('  |  Official WordPress Marketplace  |  ', end='')
    try:  # Official WordPress Marketplace
      source = self.get_soup('wp_mkt', self.plugin_slug)
      self.wp_mkt_get_plugin_info(info, source)
      print('X  |')
      tData.update({'wp_mkt':info})
      print('  +----------------------------------------+')
    except AttributeError as e:
      print('   |')
      print('  +----------------------------------------+')
      if verbose:
        print('\n' + str(e) + '\n')
        print('  +----------------------------------------+')
    stdout.flush()

    info = self.initTelemetryData()
    print('  |  Official Joomla Marketplace     |  ', end='')
    try:  # Official Joomla Marketplace
      source = self.get_soup('joomla_mkt', self.plugin_slug)
      self.joomla_mkt_get_plugin_info(info, source)
      print('X  |')
      tData.update({'joomla_mkt':info})
      print('  +----------------------------------------+')
    except AttributeError as e:
      print('   |')
      print('  +----------------------------------------+')
      if verbose:
        print('\n' + str(e) + '\n')
        print('  +----------------------------------------+')
    stdout.flush()

    info = self.initTelemetryData()
    print('  |  Official Drupal Marketplace     |  ', end='')
    try: # Official Drupal Marketplace
      source = self.get_soup('drupal_mkt', self.plugin_slug)
      self.drupal_mkt_get_plugin_info(info, source)
      print('X  |')
      tData.update({'drupal_mkt':info})
      print('  +----------------------------------------+')
    except AttributeError as e:
      print('   |')
      print('  +----------------------------------------+')
      if verbose:
        print('\n' + str(e) + '\n')
        print('  +----------------------------------------+') 
    stdout.flush()

    info = self.initTelemetryData()
    print('  |  StoreJExtensions Marketplace    |  ', end='')
    try:  # StoreJExtenstions
      source = self.get_soup('jext', self.plugin_slug)
      self.jext_get_plugin_info(info, source)
      print('X  |')
      tData.update({'jext':info})
      print('  +----------------------------------------+')
    except (Exception, AttributeError) as e:
      print('   |')
      print('  +----------------------------------------+')
      if verbose:
        print('\n' + str(e) + '\n')
        print('  +----------------------------------------+')
    stdout.flush()
    
    info = self.initTelemetryData()
    print('  |  CodeCanyon Marketplace          |  ', end='')
    try:  # CodeCanyon Marketplace
      source = self.get_soup('codecanyon', self.plugin_slug)
      self.codecanyon_scrape_listing(source, info)
      print('X  |')
      tData.update({'codecanyon':info})
      print('  +----------------------------------------+')
    except (Exception, AttributeError) as e:
      print('   |')
      print('  +----------------------------------------+')
      if verbose:
        print('\n' + str(e) + '\n')
        print('  +----------------------------------------+')
    stdout.flush()

    info = self.initTelemetryData()
    print('  |  Easy Digital Downloads          |  ', end='')
    try:  # Easy Digital Downloads
      source = self.get_soup('edd', self.plugin_slug)
      self.edd_scrape_listing(source, info)
      print('X  |')
      tData.update({'edd':info})
      print('  +----------------------------------------+')
    except (Exception, AttributeError) as e:
      print('   |')
      print('  +----------------------------------------+')
      if verbose:
        print('\n' + str(e) + '\n')
        print('  +----------------------------------------+')
    stdout.flush()

    info = self.initTelemetryData()
    print('  |  WPMU-DEV                        |  ', end='')
    try:  # WPMU-DEV
      source = self.get_soup('wpmudev', self.plugin_slug)
      self.wpmudev_get_plugin_info(info, source)
      print('X  |')
      tData.update({'wpmudev':info})
      print('  +----------------------------------------+')
    except (Exception, AttributeError) as e:
      print('   |')
      print('  +----------------------------------------+')
      if verbose:
        print('\n' + str(e) + '\n')
        print('  +----------------------------------------+')
    stdout.flush()

    info = self.initTelemetryData()
    print('  |  GitHub                          |  ', end='')
    try:  # GITHUB
      plugin_repo = self.github_search(self.plugin_slug)
      self.scrape_git_repo(plugin_repo, info)
      print('X  |')
      tData.update({'github':info})
      print('  +----------------------------------------+')
    except (Exception, AttributeError) as e:
      print('   |')
      print('  +----------------------------------------+')
      if verbose:
        print('\n' + str(e) + '\n')
        print('  +----------------------------------------+')
    stdout.flush()

    info = self.initTelemetryData()
    print('  |  ThemeForest Marketplace         |  ', end='')
    try:  # ThemeForest Marketplace
      source = self.get_soup('themeforest', self.plugin_slug)
      self.themeforest_scrape_listing(source, info)
      print('X  |')
      tData.update({'themeforest':info})
      print('  +----------------------------------------+')
    except (Exception, AttributeError) as e:
      print('   |')
      print('  +----------------------------------------+')
      if verbose:
        print('\n' + str(e) + '\n')
        print('  +----------------------------------------+')
    stdout.flush()

    if tData.keys(): # DUMP TELEMETRY DATA
      for mkt in tData.keys():
        try:
          self.dump_telemetry(mkt, tData[mkt], self.database_name)
        except Exception as e:
          print('There was a problem dumping the telemetry data to {}:'.format(self.database_name))
          print(e)
    else:
        print('\n{} was not found in any of the currently supported marketplaces!\n'.format(self.plugin_slug))

    return tData

####################################################################################
if __name__=='__main__':
  from sys import argv
  TS = TelemetryScanner()
  TS.run(
          argv[1],
          # verbose=True,
          jdump=True
        )

# OLD MAIN:
  # parser = argparse.ArgumentParser(formatter_class = argparse.RawTextHelpFormatter,
	# 																description = "Perform Telemetry Analysis on specified Plugin")
  # parser.add_argument('-v', '--verbose', action='store_true',
  #                     help='Print more verbose output, error messages, etc.')
  # parser.add_argument('-j', '--json', action='store_true',
  #                     help='Dump telemetry data to a json file in telemetry_reports/')
  # parser.add_argument('PLUGIN_SLUG', type=str, help='Slug of the Plugin on which to perform Telemetry Analysis')
  # args = parser.parse_args()

  # verbose = args.verbose
  # jdump = args.json
  # plugin_slug = args.PLUGIN_SLUG

  # plugin_found = False
  # initTelemetryDB(database_name)
  # tData = {}
  
  # print('Telemetry Analysis for {}:'.format(plugin_slug))
  # print('  +----------------------------------------+')

  # info = initTelemetryData()
  # print('  |  Official WordPress Marketplace  |  ', end='')
  # try:  # Official WordPress Marketplace
  #   source = get_soup('wp_mkt', plugin_slug)
  #   wp_mkt_get_plugin_info(info, source)
  #   print('X  |')
  #   tData.update({'wp_mkt':info})
  #   print('  +----------------------------------------+')
  #   plugin_found = True
  # except AttributeError as e:
  #   print('   |')
  #   print('  +----------------------------------------+')
  #   if verbose:
  #     print('\n' + str(e) + '\n')
  #     print('  +----------------------------------------+')
  # stdout.flush()

  # info = initTelemetryData()
  # print('  |  Official Joomla Marketplace     |  ', end='')
  # try:  # Official Joomla Marketplace
  #   source = get_soup('joomla_mkt', plugin_slug)
  #   joomla_mkt_get_plugin_info(info, source)
  #   print('X  |')
  #   tData.update({'joomla_mkt':info})
  #   print('  +----------------------------------------+')
  #   plugin_found = True
  # except AttributeError as e:
  #   print('   |')
  #   print('  +----------------------------------------+')
  #   if verbose:
  #     print('\n' + str(e) + '\n')
  #     print('  +----------------------------------------+')
  # stdout.flush()

  # info = initTelemetryData()
  # print('  |  Official Drupal Marketplace     |  ', end='')
  # try: # Official Drupal Marketplace
  #   source = get_soup('drupal_mkt', plugin_slug)
  #   drupal_mkt_get_plugin_info(info, source)
  #   print('X  |')
  #   tData.update({'drupal_mkt':info})
  #   print('  +----------------------------------------+')
  #   plugin_found = True
  # except AttributeError as e:
  #   print('   |')
  #   print('  +----------------------------------------+')
  #   if verbose:
  #     print('\n' + str(e) + '\n')
  #     print('  +----------------------------------------+') 
  # stdout.flush()

  # info = initTelemetryData()
  # print('  |  StoreJExtensions Marketplace    |  ', end='')
  # try:  # StoreJExtenstions
  #   source = get_soup('jext', plugin_slug)
  #   jext_get_plugin_info(info, source)
  #   print('X  |')
  #   tData.update({'jext':info})
  #   print('  +----------------------------------------+')
  #   plugin_found = True
  # except (Exception, AttributeError) as e:
  #   print('   |')
  #   print('  +----------------------------------------+')
  #   if verbose:
  #     print('\n' + str(e) + '\n')
  #     print('  +----------------------------------------+')
  # stdout.flush()
  
  # info = initTelemetryData()
  # print('  |  CodeCanyon Marketplace          |  ', end='')
  # try:  # CodeCanyon Marketplace
  #   source = get_soup('codecanyon', plugin_slug)
  #   codecanyon_scrape_listing(source, info)
  #   print('X  |')
  #   tData.update({'codecanyon':info})
  #   print('  +----------------------------------------+')
  #   plugin_found = True
  # except (Exception, AttributeError) as e:
  #   print('   |')
  #   print('  +----------------------------------------+')
  #   if verbose:
  #     print('\n' + str(e) + '\n')
  #     print('  +----------------------------------------+')
  # stdout.flush()

  # info = initTelemetryData()
  # print('  |  Easy Digital Downloads          |  ', end='')
  # try:  # Easy Digital Downloads
  #   source = get_soup('edd', plugin_slug)
  #   edd_scrape_listing(source, info)
  #   print('X  |')
  #   tData.update({'edd':info})
  #   print('  +----------------------------------------+')
  #   plugin_found = True
  # except (Exception, AttributeError) as e:
  #   print('   |')
  #   print('  +----------------------------------------+')
  #   if verbose:
  #     print('\n' + str(e) + '\n')
  #     print('  +----------------------------------------+')
  # stdout.flush()

  # info = initTelemetryData()
  # print('  |  WPMU-DEV                        |  ', end='')
  # try:  # GITHUB
  #   source = get_soup('wpmudev', plugin_slug)
  #   wpmudev_get_plugin_info(info, source)
  #   print('X  |')
  #   tData.update({'wpmudev':info})
  #   print('  +----------------------------------------+')
  # except (Exception, AttributeError) as e:
  #   print('   |')
  #   print('  +----------------------------------------+')
  #   if verbose:
  #     print('\n' + str(e) + '\n')
  #     print('  +----------------------------------------+')
  # stdout.flush()

  # info = initTelemetryData()
  # print('  |  GitHub                          |  ', end='')
  # try:  # GITHUB
  #   plugin_repo = github_search(plugin_slug)
  #   scrape_git_repo(plugin_repo, info)
  #   print('X  |')
  #   tData.update({'github':info})
  #   print('  +----------------------------------------+')
  # except (Exception, AttributeError) as e:
  #   print('   |')
  #   print('  +----------------------------------------+')
  #   if verbose:
  #     print('\n' + str(e) + '\n')
  #     print('  +----------------------------------------+')
  # stdout.flush()

  # if tData.keys(): # DUMP TELEMETRY DATA
  #   for mkt in tData.keys():
  #     try:
  #       dump_telemetry(mkt, tData[mkt], database_name)
  #     except Exception as e:
  #       print('There was a problem dumping the telemetry data to {}:'.format(database_name))
  #       print(e)
  # else:
  #     print('\n{} was not found in any of the currently supported marketplaces!\n'.format(plugin_slug))