import requests
import re
import pymysql
import time
import codecs

#用于存放初始用户ID
useridlist=[]

postUrl="https://plus.google.com/_/PlusAppUi/data?ds.extension=64399324&f.sid=3038417477135081102&hl=zh-CN&soc-app=199&soc-platform=1&soc-device=1&_reqid=783006&rt=c"

headers={
	'content-type':'application/x-www-form-urlencoded;charset=UTF-8',
	'cookie':'SID=AQYJ8l8Oo-FbNv5KgyIRqpXSMKnDdIdamXbrsMqaAyD5zJNWgqs0RvYRY3NKDZQKG8rYTg.; HSID=A4neZRW0yG3tWIwUj; SSID=ARdZwWFS6AwSGUfGF; APISID=pQzc8lCsg9VguQJe/AEOnslkK_aFQQJo5W; SAPISID=8vsqmKd7e5CWxYSM/AwIETsSF0XDusPo4P; CONSENT=YES+CN.zh-CN+20180204-00-0; OTZ=4358363_24_24__24_; 1P_JAR=2018-5-13-6; NID=130=adVRo7JwHd0DdwbM2NvTsERkFEmcccoAy_gSt43mJ9vRgMzMbWeiQEOYxP_jc70DoawoTuEvgKqih0hBaNzvXHSxtvYlBjBIHs29LhuWy4aImGCAH3EPqZ14DGxrpMgNi8D_9F3oP3Mrrbrv9R5vvwQcDzskI7FrFGQHgCxxMukVTjSoOvsn1j42lm0rtpoAhBT2rCkXgukoYBKqSw-gLXy8kZvLnb3oGCRebD_O05XTSg; SIDCC=AEfoLeZ9ihPjUlW6zLds18c5MZtD5RutVlPe3wwVPMN1gxch1tKAnSIZPqF6YOCQt_-WE4AKZQ',
	'origin':'https://plus.google.com',
	'referer': 'https://plus.google.com/',
	'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
	}

#连接数据库
db= pymysql.connect("localhost","root","123456","flicker",charset="utf8")  
# 使用cursor()方法获取操作游标  
cur = db.cursor()

def idmaker():
	global useridlist
	db=pymysql.connect("localhost","root","123456","flicker")
	cur=db.cursor()
	sql="select * from twitteruserprofile"
	#断点，用于程序的重启动
	breakpoint="select * from googleplusintro"
	try:
		cur.execute(sql)
		results=cur.fetchall()
		cur.execute(breakpoint)
		savedData=cur.fetchall()
		#当程序不是第一次运行时，执行if语句，即重启动，从上次中断的下一条数据开始爬取
		if len(savedData):
			savedDataTar=savedData[-1]
			savedId=savedDataTar[0]
			flag=0
			for row in results:
				if row[0]==savedId:
					flag=1
					continue
				if flag==1:
					id=row[0]
					useridlist.append(id)
		else:
			for row in results:
				id=row[0]
				useridlist.append(id)
	except:  
	    print("error")
	finally:  
	    db.close()  #关闭连接  


#获取用户发布内容网页
def getGetHtml(url):
	#try:
	r=requests.get(url,headers=headers)
	r.raise_for_status()
	r.encoding='utf-8'
	html=r.text 
	#print(html)
	return html
	#except:
	#	print('getGetHtml error')

#获取用户发表内容
def parseGetHtml(html,id):
	finText=''
	count=0
	text=re.findall(r'<div class="jVjeQd" jsname="EjRJtf" dir="ltr">(.*?)</div>',html)
	#解决编码问题，并批量插入
	for i in text:
		s=re.sub(r'<[^>]+>','',i).strip()#.encode('unicode-escape').decode('utf-8')
		s=codecs.getdecoder("unicode_escape")(s)[0]
		#print(s)
		s=s.replace('\n','').replace('&#39;',"'").replace('&quot;','\\\"').replace('&amp;','&').replace('Â','')
		#去除掉文字中的表情
		co=re.compile(u'[\U00010000-\U0010ffff]')
		s=co.sub(u'',s)
		text='("'+id+'","'+s+'")'
		finText=finText+","+text
		count=count+1
		if count==6:
			break
	#批量插入
	if finText:
		finText=finText[1:]		
		sql_insert ='insert into googlePlusTweets(userID,tweets) values{}'.format(finText)
		#print("2")
		try:  
			cur.execute(sql_insert)  
			#提交  
			db.commit()  
		except Exception as e:  
			#错误回滚  
			db.rollback()
	return count
	#print("content:\n{}\n".format(finText))
	#print('用户发表内容：\n{}\n'.format(finText))


#通过一次无效的访问来获取xsrf的键值对
def getXsrf(data):
	#try:
	r=requests.post(postUrl,headers=headers,data=data)
		#此处因为需要一个无效的响应返回xsrf，故不添加r.raise_for_status()
	r.encoding='utf-8'
	html=r.text
	xsrf=re.findall(r'"xsrf","(.*?)"',html)
	#print(html)
	time.sleep(20)
	#print(xsrf[0])
	return xsrf[0]
	#except:
	#	print('getXsrf error')


#获取xsrf键值对之后，可以成功获取post返回的数据，该数据包括用户信息，用户三方链接，用户关系
def getPostHtml(xsrf,data):
	#try:
	data['at']=xsrf
	r=requests.post(postUrl,headers=headers,data=data)
	r.raise_for_status()
	r.encoding='utf-8'
	html=r.text
	#print(html)
	return html
	#except:
	#	print('getPostHtml error')


def parsePostHtml(html,id,tweetsCount):
	#获取用户id
	grouplist=''
	global useridlist
	userId=re.findall(r'\d{21}',html)
	ls=sorted(set(userId),key = userId.index)
	#print(ls)
	userConnection=re.findall(r'\["(.*?)","\d{21}",.*?\]',html)
	#print(userConnection)
	del ls[0:1]
	del ls[len(userConnection):]

	#用于扩展id
	#useridlist.extend(ls)
	#useridlist=sorted(set(useridlist),key = useridlist.index)

	#批量插入
	for i in ls:
		text='("'+id+'","'+i+'")'
		grouplist=grouplist+','+text
	followersCount=len(ls)
	grouplist=grouplist[1:]
	sql_insert ='insert into googlePlusFollowers(userID,friendID) values{}'.format(grouplist)
	#print("2")
	try:  
		cur.execute(sql_insert)  
		#提交  
		db.commit()  
	except Exception as e:  
		#错误回滚  
		db.rollback()

	#获取用户连接
	link=''
	#用户链接存在于两种各种中，一种是false，一种是true
	userLink=re.findall(r'\[false\][\s],".*?","(http://.*?|https://.*?)"',html)
	userLink0=re.findall(r'\[true\][\s],".*?","(http://.*?|https://.*?)"',html)
	userLink=userLink+userLink0
	#批量插入
	for i in userLink:
		i=i.strip().encode('utf-8').decode('unicode-escape')
		text='("'+id+'","'+i+'")'
		link=link+','+text
	linkCount=len(userLink)
	link=link[1:]

	sql_insert ='insert into googlePlusLink(userID,link) values{}'.format(link)
	#print("2")
	try:  
		cur.execute(sql_insert)  
		#提交  
		db.commit()  
	except Exception as e:  
		#错误回滚  
		db.rollback()
	

	#获取用户个人介绍
	new_userInform_plus=''
	u=re.findall(r'null,null,null,null,\[\[\[true\][\s],(.*?)\][\s]\]',html,re.S)
	if len(u)!=0:
		userInform=u[0]
		#去除表情
		co=re.compile(u'[\U00010000-\U0010ffff]')
		userInform=co.sub(u'',userInform)
		new_userInform=re.sub(r',\[null.*','',userInform).strip()
		#转换unicode编码
		new_userInform=codecs.getdecoder("unicode_escape")(new_userInform)[0]
		new_userInform=re.sub(r'(<.*?>|Â)','',new_userInform)
		new_userInform_plus=new_userInform.replace('\n','').replace('&#39;',"'").replace('"',"'").replace('&quot;','\\\"').replace('â','').replace('â',"'").replace('&amp;','&')
		print(new_userInform_plus)
	else:
		new_userInform_plus=''
	#插入统计数据
	sql_insert ='insert into googlePlusIntro(userID,intro,linkCount,tweetsCount,followCount) values("{}","{}",{},{},{})'.format(id,new_userInform_plus,linkCount,tweetsCount,followersCount)
	#print("2")
	try:  
		cur.execute(sql_insert)  
		#提交  
		db.commit()  
	except Exception as e:  
		#错误回滚  
		db.rollback()



n=0
def main():
	global n
	idmaker()
	i=0
	while i<=len(useridlist):
		id=useridlist[i]
		print(id)
		getUrl="https://plus.google.com/"+id
		data={
			'f.req': '[[[64399324,[{"64399324":[null,null,[[null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[[null,[2,null,"'+id+'"]]]],[null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[[null,[2,null,"'+id+'"]]]],[null,null,null,null,[[null,[2,null,"'+id+'"]]]],[null,null,null,null,null,null,null,null,null,null,null,null,null,null,[2,[[[2,null,"'+id+'"]]]]],[null,null,null,null,null,null,null,null,null,null,[[null,[2,null,"'+id+'"]]]],[null,[[null,[2,null,"'+id+'"]],3]],[null,null,null,null,null,null,null,[[null,[2,null,"'+id+'"]],3]],[null,null,[[null,[2,null,"'+id+'"]]]],[null,null,null,[[null,[2,null,"'+id+'"]],8,null]],[null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,[[null,[2,null,"'+id+'"]]]],[null,null,null,null,null,null,null,null,[[null,[2,null,"'+id+'"]],null,true]]],[null,[2,null,"'+id+'"]]]}],null,null,0]]]'
			}
		try:
			getHtml=getGetHtml(getUrl)
			xsrf=getXsrf(data)
			postHtml=getPostHtml(xsrf,data)
			print("获取成功：\n{}\n".format(id))
		except:
			print("获取失败,开始重新获取：\n{}\n".format(id))
			n+=1
			time.sleep(5)
			#失败6次便将此id视为无效id
			if n>5:
				i+=1
				n=0
			continue
		count=parseGetHtml(getHtml,id)
		parsePostHtml(postHtml,id,count)
		i+=1
	db.close()
	time.sleep(1)

if __name__=='__main__':
	main()
