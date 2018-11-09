import re
import os
import time
import subprocess
from lxml import etree
import xml.etree.ElementTree as xtree
import requests
import validators
import getpass
from urllib.parse import unquote
#written for WPI ingesting from URL
class UrlException(ValueError):
	pass
def get_file_name_from_url(url):
	match = re.search("[/][^/]+[/]$",url)
	if match:#Directory with / at the end
		start = match.start() +1
		end = match.end() -1
		fileName = url[start:end]
		fileName = unquote(fileName)
		return fileName
	match = re.search("[/][^/]+$",url)
	if match:
		start = match.start() +1
		end = match.end()
		fileName = url[start:end]
		fileName = unquote(fileName)
		return fileName
	raise ValueError('unable to figure anything out whatso ever {} '.format(url))

def grant_access(path,rights = '775'):
	this_user = getpass.getuser()
	subprocess.run(['sudo','chmod',rights,path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
	return subprocess.run(['sudo','chown',this_user,path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)


def download_file(url,dwnld_dir = None):
	""" if the given url is valid and we have access to the file attached to it. this funciton
	will download said file to the directory given or just put it in the current dir."""
	local_filename = get_file_name_from_url(url)
	if dwnld_dir is not None:
		if dwnld_dir[-1] == '/':
			local_filename = dwnld_dir+local_filename
		else:
			local_filename = dwnld_dir+'/'+local_filename
	else:# dwnld_dir is None
		dwnld_dir = '.'
	if not os.path.exists(dwnld_dir):
		mkdir(dwnld_dir,['-p'])#make directory and make all directories that dont exist on the way
	# NOTE the stream=True parameter
	while True:
		try:
			if not validators.url(url.replace('[','B').replace(']','Be')):
				raise UrlException('Invalid url: {}'.format(url))

			r = requests.get(url, stream =True)
			break
		except requests.exceptions.ConnectionError as e:
			print('i never give up\n',e,'\n',url)
			time.sleep(2)

	if 200 <= r.status_code <= 299:
		try:
			print('downloading file from {}'.format(url))
			with open(local_filename, 'wb') as f:
				for chunk in r.iter_content(chunk_size=1024):
					if chunk: # filter out keep-alive new chunks
						f.write(chunk)
						#f.flush() commented by recommendation from J.F.Sebastian
			file_size = os.path.getsize(local_filename)
			print('done downloading %s' % (local_filename),"file size:",file_size)

			if file_size == 0:
				raise
			return os.path.abspath(local_filename)
		except PermissionError as e:
			if dwnld_dir:
				print('granting access to file')

				if grant_access(dwnld_dir).returncode == 0:
					print('success')
					return download_file(url,dwnld_dir)

			raise
	print('failed to download file error:{}, {}'.format(r.status_code,url))
	text = ''
	if r.text is not None:
		if len(r.text)>= 100:
			text = r.text[:100]+'...'
		else:
			text = r.text
	raise UrlException('failed to download file.@{} code:{},body:{}'.format(url,r.status_code,text))

def mkdir(path,args = None):
	if args is None:
		args = []
	status = subprocess.run(['mkdir']+args+[path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
	if status.returncode == 0:
		return
	this_user = getpass.getuser()
	subprocess.run(['sudo','mkdir','-m','775']+args+[path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
	return subprocess.run(['sudo','chown',this_user,path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
