#!/usr/bin/env python

# Multi-usage daemon
# This daemon can be used for file transfert, file conversion...

# $Id$

import sys, os, time, signal, socket
from signal import SIGTERM
from signal import SIGHUP

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
configuration_file = 'mudaemon.conf'
errorlog = '/tmp/daemon.log'
infolog = '/tmp/daemon.log'
pidfile = '/tmp/daemon.pid'
debug = 'false'
polltime = 10
listefile = '/tmp/liste'
command = ''

def dolog(message):
	'''Turning log formating into standard way
	'''

	# Vars
	global pidfile

	# Get pid
	pf  = file(pidfile,'r')
	pid = int(pf.read().strip())

	# Log format: [Short day] [Numeric day] [Time] [Hostname] [Service[Pid]] : [Message]
	Time = time.strftime("%b %d %H:%M:%S", time.localtime())
	Hostname = socket.gethostname()
	Service = os.path.basename(sys.argv[0])
	Pid = pid
	Message = message

	# Log
	logline = "%s %s %s[%d] : %s" % (Time, Hostname, Service, Pid, Message)

	return logline


def read_conf(signum=0, frame=''):
    ''' Reading configuration file
    '''

    import ConfigParser
    global configuration_file
    global errorlog, infolog, pidfile, debug
    global polltime, listefile, command, rhost, ruser, rpath

    if debug == 'true':
    	sys.stdout.write(dolog("Loading configuration file...\n"))
	sys.stdout.flush()

    # lecture du fichier de conf
    config = ConfigParser.ConfigParser()
    config.read(configuration_file)

    # recuperation des optionss
    for section in config.sections():
    	if section == 'LOG':
		for option in config.options(section):
			if option == 'errorlog':
				errorlog = config.get(section,option)
			elif option == 'infolog':
				infolog = config.get(section, option)
			elif option == 'pidfile':
				pidfile = config.get(section, option)
			elif option == 'debug':
				debug = config.get(section, option)
	elif section == 'GLOBAL':
		for option in config.options(section):
			if option == 'polltime':
				polltime = int(config.get(section, option))
			elif option == 'listefile':
				listefile = config.get(section, option)
			elif option == 'command':
				command = config.get(section, option)

def process_file(file='/tmp/liste'):
    '''Lecture du fichier contenant la liste a envoyer sur l'autre machine
    '''

    import popen2
    global processflag, debug

    if debug == 'true':
    	sys.stderr.write(dolog("DEBUG : process_file (flag=%s)\n" % processflag))
	sys.stderr.flush()
    if processflag == 'no':
    	sys.stderr.write(dolog("ERROR : Processing already engaged ! :)\n"))
	sys.stderr.flush()
    if os.path.exists(file) and processflag == 'yes':
	    processflag = 'no'
            sys.stdout.write(dolog("INFO : Processing engaged ! :)\n"))
	    sys.stdout.flush()
	    f = open(file,'r')
	    for data in f.read().split('\n'):
		    if data <> '':
			    sys.stdout.write(dolog("Working on: \"%s\"\n" % data))
			    sys.stdout.flush()
			    cmd = command % data
			    if debug == 'true':
			    	sys.stdout.write(dolog("DEBUG : command=%s\n" % cmd))
				sys.stdout.flush()
			    pout, pin, perr = popen2.popen3(cmd)
			    OUT = pout.read()
			    ERR = perr.read()
			    if debug == 'true':
			    	sys.stdout.write(dolog("DEBUG : out=%s err=%s\n" % (OUT, ERR)))
				sys.stdout.flush()
			    if not OUT == '':
			    	sys.stdout.write(dolog("INFO : \"%s\"\n" % OUT))
			    	sys.stdout.flush()
			    if not ERR == '':
			    	sys.stderr.write(dolog("ERROR : \"%s\"\n" % ERR))
			    	sys.stderr.flush()
	    f.close()
	    processflag = 'yes'
	    os.remove(file)
    else:
    	sys.stdout.write(dolog("Nothing to do, sleeping\n"))
	sys.stdout.flush()

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
        sys.stderr.write ("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror)    )
	sys.stderr.flush()
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
        sys.stderr.write ("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror)    )
	sys.stderr.flush()
        sys.exit(1)
        
    # Now I am a daemon!
    
    # Open file descriptors and print start message
    if not stderr: stderr = stdout
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    pid = str(os.getpid())
    sys.stderr.write("\n%s\n" % startmsg % pid)
    sys.stderr.flush()
    if pidfile: file(pidfile,'w+').write("%s\n" % pid)

    # Redirect standard file descriptors.
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

def startstop(stdout='/dev/null', stderr=None, stdin='/dev/null', pidfile='pid.txt', startmsg = 'Started with pid %s' ):
	if len(sys.argv) > 1:
		action = sys.argv[1]
		try:
			pf  = file(pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
		if 'reload' == action:
			if not pid:
				mess = "Could not reload, pid file '%s' missing\n"
				sys.stderr.write(mess % pidfile)
				sys.stderr.flush()
				sys.exit(1)
			os.kill(pid,SIGHUP)
			sys.exit(0)
		if 'stop' == action or 'restart' == action:
			if not pid:
				mess = "Could not stop, pid file '%s' missing.\n"
				sys.stderr.write(mess % pidfile)
				sys.stderr.flush()
				sys.exit(1)
			try:
				sys.stdout.write("Stopping daemon...\n")
				sys.stdout.flush()
				while 1:
					os.kill(pid,SIGTERM)
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
			if pid:
				mess = "Start aborded since pid file '%s' exists.\n"
				sys.stderr.write(mess % pidfile)
				sys.stderr.flush()
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
    sys.stdout.write ('Daemon started with pid %d\n' % os.getpid() )
    sys.stdout.write ('Daemon stdout output\n')
    sys.stdout.flush()
    sys.stderr.write ('Daemon stderr output\n')
    sys.stderr.flush()
    while 1:
	if debug == 'true':
		sys.stderr.write(dolog('DEBUG : Wainting (%d sec)\n' % polltime))
		sys.stderr.flush()
        time.sleep(polltime)
	if debug == 'true':
		sys.stderr.write(dolog('DEBUG : Do process\n'))
		sys.stderr.flush()
	process_file(listefile)
    
if __name__ == "__main__":
    processflag = 'yes'
    read_conf()

    # Reload configuration file if receiving a HUP signal
    signal.signal(signal.SIGHUP, read_conf)

    # Start/stop/restart and reload routine
    startstop(stdout=infolog, stderr=errorlog, pidfile=pidfile)

    # Main code
    main()
