import praw
import re
import time
from datetime import datetime
from threading import Timer
import string
import signal, sys
import json
import gspread
from oauth2client.client import SignedJwtAssertionCredentials

#This is required to log in to google docs
json_key = json.load(open('AGOTLCGLogin-b0a177aff2e3.json')) 
scope = ['https://spreadsheets.google.com/feeds']
credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'], scope)

#This is required to log in to reddit; password omitted for security
USERNAME = "AGOTLCGbot"
PASSWORD = "PASSWORD"
USERAGENT = "AGOTLCGbot v1.0! by /u/dios_achilleus"

r = praw.Reddit(USERAGENT)
r.login(USERNAME,PASSWORD,disable_warning=True)

#initialize global variable for spreadsheet
row_number = 1
column_number = 1

#This ensures that the bot will only search the subreddit listed
subreddit = r.get_subreddit('agameofthroneslcg')

#This copies reddit comments into a doc to parse
already_done = []
with open('agotlcg_done.txt', 'r') as f:
	for i in f:
		already_done.append(i.replace("\n", ""))


def bot_comments():
	ids = []
	sub_comments = subreddit.get_comments()
	for comment in sub_comments:
		ids.append(comment.id)
		if comment.id not in already_done and not str(comment.author) == USERNAME:
			cards = re.findall("\[\[([^\[\]]*)\]\]", comment.body) #cards is when titles have [[]] around them; prints link to pic and card text
			pics = re.findall("\(\(([^\(\)]*)\)\)", comment.body) #pics is when titles have (()) around them; prints link to pic
			cardlist = cards + pics
			reply = ""
			if len(cardlist) > 30: cardlist = cardlist[0,30]
			for i in set(pics):
				print i 
				i = i.split('/')[0]
				i = string.capwords(i) #capitalizes all words to prevent search errors 
				
				# Checks if a card exists
				card_id = card_check(i)
				if card_id:
					gc = gspread.authorize(credentials)
					worksheet = gc.open('AGOTLCG Cards').sheet1
					cell = worksheet.find('%s' % i)
					row_number = cell.row
					column_number = cell.col
					card_number = row_number - 1

          				# Builds the post
					reply += "[%s](http://ThronesDB.com/card/%s%s)\n\n" % (worksheet.cell(row_number, 3).value, worksheet.cell(row_number, 1).value, worksheet.cell(row_number, 2).value)
				else: reply += "I cannot find %s \n\n" % i
			for i in set(cards):
				print i 
				i = i.split('/')[0]
				i = string.capwords(i)
				
				# Checks if a card exists
				card_id = card_check(i)
				if card_id:
					gc = gspread.authorize(credentials)
					worksheet = gc.open('AGOTLCG Cards').sheet1
					cell = worksheet.find('%s' % i)
					row_number = cell.row
					column_number = cell.col
					card_number = row_number - 1

        				  # Builds the post
					if (worksheet.cell(row_number, 4).value) == 'Plot':
						reply += "[%s](http://ThronesDB.com/card/%s%s)\n\n" % (worksheet.cell(row_number, 3).value, worksheet.cell(row_number, 1).value, worksheet.cell(row_number, 2).value)
						reply += "Type: %s, " % (worksheet.cell(row_number, 4).value)
						reply += "Gold: %s, " % (worksheet.cell(row_number, 6).value)
						reply += "Initiative: %s, " % (worksheet.cell(row_number, 7).value)
						reply += "Claim: %s, " % (worksheet.cell(row_number, 8).value)
						reply += "Reserve: %s \n\n" % (worksheet.cell(row_number, 9).value)
						reply += "Text: %s \n\n" % (worksheet.cell(row_number, 12).value)
					elif (worksheet.cell(row_number, 4).value) == 'Character':
						reply += "[%s](http://ThronesDB.com/card/%s%s)\n\n" % (worksheet.cell(row_number, 3).value, worksheet.cell(row_number, 1).value, worksheet.cell(row_number, 2).value)
						reply += "Type: %s %s, " % ((worksheet.cell(row_number, 5).value), (worksheet.cell(row_number, 4).value))
						reply += "Gold: %s, " % (worksheet.cell(row_number, 6).value)
						reply += "Strength: %s, " % (worksheet.cell(row_number, 7).value)
						reply += "Icons: %s" % (worksheet.cell(row_number, 10).value)
						if (worksheet.cell(row_number, 11).value) == 'Y':
							reply += ", Loyal: Yes \n\n"
						else:
							reply += "\n\n"
						reply += "Text: %s \n\n" % (worksheet.cell(row_number, 12).value)
					elif (worksheet.cell(row_number, 4).value) == 'Agenda':
						reply += "[%s](http://ThronesDB.com/card/%s%s)\n\n" % (worksheet.cell(row_number, 3).value, worksheet.cell(row_number, 1).value, worksheet.cell(row_number, 2).value)
						reply += "Type: %s" % (worksheet.cell(row_number, 4).value)
						if (worksheet.cell(row_number, 11).value) == 'Y':
							reply += ", Loyal: Yes \n\n"
						else:
							reply += "\n\n"
						reply += "Text: %s \n\n" % (worksheet.cell(row_number, 12).value)
					else:
						reply += "[%s](http://ThronesDB.com/card/%s%s)\n\n" % (worksheet.cell(row_number, 3).value, worksheet.cell(row_number, 1).value, worksheet.cell(row_number, 2).value)
						reply += "Type: %s %s, " % ((worksheet.cell(row_number, 5).value), (worksheet.cell(row_number, 4).value))
						reply += "Gold: %s" % (worksheet.cell(row_number, 6).value)
						if (worksheet.cell(row_number, 11).value) == 'Y':
							reply += ", Loyal: Yes \n\n"
						else:
							reply += "\n\n"
						reply += "Text: %s \n\n" % (worksheet.cell(row_number, 12).value)
				else: reply += "I cannot find %s \n\n" % i
			if reply:
				reply += "&nbsp; \n\n ^^Am ^^I ^^drinking ^^too ^^much ^^milk ^^of ^^the ^^poppy? ^^Message ^^/u/dios_achilleus"
				# Posting might fail (too long, ban, reddit down etc), so cancel the post and print the error
				try:
					comment.reply(reply)
				except Exception,e: print str(e)
			# Add the post to the list of parsed comments
			already_done.append(comment.id)
	# Finally, return the list of parsed comments (seperate from already_done)
	return ids
    
    
# Function that checks if the requested card exists and returns the database row it's found on
def card_check(card):
	try:
		gc = gspread.authorize(credentials)
		worksheet = gc.open('AGOTLCG Cards').sheet1
		cell = worksheet.find('%s' % card)
		return cell.row
	except gspread.exceptions.CellNotFound:
		print "ERROR"
		return False

    
    
    
# Function that backs up current parsed comments
def write_done():
	with open("agotlcg_done.txt", "w") as f:
		for i in already_done:
			f.write(str(i) + '\n')
            
            
# Function that is called when ctrl-c is pressed. It backups the current parsed comments into a backup file and then quits.
def signal_handler(signal, frame):
	write_done()
	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)



# Infinite loop that calls the function. The function outputs the post-ID's of all parsed comments.
# The ID's of parsed comments is compared with the already parsed comments so the list stays clean
# and memory is not increased. It sleeps for 4 minutes to wait for new posts.
while True:
	ids = bot_comments()
	time.sleep(15)
	new_done = []
	# Checks for both comments and submissions
	for i in already_done:
		if i in ids:
			new_done.append(i)
	already_done = new_done[:]
	# Back up the parsed comments to a file
	write_done()
	time.sleep(210)
