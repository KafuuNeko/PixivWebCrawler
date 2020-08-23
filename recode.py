#Pixiv已爬取数据统计

import re
import os
import sqlite3
import json

def getDirList(query_path):
    dir_list = []
    for dir_name in os.listdir(query_path):
        dir_list.append(dir_name)

    return dir_list

def recodeImage(tagdir, imageDir, conn):
    cursor = conn.cursor()
    
    if os.path.exists(imageDir + 'json.txt'):
        json_file = open(imageDir + 'json.txt', 'r', encoding = 'UTF-8')
        info_file = open(imageDir + 'info.txt', 'rb')
        json_obj = json.loads(str(json_file.read()))

        info_str = str(info_file.read())
        matchObj = re.search( r'likeCount:([0-9]*)', info_str)
        likeCount = -1
        if matchObj:
            likeCount = matchObj.group(1)
        else:
            print("[error] [" + imageDir + "] 无likeCount")

        matchObj = re.search( r'bookmarkCount:([0-9]*)', info_str)
        bookmarkCount = -1
        if matchObj:
            bookmarkCount = matchObj.group(1)
        else:
            print("[error] [" + imageDir + "] 无bookmarkCount")
            

        json_file.close()
        info_file.close()

        tags = json_obj['tags']

        sql = '''INSERT INTO WorksInfo(pid, illustId, likeCount, bookmarkCount, X_rated, illustType, info_json, tagdir) VALUES(:pid, :illustId, :likeCount, :bookmarkCount,:X_rated, :illustType, :info_json, :tagdir)'''
        cursor.execute(sql, {'pid':json_obj['id'], 'illustId':json_obj['illustId'], 'likeCount':likeCount, 'bookmarkCount':bookmarkCount, 'X_rated':(('R-18' in tags) or ('R-18G' in tags)), 'illustType':json_obj['illustType'], 'info_json': json.dumps(json_obj), 'tagdir':tagdir})
        
        for tag in tags:
            sql = '''INSERT INTO WorksTag(pid, tag) VALUES(:pid, :tag)'''
            cursor.execute(sql, {'pid':json_obj['id'], 'tag':tag})

    elif os.path.exists(imageDir + 'jume.txt') == False:
        print("[error] [" + imageDir + "] 无json文件")
            
rDir = './pixiv/'

print('正在统计数据...')

conn = sqlite3.connect('./recode.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS WorksTag(pid varchar, tag varchar)')
cursor.execute('CREATE TABLE IF NOT EXISTS WorksInfo(pid varchar, illustId varchar, likeCount int, bookmarkCount int, X_rated bool, illustType int, info_json varchar, tagdir varchar)')

cursor.execute('DELETE FROM WorksTag')
cursor.execute('DELETE FROM WorksInfo')
cursor.close()

for tag in getDirList(rDir):
    if os.path.isdir(rDir + tag) == False:
        continue
    for pid in getDirList(rDir + tag):
        imageDir = rDir + tag + '/' + pid + '/'
        if os.path.isdir(imageDir) == False:
            continue
        recodeImage(tag, imageDir, conn)

conn.commit()
conn.close()

print('已完成数据统计...')
