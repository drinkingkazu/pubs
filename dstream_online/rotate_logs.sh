#! /bin/bash

case `uname -n` in
    (*ubdaq-prod-near1*)
	echo Host is ubdaq-prod-near1, preparing to rotate logs
	;;
    (*)
	echo Script must be run on ubdaq-prod-near1!!!
	echo Exiting with extreme prejudice.
	exit 1
	;;
esac

case `whoami` in
    (uboonepro)
       echo Rotating PUBS logs into /datalocal/uboonepro/pubslog
	;;
    (*)
        echo This should only be used for uboonepro account!!!
	echo Exiting with extreme prejudice.
	exit 1
	;;
esac

dir=/home/uboonepro/pubs/log

# Rename log files above a minimum size.

logdir=/datalocal/uboonepro/pubslog/

now=`date +"%d_%m_%Y"`

find $dir -name \*.log | while read log
do
  s=`stat -c %s $log`
  if [ $s -gt 10000 ]; then
    dest=${logdir}`basename ${log}.${now}`
    mv -f ${log} ${dest}
    tar czf ${dest}.tgz ${dest}
    mkdir -p $logdir/log_$now
    if [ -e "${dest}.tgz" ] ; then
	mv ${dest}.tgz $logdir/log_$now
	rm -f ${dest}
	rm -f ${log}
    else
	echo "the tarball failed to be created!!!"
	exit 1
    fi
  fi
done

# Delete unused log files older than 30 days.

find $dir -name \*.log.\* -ctime +30 | while read log
do
  rm -f $log
done
