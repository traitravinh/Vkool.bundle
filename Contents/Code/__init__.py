# __author__ = 'traitravinh'
import re
from BeautifulSoup import BeautifulSoup
################################## Vkool #########################################
NAME = "Vkool"
BASE_URL = "http://m.vkool.net"
SEARH_URL = 'http://m.vkool.net/search/%s%s'
DEFAULT_ICO = 'icon-default.png'
SEARCH_ICO = 'icon-search.png'
NEXT_ICO = 'icon-next.png'
##### REGEX #####
####################################################################################################

def Start():
    ObjectContainer.title1 = NAME
    HTTP.CacheTime = CACHE_1HOUR
    # HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:22.0) Gecko/20100101 Firefox/22.0'
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16'
    HTTP.Headers['X-Requested-With'] = 'XMLHttpRequest'
####################################################################################################

@handler('/video/vkool', NAME)
def MainMenu():
    oc = ObjectContainer()
    oc.add(InputDirectoryObject(
        key=Callback(Search),
        title='SEARCH',
        thumb=R(SEARCH_ICO)
    ))
    try:
        link = HTTP.Request(BASE_URL,cacheTime=3600).content
        soup = BeautifulSoup(link)

        slists = soup('ul',{'class':'slist'})

        for s in slists:
            sli = BeautifulSoup(str(s))('li')
            for l in sli:
                lsoup = BeautifulSoup(str(l))
                llink = lsoup('a')[0]['href']
                lname = lsoup('a')[0].contents[0]
                oc.add(DirectoryObject(
                    key=Callback(Category, title=lname, catelink=llink),
                    title=lname,
                    thumb=R(DEFAULT_ICO)
                ))

    except Exception, ex:
        Log("******** Error retrieving and processing latest version information. Exception is:\n" + str(ex))

    return oc
####################################################################################################

@route('/video/vkool/search')
def Search(query=None):
    if query is not None:
        url = SEARH_URL % ((String.Quote(query, usePlus=True)), '.html')
        Log(url)
        return Category(query, url)

@route('/video/vkool/category')
def Category(title, catelink):
    oc = ObjectContainer(title2=title)
    link = HTTP.Request(catelink,cacheTime=3600).content
    soup = BeautifulSoup(link)

    content_items = soup('a',{'class':'content-items'})
    for citem in content_items:
        cisoup = BeautifulSoup(str(citem))
        cname = cisoup('h3')[0].next
        clink = cisoup('a')[0]['href']
        cimage = cisoup('img')[0]['src']
        # cinfo = cisoup('li')[3].next
        oc.add(DirectoryObject(
            key=Callback(Server, title=cname, svlink=clink, svthumb=cimage, inum=None),
            title=cname,
            thumb=cimage
        ))
    try:
        pagination = soup('div',{'class':'pagination'})
        page = BeautifulSoup(str(pagination[0]))('a')
        for p in page:
            psoup = BeautifulSoup(str(p))
            try:
                pactive=psoup('a',{'class':'active'})[0]
            except:
                ptitle = psoup('a')[0].contents[0]
                plink = psoup('a')[0]['href']
                oc.add(DirectoryObject(
                    key=Callback(Category, title=ptitle, catelink=plink),
                    title=ptitle,
                    thumb=R(NEXT_ICO)
                ))
    except:pass

    return oc

####################################################################################################
@route('/video/vkool/server')
def Server(title, svlink, svthumb, inum):
    oc = ObjectContainer(title2=title)
    link = HTTP.Request(svlink,cacheTime=3600).content
    soup = BeautifulSoup(link)
    serverlink = BeautifulSoup(str(soup('a',{'class':'click-watch button'})))('a')[0]['href']
    newlink = HTTP.Request(serverlink,cacheTime=3600).content
    nsoup = BeautifulSoup(newlink)
    if inum is None:
        server_item = nsoup('div', {'class':'server_item'})
        for i in range(0,len(server_item)):
            svtitle = BeautifulSoup(str(server_item[i]))('strong')[0].text
            svindex = i
            oc.add(DirectoryObject(
                key=Callback(Server, title=svtitle, svlink=svlink, svthumb=svthumb, inum=svindex),
                title=svtitle,
                thumb=svthumb
            ))
    else:
        server_item = nsoup('div', {'class':'server_item'})[int(inum)]
        span = BeautifulSoup(str(server_item))('span')
        for s in span:
            ssoup = BeautifulSoup(str(s))
            try:
                s['class']
                sname = '1'
                slink = ssoup('a')[0]['href']
                oc.add(createMediaObject(
                    url=slink,
                    title=sname,
                    thumb=svthumb,
                    rating_key=sname
                ))
            except KeyError:
                slink = ssoup('a')[0]['href']
                sname = ssoup('a')[0].contents[0]
                oc.add(createMediaObject(
                    url=slink,
                    title=sname,
                    thumb=svthumb,
                    rating_key=sname
                ))
    return oc

@route('/video/vkool/createMediaObject')
def createMediaObject(url, title,thumb,rating_key,include_container=False):
    container = Container.MP4
    video_codec = VideoCodec.H264
    audio_codec = AudioCodec.AAC
    audio_channels = 2
    track_object = EpisodeObject(
        key = Callback(
            createMediaObject,
            url=url,
            title=title,
            thumb=thumb,
            rating_key=rating_key,
            include_container=True
        ),
        title = title,
        thumb=thumb,
        rating_key=rating_key,
        items = [
            MediaObject(
                parts=[
                    PartObject(key=Callback(PlayVideo, url=url))
                ],
                container = container,
                video_resolution = '720',
                video_codec = video_codec,
                audio_codec = audio_codec,
                audio_channels = audio_channels,
                optimized_for_streaming = True
            )
        ]
    )

    if include_container:
        return ObjectContainer(objects=[track_object])
    else:
        return track_object

@indirect
def PlayVideo(url):
    url = videolinks(url)
    if str(url).find('youtube')!=-1:
        oc = ObjectContainer(title2='Youtube Video')
        oc.add(VideoClipObject(
            url=url,
            title='Youtube video',
            thumb=R(DEFAULT_ICO)
        ))
        return oc
    else:
        return IndirectResponse(VideoClipObject, key=url)

def videolinks(url):
    Log(url)
    link = HTTP.Request(url,cacheTime=3600).content
    soup = BeautifulSoup(link)
    if link.find('youtube.com')!=-1:
        vlink = soup('iframe')[1]['src']
    elif link.find('<div id="player">')!=-1:
        vsources = soup('source')
        vlink = BeautifulSoup(str(vsources[len(vsources)-1]))('source')[0]['src']
    return vlink

####################################################################################################
