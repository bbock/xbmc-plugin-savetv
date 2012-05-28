# Save.TV plugin by Bernhard Bock <bernhard@bock.nu>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys,random,urllib,urllib2,re
import xbmc,xbmcaddon,xbmcgui,xbmcplugin
import cookielib,string

cookies = cookielib.LWPCookieJar()
cookiefile = xbmc.translatePath('special://profile/addon_data/plugin.video.savetv/')+'stvcookie'
httpheaders = [('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:6.0.2) Gecko/20100101 Firefox/6.0.2'),
               ('Accept-Language', 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3'),
               ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
               ('Connection', 'keep-alive')]

def index():
    url = 'http://www.save.tv/STV/M/obj/user/usShowVideoArchive.cfm'
    try:
        cookies.load(cookiefile, True, True)
    except:
        stvLogin()
    
    response = urllib2.urlopen(url)
    listofrecordings=response.read()
    response.close()

    if not re.match(r'Mein Videoarchiv', listofrecordings):
        # cookies from cookiejar got invalid, re-login
        stvLogin()
        response = urllib2.urlopen(url)
        listofrecordings=response.read()
        response.close()

    parseVideoArchivePage(listofrecordings)

    # pagination
    match = re.compile(r'usShowVideoArchive\.cfm\?iPageNumber=(\d+)\&bLoadLast=1">\d+<\/a>').findall(listofrecordings)
    for page in match:
        print "found page"+page+"!!\n"
        response = urllib2.urlopen(url + "?iPageNumber=" + page)
        listofrecordings=response.read()
        response.close()
        parseVideoArchivePage(listofrecordings)

def parseVideoArchivePage(stvHtmlPage):
    # Get rid of whitespace and linebreaks to make recording titles look nice
    stvHtmlPage = re.sub(r'\s+', ' ', stvHtmlPage)

    # extract titles, links and add them to xbmc listing
    match=re.compile(r'a href="([^"]*)" class="(normal|child)">(.*?)<\/td>').findall(stvHtmlPage)
    for detailslinkurl,unused,name in match:
        recordingtitle = string.replace(name, '</a>', '')
        telecastid = re.findall(r'TelecastID=(\d+)', detailslinkurl).pop()
        addItemForTelecastId(recordingtitle,telecastid,'')

            
def downloadVideoFile(telecastid, name):
    dlurl = getLinkForTelecastId(telecastid)
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png")
    liz.setInfo( type="Video", infoLabels={ "Title": name } )

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=dlurl,listitem=liz)

def getLinkForTelecastId(telecastid):
    ajaxlink = 'http://www.save.tv/STV/M/obj/cRecordOrder/croGetDownloadUrl.cfm?null.GetDownloadUrl'
    ajaxparameters = {
        "ajax" : "true",
        "clientAuthenticationKey" : "",
        "callCount" : "1",
        "c0-scriptName" : "null",
        "c0-methodName" : "GetDownloadUrl",
        "c0-id" : "",
        "c0-param0" : "number:"+str(telecastid),
        "c0-param1" : "number:0", # high resolution, set to 1 for mobile
        "c0-param2" : "boolean:true", # adfree or not
        "xml" : "true"
        }
    data = urllib.urlencode(ajaxparameters)

    cookies.load(cookiefile, True, True)
    
    req = urllib2.Request(ajaxlink, data)
    response = urllib2.urlopen(req)
    ajaxanswer=response.read()
    response.close()
    print ajaxanswer
    downloadurl = re.findall(r'(http://[^\']*)', ajaxanswer).pop()
    return downloadurl

                
def getParams():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=urllib.unquote_plus(splitparams[1])
    return param


def addItemForTelecastId(name,telecastid,iconimage):
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    u=sys.argv[0]+"getTelecast?telecastid="+telecastid+"&name="+urllib.quote_plus(name)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)


def stvLogin():
    loginvalues = {
        'sUsername' : xbmcplugin.getSetting(int(sys.argv[1]),'stv_username'),
        'sPassword' : xbmcplugin.getSetting(int(sys.argv[1]),'stv_password'),
        'image.x'   : random.randint(1,100),
        'image.y'   : random.randint(1,100),
        'image'     : 'Login',
        'AutoLoginActivate' : '1'
        }
    loginurl = 'http://www.save.tv/STV/M/Index.cfm?sk=PREMIUM'
    data = urllib.urlencode(loginvalues)

    request = urllib2.Request(loginurl, data)
    response = urllib2.urlopen(request)

    cookies.extract_cookies(response, request) 
    cookies.save(cookiefile, True, True)
              

httpconn = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))
httpconn.addheaders = httpheaders
urllib2.install_opener(httpconn)

if sys.argv[0] == 'plugin://plugin.video.savetv/getTelecast':
    params=getParams()
    downloadVideoFile(params["telecastid"],params["name"])
else:
    index()

xbmcplugin.endOfDirectory(int(sys.argv[1]))
