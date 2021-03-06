TITLE       = 'TV3 Play'
PREFIX      = '/video/tv3play'
PATH        = 'http://www.tv3play.dk'
PATH_RSS    = 'http://www.tv3play.dk/rss/'
PATH_INFO   = 'http://viastream.viasat.tv/PlayProduct/'
NAMESPACE   = {'content':'http://purl.org/rss/1.0/modules/content/', 'wfw':'http://wellformedweb.org/CommentAPI/'}
ART         = 'fanart.png'
ICON        = 'icon.png'

###################################################################################################

def Start():
    
    # Plugin setup
    Plugin.AddPrefixHandler(PREFIX, MainMenu, TITLE, ICON, ART)
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
    
    # Object / Directory / VideoClip setup
    ObjectContainer.title1      = TITLE
    ObjectContainer.view_group  = 'InfoList'
    ObjectContainer.art         = R(ART)
    DirectoryObject.thumb       = R(ICON)
    DirectoryObject.art         = R(ART)
    VideoClipObject.thumb       = R(ICON)
    VideoClipObject.art         = R(ART)
    
    # HTTP setup
    HTTP.CacheTime              = CACHE_1HOUR
    HTTP.Headers['User-Agent']  = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:12.0) Gecko/20100101 Firefox/12.0'

###################################################################################################

def MainMenu():
    
    # create container
    oc = ObjectContainer()
    
    # add elements to container
    oc.add(DirectoryObject(
        key        = Callback(BrowsePrograms, title=L('Programmer')),
        title      = L('Programmer'),
        summary    = L('Alle programmer fra TV3 Play.')
    ))
    oc.add(DirectoryObject(
        key        = Callback(GetRSS, title=L('Nyeste videoer'), rss='recent'),
        title      = L('Nyeste videoer'),
        summary    = L('De nyeste videoer fra TV3 Play.')
    ))
    oc.add(DirectoryObject(
        key        = Callback(GetRSS, title=L('Mest sete'), rss='mostviewed'),
        title      = L('Mest sete'),
        summary    = L('De mest sete videoer fra TV3 Play.')
    ))
    oc.add(DirectoryObject(
        key        = Callback(GetRSS, title=L('Mest populaere'), rss='highestrated'),
        title      = L('Mest populaere'),
        summary    = L('De mest populaere videoer fra TV3 Play.')
    ))
    oc.add(DirectoryObject(
        key        = Callback(GetRSS, title=L('Nyeste klip'), rss='recent?type=clip'),
        title      = L('Nyeste klip'),
        summary    = L('De nyeste klip fra TV3 Play.')
    ))

    return oc

###################################################################################################

def GetRSS(title, rss):

    # create container
    oc = ObjectContainer(title2 = '%s' % (title))
  
    # run through videos from rss feed
    for video in XML.ElementFromURL(PATH_RSS + rss).xpath('//item'):
        
        # get variables
        id        = video.xpath('./id')[0].text
        name      = video.xpath('./title')[0].text
        duration  = int(video.xpath('./length', namespaces=NAMESPACE)[0].text) * 1000
         
        # create video object
        video = CreateVideoObj(id, name, duration)
            
        # add video to container
        oc.add(video)
        
    return oc

####################################################################################################

def BrowsePrograms(title):

    # create container
    oc = ObjectContainer(title2='%s' % (title))
    
    # fetch html from url
    html = HTML.ElementFromURL(PATH + '/program', cacheTime=CACHE_1HOUR)
    
    # find all programs
    programs = html.xpath('.//div[@id="main-content"]/div/ul/li/a')
    
    # run through programs
    for num in range(len(programs)):
        
        # get program from range
        program   = programs[num]
        
        # set variables
        url       = program.get('href')
        name      = program.text_content()
        thumb     = ''
    
        # add directory to container
        oc.add(DirectoryObject(key = Callback(BrowseSeasons, url = url, title = name),
                title       = name,
                art         = Resource.ContentsOfURLWithFallback(thumb,fallback=R(ART)),
                thumb       = Resource.ContentsOfURLWithFallback(thumb,fallback=R(ICON))
        ))

    return oc

####################################################################################################

def BrowseSeasons(url, title):
    
    # create container
    oc = ObjectContainer(title2='%s' % (title))
    
    # fetch html from url
    html = HTML.ElementFromURL(PATH + url, cacheTime=CACHE_1HOUR)
    
    # get season/clip table list
    table = html.xpath('.//div[@id="main-content"]/div/div/table/tbody')
    
    # get seasons
    seasons = table[0].xpath('.//tr[contains(@class, "season-head")]')

    # find video id
    id = table[0].xpath('.//tr/th[@class="col1"]/a')[0].get('href').split('/')[2]
    
    # get video xml
    xml = GetVideoXML(id)
    
    # set variables
    thumb = GetThumb(xml, 'PlayImage')
    
    # run through seasons
    for num in range(len(seasons)):
        
        # get season from range
        season = seasons[num]
        
        # set variables
        url         = url
        name        = season.xpath('.//td/a/strong')[0].text_content()
        summary     = '%s af %s' % (season.xpath('.//td/a/strong')[0].text_content(), title)
        seasonid    = season.get('class').split(' ')[len(season.get('class').split(' '))-1].split('-')[1]
        
        # add directory to container
        oc.add(DirectoryObject(key = Callback(BrowseVideos, url = url,  title = '%s - %s' % (title, name), season = seasonid),
                title       = name,
                summary     = summary,
                art         = Resource.ContentsOfURLWithFallback(thumb,fallback=R(ART)),
                thumb       = Resource.ContentsOfURLWithFallback(thumb,fallback=R(ICON))
        ))
     
    # get clips
    clips = table[1].xpath('.//tr[contains(@class, "season-head")]')
    
    # run through all clips
    for num in range(len(clips)):
        
        # get clip from range
        clip = clips[num]
        
        # set variables
        url         = url
        name        = 'Klip fra ' + clip.xpath('.//td/a/strong')[0].text_content()
        summary     = 'Klip fra %s af %s' % (clip.xpath('.//td/a/strong')[0].text_content(), title)
        seasonid    = clip.get('class').split(' ')[len(clip.get('class').split(' '))-1].split('-')[1]
        
        # add directory to container
        oc.add(DirectoryObject(key = Callback(BrowseVideos, url = url, title = '%s - %s' % (title, name), season = seasonid, clips = True),
                title       = name,
                summary     = summary,
                art         = Resource.ContentsOfURLWithFallback(thumb,fallback=R(ART)),
                thumb       = Resource.ContentsOfURLWithFallback(thumb,fallback=R(ICON))
        ))
      
    return oc

####################################################################################################

def BrowseVideos(url, title, season, clips=False):
    
    # create container
    oc = ObjectContainer(title2='%s' % (title))
    
    # fetch html from url
    html = HTML.ElementFromURL(PATH + url, cacheTime=CACHE_1HOUR)
    
    # get season/clip table list
    table = html.xpath('.//div[@id="main-content"]/div/div/table/tbody')
    
    # find videos for clips or seasons
    if clips:
        video_list = table[1]
    else:
        video_list = table[0]
        
    # get videos
    videos = video_list.xpath('.//tr')
    
    # run trough all videos
    for num in range(len(videos)):
        
        # get single video from ranges
        video = videos[num]
        
        # skip season head
        if "season-head" in video.get('class'): continue
        if not 'season-' + season in video.get('class'): continue
        
        # find video url / id
        url = video.xpath('.//th[@class="col1"]/a')[0].get('href')
        id = url.split('/')[2]
        
        # get video xml
        xml = GetVideoXML(id)
    
        # create title based on season or clip
        if clips:
            name = '%s' % (video.xpath('.//th[@class="col1"]/a')[0].text_content())
        else:
            name = '%s episode %s' % (video.xpath('.//th[@class="col1"]/a')[0].text_content(), video.xpath('.//td[@class="col2"]')[0].text_content())
        
        # set variables
        date        = Datetime.ParseDate(xml.findtext('BroadcastDate'))
        summary     = xml.findtext('LongDescription')
        art         = GetThumb(xml, 'PlayImage')
        thumb       = GetThumb(xml)    
        duration    = video.xpath('.//td[@class="col3"]')[0].text_content()
        duration    = int(int(duration[0:2])*60 + int(duration[3:5])) * 1000
        rating      = float(video.xpath('.//td[@class="col5"]/form/div')[0].get('class').split(' ')[1].split('-')[1]) * 2
    
        # create video object from URL Service
        video_obj = VideoClipObject(url = PATH + url, 
                                    title = name, 
                                    summary = summary, 
                                    rating = rating,
                                    art = Resource.ContentsOfURLWithFallback(art, fallback=R(ART)),
                                    thumb = Resource.ContentsOfURLWithFallback(thumb, fallback=R(ICON)),
                                    originally_available_at = date,
                                    duration = duration)
        
        # add video to container
        oc.add(video_obj)
        
    return oc

####################################################################################################

def GetThumb(xml, type='Boxart_small'):
    
    url = ''
    
    for node in xml.findall('Images/ImageMedia'):
        if node.findtext('Usage') == type:
            url = node.findtext('Url')
            break
    
    return url;

####################################################################################################

def GetVideoXML(id):
    
    try:
        xml = XML.ElementFromURL(PATH_INFO + id)
        return xml.xpath('//Product')[0]
    except:
        xml = XML.ElementFromURL('http://viastream.player.mtgnewmedia.se/xml/xmltoplayer.php?type=Products&category=' + id)
        return False
####################################################################################################