#===============================#
#==# Import all dependencies #==#
#===============================#
import json, os, sys, math, re
import numpy as np
from operator import itemgetter
import sqlite3
from StringIO import StringIO
from pprint import pprint
import urllib2

#=================================================#
#==# Load Application Questionable Permissions #==#
#=================================================#
filename = raw_input("Input path to JSON of application TOTAL permissions: ")
#filename = os.path.expanduser("~/Documents/Northwestern/Spring14/EECS450/allquestdict2.json")
json_data = open(filename)
quest_perms = json.load(json_data)
print("\n\nNumber of Apps with Questionable Perm Data: " + str(len(quest_perms)))

#==========================================#
#==# Load Application Total Permissions #==#
#==========================================#
filename = raw_input("Input path to JSON of application QUESTIONABLE permissions: ")
#filename = os.path.expanduser("~/Documents/Northwestern/Spring14/EECS450/all_permdict2.json")
json_data = open(filename)
all_perms = json.load(json_data)
print("Number of Apps with Total Perm Data: " + str(len(all_perms)))

#=============================================#
#==# Load Database of Application Metadata #==#
#=============================================#
filename = raw_input("Input path to DB of application metadata: ")
#filename = os.path.expanduser("autocog2.db")
db_data = sqlite3.connect(filename)
c = db_data.cursor()

#==============================================#
#==# Variables to Store Data During Parsing #==#
#==============================================#
devs = dict()
total_fail1 = 0
total_fail2 = 0

#===================================#
#==# Pull Metadata from Database #==#
#===================================#
for row in c.execute('SELECT apkname, category, developer, more_from_developer, rating FROM apps'):
	apkname = row[0]
	category = row[1]
	developer = row[2]
	more_apps = row[3]
	rating = row[4]

	#get the autocog output matching this application
	try: 
		perms_list = quest_perms[row[0] + '.apk']
	except:
		total_fail1+= 1
		continue
	try:
		all_list = all_perms[row[0] + '.apk']
	except:
		total_fail2+= 1
		continue

	#add the developer to the developer dict
	if not developer in devs:
		devs[developer] = dict()
		devs[developer]['count'] = 1
		devs[developer]['ratings'] = dict()
		devs[developer]['categories'] = dict()
		devs[developer]['qperms'] = dict()
		devs[developer]['all_perms'] = dict()
		devs[developer]['all_perms_list'] = dict()
	else :
		devs[developer]['count']+= 1 #increment the count

	#increment the rating count for a developer's rating
	if rating in devs[developer]['ratings']:
		devs[developer]['ratings'][rating]+= 1
	else:
		devs[developer]['ratings'][rating] = 1
	#increment the category count for the developer's category
	if category in devs[developer]['categories']:
		devs[developer]['categories'][category]+= 1
	else:
		devs[developer]['categories'][category] = 1
	#increment the number of times each questionable permission was used by the developer
	for p in perms_list:
		if p in devs[developer]['qperms']:
			devs[developer]['qperms'][p]+= 1
		else:
			devs[developer]['qperms'][p] = 1
	#increment the number of times each permission was used by the developer
	for p in all_list:
		if p in devs[developer]['all_perms']:
			devs[developer]['all_perms'][p]+= 1
		else:
			devs[developer]['all_perms'][p] = 1
	#increment the number of times the same permission set was used by the developer in all apps
	plist = ""
	for item in all_list:
		plist+= item + '.' #make a string of the permission set
	if plist in devs[developer]['all_perms_list']:
		devs[developer]['all_perms_list'][plist]+= 1
	else:
		devs[developer]['all_perms_list'][plist] = 1

#==============================================#
#==# Variables to Store Data During Parsing #==#
#==============================================#
i = 0
num = len(devs)
num_mult = 0
match_num = 0
close_match = 0
most_perms = dict()
wes_perms = 0
all_same_perms = 0
nearly_same_perms = 0
same_categories = 0
same_ratings = 0
total_matching_perms = 0

#iterate through the dict of developers
for d in devs:
	#narrow the scope to developers with more than one app in the database
	if devs[d]['count'] > 1:
		num_mult+= 1 #increment the number of developers being parsed
		#if the developer used questionable permissions
		if devs[d]['qperms']:
			#get the highest instance of questionable permissions
			max_perm = max(devs[d]['qperms'], key=devs[d]['qperms'].get)
			#if the number of q_perms == number of apps created
			if devs[d]['count']==devs[d]['qperms'][max_perm]:
				match_num+= 1 #increment the number of developers using q_perms in every app
			#if the number of q_perms == number of apps created - 1
			elif devs[d]['count']-1==devs[d]['qperms'][max_perm]:
				close_match+= 1 #increment the number of developers using q_perms in all but one app
			#if the developers q_perm was the most requested q_perm (in all applications created) in database
			if max_perm in most_perms:
				most_perms[max_perm]+= 1
			else:
				most_perms[max_perm] = 1
			#if the most common q_perm was used at all
			if 'WRITE_EXTERNAL_STORAGE' in devs[d]['qperms']:
				wes_perms+= 1
		#if the developer didn't use questionable permissions
		else:
			if devs[d]['count'] == 0:
				match_num+= 1
		#if the developer used permissions
		if devs[d]['all_perms']:
			max_a_perm = max(devs[d]['all_perms'], key=devs[d]['all_perms'].get)
			#if the developer used the same permission in all applications
			if devs[d]['count']==devs[d]['all_perms'][max_a_perm]:
				total_matching_perms+=1
		#if the developer used any set of permissions in all apps
		if devs[d]['all_perms_list']:
			#get the most commonly used set of permissions
			max_same_perms = max(devs[d]['all_perms_list'], key=devs[d]['all_perms_list'].get)
			#if the developer used this set of permissions in all apps
			if devs[d]['count']==devs[d]['all_perms_list'][max_same_perms]:
				all_same_perms+= 1 #increment
			#if the developer used this set of permissions in all but one app
			elif devs[d]['count']==devs[d]['all_perms_list'][max_same_perms]+1:
				nearly_same_perms+= 1 #increment
		#if the developer has listed categories
		if devs[d]['categories']:
			#get the most commonly used category
			max_same_cat = max(devs[d]['categories'], key=devs[d]['categories'].get)
			#if the developer created apps all in the same category
			if devs[d]['categories'][max_same_cat]==devs[d]['count']:
				same_categories+= 1 #increment
		#if the developer has ratings listed
		if devs[d]['ratings']:
			#get the most common rating
			max_rating = max(devs[d]['ratings'], key=devs[d]['ratings'].get)
			checker = True
			#check if all of the developer's apps have a rating in a .2 bound of the most common rating
			for r in devs[d]['ratings']:
				if abs(float(max_rating)-float(r))>.2:
					checker = False
					break
			if checker==True:
				same_ratings+= 1 #increment the number of developers with this narrow span of ratings

print("\n\t+----------------------------------------+-------------------------------------+")
print("\t| %38s | %35s | " % 
	("Number of Devs".center(38), #number of developers
		str(num).center(35)))
print("\t+----------------------------------------+-------------------------------------+")
print("\t| %38s | %35s | " % 
	("Dev's w/ Multiple Apps".center(38), #number of developers with multiple apps in database
		str(num_mult).center(35)))
print("\t+----------------------------------------+-------------------------------------+")
print("\t| %38s | %35s | " % 
	("Matching # Perms".center(38), #number of developers using the same q_perm in every app
		str(match_num).center(35)))
print("\t+----------------------------------------+-------------------------------------+")
print("\t| %38s | %35s | " % 
	("-1 Matching Perms".center(38), #number of developers using same q_perm in all but one app
		str(close_match).center(35)))
print("\t+========================================+=====================================+")
print("\t+========================================+=====================================+")
print("\t| %38s | %35s | " % 
	("All Same Perms".center(38), #number of developers using the same set of permissions in every app
		str(all_same_perms).center(35)))
print("\t+----------------------------------------+-------------------------------------+")
print("\t| %38s | %35s | " % 
	("-1 Same Perms".center(38), #number of developers using the same set of permissions in all but one app
		str(nearly_same_perms).center(35)))
print("\t+----------------------------------------+-------------------------------------+")
print("\t| %38s | %35s | " % 
	("Single Category".center(38), #number of developers creating all apps of the same category
		str(same_categories).center(35)))
print("\t+----------------------------------------+-------------------------------------+")
print("\t| %38s | %35s | " % 
	("Same Rating".center(38), #number of developers creating apps with ratings within a .4 span
		str(same_ratings).center(35)))
print("\t+========================================+=====================================+")
print("\t+========================================+=====================================+")
print("\t| %38s | %35s | " % 
	("Same Perm in All Apps".center(38), #number of developers using the same permissions in all apps
		str(total_matching_perms).center(35)))
print("\t+----------------------------------------+-------------------------------------+")
max_perm = max(most_perms, key=most_perms.get)
print("\t| %38s | %35s | " % 
	("Most Requested Permission".center(38), #most commonly requested q_perm
		(max_perm+" ("+str(most_perms[max_perm])+")").center(35)))
print("\t+----------------------------------------+-------------------------------------+")
print("\t| %38s | %35s | " % 
	("Total Using Most Requested".center(38), #number of developers using the most common q_perm
		str(wes_perms).center(35)))
print("\t+----------------------------------------+-------------------------------------+")
del most_perms[max_perm]
max_perm = max(most_perms, key=most_perms.get)
print("\t| %38s | %35s | " % 
	("2nd Most Requested Perm".center(38), #second most commonly requested q_perm
		(max_perm+" ("+str(most_perms[max_perm])+")").center(35)))
print("\t+----------------------------------------+-------------------------------------+")
del most_perms[max_perm]
max_perm = max(most_perms, key=most_perms.get)
print("\t| %38s | %35s | " % 
	("3rd Most Requested Perm".center(38), #third most commonly requested q_perm
		(max_perm+" ("+str(most_perms[max_perm])+")").center(35)))
print("\t+----------------------------------------+-------------------------------------+\n\n")











