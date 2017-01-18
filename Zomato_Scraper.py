import urllib
import urllib2
from bs4 import BeautifulSoup
import json
import xlwt
import os
import time

Folder='Zomato Files'
IndexFileFolder='Index Files'
ErrorFolder='Error'
RawJson='Raw JSON'
AnalyzedJson='Corrected JSON'
PinCodeUpdateFolder='PinCode Update JSON'
PhoneNumberFolder='PhoneNumber'
UpdatedJson='Updated JSON'
TempFileName='a.html'
TempJSONFile='a.json'
ExcelFileName='Restaurants'
AllDataFolder='All Data'

def CreateFolder(FolderName):
	try:
		os.makedirs(FolderName)
	except OSError:
		pass	

def FileDownloader(start,end,Folder):
	
	CreateFolder(Folder)
		
	BaseUrl = "https://www.zomato.com/kolkata/restaurants?page="
	print 'Downloading Files Started'
	print 
	
	for Page in range(start,end):
		Url=BaseUrl+str(Page)
		FileName=str(Page)+'.html'
		print Url
		urllib.urlretrieve(Url, Folder+'/'+FileName)
		
		if Page%5==0: 
			print 'Sleeping For 15 Seconds'
			time.sleep(15)
			
def OLTagIsolation(Folder,file):
	search=''
	readopen=0
	f=open(Folder+'/'+file,'r')
		
	for line in f:
		if line.find('<ol>')!=-1:
			readopen=1
		if readopen==1:
			search+=line
		if line.find('</ol>')!=-1:
			readopen=0
				
	f.close()

	return search

def MapDataIsolation(Folder,file):
	search=''
	readopen=0
	f=open(Folder+'/'+file,'r')
	
	for line in f:
		if line.find('zomato.DailyMenuMap.mapData')!=-1:
			readopen=1
		if readopen==1:
			search+=line
			break
	
	f.close()
	
	search=search[34:-2]
	
	return search
	
def TempFileCreator(FileName,search):
	f=open(FileName,'w')
	f.write(search)
	f.close()

def ListCreator():
	search=''
	SingleList=[]
	readopen=0
	f=open(TempFileName,'r')
	
	for line in f:
		if line.find('<li')!=-1:
			readopen=1
		if readopen==1:
			search+=line
		if line.find('</li>')!=-1:
			readopen=0
			SingleList.append(search)
			search=''
	
	f.close()
	return SingleList

def DictionaryCreator(Name,Link,Locality,Address,Cusine,Cost):
	dict={}	
	dict['Name']=Name
	dict['Link']=Link
	dict['Locality']=Locality
	dict['Address']=Address
	dict['Cusine']=Cusine
	dict['Cost']=Cost
	
	return dict

	
def SoupAnalyzer(soup):

	for aclass in soup.findAll('a', attrs={'class': 'result-title'}):
		Name=aclass.string.encode("utf-8")
		Link=aclass.get('href').encode("utf-8")

	for aclass in soup.findAll('a', attrs={'class': 'cblack search-page-text'}):
		Locality=aclass.string.encode("utf-8")

	for aclass in soup.findAll('span', attrs={'class': 'search-result-address'}):
		Address=aclass.get('title').encode("utf-8")

	t=soup.findAll('div', attrs={'class': 'res-snippet-small-cuisine truncate search-page-text'})[-1]
	s=t.encode("utf-8")
	CusineStarter=s.find("</a>")+8
	Cusine=s[CusineStarter:-6].encode("utf-8")

	t=soup.findAll('div', attrs={'class': 'search-page-text'})[-1]
	if t!=[]:
		s=t.encode("utf-8")
		CostStarter=s.find("</span>")+7
		CostEnder=s[CostStarter:].find("\n")
		Cost=s[CostStarter:CostStarter+CostEnder].encode("utf-8")
	else:
		Cost=''
	
	dict=DictionaryCreator(Name,Link,Locality,Address,Cusine,Cost)
	
	return dict
	
def JsonWrite(Folder,PageRestaurant,FileName):
		
	f=open(Folder+'/'+FileName+'.json','w')
	json.dump(PageRestaurant,f,indent=4)
	f.close()


def JsonRead(Folder,File):

	if Folder=='':
		f=open(File,'r')
	else:
		f=open(Folder+'/'+File,'r')
	
	str=f.read()
	
	try:
		data=json.loads(str)
	except ValueError:
		data=[]
		pass
	
	f.close()
	
	return data
	
def JsonUpdate(Folder):

	CreateFolder(AnalyzedJson)

	for file in os.listdir(Folder):
		
		print 'Updating',file
		data=JsonRead(Folder,file)
		
		for dict in data:
			s=dict['Cusine']
			if s.find("Cuisines:")!=-1:
				dict['Cusine']=s[s.find("Cuisines:")+9:]
			
			s=dict['Cost']
			if s.find("Rs")==-1:
				dict['Cost']=''
	
		print 'Writing Updated File'
		print
		JsonWrite(AnalyzedJson,data,file[:-5])
	
	print 'Updating JSON Complete'

def JsonList(Folder):

	AllData=[]
	
	for file in os.listdir(Folder):
		data=JsonRead(Folder,file)
		AllData.append(data)
	
	return AllData

def ListAnalyzer(SingleList):
	
	PageRestaurant=[]
	
	for i in SingleList:
		soup=BeautifulSoup(i)
		dict=SoupAnalyzer(soup)
		PageRestaurant.append(dict)
		
	return PageRestaurant
	
def LatLongExtractor(PageRestaurant):
	
	data=JsonRead('',TempJSONFile)
	
	i=1
	for dict in PageRestaurant:
		dict["Lat"]=data[str(i)]["lat"]
		dict["Long"]=data[str(i)]["lon"]
		i+=1
	
	return PageRestaurant

def PinCodeExtractor(PageRestaurant):
	
	Base_Url = "http://maps.googleapis.com/maps/api/geocode/json?latlng="
	
	i=1
	for dict in PageRestaurant:
		
		if i%10==0:
			print 'Waiting For 5 Seconds'
			time.sleep(5)
		i+=1
		
		GeoCode_Url=Base_Url+str(dict["Lat"])+","+str(dict["Long"])+"&sensor=true"
		Request = urllib2.urlopen(GeoCode_Url)
		Data = json.loads(Request.read())
		if Data["status"]=="OK":
			dict["PinCode"]=Data["results"][0]["address_components"][-1]["long_name"]
		else:
			dict["PinCode"]="Not Available"
			
	return PageRestaurant

def PinCodeUpdater(Folder):
	
	CreateFolder(PinCodeUpdateFolder)
	
	for file in os.listdir(Folder):
		print 'Updating Pin Code',file
		data=JsonRead(Folder,file)
		
		for dict in data:
			s=dict['PinCode']
			s=str(s)
			
			#if s.find("India")!=-1:
				#dict=PinCodeDict(dict,0)
			
			if s.find("Not Available")!=-1:
				dict=PinCodeDict(dict,1)
	
		print 'Writing Updated File'
		print
		JsonWrite(PinCodeUpdateFolder,data,file[:-5])
		
	print 'Pin Code Updated'

def PinCodeDict(dict,Status):

	if Status==0:
		GeoCode_Url = 'http://maps.googleapis.com/maps/api/geocode/json?address="'+str(dict["Address"])+'"&sensor=true'
	else:
		GeoCode_Url="http://maps.googleapis.com/maps/api/geocode/json?latlng="+str(dict["Lat"])+","+str(dict["Long"])+"&sensor=true"
	
	Request = urllib2.urlopen(GeoCode_Url)
	Data = json.loads(Request.read())
	if Data["status"]=="OK":
		dict["PinCode"]=Data["results"][0]["address_components"][-1]["long_name"]
	else:
		dict["PinCode"]="Not Available"
			
	return dict		
def FileAnaylzer(Folder,JSONFolder):

	CreateFolder(JSONFolder)
	
	for file in os.listdir(Folder):
	
		print file
		
		search=OLTagIsolation(Folder,file)
		TempFileCreator(TempFileName,search)
		print 'Temporary File Created'
		
		search=MapDataIsolation(Folder,file)
		TempFileCreator(TempJSONFile,search)
		print 'Temporary JSON File Created'
		
		SingleList=ListCreator()
		PageRestaurant=ListAnalyzer(SingleList)
		print 'Basic Data Extracted'

		PageRestaurant=LatLongExtractor(PageRestaurant)
		print 'Latitute And Longitude Extracted'
		
		PageRestaurant=PinCodeExtractor(PageRestaurant)
		print 'Pin Code Extracted'
		
		JsonWrite(JSONFolder,PageRestaurant,file[:-5])
		print 'JSON Write Ended'
		
		print
	
	print 'Analyzing Complete'		

def FileComparator():
	
	CreateFolder(UpdatedJson)
	
	for File in os.listdir(PhoneNumberFolder):
		Data=JsonRead(PinCodeUpdateFolder,File)
		PhoneData=JsonRead(PhoneNumberFolder,File)
		
		for dict in Data:
			dict["PhoneNumber"]='Not Avaliable'
		
		for dict in Data:
			for PhoneDict in PhoneData:
				if dict["Name"]==PhoneDict["Name"]:
					dict["PhoneNumber"]=PhoneDict["PhoneNumber"]
					
		JsonWrite(UpdatedJson,Data,File[:-5])
		print 'Updated',File	
	
def ExcelWrite(Data,ExcelFileName):

	Week=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
	Add=10
	
	print 'Excel Write Started'
	
	book = xlwt.Workbook(encoding="utf-8")
	sheet=book.add_sheet('Names')
	
	row=0
	sheet.write(row,0,'Name')
	sheet.write(row,1,'Locality')
	sheet.write(row,2,'Address')
	sheet.write(row,3,'Pin Codes')
	sheet.write(row,4,'Phone Number 1')
	sheet.write(row,5,'Phone Number 2')
	sheet.write(row,6,'Cusine')
	sheet.write(row,7,'Cost For 2')
	sheet.write(row,8,'Latitude')
	sheet.write(row,9,'Longitude')
	
	for n,day in enumerate(Week):
		sheet.write(row,Add+n,day)
		
	row+=1
	
	for SinglePage in Data:
		for dict in SinglePage:
			sheet.write(row,0,dict['Name'])
			sheet.write(row,1,dict['Locality'])
			sheet.write(row,2,dict['Address'])
			sheet.write(row,3,dict['PinCode'])
			sheet.write(row,4,dict['PH1'])
			sheet.write(row,5,dict['PH2'])
			sheet.write(row,6,dict['Cusine'])
			sheet.write(row,7,dict['Cost'])
			sheet.write(row,8,dict['Lat'])
			sheet.write(row,9,dict['Long'])
			
			for n,day in enumerate(Week):
				sheet.write(row,Add+n,dict[day])
	
			row+=1
	
	print 'Saving Excel File'
	book.save(ExcelFileName+'.xls')
	print 'Excel File Saved' 
	
	
if __name__=='__main__':
	FileDownloader(1,97,Folder)
	FileAnaylzer(Folder,RawJson)
	JsonUpdate(RawJson)
	PinCodeUpdater(AnalyzedJson)
	FileComparator()
	AllData=JsonList(AllDataFolder)
	ExcelWrite(AllData,ExcelFileName)
