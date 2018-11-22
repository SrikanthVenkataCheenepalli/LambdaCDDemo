import boto3
import botocore
import csv
import urllib2
import urllib

from datetime import datetime, timedelta
Bucket_Name="infrastructure-cleanup-reports"
ec2Resource = boto3.resource('ec2')
File_Name="DELETE_EC2_Older.csv"

def Ec2Terminate(event, context):
    Ec2Deleted = 0
    Ec2DoesNotExists = 0
    s3Resource = boto3.resource('s3')
    
    now = datetime.now()
    bucket = s3Resource.Bucket(Bucket_Name)
    
    #for key in bucket.objects.filter(Prefix='DELETE'):
        #File_Name=key.key
        #print(key.key)
        
    
    
    DeleteEc2S3URL="https://s3.eu-central-1.amazonaws.com/"+Bucket_Name+"/"+File_Name
    
    print "CSV file S3 URL:", DeleteEc2S3URL
    try:
        response = urllib2.urlopen(DeleteEc2S3URL)
    except urllib.error.HTTPError:
        print "Permission denied"
    
    DeleteEc2DataObj = csv.reader(response,delimiter=';')
    for rowdata in DeleteEc2DataObj:
        Ec2id = rowdata[0]
        
        if(Ec2id !="InstanceId"):
            try: 
                Ec2Inst = ec2Resource.Instance(Ec2id)
                Ec2InstStatus = Ec2Inst.state['Name']
                if Ec2InstStatus == 'stopped' :
                    print "Ec2Inst object: ",Ec2Inst
                    print "Ec2Inst state: ",Ec2InstStatus
                    print "Ec2 Instance terminated: ",Ec2Inst.id
                    Ec2Inst.terminate()
                    
                    Ec2Deleted = Ec2Deleted + 1
                else:
                    print "EC2 Instance is not in stopped state:",Ec2Inst.id
            except botocore.exceptions.ClientError as e:
                
                print "Error details : ",e
                Ec2DoesNotExists = Ec2DoesNotExists + 1
            

    print " Total no. of Snapshots found : %d" % ((Ec2DoesNotExists + Ec2Deleted)-1)            
    print " No. of Snapshots deleted : %d" % (Ec2Deleted)
    print " No. of Snapshots Doesn't exists  : %d" % ((Ec2DoesNotExists)-1)
    return "success"
    #raise Exception('Something went wrong')
