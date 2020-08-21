# Pixiv爬虫
# 作者：KafuuNeko
# https://kafuu.cc/

import re
import requests
import json
import os
import urllib.parse

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

#下载图片文件
def downloadImg(illustid, url, filename, rdir, cookie):
    headers = {'Referer': "https://www.pixiv.net/artworks/" + str(illustid),
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
               'cookie' : cookie}
    
    dir_path = rdir + str(illustid)
    if (os.path.exists(dir_path) == False):
        os.makedirs(dir_path)
        
    file_path = dir_path + '/' + dispFileName(str(filename))
    if os.path.exists(file_path) == False:
        imgres = requests.get(url, headers=headers, timeout = 20)
        with open(file_path, "wb") as f:
            f.write(imgres.content)
    else:
        print("---[" + dispFileName(str(filename)) + "]文件已存在")



#写作者信息
def writeInfo(rdir, illustid, filename, image_info):
    dir_path = rdir + str(illustid)
    
    if (os.path.exists(dir_path) == False):
        os.makedirs(dir_path)
    
    with open(dir_path + '/' + filename, "wb") as f:
        f.write(image_info.encode())



#获取指定ID所有图片文件，并下载
def getImg(rdir, illustId, cookie):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
        'cookie' : cookie}
    
    while(True):
        try:
            #illust 插图
            #manga 漫画
            url = 'https://www.pixiv.net/ajax/illust/' + illustId + '/pages?lang=zh'
            response = requests.get(url, headers=headers, timeout = 5)
            response.encoding = 'utf-8'
            data = json.loads(response.text)

            if (data['error'] == False):
                for value in data['body']:
                    #original 原图
                    #regular 标准
                    print('---Download:' + value['urls']['original'])
                    downloadImg(illustId, value['urls']['original'], os.path.basename(value['urls']['regular']), rdir, cookie)
                    

        except Exception as ex:
            print(ex)
            print("---下载图片失败，正在重试")

        else:
            break


#爬取指定Tag
def crawl(tag, start_page, cookie):
    rdir = './pixiv/' + dispFileName(tag) + '/'
    if (os.path.exists(rdir) == False):
        os.makedirs(rdir)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
        'cookie' : cookie}
    
    tag_u8 = urllib.parse.quote(tag)

    page = start_page
    while (True):
        
        with open(rdir + 'info.txt', "wb") as f:
            f.write(("当前查询页码：" + str(page)).encode())
            
        #illustrations 插图
        #manga 漫画
        url = "https://www.pixiv.net/ajax/search/artworks/" + tag_u8 + "?word=" + tag_u8 + "&order=date_d&mode=all&p=" + str(page) + "&s_mode=s_tag_full&type=all&lang=zh"
        
        print("正在查询第" + str(page) + "页")
        print("Url:" + url)
        print('\n')
        
        while(True):
            try:
                response = requests.get(url, headers=headers, timeout = 5)
                response.encoding = 'utf-8'
                data = json.loads(response.text)
            except Exception:
                print("搜索异常，正在重试")
            else:
                break

        if data['error']:
            break
        
        illustMangaList = data['body']['illustManga']['data']
        print("此页共" + str(len(illustMangaList)) + "个项目")
        if len(illustMangaList) == 0:
            break
        
        #illust 插图
        #manga 漫画
        for value in illustMangaList:
            info = 'illustid:' + value['illustId'] + '\n'
            info += 'id:' + value['id'] + '\n'
            info += 'illustTitle:' + value['illustTitle'] + '\n'
            info += 'title:' + value['title'] + '\n'
            info += 'author:' + value['userName'] + '\n'
            info += 'authorId:' + value['userId'] + '\n'
            info += 'url:' + 'https://www.pixiv.net/artworks/' + value['illustId']
            print('正在抓取：https://www.pixiv.net/artworks/' + value['illustId'])
        
            getImg(rdir, value['illustId'], cookie)
            writeInfo(rdir, value['illustId'], "info.txt", info)
            writeInfo(rdir, value['illustId'], "json.txt", str(value))
        
            print('\n')

        page = page + 1

cookie=''
page = input("请输入起始页码：")
crawl("ごちうさ1000users入り", int(page), cookie)
input("爬取完成")
