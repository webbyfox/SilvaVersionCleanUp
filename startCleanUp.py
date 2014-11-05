from Products.SilvaVersionCleanUp.VersionCleanUp import VersionCleanUp

def startCleanUp(self, max_age, number_to_keep=None, pub_path=None):
        '''
        Starts the clean up of old versions of Silva documents External Method.
        '''
        vcup = VersionCleanUp('cleanup',max_age, number_to_keep, pub_path)

        path = self.restrictedTraverse(pub_path)
       	vcup.start_scan(path,-1)
       	return "Version Control finish at: " + str(pub_path)