#!/usr/bin/env python
import sys, os, time, signal
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
errorlog = '/tmp/daemon.log'
infolog = '/tmp/daemon.log'
pidfile = '/tmp/daemon.pid'
debug = 'false'
polltime = 10
listefile = '/tmp/liste'
command = ''

def read_conf(signum=0, frame=''):
    ''' Lecture du fichier de configuration
    '''

    import ConfigParser
    global configuration_file
    global errorlog, infolog, pidfile, debug
    global polltime, listefile, command, rhost, ruser, rpath

    if debug == 'true': sys.stdout.write("Loading configuration file...\n")

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

    if debug == 'true': sys.stderr.write("DEBUG : process_file (flag=%s)\n" % processflag)
    if processflag == 'no' : sys.stderr.write("ERROR : Processing already engaged ! :)\n")
    if os.path.exists(file) and processflag == 'yes':
	    processflag = 'no'
            sys.stdout.write("INFO : Processing engaged ! :)\n")
	    i = 0
	    f = open(file,'r')
	    data = f.read().split('\n')
	    i = len(data)
	    while 0 < i:
		    i -= 1
		    if data[0] <> '':
			    sys.stdout.write("Sending \"%s\"\n" % data[0])
			    cmd = command % data[0]
			    if debug == 'true': sys.stdout.write("DEBUG : command=%s" % cmd)
			    pout, pin, perr = popen2.popen3(cmd)
			    OUT = pout.read()
			    ERR = perr.read()
			    if debug == 'true': sys.stdout.write("DEBUG : out=%s err=%s\n" % (OUT, ERR))
			    if not OUT == '': sys.stdout.write("INFO : \"%s\"\n" % OUT)
			    if not ERR == '': sys.stderr.write("ERROR : \"%s\"\n" % ERR)
			    sys.stdout.flush()
			    sys.stderr.flush()
		    del data[0]
	    f.close()
	    processflag = 'yes'
	    os.remove(file)


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
				sys.exit(1)
			daemonize(stdout=stdout, stderr=stderr, stdin=stdin, pidfile=pidfile, startmsg=startmsg)
			return
	else:
		print "usage: %s start|stop|restart|reload" % sys.argv[0]
		sys.exit(2)

def main():
    '''This is an example main function run by the daemon.
       This prints a count and timestamp once per second.
    '''
    sys.stdout.write ('Daemon started with pid %d\n' % os.getpid() )
    sys.stdout.write ('Daemon stdout output\n')
    sys.stderr.write ('Daemon stderr output\n')
    c = 0
    while 1:
        sys.stdout.write ('%d: %s\n' % (c, time.ctime(time.time())) )
        sys.stdout.flush()
        c = c + 1
	if debug == 'true': sys.stderr.write ('DEBUG : Wainting (%d sec)\n' % polltime)
        time.sleep(polltime)
	if debug == 'true': sys.stderr.write ('DEBUG : Do process\n')
	process_file(listefile)
    
if __name__ == "__main__":
    processflag = 'yes'
    configuration_file = '/usr2/tools/mudaemon/mudaemon.conf'
    read_conf()

    # Reload configuration file if receiving a HUP signal
    signal.signal(signal.SIGHUP, read_conf)

    # Start/stop/restart and reload routine
    startstop(stdout=infolog, stderr=errorlog, pidfile=pidfile)

    # Main code
    main()
