#!/bin/bash -u

## Make Annulus Regions for SCF Effect

################################################################################
## VARIABLES
################################################################################
SCRIPTFILE=$0
[ -L ${SCRIPTFILE} ] && SCRIPTFILE=$(readlink $0)
SCRIPTNAME=$(basename ${SCRIPTFILE})
AUTHOR="Y.Yoshida"
LOG_LEVEL_CRITERIA=1
COMMAND_NOT_FOUND=0


################################################################################
## FUNCTIONS
################################################################################
title(){
    echo "${SCRIPTNAME} -- Make annulus regions for SCF effect of XIS"
    echo "Written by ${AUTHOR}"
    echo ""
}

usage(){
    echo "USAGE:"
    echo "  ${SCRIPTNAME} <DIRECTORY> <XIS> <REGNUM> \\"
    echo "  <SKYX> <SKYY> <INNER_RADIUS> <OUTER_RADIUS>"
    echo ""
    echo "PARAMETERS:"
    echo "  DIRECTORY       Path to observation data directory"
    echo "  XIS             XIS detector id"
    echo "  REGNUM          Number of regions"    
    echo "  SKYX            SKYX of middle of region"
    echo "  SKYY            SKYY of middle of region"
    echo "  INNER_RADIUS    Inner radius of innermost region in unit of arcmin"
    echo "  OUTER_RADIUS    Outer radius of outermost region in unit of arcmin"
    exit 0
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
        NotFoundDirectory) local message="Not found observation data directory !!" ;;
        NotFoundEventDirectory) local message="Not found unscreened event directory !!" ;;
        *) local message="Abort !!" ;;
    esac
    logger 3 "${message}"
    exit 1
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


make_unfiltered_event_list(){
    local outputevtlst=$1
    local evtdir=${xisdir}/event_uf

    if [ -d ${evtdir} ];then
        if [ ! -f ${outputevtlst} ] ;then
            /bin/ls -1 ${evtdir}/ae${seq}xi${id}_?_?x??????_uf.evt.* > ${outputevtlst} 2>/dev/null
            if [ $? -ne 0 ];then
                logger 0 "Event file of XIS${id} is not found"
                rm -f ${outputevtlst}
            else
                logger 0 "Make unfiltered event list: ${outputevtlst}"
            fi
        fi
    else
        abort NotFoundEventDirectory
    fi
}


make_all_grade_image_xco(){
    local evtlst=$(basename $1)
    local outputxco=$2
    local img_file_name=$3
    cat /dev/null > ${outputxco}
    echo "xsl_all_grade_image" >> ${outputxco}
    echo "read event ${evtlst} ./" >> ${outputxco}
    echo "set xybinsize 1" >> ${outputxco}
    echo "set xyname X Y" >> ${outputxco}
    echo "filter grade 0-7" >> ${outputxco}
    echo "extract image" >> ${outputxco}
    echo "save image ${img_file_name}" >> ${outputxco}
    echo "exit" >> ${outputxco}
    echo "no" >> ${outputxco}
    logger 0 "Make xco file to extract all grade image: `basename ${outputxco}`"
}


make_all_grade_image(){
    local evtlst=$1
    local outputimg=${2%.gz}
    local xco_prefix=$(basename ${outputimg}|cut -d. -f1)
    local xco=${anadir}/evt/${xco_prefix}_xsl.xco

    [ -e ${xco} ]&& rm -f ${xco}
    if [ ! -e ${outputimg}.gz ] ;then
        make_unfiltered_event_list ${evtlst}
        make_all_grade_image_xco ${evtlst} ${xco} ${outputimg}
        logger 1 "Extracting all grade image from unfiltered events"
        cd ${xisdir}/analysis/evt
        xselect < ${xco} 1 > /dev/null
        rm -f ${xco}
        logger 1 "Make image: ${outputimg}"
        gzip ${outputimg} && logger 1 "Zipped image"
    fi
}


make_whole_circle_region(){
    local outputreg=$1
    local radius_arcmin=$2
    local skyx=$3
    local skyy=$4
    local radius_pixel=`awk -v r=${radius_arcmin} 'BEGIN{printf "%5.2f",r*57.53}'`
    [ -e ${outputreg} ]&&rm -f ${outputreg}
    cat /dev/null > ${outputreg}
    echo "# Region file format: DS9" >> ${outputreg}
    echo "physical" >> ${outputreg}
    echo "circle(${skyx},${skyy},${radius_pixel})" >> ${outputreg}
    logger 0 "Make region: `basename ${outputreg}`"
}


check_count_for_each_region(){
    local test=$1
    local each=$2
    awk -v t=${test} -v e=${each} 'BEGIN{th=e*0.03;if( e-th < t && t <= e+th) 
	print "1";else print "0"}'
}


write_annulus_region(){
    local output_region=$1
    local inner_radius_arcmin=$2
    local outer_radius_arcmin=$3
    local skyx=$4
    local skyy=$5
    local inner_radius_pixel=$(echo ${inner_radius_arcmin}|awk '{printf "%f", $1*57.53}')
    local outer_radius_pixel=$(echo ${outer_radius_arcmin}|awk '{printf "%f", $1*57.53}')

    cat /dev/null > ${output_region}
    echo "# Region file format: DS9" >> ${output_region}
    echo "physical" >> ${output_region}
    echo "annulus(${skyx},${skyy},${inner_radius_pixel},${outer_radius_pixel})" >> ${output_region}
}


make_annulus_region(){
    local output_region=$1
    local inner_radius_arcmin=$2
    local outer_radius_arcmin=$3
    local search_outer_radius=$4
    local skyx=$5
    local skyy=$6
    local each_count=$7
    local image=$8

    [ -e ${output_region} ] && rm -f ${output_region}

    if [ ${search_outer_radius} -eq 1 ];then
        for test_outer_radius_arcmin in $(seq ${inner_radius_arcmin} 0.01 ${outer_radius_arcmin}) ;do
            write_annulus_region ${output_region} ${inner_radius_arcmin} ${test_outer_radius_arcmin} ${skyx} ${skyy}
            local test_count=$(cntinregion.sh ${image} ${output_region}|awk '{print $1}')
            local flag=$(check_count_for_each_region ${test_count} ${each_count})
            if [ ${flag} -eq 1 ];then
                break
            else
                /bin/rm -f ${output_region}
            fi
        done
    else
        local test_outer_radius_arcmin=${outer_radius_arcmin}
        write_annulus_region ${output_region} ${inner_radius_arcmin} ${test_outer_radius_arcmin} ${skyx} ${skyy}
        local test_count=$(cntinregion.sh ${image} ${output_region}|awk '{print $1}')
    fi
    local count_ratio=$(echo ${test_count} ${each_count}|awk '{printf "%4.2f\n", $1/$2}')
    logger 1 "  inner radius: ${inner_radius_arcmin} arcmin"
    logger 1 "  outer radius: ${test_outer_radius_arcmin} arcmin"
    logger 1 "  count: ${test_count} / reference: ${each_count} = ratio: ${count_ratio}"
    innermost_radius_arcmin=${test_outer_radius_arcmin}
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
if [ $# -lt 5 ];then
    abort InvalidInputNumber
else
    ## set default value
    innermost_radius_arcmin=0.0
    innermost_radius_arcmin=3.5

    IFS_ORG=$IFS
    
    for var in $@ ;do
        IFS="="
        set -- ${var}
        par=$1
        val=$2
        # echo "${par}" #DEBUG
        # echo "${val}" #DEBUG
        case ${par} in
            "DIRECTORY"|"directory") datdir=${val} ;;
            "XIS"|"xis") id=${val} ;;
            "REGNUM"|"regnum") regnum=${val} ;;
            "SKYX"|"skyx") skyx=${val} ;;
            "SKYY"|"skyy") skyy=${val} ;;
            "INNER_RADIUS"|"inner_radius") innermost_radius_arcmin=${val} ;;
            "OUTER_RADIUS"|"outer_radius") outermost_radius_arcmin=${val} ;;        
            *) abort InvalidInput;;
        esac
    done 

    IFS=$IFS_ORG

fi


##------------------------------------------------------------------------------
## Check commands
##------------------------------------------------------------------------------
for command in xselect cntinregion.sh funds9;do
    check_command ${command}
done

[ ${COMMAND_NOT_FOUND} -eq 1 ] && abort NotFoundCommand


##------------------------------------------------------------------------------
## START LOGGER
##------------------------------------------------------------------------------
logger 1 "INPUT VALUES"
logger 1 "OBSERVATION DATA DERECTORY: ${datdir}"
logger 1 "DETECTOR: XIS${id}"
logger 1 "REGION NUMBER: ${regnum}"
logger 1 "SKYX: ${skyx}"
logger 1 "SKYY: ${skyy}"
logger 1 "INNERMOST RADIUS: ${innermost_radius_arcmin} arcmin"
logger 1 "OUTERMOST RADIUS: ${outermost_radius_arcmin} arcmin"
logger 1 "START TO MAKE REGIONS FOR SCF EFFECT"


##------------------------------------------------------------------------------
## Make directory
##------------------------------------------------------------------------------
if [ -d ${datdir} ];then
    cd ${datdir} && datdir=$PWD
    seq=$(basename ${datdir})
    xisdir=${datdir}/xis
    anadir=${xisdir}/analysis
    for wrkdir in ${anadir}/reg/scf ${anadir}/img/grade ${anadir}/evt;do
        if [ ! -d ${wrkdir} ] ;then
            mkdir -p ${wrkdir} && logger 1 "Make directory: ${wrkdir}"
        fi
    done
else
    abort NotFoundDirectory
fi


##------------------------------------------------------------------------------
## Make all grade image
##------------------------------------------------------------------------------
evtlst=${anadir}/evt/x${id}_uf.lst
all_grade_image=${anadir}/img/grade/x${id}_grade_0_7.img.gz
make_all_grade_image ${evtlst} ${all_grade_image}


##------------------------------------------------------------------------------
## Measure total count in extreme circle region
##------------------------------------------------------------------------------

## Make largest radius circle region
whole_circle_region=${anadir}/reg/scf/x${id}_circle0.reg
make_whole_circle_region ${whole_circle_region} ${outermost_radius_arcmin} ${skyx} ${skyy}

## Calculate counts in largest radius circle region
total_count=$(cntinregion.sh ${all_grade_image} ${whole_circle_region}|awk '{printf "%10.3f\n",$1}')
each_count=$(echo ${total_count} ${regnum}|awk '{printf "%d\n",$1/$2}')
logger 0 "Total count in extreme circle region: ${total_count}"
logger 0 "Count for each region: ${each_count}"


##------------------------------------------------------------------------------
## Make regions for SCF effect
##------------------------------------------------------------------------------

for i in $(seq ${regnum}) ;do
    logger 1 "Make region: ${i} / ${regnum}"
    output_region=${anadir}/reg/scf/x${id}_circle${i}.reg

    search_outer_radius=1
    [ ${i} -eq ${regnum} ] && search_outer_radius=0
    make_annulus_region ${output_region} ${innermost_radius_arcmin} ${outermost_radius_arcmin} ${search_outer_radius} ${skyx} ${skyy} ${each_count} ${all_grade_image}
done

logger 1 "Finish"

#EOF#