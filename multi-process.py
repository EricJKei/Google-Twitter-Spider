import threading
import re
import requests
import pymysql
import time
import urllib
import codecs
import sys
#import thread
from queue import Queue

sys.setrecursionlimit(30000)

#初始url队列
InitialUrl_queue=Queue()
#迭代的url队列
corsorUrl_queue=Queue()
#一爬取的网页内容队列
html_queue=Queue()
headers={
	'accept': '*/*',
	'accept-language': 'zh-CN,zh;q=0.9',
	'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
	'cookie': '_ga=GA1.2.338995979.1521532327; dnt=1; kdt=UwpX4NGkdxwtJzSh3LX9VT7KbEyoF2Gf65h6bOMt; remember_checked_on=1; csrf_same_site_set=1; csrf_same_site=1; tfw_exp=0; __utmz=43838368.1525326039.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); eu_cn=1; __utma=191792890.338995979.1521532327.1525349878.1525349878.1; __utmz=191792890.1525349878.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utma=43838368.338995979.1521532327.1525326039.1525358294.2; _gid=GA1.2.1224498230.1525506845; personalization_id="v1_oyAFBIAzoVJR/3tygamCvA=="; guest_id=v1%3A152550952961928319; gdpr_lo=1; ads_prefs="HBESAAA="; twid="u=970834376421294081"; u=b82efed02b4695a80b542bb3b8dc7cfa; auth_token=bbd1ac7a4132df8ea625ac17d867522cbe91ecaf; mbox=PC#5c7b88cadd72461a8268dc12be94fa94.22_1#1526731518|session#52c02095062647b2b28ad54c4fe494b6#1525523778|check#true#1525521978; lang=zh-cn; _gat=1; ct0=76df7d47a896caaf19e5674edf319377',
	'origin': 'https://mobile.twitter.com',
	'referer': 'https://mobile.twitter.com',
	'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
	'x-csrf-token': '76df7d47a896caaf19e5674edf319377',
	'x-twitter-active-user': 'yes',
	'x-twitter-auth-type': 'OAuth2Session',
	'x-twitter-client-language': 'zh'
	}

def idmaker():
    #global InitialUrl_queue
    db=pymysql.connect("localhost","root","123456","flicker",charset="utf8")
    cur=db.cursor()
    sql="select * from twitteruserprofile"
    breakpoint="select * from twitter"
    try:
        cur.execute(sql)
        results=cur.fetchall()
        cur.execute(breakpoint)
        savedData=cur.fetchall()
        if len(savedData):
            savedDataTar=savedData[-1]
            savedId=savedDataTar[0]
            flag=0
            for row in results:
                if row[1]==savedId:
                    flag=1
                    continue
                if flag==1:
                    id=row[1]
                    InitialUrl_queue.put(id)
        else:
            for row in results:
                id=row[1]
                InitialUrl_queue.put(id)
    except:  
        print("error")
    finally:  
        db.close()  #关闭连接  

idmaker()
eeeee=1
flag=1
global start_time
class Crwal_thread (threading.Thread):   #继承父类threading.Thread
    def __init__(self, thread_id, queue):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue
    def run(self):                   #把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        print("启动线程{}".format(self.thread_id))
        self.crawl_spider()
        print("退出线程{}".format(self.thread_id))
    def crawl_spider(self):
    	#global start_time
    	global eeeee
    	global flag
    	while True:
            #当初始url队列、迭代url队列以及next_cursor为0时，爬虫请求模块结束运行
            if InitialUrl_queue.empty() and corsorUrl_queue.empty() and next_cursor=='0':
                flag=0
                break
            else:
                #如果对于某一个id来说，程序是第一次运行，执行if语句
                if eeeee==1:
                    userId=InitialUrl_queue.get()
                    #print(userId)
                    #更改url获取其他类型数据
                    url="https://api.twitter.com/1.1/friends/list.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&skip_status=1&cursor=-1&user_id={}&count=20".format(userId)
                    eeeee=0
                #获取迭代url队列
                elif eeeee==0: 
                    url=self.queue.get()
                    #print(url)
                #start_time=time.time()
                try:
                    r=requests.get(url,headers=headers)
                    r.raise_for_status()
                    r.encoding='utf-8'
                except: 
                    #差错处理
                    while True:
                        try:
                            time.sleep(4)
                            r=requests.get(url,headers=headers)
                            r.raise_for_status()
                            r.encoding='utf-8'
                        except:
	                        continue
                html=r.text
                #游标的获取方式
                next_cursor=re.findall(r'"next_cursor_str":"([\d]*?)","previous_cursor"',html,re.S)[0]
                #print(html)
                #如果游标为0.结束请求
                if next_cursor=='0':
                	eeeee=1
                	continue
                #url的重构更改
                urlForNext="https://api.twitter.com/1.1/friends/list.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&skip_status=1&cursor={}&user_id={}&count=20".format(next_cursor,userId)
                self.queue.put(urlForNext)
                #写入userid是为了方便解析模块中数据的存储
                html_queue.put(userId+html)
                #print(html_queue.get())


class Parse_thread(threading.Thread):
    def __init__(self, thread_id, queue):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.queue = queue
    def run(self):                   #把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        print("启动线程{}".format(self.thread_id))
        self.parse_data()
        print("退出线程{}".format(self.thread_id))

    def parse_data(self):
        #global start_time
        db= pymysql.connect("localhost","root","123456","flicker",charset="utf8")  
        # 使用cursor()方法获取操作游标
        cur = db.cursor()
        start_time=time.time()
        AllConut=0
        while True:
            #当初始队列，迭代队列以及html内容队列均为空是，结束程序
            if InitialUrl_queue.empty() and corsorUrl_queue.empty() and self.queue.empty():
                break
            else:
                #从html队列中读取爬取的内容
                html=self.queue.get()
                #start_time=time.time()
                #userId的获取
                userId=re.match(r'([\d]*?){',html,re.S)[0][:-1]
                #print(userId)
                #获取关注列表中的数据
                followingId=re.findall(r'"id_str":"([\d]*?)","name"',html,re.S)
                followingScreenName=re.findall(r'"name":".*?","screen_name":"(.*?)"',html,re.S)
                contentAll=''
                for i in range(len(followingId)):
                    followingScreenName[i].replace('\\\\','\\')
                    followingScreenName[i]=codecs.getdecoder("unicode_escape")(followingScreenName[i])[0]
                    content='("'+userId+'","'+followingId[i]+'","'+followingScreenName[i]+'")'
                    contentAll=contentAll+","+content
                contentAll=contentAll[1:]
                #数据插入
                #time.sleep(0.1)
                sql_insert ='insert into rrrrr(userID,followersID,followersScreenName) values{}'.format(contentAll)
                try:
                    cur.execute(sql_insert)  
                    #提交
                    db.commit()  
                except Exception as e:  
                    #错误回滚  
                    db.rollback()
        db.close()        

threads = []
#创建线程
thread1 = Crwal_thread("Thread-1",corsorUrl_queue)
thread2 = Parse_thread("Thread-2",html_queue)
#启动线程
thread1.start()
thread2.start()
#添加到线程池
threads.append(thread1)
threads.append(thread2)
#阻塞
for t in threads:
    t.join()
 
print ("Exiting Main Thread")