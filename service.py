# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import urllib
import urllib.parse
import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin
import chardet
import requests
import json

import hashlib
from http.client import HTTPConnection, OK
import struct
from io import BytesIO
import zlib
import random

__addon__      = xbmcaddon.Addon()
__author__     = __addon__.getAddonInfo('author')
__scriptid__   = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

__cwd__        = xbmc.translatePath( __addon__.getAddonInfo('path') )
__profile__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
__temp__       = xbmc.translatePath( os.path.join( __profile__, 'temp') )

sys.path.append (__resource__)
from langconv import *

SVP_REV_NUMBER = 1543
CLIENTKEY = "SP,aerSP,aer %d &e(\xd7\x02 %s %s"
RETRY = 3

def log(module, msg):
    xbmc.log("{0}::{1} - {2}".format(__scriptname__,module,msg) ,level=xbmc.LOGDEBUG )

def cid_hash_file(path: str):
    '''
    计算文件名为cid的hash值，算法来源：https://github.com/iambus/xunlei-lixian
    :param path: 需要计算的本地文件路径
    :return: 所给路径对应文件的cid值
    '''
    h = hashlib.sha1()
    with xbmcvfs.File(path, 'rb') as stream:
        size = stream.size()
        if size < 0xF000:
            h.update(stream.readBytes())
        else:
            h.update(stream.readBytes(0x5000))
            stream.seek(size // 3)
            h.update(stream.readBytes(0x5000))
            stream.seek(size - 0x5000)
            h.update(stream.readBytes(0x5000))
    return h.hexdigest().upper()
 
def get_sub_info_list(cid: str, max_retry_times: int = 0):
    '''
    获取迅雷字幕库中字幕信息列表
    :param cid: 本地电影文件的cid值
    :param max_retry_times: 最大重试次数，非正数时会无限次重试直到获得正确结果
    :return: 字幕信息列表，超过最大重试次数还未获得正确结果时会返回None。
    '''
    url = "http://sub.xmp.sandai.net:8000/subxl/{cid}.json".format(cid=cid)
    log(sys._getframe().f_code.co_name, url)
    result = None
    if max_retry_times <= 0:
        while True:
            response = requests.get(url)
            if response.status_code == 200:
                result = json.loads(response.text)["sublist"]
                break
    else:
        for i in range(max_retry_times):
            response = requests.get(url)
            if response.status_code == 200:
                result_dict = json.loads(response.text)
                result = result_dict["sublist"]
                break
    return [i for i in result if i]
    
def getSubByHashForThunder(fpath, languagesearch, languageshort, languagelong):
    fhash = cid_hash_file(fpath)
    subdata = get_sub_info_list(fhash, 3)
    if len(subdata)>0:
        for item in subdata:
            log(sys._getframe().f_code.co_name, "subname:%s, suburl:%s" % (item["sname"], item["surl"]))
            listitem = xbmcgui.ListItem(label="Chinese", label2=item["sname"])
            listitem.setArt({'icon': "0", 'thumb': "zh"})
            listitem.setProperty( "sync", "true" )
            listitem.setProperty( "hearing_imp", "false" )
            url = "plugin://%s/?action=download&filename=%s" % (__scriptid__, item["surl"])
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)

def Search(item):
    if not xbmcvfs.exists(__temp__.replace('\\','/')):
        xbmcvfs.mkdirs(__temp__)
    dirs, files = xbmcvfs.listdir(__temp__)
    for file in files:
        xbmcvfs.delete(os.path.join(__temp__, file))
    getSubByHashForThunder(item['file_original_path'], "chn", "zh", "Chinese")
    #if 'chi' in item['3let_language']:
        #getSubByHashForThunder(item['file_original_path'], "chn", "zh", "Chinese")
    #if 'eng' in item['3let_language']:
        #getSubByHashForThunder(item['file_original_path'], "eng", "en", "English")

def ChangeFileEndcoding(filepath):
    if __addon__.getSetting("transUTF8") == "true" and os.path.splitext(filepath)[1] in [".srt", ".ssa", ".ass", ".smi"]:
        data = open(filepath, 'rb').read()
        enc = chardet.detect(data)['encoding']
        if enc:
            data = data.decode(enc, 'ignore')
            if __addon__.getSetting("transJianFan") == "1":   # translate to Simplified
                data = Converter('zh-hans').convert(data)
            elif __addon__.getSetting("transJianFan") == "2": # translate to Traditional
                data = Converter('zh-hant').convert(data)
            data = data.encode('utf-8', 'ignore')
            try:
                local_file_handle = open(filepath, "wb")
                local_file_handle.write(data)
                local_file_handle.close()
            except:
                log(sys._getframe().f_code.co_name, "Failed to save subtitles to '%s'" % (filename))

def Download(filename):
    subtitle_list = []
    ChangeFileEndcoding(filename)
    subtitle_list.append(filename)
    return subtitle_list

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=paramstring
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]

    return param

params = get_params()
if params['action'] == 'search' or params['action'] == 'manualsearch':
    item = {}
    item['temp']               = False
    item['rar']                = False
    item['mansearch']          = False
    item['year']               = xbmc.getInfoLabel("VideoPlayer.Year")                 # Year
    item['season']             = str(xbmc.getInfoLabel("VideoPlayer.Season"))          # Season
    item['episode']            = str(xbmc.getInfoLabel("VideoPlayer.Episode"))         # Episode
    item['tvshow']             = xbmc.getInfoLabel("VideoPlayer.TVshowtitle")          # Show
    item['title']              = xbmc.getInfoLabel("VideoPlayer.OriginalTitle")        # try to get original title
    item['file_original_path'] = urllib.parse.unquote(xbmc.Player().getPlayingFile())  # Full path of a playing file
    item['3let_language']      = []

    if 'searchstring' in params:
        item['mansearch'] = True
        item['mansearchstr'] = params['searchstring']

    for lang in urllib.parse.unquote(params['languages']).split(","):
        item['3let_language'].append(xbmc.convertLanguage(lang,xbmc.ISO_639_2))

    if item['title'] == "":
        item['title'] = xbmc.getInfoLabel("VideoPlayer.Title")                         # no original title, get just Title
        if item['title'] == os.path.basename(xbmc.Player().getPlayingFile()):          # get movie title and year if is filename
            title, year = xbmc.getCleanMovieTitle(item['title'])
            item['title'] = title.replace('[','').replace(']','')
            item['year'] = year

    if item['episode'].lower().find("s") > -1:                                         # Check if season is "Special"
        item['season'] = "0"                                                           #
        item['episode'] = item['episode'][-1:]

    if ( item['file_original_path'].find("http") > -1 ):
        item['temp'] = True

    elif ( item['file_original_path'].find("rar://") > -1 ):
        item['rar']  = True
        item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

    elif ( item['file_original_path'].find("stack://") > -1 ):
        stackPath = item['file_original_path'].split(" , ")
        item['file_original_path'] = stackPath[0][8:]

    Search(item)

elif params['action'] == 'download':
    log(sys._getframe().f_code.co_name, "download filename %s)" % (params["filename"]))
    subs = Download(params["filename"])
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
