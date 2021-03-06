#!/usr/bin/env bash

# If PUB_TOP_DIR not set, try to guess
if [[ -z $PUB_TOP_DIR ]]; then
    # Find the location of this script:
    me="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    # Find the directory one above.
    export PUB_TOP_DIR="$( cd "$( dirname "$me" )" && pwd )"
fi

case `whoami` in
    (uboonepro)
        echo Setting up PUBS for uboonepro account...
	;;
    (*)
        echo This should only be used for uboonepro account!!!
	echo Exiting with exterme prejudice.
	return 1
	;;
esac


#
# PSQL configuration
#
export PGOPTIONS="-c client_min_messages=WARNING";

#
# Python configuration
#
# Set PATH
export PATH=$PUB_TOP_DIR/bin:$PATH
# Set PYTHONPATH
export PYTHONPATH=$PUB_TOP_DIR:$PYTHONPATH
# BIN executable directory
export PUB_BIN_DIR=$PUB_TOP_DIR
export PATH=$PUB_BIN_DIR:$PATH

#
# Project configuration
# 
# Default logger level
export PUB_LOGGER_LEVEL=kLOGGER_DEBUG
#shifters don't need the cout spam
if [ `whoami` == 'uboonedaq' ]; then
    export PUB_LOGGER_LEVEL=kLOGGER_ERROR
fi
# Default message drain
export PUB_LOGGER_DRAIN=kLOGGER_COUT
#export PUB_LOGGER_DRAIN=kLOGGER_FILE
export PUB_LOGGER_FILE_LOCATION=$PUB_TOP_DIR/log

#
# Daemon configuration
#
export PUB_DAEMON_LOG_MODULE=""
export PUB_DAEMON_HANDLER_MODULE=""

#
# Larbatch configuration.
#
#export LARBATCH_DEBUG=1

#
# Server-specific configuration
#
case `uname -n` in
    (*uboonegpvm* | *uboonepubsgpvm* | *uboonetmp* )
	echo Setting up for uboonegpvm...
	if [ -z $HOME/.sqlaccess/prod_access.sh ]; then
	    echo 'Configuration @ gpvm requires \$HOME/.sqlaccess/prod_access.sh!'
	    echo 'Exiting...'
	    echo 
	    return;
	fi
	source $HOME/.sqlaccess/prod_access.sh
	source /grid/fermiapp/products/uboone/setup_uboone.sh
	source /uboone/app/users/uboonepro/mrb/localProducts_larsoft_v05_08_00_e9_prof/setup
	#setup uboonecode v04_26_03_01 -q e7:prof # Used till Nov. 30th. 2015
	#setup uboonecode v04_26_03_02 -q e7:prof
	case `uname -n` in
	    (uboonetmp02*)
	        setup uboonecode v06_26_01_10 -q e10:prof
	        #setup larbatch v01_32_06
		;;
	    (uboonegpvm01*)
	        #setup uboonecode v05_08_00_05 -q e9:prof
                #setup ubutil v06_16_00 -q e10:prof
		#setup larbatch v01_25_00
	        setup uboonecode v06_26_01_08 -q e10:prof
	        setup larbatch v01_32_06
		;;
	    (uboonegpvm02*)
	        setup uboonecode v06_26_01_09 -q e10:prof
		setup larbatch v01_34_03
		;;
	    (uboonegpvm03*)
	        setup uboonecode v05_08_00_06 -q e9:prof
                setup ubutil v06_16_00 -q e10:prof
                setup larbatch v01_26_05
	        #setup uboonecode v06_26_01 -q e10:prof
                #setup larbatch v01_21_05
                #setup larbatch v01_23_07
		;;
	    (uboonegpvm04*)
	        #setup uboonecode v04_26_04_09 -q e7:prof
	        setup uboonecode v05_08_00_10 -q e9:prof
                #setup larbatch v01_23_03
                #setup larbatch v01_23_07
                #setup ubutil v06_16_00 -q e10:prof
		#setup larbatch v01_32_04
		;;
	    (uboonegpvm05*)
	        setup uboonecode v05_08_00_05 -q e9:prof
                #setup larbatch v01_21_05
                #setup larbatch v01_23_07
                setup ubutil v06_16_00 -q e10:prof
		setup larbatch v01_31_00
		;;
	    (uboonegpvm06*)
	        #setup uboonecode v04_26_04_09 -q e7:prof
	        setup uboonecode v05_08_00_09 -q e9:prof
                #setup larbatch v01_23_03
                #setup larbatch v01_23_07
                #setup ubutil v06_16_00 -q e10:prof
		setup larbatch v01_32_04
		;;
            (uboonegpvm07*)
                #setup uboonecode v05_11_01 -q e9:prof
                setup uboonecode v06_26_01 -q e10:prof
                #setup larbatch v01_21_05
                ;;

	    (uboonepubsgpvm01*)
	        setup uboonecode v05_08_00_08 -q e9:prof
                ;;

	    (uboonepubsgpvm02*)
	        setup uboonecode v05_08_00_07 -q e9:prof
                setup ubutil v06_16_00 -q e10:prof
                setup larbatch v01_26_05
	        #setup uboonecode v06_26_01_01 -q e10:prof
                #setup ubutil v06_16_00 -q e10:prof
                #setup larbatch v01_26_05
                ;;

	    (uboonepubsgpvm03*)
	        setup uboonecode v06_26_01_10 -q e10:prof
                #setup ubutil v06_16_00 -q e10:prof
                #setup larbatch v01_26_05
                ;;

	    (uboonepubsgpvm04*)
	        setup uboonecode v06_26_01 -q e10:prof
		setup ubutil v06_16_00 -q e10:prof
		setup larbatch v01_32_05
                #setup ubutil v06_16_00 -q e10:prof
                #setup larbatch v01_26_05
                ;;

	    (uboonepubsgpvm05*)
	        setup uboonecode v06_26_01_07 -q e10:prof
                #setup ubutil v06_16_00 -q e10:prof
                #setup larbatch v01_26_05
                ;;

	    (uboonepubsgpvm06*)
	        setup uboonecode v06_26_01_01 -q e10:prof

                #setup ubutil v06_16_00 -q e10:prof
                #setup larbatch v01_26_05
                ;;

	    (*)
	        echo "Unknown node"
		;;
	esac
	#setup postgresql v9_3_6 -q p279
	#setup larbatch v01_21_05
	#setup ubutil v01_39_00 -q e9:prof
	#setup sam_web_client v2_0
	export PYTHONPATH=/uboone/app/users/uboonepro/requests/build/lib:$PYTHONPATH

	case `uname -n` in
	    (uboonetmp0*)
	        export PUB_LOGGER_FILE_LOCATION=$PUB_TOP_DIR/log/`uname -n`
		;;
	    (uboonegpvm0*)
	        export PUB_LOGGER_FILE_LOCATION=$PUB_TOP_DIR/log/`uname -n`
		;;
	    (uboonepubsgpvm*)
		export PUB_LOGGER_FILE_LOCATION=/scratch/uboonepro/pubs/log/`uname -n`
		;;
	    (*)
	        echo "Unknown node"
		;;
	esac
	mkdir -p $PUB_LOGGER_FILE_LOCATION;
	export PUB_DAEMON_LOG_MODULE=dstream_prod.gpvm_logger
	export PATH=$HOME/bin:$PATH
	;;
    (*)
        echo This should only be used for uboonegpvm account!!!
	echo Exiting with exterme prejudice.
	return 1
	;;
esac



