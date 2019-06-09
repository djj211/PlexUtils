from PlexUtils import PlexUtils

username = "" #Plex Account Username
password = "" #Plex Account Password
server = "" #Plex Server Address
port = "" #Plex Port
useHttps = False #Sepcify Whether to Use Https or Not
days = 30 #Days Passed After Watch Before Delete
library = "" #Library to Clean
skip = ["", ""] #Array of Show Titles that Should not be deleted. Matches name in plex.

#Get instance of Plextils
utils = PlexUtils(username, password, server, port, useHttps)

utils.logger.info("------------------- Starting Script " + __file__ + " --------------------")

#Call Clean Plex
utils.cleanPlex(days, library, skip)

utils.logger.info("Script " + __file__ + " Complete")
