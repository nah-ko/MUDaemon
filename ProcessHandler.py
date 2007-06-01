#!/usr/bin/env python

class ProcessHandler:
	def __init__(self, log, options):
		self.log = log
		self.options = options

	def file(self, file="/tmp/file"):
		'''Lecture du fichier contenant la liste a envoyer sur l'autre machine
		'''

		import popen2
		global processflag, log

		log.debug ("in process_file (flag=%s)" % processflag)
		if processflag == 'no':
			log.err ("Processing already engaged ! :)")
		if os.path.exists(file) and processflag == 'yes':
			processflag = 'no'
			log.info ("Processing engaged ! :)")
			f = open(file,'r')
			for data in f.read().split('\n'):
				if data <> '':
					log.info ("Working on: %s" % data)
					cmd = command % data
					log.debug ("command=%s" % cmd)
					pout, pin, perr = popen2.popen3(cmd)
					OUT = pout.read()
					ERR = perr.read()
					log.debug ("out=%s err=%s" % (OUT, ERR))
					if not OUT == '':
						log.err ("%s" % OUT)
					if not ERR == '':
						log.err ("%s" % ERR)
			f.close()
			processflag = 'yes'
			os.remove(file)
		else:
			log.debug ("Nothing to do, sleeping")

	def directory(self, directory="/tmp/mudaemon"):
		'''Scan d'un repertoire en vue de l'execution d'une
		commande selon le fichier qui y sera depose
		'''

		import fnmatch, os, shutil, time, commands

		for Cle in Dico.keys():
			DicoSousCle = Dico.get(Cle)
			for SousCle in DicoSousCle.keys():
				#print "Cle: %s - SousCle: %s" % (Cle, SousCle)
				for F in fnmatch.filter(os.listdir(Rep2Depot), SousCle):
					Fichier     = Rep2Depot + F
					Dest        = Rep2Envoi + DicoSousCle.get(SousCle) + '.TXT'
					#print "Fichier: %s - Dest: %s" % (Fichier, Dest)
					TailleAvant = os.stat(Fichier).st_size
					time.sleep(3)
					TailleApres = os.stat(Fichier).st_size
					if TailleApres == TailleAvant:
						try:
							shutil.copy(Fichier, Dest)
						except (IOError, os.error), why:
							print "Can't copy %s to %s: %s" % (Fichier,\
								Dest, \
								str(why))
			
						Commande = "almacom -f %s -t %s" % \
							(Fichier, DicoSousCle.get(SousCle))
						Status, Output = commands.getstatusoutput(Commande)

						if Status == 0:
							Archives = Rep2Depot + 'archives/' +\
						   		Cle +'/'
							print "Archives: %s" % Archives
							try:
								shutil.move(Fichier, Archives)
							except (IOError, os.error), why:
								print "Can't copy %s to %s: %s" % (Fichier,\
									Archives, \
									str(why))
						else:
							print "Erreur: %s" % Output
