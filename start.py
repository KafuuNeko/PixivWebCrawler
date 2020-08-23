# Pixiv爬虫
# 作者：KafuuNeko
# https://kafuu.cc/

import re
import requests
import json
import os
import urllib.parse
import _thread
import time
import threading

MaxThreadCount = 50
gThreadCount = 0
crawlWorksLock = threading.RLock()

def requestThreadPermission():
    global MaxThreadCount
    global gThreadCount
    global crawlWorksLock
    crawlWorksLock.acquire()

    result = (gThreadCount < MaxThreadCount)
    if result:
        gThreadCount = gThreadCount + 1

    crawlWorksLock.release()

    return result
    

def dispFileName(name):
    name = name.replace('?', '-')
    name = name.replace('/', '-')
    name = name.replace('\\', '-')
    name = name.replace(':', '-')
    name = name.replace('*', '-')
    name = name.replace('"', '-')
    name = name.replace('<', '-')
    name = name.replace('>', '-')
    name = name.replace('|', '-')
    return name

def getPixivHtml(pid, head_info):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063'}

    while True:
        try:
            url = 'https://www.pixiv.net/artworks/' + str(pid)
            response = requests.get(url, headers=headers, timeout = 10)
            response.encoding = 'utf-8'
            return response.text
        except Exception as ex:
            print(head_info + "取" + str(pid) + "的页面代码时发生错误，正在重试")


#获取作品相似数      
def getLikeCount(pixivHtml):
    matchObj = re.search( r'"likeCount":([0-9]*)', pixivHtml)
    if matchObj:
        return int(matchObj.group(1))
    return -1


#获取指定作品喜欢人数
def getBookmarkCount(pixivHtml):
    matchObj = re.search( r'"bookmarkCount":([0-9]*)', pixivHtml)
    if matchObj:
        return int(matchObj.group(1))
    return -1

	

#校验Cookie是否有效
def checkCookie(cookie, head_info):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
        'cookie' : cookie}
    check_url = 'https://www.pixiv.net/tags/%E5%B0%91%E5%A5%B3/illustrations?p=30'
    while True:
        try:
            return requests.get(check_url, headers=headers).url == check_url;
        except Exception as ex:
            print(head_info + str(ex))
            print(head_info + "Cookie校验失败，正在重试")

#查询illustid是否已存在别的tag目录
def queryIllustidExist(illustid, root_dir, tag):
    for dir_name in os.listdir(root_dir):
        #print(head_info + root_dir + dir_name + '/' + str(illustid))
        if dir_name != dispFileName(tag) and os.path.exists(root_dir + dir_name + '/' + str(illustid) + '/json.txt'):
            return dir_name
    return None
                
	

#下载图片文件
def downloadImg(illustid, url, filename, tag_dir, cookie, head_info):
    headers = {'Referer': "https://www.pixiv.net/artworks/" + str(illustid),
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
               'cookie' : cookie}
    
    dir_path = tag_dir + str(illustid)
    if (os.path.exists(dir_path) == False):
        os.makedirs(dir_path)
        
    file_path = dir_path + '/' + dispFileName(str(filename))
    if os.path.exists(file_path) == False:
        imgres = requests.get(url, headers=headers, timeout = 60)
        with open(file_path, "wb") as f:
            f.write(imgres.content)
    else:
        print(head_info + "---[" + dispFileName(str(filename)) + "]文件已存在")



#写文本信息
def writeInfo(tag_dir, illustid, filename, image_info):
    dir_path = tag_dir + str(illustid)
    
    if (os.path.exists(dir_path) == False):
        os.makedirs(dir_path)
    
    with open(dir_path + '/' + filename, "wb") as f:
        f.write(image_info.encode())



#获取指定ID所有图片文件，并下载
def getImg(tag_dir, illustId, cookie, head_info):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
        'cookie' : cookie}
    
    while(True):
        try:
            #illust 插图
            #manga 漫画
            url = 'https://www.pixiv.net/ajax/illust/' + illustId + '/pages?lang=zh'
            response = requests.get(url, headers=headers, timeout = 10)
            response.encoding = 'utf-8'
            data = json.loads(response.text)

            if (data['error'] == False):
                for value in data['body']:
                    #original 原图
                    #regular 标准
                    print(head_info + '---Download:' + os.path.basename(value['urls']['regular']))
                    downloadImg(illustId, value['urls']['original'], os.path.basename(value['urls']['regular']), tag_dir, cookie, head_info)
                    

        except Exception as ex:
            print(head_info + str(ex))
            print(head_info + "---下载图片失败，正在重试")

        else:
            break


def crawlWorks(value, root_dir, tag, likeCountLimit, bookmarkCountLimit, head_info, tag_dir, remainingWorks):
    global MaxThreadCount
    global gThreadCount
    global crawlWorksLock
    
    print(head_info + '正在抓取：https://www.pixiv.net/artworks/' + value['illustId'])

    query_tag = queryIllustidExist(value['illustId'], root_dir, tag)
    if query_tag!=None:
        writeInfo(tag_dir, value['illustId'], "jume.txt", query_tag)
        print(head_info + "检测到此资源已存在在[" + query_tag + "]中")
        remainingWorks[0] = remainingWorks[0] - 1
        gThreadCount = gThreadCount - 1
        return False

    pixivHtml = getPixivHtml(value['id'], head_info)
            
    likeCount = getLikeCount(pixivHtml)
    bookmarkCount = getBookmarkCount(pixivHtml)
            
    if bookmarkCount < bookmarkCountLimit:
        print(head_info + "作品收藏数量低于" + str(bookmarkCountLimit) + "已跳过")
        remainingWorks[0] = remainingWorks[0] - 1
        gThreadCount = gThreadCount - 1
        return False
    if likeCount < likeCountLimit:
        print(head_info + "作品喜欢数量低于" + str(likeCountLimit) + "已跳过")
        remainingWorks[0] = remainingWorks[0] - 1
        gThreadCount = gThreadCount - 1
        return False
                
    info = 'illustid:' + value['illustId'] + '\n'
    info += 'id:' + value['id'] + '\n'
    info += 'illustTitle:' + value['illustTitle'] + '\n'
    info += 'title:' + value['title'] + '\n'
    info += 'author:' + value['userName'] + '\n'
    info += 'authorId:' + value['userId'] + '\n'
    info += 'likeCount:' + str(likeCount) + '\n'
    info += 'bookmarkCount:' + str(bookmarkCount) + '\n'
    info += 'url:' + 'https://www.pixiv.net/artworks/' + value['illustId']
            
    if value['illustId'] != value['id']:
        print(head_info + "illustId != id")
                
    writeInfo(tag_dir, value['illustId'], "info.txt", info)
    writeInfo(tag_dir, value['illustId'], "json.txt", json.dumps(value))
    writeInfo(tag_dir, value['illustId'], "view.htm", pixivHtml)
			
    getImg(tag_dir, value['illustId'], cookie, head_info)

    remainingWorks[0] = remainingWorks[0] - 1
    gThreadCount = gThreadCount - 1
    return True

#爬取指定Tag
def crawl(tag, cookie, start_page = None, likeCountLimit = 0, bookmarkCountLimit = 0):
    global MaxThreadCount
    global gThreadCount
    global crawlWorksLock
    
    root_dir = './pixiv/'
    tag_dir = root_dir + dispFileName(tag) + '/'
    
    if (os.path.exists(tag_dir) == False):
        os.makedirs(tag_dir)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
        'cookie' : cookie}
    
    tag_u8 = urllib.parse.quote(tag)

    
    if start_page == None:
        page = 1
    else:
        page = start_page
    
    while (True):
        head_info = '[' + tag + '第' + str(page) + '页] '
        
        if page > 10:
            print(head_info + "因为页码>10，正在校验Cookie是否有效，无效则退出");
            if checkCookie(cookie, head_info) == False:
                print(head_info + "Cookie校验失败，已终止查询")
                break;
            else:
                print(head_info + "Cookie校验成功，继续查询")
                
        
        with open(tag_dir + 'info.txt', "wb") as f:
            f.write(("当前查询页码：" + str(page)).encode())
            
        #illustrations 插图
        #manga 漫画
        url = "https://www.pixiv.net/ajax/search/artworks/" + tag_u8 + "?word=" + tag_u8 + "&order=date_d&mode=all&p=" + str(page) + "&s_mode=s_tag_full&type=all&lang=zh"
        
        print(head_info + "正在查询第" + str(page) + "页")
        #print(head_info + "Url:" + url)
        
        while(True):
            try:
                response = requests.get(url, headers=headers, timeout = 10)
                response.encoding = 'utf-8'
                data = json.loads(response.text)
            except Exception as ex:
                print(head_info + str(ex))
                print(head_info + "搜索异常，正在重试")
            else:
                break

        if data['error']:
            break
        
        
        illustMangaList = data['body']['illustManga']['data']
        worksNumber = len(illustMangaList)
        print(head_info + "此页共" + str(worksNumber) + "个项目")
        if len(illustMangaList) == 0:
            break

        remainingWorks = [worksNumber]
        #illust 插图
        #manga 漫画
        for value in illustMangaList:
            while requestThreadPermission() == False:
                time.sleep(1)
            
            _thread.start_new_thread ( crawlWorks, (value, root_dir, tag, likeCountLimit, bookmarkCountLimit, head_info, tag_dir, remainingWorks) )

        while remainingWorks[0] != 0:
            time.sleep(1)

        print(head_info + '此页爬取完成')
        
        page = page + 1
        
    with open(tag_dir + 'info.txt', "wb") as f:
        f.write("爬取完成".encode())
    
    print(tag + "爬取完成")
    

cookie = ''

if os.path.exists('./PixivCookie.txt'):
    cookie_file = open('./PixivCookie.txt')
    cookie = str(cookie_file.read())
    print("Cookie:" + cookie)
else:
    print("未检测到PixivCookie.txt文件，无Cookie将只能爬取600项资源")



#请自行添加要爬取的Tag

_thread.start_new_thread ( crawl, ("香風智乃", cookie, 1, 100) )
_thread.start_new_thread ( crawl, ("大妖精", cookie, 1) )
_thread.start_new_thread ( crawl, ("ご注文はうさぎですか?", cookie, 1, 1000) ) #1000以上likeCount的爬取完成


while True:
    pass
