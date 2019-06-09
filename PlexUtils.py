import httplib, urllib, base64, json, urllib2, logging, requests, sqlite3, os
from xml.etree.ElementTree import XML, SubElement, Element, tostring

class PlexUtils:
	'Common Class for Plex Operations'
	version = "0.0.1"
	
	#Setup Logger and Handler
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)
	
	#Get Script Path so log is created in same dir a script when ran as cron
	logPath = os.path.dirname(os.path.realpath(__file__))
	
	handler = logging.FileHandler(logPath + '/PlexUtils.log')
	handler.setLevel(logging.INFO)

	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	handler.setFormatter(formatter)

	logger.addHandler(handler)

	def __init__(self, user, password, server, port, https):
		self.user = user
		self.password = password
		self.server = server
		self.port = port
		self.token = ""
		self.host = "http://" + self.server + ":" + str(self.port)
		if https:
			self.host = "https://" + self.server + ":" + str(self.port)

	def updateLibrary(self, ids, force):
		try:
			#Get or Set X-Plex-Token
			self.getToken()

			#Loop Over All Ids and update
			for id in ids:
				lib = id
				self.logger.info("Updating Plex Library: " + str(id))
				
				if isinstance(id, basestring):
					self.logger.info("Looking up id for library " + id)
					id = self.getLibId(id)
 	
				#Set URL
				url = self.host + "/library/sections/" + str(id) + "/refresh?force=" + str(force) + "&X-Plex-Token=" + self.token
				
				#Make Request
				r = requests.get(url)
				
				#Check for Successful Request. If Status Code is 200 and text is empty = Success
				if r.status_code != 200 and not r.text:
					self.logger.error("Error " + str(r.status_code) + " Update Plex Library From URL: " + url)
					self.logger.error(r.text)
					#Throw Exception if there is a Request Error
					raise Exception('Error Updating Library. Could Not Connect to: ' + url)
				else:
					#Log Success
					self.logger.info("Successfully Updated Libary: " + str(id))
		

		except Exception as err:
			#Log Exception
			self.logger.exception(err)

        def cleanPlex(self, days, library, exempts):
		
		conn = None

                try:
	
			#Query to find watched shows
                        query = """ SELECT metadata_items.title, media_parts.file, library_sections.id, accounts.id, accounts.name, metadata_item_settings.view_count, metadata_item_settings.last_viewed_at
                                    FROM metadata_item_settings
                                    JOIN accounts
                                    ON metadata_item_settings.account_id = accounts.id
                                    JOIN metadata_items
                                    ON metadata_item_settings.guid = metadata_items.guid
                                    JOIN media_items
                                    ON  metadata_items.id = media_items.metadata_item_id
                                    JOIN media_parts
                                    ON media_items.id = media_parts.media_item_id
                                    JOIN library_sections
                                    ON media_items.library_section_id = library_sections.id
                                    WHERE metadata_item_settings.view_count > 0 AND library_sections.name = '{library}' AND metadata_item_settings.last_viewed_at <= date('now','-{days} day')"""

                        exempt = ""
			
			self.logger.info("Constructing Query")
			self.logger.info("Looking Up Skipped Shows")
			#Loop Over Exempt shows and build exempt query part
                        for show in exempts:
                                self.logger.info("Show " + show + " marked as skip from deletion. Adding to Query to exclude")
                                #Add Skip to Query
				exempt = exempt + " AND hints NOT LIKE '%{show}%'".format(show=show)
			
			#String Replace Variables AND add exemtpion to the query
			query = query.format(library=library, days=str(days)) + exempt

			self.logger.info("Query Constructed")
                        self.logger.info("Opening Plex SQLite Database")

                        dbFile = "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db"

			#Open SQLite Connection
                        conn = sqlite3.connect(dbFile)
        		
		        c = conn.cursor()
			#Execute
			c.execute(query)
			
			self.logger.info("Getting Watched Shows From the Last " + str(days) + " days")

			#Get Rows
			rows = c.fetchall()
			
			#Check if there are any files to delete
			if not rows:
				self.logger.info("No Shows Watched in Last " + str(days))
			else:
	                        self.logger.info("Deleting Watched Shows From the Last " + str(days) + " days")

	                        #Declare Library for update
	                        libId = ""

				#Loop Over All the Watched TV Rows
				for row in rows:
					episodeFile = row[1]
					#Check if is File or Directory...Delete Appropiately
					if os.path.isdir(episodeFile):
						self.logger.info("This is a Directory! Deleting Watched Directory: " + episodeFile)
						#Delete the Directory and it's Contents
						shutil.rmtree(episodeFile)
					else:
						self.logger.info("Deleting Watched File: " + episodeFile)
						#Delete The File
						os.remove(episodeFile)
				
					self.logger.info("Delete Successful")				

					#Set Library ID For Update Library Refresh Call				
					libId = row[2]
			
				#Refresh Library After Delete
				self.updateLibrary(str(libId), 1)

                except Exception as err:
                        #Log Exception
                        self.logger.info("Error Cleaning Plex Watched Shows")
			self.logger.exception(err)

		finally:
			if conn:
				conn.close()

	def getLibId(self, library):
                try:
                        #Get or Set X-Plex-Token
                        self.getToken()

                        #Loop Over All Ids and update

                        self.logger.info("Getting id for Plex Library: " + library)

                        #Set URL
                        url = self.host + "/library/sections?X-Plex-Token=" + self.token

                        #Make Request
                        r = requests.get(url)

			id = None

                        #Check for Successful Request. If Status Code is 200 and text is empty = Success
                        if r.status_code != 200:
	                        self.logger.error("Error " + str(r.status_code) + " Getting  Plex Library From URL: " + url)
                                self.logger.error(r.text)
                                #Throw Exception if there is a Request Error
                                raise Exception('Error Getting Library. Could Not Connect to: ' + url)
                        else:
				
				elem = XML(r.text)
				
				tvNode = elem.find('.//Directory[@title="{library}"]'.format(library=library))
				if tvNode is None:
					raise Exception("Error Could Not find Library: " + library)
				else:
					id = tvNode.attrib['key']
                	        	#Log Success
        	                        self.logger.info("Successfully Got Libary: id: " + str(id))
			
			return id

                except Exception as err:
                        #Log Exception
                        self.logger.exception(err)
		

	def getToken(self):
		if not self.token:
			self.logger.info("Getting Plex X-Plex-Token for user: " + self.user)
		
			#Encode username and password
			base64string = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n', '')
			txdata = ""
		
			#Set Headers
			headers={'Authorization': "Basic %s" % base64string,
							'X-Plex-Client-Identifier': "PlexUtils",
							'X-Plex-Product': "PlexUtils 01282016",
							'X-Plex-Version': PlexUtils.version}
		
			#Create Connection
			conn = httplib.HTTPSConnection("plex.tv")
			#Make Request
			conn.request("POST","/users/sign_in.json",txdata,headers)
		
			#Get Response
			response = conn.getresponse()
		
			#Check if request was success. Response Status 201 = Success
			if response.status != 201:
				#Log Error
				self.logger.error("Error " + str(response.status) + " Getting Plex Token")
				self.logger.error(response.reason)
				#Throw Exception
				raise Exception('Could Not Get Token')
			else:
				#Read Json to get token
				data = response.read()
				resp_dict = json.loads(data)
				self.token = resp_dict['user']['authToken']
				#Log Success
				self.logger.info("Token set successfully " + str(response.status))
				self.logger.info("New Token: " + self.token)
		
			#Cose Connection
			conn.close()
		else:
			self.logger.info("Plex Token Already Set: " + self.token + "...Continuing")

