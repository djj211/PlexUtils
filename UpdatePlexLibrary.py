#!/usr/bin/python
from PlexUtils import PlexUtils

username = ""
password = ""
server = ""
port = ""
plexLibIds = ["" , ""]
updateAll = 1
useHttps = False

utils = PlexUtils(username, password, server, port, useHttps)

utils.logger.info("-------------------Starting Script " + __file__ + "--------------------")

utils.updateLibrary(plexLibIds, 0)

utils.logger.info("Script " + __file__ + " Complete")
