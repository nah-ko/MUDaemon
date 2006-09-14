#!/usr/bin/env python

# Multi-usage daemon
# This daemon can be used for file transfert, file conversion...

# $Id$

import sys, os, time, signal, socket
import Logger
from signal import SIGTERM
from signal import SIGHUP
from signal import SIGUSR1

'''This module is used to fork the current process into a daemon.
    Almost none of this is necessary (or advisable) if your daemon 
    is being started by inetd. In that case, stdin, stdout and stderr are 
    all set up for you to refer to the network connection, and the fork()s 
    and session manipulation should not be done (to avoid confusing inetd). 
    Only the chdir() and umask() steps remain as useful.
    References:
        UNIX Programming FAQ
            1.7 How do I get my program to act like a daemon?
                http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
    
        Advanced Programming in the Unix Environment
            W. Richard Stevens, 1992, Addison-Wesley, ISBN 0-201-56317-7.
    '''

# Global vars (default values)
ProgPath           = os.path.dirname(os.path.realpath(sys.argv[0]))
configuration_file = ProgPath + '/mudaemon.conf'
loglevel           = 'info'
pidfile            = '/tmp/daemon.pid'
polltime           = 10
listfile           = '/tmp/liste'
command            = ''

def stop(signum=0, frame=''):
    '''Stopping daemon
    '''

    log.debug('In stop function')
    #log.info('Stopping MuDaemon')
    try:
	pf  = file(pidfile,'r')
	pid = int(pf.read().strip())
	log.debug('pid : %d' % pid)
	pf.close()
    except IOError:
	pid = None
    if not pid:
	log.debug('No pid file')
        mess = "Could not stop, pid file '%s' missing.\n"
	sys.stderr.write(mess % pidfile)
	sys.exit(1)
    try:
        sys.stdout.write("Stopping daemon...\n")
	log.info('Stopping Mu-Daemon...')
	while 1:
	    # tentative d'arret avec SIGUSR1 au lieu
	    # de SIGTERM
	    os.kill(pid,SIGUSR1)
	    time.sleep(1)
    except OSError, err:
        err = str(err)
	if err.find("No such process") > 0:
	    log.debug('Remove pidfile %s' % pidfile )
	    os.remove(pidfile)
	    if 'stop' == action:
	        sys.exit(0)
	    action = 'start'
	    pid = None
	else:
	    print str(err)
	    sys.exit(1)

def reload(signum=0, frame=''):
    ''' Reload daemon
    '''

    log.info('Reloading MuDaemon...')
    read_conf()

def read_conf():
    ''' Reading configuration file
    '''

    import ConfigParser
    global configuration_file
    global loglevel, pidfile
    global polltime, listfile, command

    sys.stdout.write("Loading configuration file '%s'\n" \
			% configuration_file )
    sys.stdout.flush()

    # lecture du fichier de conf
    config = ConfigParser.ConfigParser()
    config.read(configuration_file)

    # recuperation des optionss
    pidfile  = config.get('LOG', 'pidfile')
    loglevel = config.get('LOG', 'loglevel')

    polltime = config.getint('GLOBAL', 'polltime')
    listfile = config.get('GLOBAL', 'listfile')
    command  = config.get('GLOBAL', 'command')

def process_file(file='/tmp/liste'):
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

def daemonize(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', pidfile=None, startmsg = 'started with pid %s'):
    '''This forks the current process into a daemon.
    The stdin, stdout, and stderr arguments are file names that
    will be opened and be used to replace the standard file descriptors
    in sys.stdin, sys.stdout, and sys.stderr.
    These arguments are optional and default to /dev/null.
    Note that stderr is opened unbuffered, so
    if it shares a file with stdout then interleaved output
    may not appear in the order that you expect.
    '''
    # Do first fork.
    try: 
        pid = os.fork() 
        if pid > 0:
            sys.exit(0) # Exit first parent.
    except OSError, e: 
        log.err ("fork #1 failed: (%d) %s" % (e.errno, e.strerror))
        sys.exit(1)
        
    # Decouple from parent environment.
    os.chdir("/") 
    os.umask(0) 
    os.setsid() 
    
    # Do second fork.
    try: 
        pid = os.fork() 
        if pid > 0:
            sys.exit(0) # Exit second parent.
    except OSError, e: 
        log.err ("fork #2 failed: (%d) %s" % (e.errno, e.strerror))
        sys.exit(1)
        
    # Now I am a daemon!
    
    # Open file descriptors and print start message
    if not stderr: stderr = stdout
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    pid = str(os.getpid())
    sys.stderr.write("\n%s\n" % startmsg % pid)
    if pidfile: file(pidfile,'w+').write("%s\n" % pid)

    # Redirect standard file descriptors.
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

def startstop(stdout='/dev/null', stderr=None, stdin='/dev/null', pidfile='pid.txt', startmsg = 'Started with pid %s' ):
    '''Start, stop restart and reload function.
    '''

    if len(sys.argv) > 1:
	action = sys.argv[1]
	try:
		pf  = file(pidfile,'r')
		pid = int(pf.read().strip())
		pf.close()
	except IOError:
		pid = None
	if 'reload' == action:
		sys.stdout.write("Reloading MUdaemon\n")
		sys.stdout.flush()
		if not pid:
			mess = "Could not reload, pid file '%s' missing\n"
			sys.stderr.write(mess % pidfile)
			sys.exit(1)
		os.kill(pid,SIGHUP)
		sys.exit(0)
	if 'stop' == action or 'restart' == action:
		if not pid:
			mess = "Could not stop, pid file '%s' missing.\n"
			sys.stderr.write(mess % pidfile)
			sys.exit(1)
		try:
			sys.stdout.write("Stopping daemon...\n")
			log.info('Stopping Mu-Daemon...')
			while 1:
				# tentative d'arret avec SIGUSR1 au lieu
				# de SIGTERM
				os.kill(pid,SIGUSR1)
				time.sleep(1)
		except OSError, err:
			err = str(err)
			if err.find("No such process") > 0:
				os.remove(pidfile)
				if 'stop' == action:
					sys.exit(0)
				action = 'start'
				pid = None
			else:
				print str(err)
				sys.exit(1)
	if 'start' == action:
		sys.stdout.write("MUdaemon starting \n")
		sys.stdout.flush()
		if pid:
			mess = "Start aborded since pid file '%s' exists.\n"
			sys.stderr.write(mess % pidfile)
			sys.exit(1)
		daemonize(stdout=stdout, stderr=stderr, stdin=stdin, pidfile=pidfile, startmsg=startmsg)
		return
    else:
	print "usage: %s start|stop|restart|reload" % sys.argv[0]
	sys.exit(2)

def main():
    '''This is the main function run by the daemon.
       This execute the "process_file" function waiting during
       "polltime" seconds.
    '''
    log.info ('Mu-Daemon started with pid %d' % os.getpid() )
    while 1:
	log.debug('Waiting... (%d sec)' % polltime)
        time.sleep(polltime)
	log.debug('Do process')
	process_file(listfile)
    
if __name__ == "__main__":
    processflag = 'yes'

    # Read config file and initialize logger
    read_conf()
    log = Logger.Logger(loglevel)

    # Reload configuration file if receiving a HUP signal
    signal.signal(signal.SIGHUP, reload)
    # Stop daemon if receiving a TERM signal
    signal.signal(signal.SIGTERM, stop)

    # Start/stop/restart and reload routine
    startstop(pidfile=pidfile)

    # Main code
    main()
