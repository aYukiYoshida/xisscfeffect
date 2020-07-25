#!/bin/bash -u

SCRIPTFILE=$0
[ -L ${SCRIPTFILE} ] && SCRIPTFILE=$(readlink $0)
SCRIPTNAME=$(basename ${SCRIPTFILE})
AUTHOR="Y.Yoshida"

################################################################################
## FUNCTIONS
################################################################################

usage(){
    echo "USAGE   : ${SCRIPTNAME} <IMAGE FITS> <REGION>"
    echo "EXAMPLE : ${SCRIPTNAME} xis0.img xis0_src.reg"
    echo ""
    echo "OUTPUT FORMAT"
    echo "  <COUNTS> <ERROR> <PIXEL>"
    exit 0
}

################################################################################
## OPTIONS
################################################################################
GETOPT=`getopt -q -o u -l usage -- "$@"` ; [ $? != 0 ] && usage
eval set -- "$GETOPT"
while true ;do
    case $1 in
        -u|--usage) usage
            ;;
        --) shift ; break 
            ;;
        *) usage
            ;;
    esac
done

################################################################################
## MAIN
################################################################################

if [ $# -ne 2 ];then
    usage
else
    # set value
    img=$1
    reg=$2

    script=$(echo $(sed -n '/physical/,$p' ${reg}|awk '{print $1}'|sed 's/$/;/g')|sed 's/ //g')

    # funtools command
    result=$(funds9 funcnts "ds9" "${img}" "${script}" "" |sed -n 's/   1/_/p')
    count=$(echo $result|awk -F_ '{print $2}'|awk '{print $1}')
    error=$(echo $result|awk -F_ '{print $2}'|awk '{print $2}')
    pixel=$(echo $result|awk -F_ '{print $3}'|awk '{print $2}')
    echo ${count} ${error} ${pixel}
fi

#EOF#



