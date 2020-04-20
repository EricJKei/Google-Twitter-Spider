import re
import requests
import pymysql
import time
import urllib
import codecs
import sys

#迭代的最大深度
sys.setrecursionlimit(50000)

#初始id列表
userIdList=[]
#统计数据
tweetsCount=0
followingCount=0
followersCount=0

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

#读取初始id，同google+相同
def idmaker():
	global userIdList
	db=pymysql.connect("localhost","root","123456","flicker")
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
				#if row[1]=='47169698':
					flag=1
					continue
				if flag==1:
					id=row[1]
					userIdList.append(id)
		else:
			for row in results:
				id=row[1]
				userIdList.append(id)
	except:  
	    print("error")
	finally:  
		#关闭连接 
	    db.close()  


idmaker()

db= pymysql.connect("localhost","root","123456","flicker",charset="utf8")  

# 使用cursor()方法获取操作游标  
cur = db.cursor()


def getTimelineHtml(num,url):
	#当连续6次请求失败，将该id视为无效id
	if num>5:
		print("请检查账号有效性")
		return 0
	try:
		r=requests.get(url,headers=headers)
		r.raise_for_status()
		r.encoding='utf-8'
		html=r.text.replace('\n','')
	except:
		#重复请求
		print("\nget timeline error,try again\n")
		num+=1
		time.sleep(5)
		html=getTimelineHtml(num,url)
	return html



#当获得的globalObjects为空时，结束该用户tweets的获取
#当获取到10页推文的时候，结束该用户tweets的获取
#解析出当前timeline获得的tweets
#获得cursor-bottom的value值，进行下一页的提取，并再次进行分析
#在该函数内部进行递归
def parseTimelineHtml(userId,count,url,html):
	global tweetsCount

	#统计递归次数，6次为上限
	count+=1

	#获取发表日期
	created_at=re.findall(r':{"created_at":"(.*?)","id_str"',html,re.S)
	#print("{}\n".format(created_at))

	#获取发表方式
	newSource=[]
	source=re.findall(r',"source":"(.*?)","user_id_str":".*?"',html,re.S)
	#print("{}\n".format(source))
	for place in source:
		s=re.findall(r'\\u003e(.*?)\\u003c',place,re.S)
		if s:
			place=s[0]
		else:
			place=''
		newSource.append(place)
	#print(newSource)


	#获取tweets
	full_text=re.findall(r'"full_text":"(.*?)","display_text_range"',html,re.S)
	#print(full_text)
	print("1")
	for i in range(len(full_text)):
		full_text[i].replace('"','\\"')
		#去除表情
		co=re.compile(u'[\U00010000-\U0010ffff]')
		full_text[i]=co.sub(u'',full_text[i])
		#转换unicode编码
		full_text[i]=codecs.getdecoder("unicode_escape")(full_text[i])[0]
		#print(full_text[i])
		newSource[i]=codecs.getdecoder("unicode_escape")(newSource[i])[0]

		#将用户ID，推文时间，推文地点，推文内容存入数据库
		sql_insert ='insert into tweets(userID,publishTime,publishWay,publishContent) values("{}","{}","{}","{}")'.format(userId,created_at[i],newSource[i],full_text[i])
		try:  
		    cur.execute(sql_insert)  
		    #提交  
		    db.commit()  
		    tweetsCount+=1
		except Exception as e:  
		    #错误回滚  
		    db.rollback()


	#获取cursor，用于迭代url，获取该用户的下一组推文数据
	if len(re.findall(r'"value":"HBa(.*?)"',html,re.S)):
		cursor=re.findall(r'"value":"HBa(.*?)"',html,re.S)[0]
		cursor="HBa"+cursor
		#url编码
		cursor=urllib.parse.quote(cursor)
		#print(cursor)
	else:
		return

	#获取10页推文为上限
	if count==10:
		return

	#重构推文的url
	urlForNextTimeline=url+"&cursor="+cursor
	num=0
	#time.sleep(1)
	#进行递归
	timelineHtml=getTimelineHtml(num,urlForNextTimeline)
	parseTimelineHtml(userId,count,url,timelineHtml)


#global start_time
#获取用户的关注列表
def getFollowingHtml(num,url):
	#global start_time
	#start_time=time.time()
	if num>5:
		print("请检查账号有效性")
		return 0
	try:
		r=requests.get(url,headers=headers,timeout=6)
		r.raise_for_status()
		r.encoding='utf-8'
		html=r.text.replace('\n','')
		#print(html)
	except:
		print("\nget following html fail,try again\n")
		num+=1
		time.sleep(5)
		html=getFollowingHtml(num,url)
	return html

#AllCount=0
#数据清洗
def parseFollowingHtml(userId,html):
	#global start_time
	#获取following
	#start_time=time.time()
	#global AllCount
	global followingCount
	#获取用户id
	followingId=re.findall(r'"id_str":"([\d]*?)","name"',html,re.S)
	#获取用户显示的名称，该数据可用于重构用户主页的url
	followingScreenName=re.findall(r'"name":".*?","screen_name":"(.*?)"',html,re.S)
	contentAll=''
	#统计关注人数
	followingCount+=len(followingId)
	for i in range(len(followingId)):
		#解决unicode编码问题
		followingScreenName[i].replace('\\\\','\\')
		followingScreenName[i]=codecs.getdecoder("unicode_escape")(followingScreenName[i])[0]
		content='("'+userId+'","'+followingId[i]+'","'+followingScreenName[i]+'")'
		contentAll=contentAll+","+content
		#AllCount+=s
	contentAll=contentAll[1:]
	#批量插入
	sql_insert ='insert into following(userID,followingID,followingScreenName) values{}'.format(contentAll)
	print(sql_insert)
	try:  
		cur.execute(sql_insert)  
		#提交  
		db.commit()  
	except Exception as e:  
		#错误回滚  
		db.rollback()
	#AllCount+=s
	#if AllCount>2000:
	#	print('单条插入千条数据时间{}'.format(time.time()-start_time))

	
	#获取next_cursor，用于迭代url
	next_cursor=re.findall(r'"next_cursor_str":"([\d]*?)","previous_cursor"',html,re.S)[0]
	#print(next_cursor)

	#当next_cursor为0，代表已经获取全部关注列表数据
	if next_cursor=='0':
		return

	#重构url
	urlForNextFollowing="https://api.twitter.com/1.1/friends/list.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&skip_status=1&cursor={}&user_id={}&count=20".format(next_cursor,userId)
	num=0
	#time.sleep(1)
	#递归，超过6次请求失败，开始下一跳数据的获取
	followingHtml=getFollowingHtml(num,urlForNextFollowing)
	if followingHtml==0:
		with open('C:\\Users\\Eric\\id.txt','a',encoding='utf-8') as f:
			f.write(userId+'\n')
		f.close()
	else:
		parseFollowingHtml(userId,followingHtml)


def main():
	global userIdList
	global tweetsCount
	global followingCount
	idmaker()
	ssss=0
	#start_time=time.time()
	for userId in userIdList:
		print(userId)

		count=0
		#判断账号有效性
		numTimeline=0
		numFollowing=0
		#判断获取信息数量
		tweetsCount=0
		followingCount=0
		
		#获取tweet
		urlForTimeline="https://api.twitter.com/2/timeline/profile/{}.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&skip_status=1&cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_reply_count=1&tweet_mode=extended&include_entities=true&include_user_entities=true&include_ext_media_color=true&send_error_codes=true&include_tweet_replies=false&userId={}&count=20".format(userId,userId)
		timelineHtml=getTimelineHtml(numTimeline,urlForTimeline)
		if timelineHtml==0:
			with open('C:\\Users\\Eric\\id.txt','a',encoding='utf-8') as f:
				f.write(userId+'\n')
			f.close()
			continue
		else:
			parseTimelineHtml(userId,count,urlForTimeline,timelineHtml)
		
		
		#获取following
		urlForFollowing="https://api.twitter.com/1.1/friends/list.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&skip_status=1&cursor=-1&user_id={}&count=20".format(userId)
		followingHtml=getFollowingHtml(numFollowing,urlForFollowing)
		if followingHtml==0:
			with open('C:\\Users\\Eric\\id.txt','a',encoding='utf-8') as f:
				f.write(userId+'\n')
			f.close()
			#continue
		else:
			parseFollowingHtml(userId,followingHtml)

		sql_insert='insert into twitter(userId,tweetsCount,followingCount) values("{}",{},{})'.format(userId,tweetsCount,followingCount)
		try:  
		    cur.execute(sql_insert)  
		    #提交  
		    db.commit()  
		except Exception as e:  
		    #错误回滚  
		    db.rollback()

		#break
	#关闭连接
	db.close()   

if __name__=='__main__':
	main()


