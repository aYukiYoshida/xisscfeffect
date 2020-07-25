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
    echo "USAGE:  ${SCRIPTNAME} <DIRECTORY> <XIS> <REGNUM> <SKYX> <SKYY> <RADIUS>"
    echo ""
    echo "PARAMETERS:"
    echo "    DIRECTORY    Path to observation data directory"
    echo "    XIS          XIS detector id"
    echo "    REGNUM       Number of regions"    
    echo "    SKYX         SKYX of middle of region"
    echo "    SKYY         SKYY of middle of region"
    echo "    RADIUS       Radius of extreme circle region in unit of arcmin"
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
    local evtlst=$(basename $1)
    local outputimg=${2%.gz}
    local xco_prefix=$(basename ${outputimg}|cut -d. -f1)
    local xco=${anadir}/evt/${xco_prefix}_xsl.xco

    [ -e ${xco} ]&& rm -f ${xco}
    if [ ! -e ${outputimg}.gz ] ;then
        make_all_grade_image_xco ${evtlst} ${xco} ${outputimg}
        logger 1 "Extracting all grade image from unfiltered events"
        cd ${xisdir}/analysis/evt
        xselect < ${xco} 1 > /dev/null
        rm -f ${xco}
        logger 1 "Make image: ${outputimg}"
        gzip ${outputimg} && logger 1 "Zipped image"
    fi
}


make_extreme_circle_region(){
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


make_innermost_region(){
    local outputreg=$1
    local outermost_radius_arcmin=$2
    local skyx=$3
    local skyy=$4
    local each_count=$5
    local img=$6
    local number=1

    logger 1 "Make region: ${number} / ${regnum}"
    [ -e ${outputreg} ]&&rm -f ${outputreg}
    for r in $(seq 0.1 0.01 ${outermost_radius_arcmin}) ;do
        local radius_pixel=`awk -v r=${r} 'BEGIN{printf "%f",r*57.53}'`
        cat /dev/null > ${outputreg}
        echo "# Region file format: DS9" >> ${outputreg}
        echo "physical" >> ${outputreg}
        echo "circle(${skyx},${skyy},${radius_pixel})" >> ${outputreg}
        local test_count=`cntinregion.sh ${img} ${outputreg}|awk '{print $1}'`
        local flag=`check_count_for_each_region ${test_count} ${each_count}`
        if [ ${flag} -eq 1 ];then
            logger 1 "  Determined radius: ${r} arcmin"
            logger 1 "  Count in region: ${test_count} (reference: ${each_count})"
            break
        else
            /bin/rm -f ${outputreg}
        fi
    done
}


make_annulus_region(){
    local innermost_radius_arcmin=$1
    local outermost_radius_arcmin=$2
    local skyx=$3
    local skyy=$4
    local each_count=$5
    local img=$6
    local number=$(expr ${regnum} - 1)
    for i in $(seq 2 ${number}) ;do
        logger 1 "Make region: ${i} / ${regnum}"
        logger 0 "innermost_radius_arcmin=${innermost_radius_arcmin}"

        local outputreg=${anadir}/reg/scf/x${id}_circle${i}.reg
        [ -e ${outputreg} ]&&rm -f ${outputreg}

        local inner_radius_pixel=`awk -v r=${innermost_radius_arcmin} 'BEGIN{printf "%f",r*57.53}'`

        for r in $(seq ${innermost_radius_arcmin} 0.01 ${outermost_radius_arcmin}) ;do
            local outer_radius_pixel=`awk -v r=${r} 'BEGIN{printf "%f",r*57.53}'`
            cat /dev/null > ${outputreg}
            echo "# Region file format: DS9" >> ${outputreg}
            echo "physical" >> ${outputreg}
            echo "annulus(${skyx},${skyy},${inner_radius_pixel},${outer_radius_pixel})" >> ${outputreg}
            local test_count=`cntinregion.sh ${img} ${outputreg}|awk '{print $1}'`
            local flag=`check_count_for_each_region ${test_count} ${each_count}`
            if [ ${flag} -eq 1 ];then
                logger 1 "  Determined inner radius: ${innermost_radius_arcmin} arcmin"
                logger 1 "  Determined outer radius: ${r} arcmin"
                logger 1 "  Count in region: ${test_count} (reference: ${each_count})"
                local innermost_radius_arcmin=${r}
                break
            else
                /bin/rm -f ${outputreg}
            fi
        done
        
    done
}


make_outermost_region(){
    local inner_radius_pixel=$1
    local outer_radius_pixel=$2
    local skyx=$3
    local skyy=$4
    local each_count=$5
    local img=$6

    local number=${regnum}
    logger 1 "Make region: ${number} / ${regnum}"
    
    local outputreg=${anadir}/reg/scf/x${id}_circle${number}.reg
    [ -e ${outputreg} ]&&rm -f ${outputreg}

    cat /dev/null > ${outputreg}
    echo "# Region file format: DS9" >> ${outputreg}
    echo "physical" >> ${outputreg}
    echo "annulus(${skyx},${skyy},${inner_radius_pixel},${outer_radius_pixel})" >> ${outputreg}
    
    local inner_radius_arcmin=`awk -v r=${inner_radius_pixel} 'BEGIN{printf "%5.3f\n",r/57.53}'`
    local outer_radius_arcmin=`awk -v r=${outer_radius_pixel} 'BEGIN{printf "%5.3f\n",r/57.53}'`
    local test_count=`cntinregion.sh ${img} ${outputreg}|awk '{print $1}'`
    
    logger 1 "  Determined inner radius: ${inner_radius_arcmin} arcmin"
    logger 1 "  Determined outer radius: ${outer_radius_arcmin} arcmin"
    logger 1 "  Count in region: ${test_count} (reference: ${each_count})"

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
if [ $# -ne 6 ];then
    abort InvalidInputNumber
else
    var1=$1 #;echo ${var1}
    var2=$2 #;echo ${var2}
    var3=$3 #;echo ${var3}
    var4=$4 #;echo ${var4}
    var5=$5 #;echo ${var5}
    var6=$6 #;echo ${var6}
fi

IFS_ORG=$IFS

for var in ${var1} ${var2} ${var3} ${var4} ${var5} ${var6};do
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
        "RADIUS"|"radius") extreme_radius_arcmin=${val} ;;
        *) abort InvalidInput;;
    esac
done 

IFS=$IFS_ORG


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
logger 1 "OUTERMOST RADIUS: ${extreme_radius_arcmin} arcmin"
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
## Make unscreened events list
##------------------------------------------------------------------------------
evtlst=${anadir}/evt/x${id}_uf.lst
make_unfiltered_event_list ${evtlst}


##------------------------------------------------------------------------------
## Make all grade image
##------------------------------------------------------------------------------
all_grade_image=${anadir}/img/grade/x${id}_grade_0_7.img.gz
make_all_grade_image ${evtlst} ${all_grade_image}


##------------------------------------------------------------------------------
## Count total count in extreme circle region
##------------------------------------------------------------------------------

## Make largest radius circle region
region0=${anadir}/reg/scf/x${id}_circle0.reg
make_extreme_circle_region ${region0} ${extreme_radius_arcmin} ${skyx} ${skyy}

## Calculate counts in largest radius circle region
total_count=`cntinregion.sh ${all_grade_image} ${region0}|awk '{printf "%10.3f\n",$1}'`
each_count=`awk -v n=${regnum} -v cnt=${total_count} 'BEGIN{printf "%10d\n",cnt/n}'`
logger 0 "Total count in extreme circle region: ${total_count}"
logger 0 "Count for each region: ${each_count}"


##------------------------------------------------------------------------------
## Make regions for SCF effect
##------------------------------------------------------------------------------

## Make innermost circle region
region1=${anadir}/reg/scf/x${id}_circle1.reg
make_innermost_region ${region1} ${extreme_radius_arcmin} ${skyx} ${skyy} ${each_count} ${all_grade_image}

## Make annulas region (No.2 - No.(${regnum}-1))
innermost_radius_pixel=`sed -n '/circle/p' ${region1}|sed 's/)//g'|cut -d',' -f3`
innermost_radius_arcmin=`echo ${innermost_radius_pixel}|awk '{printf "%f\n",$1/57.53}'`
make_annulus_region ${innermost_radius_arcmin} ${extreme_radius_arcmin} ${skyx} ${skyy} ${each_count} ${all_grade_image}

## Make outermost annulas region
regionR=${anadir}/reg/scf/x${id}_circle$(expr ${regnum} - 1).reg
outermost_region_inner_radius_pixel=$(cat ${regionR}|grep annulus|sed 's/^annulus(//;s/)$//'|awk -F, '{print $4}')
outermost_region_radius_pixel=`awk -v r=${extreme_radius_arcmin} 'BEGIN{printf "%5.2f\n",r*57.53}'`
make_outermost_region ${outermost_region_inner_radius_pixel} ${outermost_region_radius_pixel} ${skyx} ${skyy} ${each_count} ${all_grade_image}

logger 1 "Finish"

#EOF#