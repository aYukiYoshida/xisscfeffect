#!/bin/bash

################################################################################
## VARIABLES
################################################################################
SCRIPTNAME=`basename $0`
VERSION="3.1"
AUTHER="Y.Yoshida"
LOG_LEVEL_CRITERIA=1 # initialize
COMMAND_NOT_FOUND=0 # initialize
ARGUMENT_NOT_FOUND=0 # initialize


################################################################################
## FUNCTIONS
################################################################################

title(){
    echo "${SCRIPTNAME} -- Gain correction for SCF effect of XIS"
    echo "version ${VERSION} written by ${AUTHER}"
    echo ""
}


usage(){
    echo "USAGE: ${SCRIPTNAME} <INPUT> <OUTPUT> <ACTUAL> <EXPECT>"
    echo ""    
    echo "EXAMPLE: ${SCRIPTNAME} input=xis0.pi output=xis0_gcor.pi \\"
    echo "          actual=6.35 expect=6.4"
    echo ""
    echo "PARAMETERS:"
    echo "    INPUT     Input spectrum FITS file name"
    echo "    OUTPUT    Output spectrum FITS file name"
    echo "    ACTUAL    Actual energy in keV"
    echo "    EXPECT    Expected energy in keV"
    exit 0
}


check_argument(){
    local argument=$1
    if [ -v ${argument} ];then
        :
    else
        ARGUMENT_NOT_FOUND=1
        logger 2 "Argument not found: ${argument}"
    fi
    logger 0 "ARGUMENT_NOT_FOUND=${ARGUMENT_NOT_FOUND}"
}


check_command(){
    local command=$1
    which ${command} > /dev/null 2>&1
    if [ $? -eq 1 ];then
        COMMAND_NOT_FOUND=1
        logger 2 "Command not found: ${command}"
    fi
    logger 0 "COMMAND_NOT_FOUND=${COMMAND_NOT_FOUND}"
}


logger(){
    local level=$1
    local message=$2
    case ${level} in
        0) local context="DEBUG" ;;
        1) local context="INFO" ;;
        2) local context="WARNING" ;;        
        3) local context="ERROR" ;;
    esac
    [ ${level} -ge ${LOG_LEVEL_CRITERIA} ] && echo "[${context}] ${message}"
}


abort(){
    local evt=$1
    case ${evt} in
        InvalidInput) local message="Invalid arguments !!" ;;
        InvalidInputNumber) local message="Input is excess or deficiency !!" ;;        
        InvalidOption) local message="Invalid input option !!" ;;
        NotFoundCommand) local message="Not found necessary command !!" ;;
        *) local message="Abort !!" ;;
    esac
    logger 3 "${message}"
    exit 1
}


prepare_dump_pi(){
    local script=$1
    local pifile=$2
    local outfile=$3

    cat << EOT > ${script}
${pifile}+1
${outfile}
'"CHANNEL","COUNTS"'
-
EOT
}


dump_pi_data(){
    local script=$1
    fdump prhead=no clobber=yes < ${script} > /dev/null
    rm -f ${script}
    punlearn fdump
}


prepare_data_ascii(){
    local datfile=$1
    local outfile=$2
    cat ${datfile}|sed '1,/count/d' > ${outfile}
    rm -f ${datfile}
}


dump_pi_head(){
    local script=$1
    fdump prdata=no clobber=yes < ${script} > /dev/null
    rm -f ${script}
    punlearn fdump
}


prepare_head_ascii(){
    local datfile=$1
    local outfile=$2
    cat ${datfile}|sed '1,/EXTNAME/d' > ${outfile}
    rm -f ${datfile}
}


correct_pi_gain(){
    local pifile=$1
    local e_actual=$2
    local e_expect=$3
    
    prepare_dump_pi fdump_data.dat ${pifile} tmp_data.dat
    dump_pi_data fdump_data.dat
    prepare_data_ascii tmp_data.dat data.dat

    prepare_dump_pi fdump_head.dat ${pifile} tmp_head.dat
    dump_pi_head fdump_head.dat
    prepare_head_ascii tmp_head.dat head.dat

    pigaincorrect data.dat data_cor.dat ${e_actual} ${e_expect}
    rm -f data.dat
}


create_corrected_pi(){
    local outfile=$1
    local clobber=$2

    cat /dev/null > cdf.dat 
    echo "CHANNEL I" >> cdf.dat
    echo "COUNTS J count" >> cdf.dat

    fcreate cdf.dat data_cor.dat headfile=head.dat ${outfile} extname=SPECTRUM clobber=${clobber}
    rm -f cdf.dat data_cor.dat head.dat
    punlearn fcreate
}


################################################################################
## MAIN
################################################################################
title


##------------------------------------------------------------------------------
## Parse options
##------------------------------------------------------------------------------
GETOPT=`getopt -q -o uhl: -l help,usage,loglevel: -- "$@"` ; [ $? != 0 ] && abort InvalidOption
eval set -- "$GETOPT"
while true ;do
    case $1 in
        -u|-h|--usage|--help)
            usage ;;
        -l|--loglevel) 
            LOG_LEVEL_CRITERIA=$2; shift 2 ;;
        --) shift ; break  ;;
    esac
done


##------------------------------------------------------------------------------
## Parse inputs
##------------------------------------------------------------------------------
if [ $# -eq 4 ]||[ $# -eq 3 ];then
    var1=$1 #;echo ${var1}
    var2=$2 #;echo ${var2}
    var3=$3 #;echo ${var3}
    var4=$4 #;echo ${var4}
else
    abort InvalidInputNumber
fi

for var in ${var1} ${var2} ${var3} ${var4};do
    IFS="="
    set -- ${var}
    key=$1
    val=$2
    # echo "${key}" #DEBUG
    # echo "${val}" #DEBUG
    case ${key} in
        "INPUT"|"input") input=${val} ;;
        "OUTPUT"|"output") output=${val} ;;
        "ACTUAL"|"actual") actual=${val} ;;
        "EXPECT"|"expect") expect=${val} ;;
        *) abort InvalidInput;;
    esac
done


##------------------------------------------------------------------------------
## Check arguments
##------------------------------------------------------------------------------
for var in input actual expect ;do
    check_argument ${var}
done

[ ${ARGUMENT_NOT_FOUND} -eq 1 ] && abort InvalidInputNumber

if [ ! -e ${input} ];then
    logger 3 "${input} is not found !!"
    abort InvalidInput
fi


##------------------------------------------------------------------------------
## Check commands
##------------------------------------------------------------------------------
for command in fdump fcreate ;do
    check_command ${command}
done

[ ${COMMAND_NOT_FOUND} -eq 1 ] && abort NotFoundCommand


output=${output:=${input%.pi}_cor.pi}
logger 1 "Input spectrum FITS file  : ${input}"
logger 1 "Output spectrum FITS file : ${output}"
logger 1 "Actual energy in keV      : ${actual}"
logger 1 "Expected energy in keV    : ${expect}"


if [ ! -e ${output} ]  ;then
    correct_pi_gain ${input} ${actual} ${expect}
    create_corrected_pi ${output} no

else
    logger 2 "${output} already exists !!"
    echo -n "Overwrite ?? (y/n) >> "
    read answer
    case ${answer} in
        y|Y|yes|Yes|YES)
            correct_pi_gain ${input} ${actual} ${expect}
            create_corrected_pi ${output} yes
            ;;
        n|N|no|No|NO)
            logger 1 "${SCRIPTNAME} has not been executed."
            ;;
        *)
            logger 1 "${SCRIPTNAME} has not been executed."
    esac
fi
logger 1 "Finish"

#EOF#