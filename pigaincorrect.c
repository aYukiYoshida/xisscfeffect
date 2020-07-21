#include "pigaincorrect.h"

int main(int argc, char *argv[]){
    int i,ii,j,jj,k,l,m=0,n=0;
    int s,t,u,p,q;
    int row[NUM],ch[NUM],cnt1[NUM],out[NUM]; //cnt1[NUM]:������
    int R;
    char *input_data, *output_data;
    float e1_width;
    //double e1_width;
    float e0[NUM],e1[NUM],cnt0[NUM]; //cnt0[NUM]:��餦
    //double e0[NUM],e1[NUM],cnt0[NUM]; //cnt0[NUM]:��餦
    float estart=0.0,estop=0.0,estopplus=0.0,data=0.0;
    //double estart=0.0,estop=0.0,estopplus=0.0,data=0.0;
    float integer,decimal,rnd;
    //double integer,decimal,rnd;
    float efunc,etrue;

    FILE *fp;

    input_data = argv[1];
    output_data = argv[2];
    efunc=atof(argv[3]); //���٥��̩�٤ȵ������濴���ͥ륮������شؿ���������줿���ͥ륮�����ɹ�
    etrue=atof(argv[4]); //���٥��̩�٤ȵ������濴���ͥ륮������شؿ��μ�«���ͥ륮�����ɹ�
    
    e1_width=E0_WIDTH*etrue/efunc;
    // printf("Correlation Energy(keV) = %f\n",efunc);
    // printf("Convergent Energy(keV)  = %f\n",etrue);
    // printf("True Energy Width(eV)  = %f\n",E0_WIDTH);
    // printf("Wrong Energy Width(eV) = %f\n",e1_width);

    fp=fopen(input_data,"r");
    for(i=0;i<NUM;i++){
        fscanf(fp,"%d %d %d \n",&row[i],&ch[i],&cnt1[i]);
    }
    fclose(fp);

    //�����
    if((fp=fopen(output_data,"w"))!=NULL){ 
        for(i=0;i<NUM;i++)
            {
            cnt0[i]=0;
            out[i]=0;
            e1[i]=e1_width*i;
            }

        for(j=0;j<NUM;j++){
            e0[j]=E0_WIDTH*j;
            //e1[j]=e1_width*j;
            estart=e0[j];
            estop=e0[j]+E0_WIDTH;
            estopplus=e0[j]+E0_WIDTH+E0_WIDTH;

            for(k=0;k<NUM;k++){
                if(e1[k]>=estart){
                    m=k;
                    break;
                }}
            
            for(l=0;l<NUM;l++){
                if(e1[l]>0.0 && e1[l]>estop){
                    n=l;
                    break;
                }}

            
            if(e1[n]<=estopplus){
                if(n-m==1){
                data=cnt1[m];
                s=j;
                t=j+1;
                u=0;
                data=cnt1[m];
                cnt0[s]=cnt0[s]+data*(estop-e1[m])/e1_width; //left���ꤲ����
                cnt0[t]=cnt0[t]+data*(e1[n]-estop)/e1_width; //right���ꤲ����
                ////////////////////////////
                //search bug
                /*
                if(j>=950&&j<=1000){
                    printf("m=%d,n=%d\n",m,n);
                    printf("cnts[%d]=%f,cntt[%d]=%f\n",s,data*(estop-e1[m])/e1_width,t,data*(e1[n]-estop)/e1_width);
                    printf("cnt0s[%d]=%f,cnt0t[%d]=%f\n",s,cnt0[s],t,cnt0[t]);
                }
                */
                //search bug
                //////////////////////////// 
                }else if(n-m==0){
                    s=j;
                    t=j+1;
                    u=j+2;
                    cnt0[s]=cnt0[s]; //left
                    cnt0[t]=cnt0[t]; //center
                    cnt0[u]=cnt0[u]; //right
                    ////////////////////////////
                    //search bug
                    /*
                    if(j>=950&&j<=1000){
                        printf("m=%d,n=%d\n",m,n);
                        printf("cnts[%d]=%f,cntt[%d]=%f\n",s,data*(estop-e1[m])/e1_width,t,data*(e1[n]-estop)/e1_width);
                        printf("cnt0s[%d]=%f,cnt0t[%d]=%f\n",s,cnt0[s],t,cnt0[t]);
                    }
                    */
                    //search bug
                    //////////////////////////// 
                    }}

            else{ 
                //e1[n]>estopplus
                data=cnt1[m];
                s=j;
                t=j+1;
                u=j+2;
                cnt0[s]=cnt0[s]+data*(estop-e1[m])/e1_width; //left���ꤲ����
                cnt0[t]=cnt0[t]+data*(estopplus-estop)/e1_width; //center���ꤲ����
                cnt0[u]=cnt0[u]+data*(e1[n]-estopplus)/e1_width; //right���ꤲ����
                ////////////////////////////
                //search bug
                /*
                if(j>=950&&j<=1000){
                    printf("m=%d,n=%d\n",m,n);
                    printf("cnts[%d]=%f,cntt[%d]=%f,cntu[%d]=%f\n",s,data*(estop-e1[m])/e1_width,t,data*(estopplus-estop)/e1_width,u,data*(e1[n]-estopplus)/e1_width);
                    printf("cnt0s[%d]=%f,cnt0t[%d]=%f,cnt0u[%d]=%f\n",s,cnt0[s],t,cnt0[t],u,cnt0[u]);
                }
                */
                //search bug
                ////////////////////////////
                }


            if(cnt0[j]>0.0){
                integer=floor(cnt0[j]); //�������ʲ����ڼΤ�
                decimal=cnt0[j]-integer;
                R=rand(); //�����դ�
                //rnd=(float)R/RAND_MAX;	//0-1�������դ�
                rnd=(double)R/RAND_MAX;	//0-1�������դ�
                if(decimal>rnd){
                    out[j]=integer+1;
                }else{
                    out[j]=integer;
                }}


            //out[0]=0;

            //fprintf(fp,"%d %d %d\n",row[j],ch[j],out[j]);
            fprintf(fp,"%d %d\n",ch[j],out[j]);
            
        } // END for(j=0;j<NUM;j++)

        fclose(fp);
    } // if((fp=fopen(output_data,"w"))!=NULL) END
    else{
        printf("File Open Error!\n");
        exit(1);
    }
    return 0;
}

/*EOF*/
