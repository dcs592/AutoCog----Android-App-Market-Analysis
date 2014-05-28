#===============================#
#==# Import all dependencies #==#
#===============================#
import json, os, sys, math, operator
import numpy as np
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
data = json.load(json_data)
print("Number of Apps with Total Perm Data: " + str(len(data)))

#=============================================#
#==# Load Database of Application Metadata #==#
#=============================================#
filename = raw_input("Input path to DB of application metadata: ")
# filename = os.path.expanduser("autocog2.db")
db_data = sqlite3.connect(filename)
c = db_data.cursor()

#==============================================#
#==# Variables to Store Data During Parsing #==#
#==============================================#
totalapks = 0
totalfailed1 = 0
totalfailed2 = 0
ratings = dict()
categories = dict()
installs = dict()
price = dict()
votes = dict()

#===================================#
#==# Pull Metadata from Database #==#
#===================================#
for row in c.execute('SELECT apkname, rating, category, installs, price, votes FROM apps'):
	totalapks+= 1
	try: #get the questionable permissions from the JSON
		Q_perms = quest_perms[row[0] + '.apk']
	except: 
		totalfailed1+= 1
		continue

	try: #get the total permissions from the JSON
		T_perms = data[row[0] + '.apk']
	except:
		totalfailed2+= 1
		continue

	len_Q_perms = len(Q_perms) #length of the questionable permissions
	len_T_perms = len(T_perms) #length of the total permissions

	#if no rating, assign it to a 0.0 rating
	if row[1]=='':
		r = '0.0'
	else:
		r = row[1]
	#add the number of q_perms and t_perms to the relevant rating
	if r in ratings:
		ratings[r][0].append(len_Q_perms)
		ratings[r][1].append(len_T_perms)
	else:
		ratings[r] = [[len_Q_perms],[len_T_perms]]
	#add the number of q_perms and t_perms to the relevant category
	if row[2] in categories:
		categories[row[2]].append(len_Q_perms)
	else:
		categories[row[2]] = [len_Q_perms]
	#average the number of installations
	if '-' in row[3]:
		a, b = row[3].split('-')
		while ',' in a:
			a = a.replace(',', '')
		while ',' in b:
			b = b.replace(',', '')
		a, b = int(a), int(b)
		average = (a+b)/2
		#add the average number of installations to the dict
		if row[1] in installs:
			installs[row[1]].append(average)
		else:
			installs[row[1]] = [average]
	#add the price to the relevant rating
	if '$' in row[4]:
		cost = float(row[4][1:])
	else: 
		cost = float(row[4])
	if row[1] in price:
		price[row[1]].append(cost)
	else:
		price[row[1]] = [cost]

	#if no vote is recorded, change it to 0
	if (row[5]==''):
		vote = 0
	else:
		vote = int(row[5])
	#add the vote to the relevant rating
	if row[1] in votes:
		votes[row[1]].append(vote)
	else:
		votes[row[1]] = [vote]

print("Total Apps: " + str(totalapks))
print("Failed Questionable Perm Queries: " + str(totalfailed1))
print("Failed Total Perm Queries: " + str(totalfailed2))

#====================================#
#==# Print Data Regarding Ratings #==#
#====================================#
print("\n\nQUESTIONABLE PERMISSIONS AND INSTALLATIONS")
print("+--------+-----------+---------+--------------+-----------+--------------+---------+-------+-------------+")
print("| %6s | %9s | %7s | %12s | %9s | %12s | %7s | %5s | %11s |  " % 
	("Rating".center(6), #rating number
		"# Q-Perms".center(9), #average number of questionable permissions
		"# Perms".center(7), #average number of total permissions
		"Ave Installs".center(12), #average number of installations
		"Med Perms".center(9), #median number of questionable permissions
		"Med Installs".center(12), #median number of installations
		"Total #".center(7), #total number of available apps at this rating
		"Price".center(5), #average price per app at this rating
		"Votes".center(11))) #average number of votes for apps at this rating
print("+========+===========+=========+==============+===========+==============+=========+=======+=============+")
keys = ratings.keys()
keys.sort()

#iterate through the values in the dicts
for k in keys:
	#sort and calculate averages and median values
	ratings[k][0] = sorted(ratings[k][0])
	ratings[k][1] = sorted(ratings[k][1])
	installs[k] = sorted(installs[k])
	total = len(ratings[k][1])
	perm_ave = np.average(ratings[k][0])
	allp_ave = np.average(ratings[k][1])
	inst_ave = np.average(installs[k])
	perm_med = np.median(ratings[k])
	inst_med = np.median(ratings[k])
	ave_price = np.average(price[k])
	ave_votes = np.average(votes[k])

	print("| %6s | %9s | %7s | %12s | %9s | %12s | %7s | %5s | %11s | " % 
		(k.center(6), 
			("%.5f" % round(perm_ave,5)).center(9), 
			("%.4f" % round(allp_ave, 4)).center(7), 
			("%.4f" % round(inst_ave, 4)).center(12), 
			("%.5f" % round(perm_med, 5)).center(9), 
			("%.5f" % round(inst_med, 5)).center(12), 
			str(total).center(7), 
			("%.2f" % round(ave_price, 2)).center(5), 
			("%.5f" % round(ave_votes, 5)).center(11)))
	print("+--------+-----------+---------+--------------+-----------+--------------+---------+-------+-------------+")

print("\n\n")

#=======================================#
#==# Print Data Regarding Categories #==#
#=======================================#
print("QUESTIONABLE PERMISSIONS BY CATEGORY")
print("+-------------------+-------------+-------------+")
print("| %17s | %11s | %11s | " % 
	("Category".center(17), #app category
		"Ave # Perms".center(11), #average number of questionable permissions
		"Med # Perms".center(11))) #median number of questionable permissions
print("+===================+=============+=============+")

keys = categories.keys()
#iterate through the values in the dicts
for k in keys:
	#sort and calculate averages and median values
	temp = sorted(categories[k])
	ave = np.average(temp)
	med = np.median(temp)
	categories[k] = [ave, med]

categories = sorted(categories.iteritems(), key=operator.itemgetter(1))
for key, value in categories:
	print("| %17s | %11s | %11s | " % 
		(key.center(17), 
			("%.5f" % round(value[0], 5)).center(11), 
			str(value[1]).center(11)))
	print("+-------------------+-------------+-------------+")
print("\n\n")






