import re
TITLE    = 'TV3 Play'
PREFIX   = '/video/tv3play'
RSS_FEED = 'http://www.tv3play.dk/rss/'
PATH     = 'http://www.tv3play.dk'
DATA_PATH = 'http://viastream.viasat.tv/PlayProduct/'
NS       = {'content':'http://purl.org/rss/1.0/modules/content/', 'wfw':'http://wellformedweb.org/CommentAPI/'}
ART      = 'fanart.png'
ICON     = 'icon.png'

###################################################################################################

def Start():
    
    Plugin.AddPrefixHandler(PREFIX, MainMenu, TITLE, ICON, ART)
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ObjectContainer.title1 = TITLE
    ObjectContainer.view_group = 'List'
    ObjectContainer.art = R(ART)

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)
    
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:12.0) Gecko/20100101 Firefox/12.0'

###################################################################################################

def MainMenu():
    
    oc = ObjectContainer(
        view_group = 'InfoList',
        objects = [
            DirectoryObject(
                key        = Callback(BrowsePrograms, title=L('Programmer')),
                title      = L('Programmer'),
                summary    = L('Alle programmer fra TV3 Play.')
            ),
            DirectoryObject(
                key        = Callback(GetRSS, title=L('Nyeste videoer'), rss='recent'),
                title      = L('Nyeste videoer'),
                summary    = L('De nyeste videoer fra TV3 Play.')
            ),
            DirectoryObject(
                key        = Callback(GetRSS, title=L('Mest sete'), rss='mostviewed'),
                title      = L('Mest sete'),
                summary    = L('De mest sete videoer fra TV3 Play.')
            ),
            DirectoryObject(
                key        = Callback(GetRSS, title=L('Mest populaere'), rss='highestrated'),
                title      = L('Mest populaere'),
                summary    = L('De mest populaere videoer fra TV3 Play.')
            ),
            DirectoryObject(
                key        = Callback(GetRSS, title=L('Nyeste klip'), rss='recent?type=clip'),
                title      = L('Nyeste klip'),
                summary    = L('De nyeste klip fra TV3 Play.')
            )
        ]
    )

    return oc

###################################################################################################

def GetRSS(title, rss):

  oc = ObjectContainer(title2 = '%s' % (title), view_group='InfoList')
  
  for video in XML.ElementFromURL(RSS_FEED + rss).xpath('//item'):
    
    id = video.xpath('./id')[0].text
    title = video.xpath('./title')[0].text
    duration = int(video.xpath('./length', namespaces=NS)[0].text) * 1000
     
    # create video object
    video = CreateVideoObj(id, title, duration)
        
    # add video to container
    oc.add(video)
    
  return oc

####################################################################################################

def BrowsePrograms(title):

    oc = ObjectContainer(title2='%s' % (title), view_group='InfoList')
    
    html = HTML.ElementFromURL(PATH + '/program', cacheTime=CACHE_1HOUR)
    
    programs = html.xpath('.//div[@id="main-content"]/div/ul/li/a')

    for num in range(len(programs)):
        
        program     = programs[num]
        p_url       = program.get('href')
        p_title     = program.text_content()
        p_thumb     = ''
        oc.add(DirectoryObject(key = Callback(BrowseSeasons, url = p_url, title = p_title),
                            title = p_title,
                            thumb = Resource.ContentsOfURLWithFallback(p_thumb,fallback=R(ICON))))

    return oc

####################################################################################################

def BrowseSeasons(url, title):
    
    oc = ObjectContainer(title2='%s' % (title), view_group='InfoList')
    
    html = HTML.ElementFromURL(PATH + url, cacheTime=CACHE_1HOUR)
    
    # get season/clip table list
    table = html.xpath('.//div[@id="main-content"]/div/div/table/tbody')
    
    # get seasons
    seasons = table[0].xpath('.//tr[contains(@class, "season-head")]')
    
    for num in range(len(seasons)):
        
        season = seasons[num]
        s_url = url
        s_title = season.xpath('.//td/a/strong')[0].text_content()
        s_summary = '%s af %s' % (season.xpath('.//td/a/strong')[0].text_content(), title)
        s_thumb = ''
        seasonid = season.get('class').split(' ')[len(season.get('class').split(' '))-1].split('-')[1]
        
        oc.add(DirectoryObject(key = Callback(BrowseVideos, url = s_url,  title = '%s - %s' % (title, s_title), season = seasonid),
                            title = s_title,
                            summary = s_summary,
                            thumb = Resource.ContentsOfURLWithFallback(s_thumb,fallback=R(ICON))))
    
    
    # get clips
    clips = table[1].xpath('.//tr[contains(@class, "season-head")]')
    
    for num in range(len(clips)):
        
        clip = clips[num]
        c_url = url
        c_title = 'Klip fra ' + clip.xpath('.//td/a/strong')[0].text_content()
        c_summary = 'Klip fra %s af %s' % (clip.xpath('.//td/a/strong')[0].text_content(), title)
        c_thumb = ''
        seasonid = clip.get('class').split(' ')[len(clip.get('class').split(' '))-1].split('-')[1]
        
        oc.add(DirectoryObject(key = Callback(BrowseVideos, url = c_url, title = '%s - %s' % (title, c_title), season = seasonid, clips = True),
                            title = c_title,
                            summary = c_summary,
                            thumb = Resource.ContentsOfURLWithFallback(c_thumb,fallback=R(ICON))))
      
    return oc

####################################################################################################

def BrowseVideos(url, title, season, clips=False):
    
    oc = ObjectContainer(title2='%s' % (title), view_group='InfoList')
    
    html = HTML.ElementFromURL(PATH + url, cacheTime=CACHE_1HOUR)
    
    # get season/clip table list
    table = html.xpath('.//div[@id="main-content"]/div/div/table/tbody')
    
    # find clips or seasons
    if clips:
        video_list = table[1]
    else:
        video_list = table[0]
        
    # get seasons
    videos = video_list.xpath('.//tr')
    
    for num in range(len(videos)):
        
        video = videos[num]
        
        # skip season head
        if "season-head" in video.get('class'): continue
        if not 'season-' + season in video.get('class'): continue
        
        # find video id
        v_id = video.xpath('.//th[@class="col1"]/a')[0].get('href').split('/')[2]
        
        # create title based on season or clip
        if clips:
            v_title = '%s' % (video.xpath('.//th[@class="col1"]/a')[0].text_content())
        else:
            v_title = '%s episode %s' % (video.xpath('.//th[@class="col1"]/a')[0].text_content(), video.xpath('.//td[@class="col2"]')[0].text_content())
        
        # fetch data
        v_duration = video.xpath('.//td[@class="col3"]')[0].text_content()
        v_duration = int(int(v_duration[0:2])*60 + int(v_duration[3:5])) * 1000
        v_rating = float(video.xpath('.//td[@class="col5"]/form/div')[0].get('class').split(' ')[1].split('-')[1]) * 2
        
        # create video object
        video = CreateVideoObj(v_id, v_title, v_duration, v_rating)
        
        # add video to container
        oc.add(video)
        
    return oc

####################################################################################################

def CreateVideoObj(id, title, duration=0, rating=0.0):

    # get video xml
    xml = GetVideoXML(id)
    
    date = Datetime.ParseDate(xml.findtext('BroadcastDate'))
    summary = xml.findtext('LongDescription')
    thumb = GetThumb(xml)
    url = GetVideo(xml)
        
    # create video object
    video = VideoClipObject(
                title = title, 
                summary = summary, 
                thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)),
                duration = duration, 
                originally_available_at = date,
                rating = rating,
                rating_key = rating,
                key = url,
                items = [
                        MediaObject(
                            parts = [
                                PartObject(
                                    key = url,
                                    duration = duration
                                )
                            ]
                        )
                ]
    )
    
    return video

####################################################################################################

def GetVideo(xml):
    
    url = ''
    
    node = xml.find('Videos/Video')
    url = node.findtext('Url')
    
    new_xml = XML.ElementFromURL(url).xpath('//GeoLock')[0]
    url = new_xml.findtext('Url')
    
    return url;

####################################################################################################

def GetThumb(xml):
    
    url = ''
    
    for node in xml.findall('Images/ImageMedia'):
        if node.findtext('Usage') == 'Boxart_small':
            url = node.findtext('Url')
            break
    
    return url;

####################################################################################################

def GetVideoXML(videoid):
     
    return XML.ElementFromURL(DATA_PATH + videoid).xpath('//Product')[0]
  
####################################################################################################