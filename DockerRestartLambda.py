import boto3
import json

'''
In below describe_load_balancers method elb names can also be passed/hardcoded to 
avoid iterating through all elbs
'''


def get_elb_names(instance_id):
    results = []
    elb_client = boto3.client('elb')
    elbs_response = elb_client.describe_load_balancers()
    for elb in elbs_response['LoadBalancerDescriptions']:
        for ec2Id in elb['Instances']:
            if ec2Id['InstanceId'] == instance_id:
                results.append(elb['LoadBalancerName'])
    return results


def get_instance_id_from_event(event):
    message = event['Records'][0]['Sns']['Message']
    parsed_message = json.loads(message)
    instance_id = parsed_message['Trigger']['Dimensions'][0]['value']
    return instance_id


def deregister_instance(elb, instance_id):
    elb_client = boto3.client('elb')
    elb_client.deregister_instances_from_load_balancer(
        LoadBalancerName=str(elb),
        Instances=[
            {
                'InstanceId': str(instance_id)
            },
        ]
    )
    print("de registered instance ID: ", instance_id, " from elb: ", elb)


def register_instance(elb, instance_id):
    elb_client = boto3.client('elb')
    elb_client.register_instances_with_load_balancer(
        LoadBalancerName=str(elb),
        Instances=[
            {
                'InstanceId': str(instance_id)
            },
        ]
    )
    print("registered instance ID: ", instance_id, " to elb: ", elb)


def lambda_handler(event, context):

    instance_id = get_instance_id_from_event(event)
    print("instance_id::", instance_id)
    if instance_id is None:
        print("No instance Id could be captured from trigger event.")
        return
    elb_names = get_elb_names(instance_id)
    print("elb_name::", elb_names)

    if not elb_names:
        print("no elb found to detach for instance id: ", instance_id)
        return
    elb_client = boto3.client('elb', 'ap-southeast-1')
    elb_names_separator = ''
    elb_names_str = ''

    for elb_name in elb_names:
        response = elb_client.describe_load_balancers(
            LoadBalancerNames=[
                str(elb_name),
            ]
        )
        total_instance = len(response['LoadBalancerDescriptions'][0]['Instances'])

        # if any elb has number of instance < 2 abort the restart process
        if(total_instance < 2):
            print("aborting restart process as this is last instance")
            return


    for elb_name in elb_names:
        deregister_instance(elb_name, instance_id)
        elb_names_str = elb_names_str + elb_names_separator + elb_name
        elb_names_separator = ','
    print("Elbs belonging to instance: " + "is: " + elb_names_str)
    #mkdir -p /home/ubuntu/dockerRestartLogs;docker restart $(docker ps -q) > /home/ubuntu/dockerRestartLogs/\"log.$(date)\"
    ssm = boto3.client('ssm')

    # replace test1.sh with your script file name and location
    # elb_names_str is comma separated elbnames that is passed as first argument in script
    commandStr = "cd /home/ubuntu; ./test1.sh " + elb_names_str
    testCommand = ssm.send_command(InstanceIds=[str(instance_id)], DocumentName='AWS-RunShellScript',
                                   Comment='some comment', Parameters={"commands": [commandStr]})
    print("Script invoked::", testCommand)
