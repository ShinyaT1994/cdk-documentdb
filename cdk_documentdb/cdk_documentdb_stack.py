from aws_cdk import (
    Stack,
    aws_docdb as docdb,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    
)
from constructs import Construct

class CdkDocumentdbStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        docdb_port = 27017
        
        # VPC
        vpc = ec2.Vpc(
            self,
            'VPC',
            max_azs=2,
            restrict_default_security_group=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name='public',
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name='private',
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )
        
        # Security Groups
        sg_bastion = ec2.SecurityGroup(
            self,
            'SecurityGroupForBastionInstance',
            vpc=vpc,
        )
        
        sg_docdb = ec2.SecurityGroup(
            self,
            'SecurityGroupForDocumentDb',
            vpc=vpc,
        )
        sg_docdb.add_ingress_rule(
            peer=ec2.Peer.security_group_id(sg_bastion.security_group_id),
            connection=ec2.Port.tcp(docdb_port),
        )
        
        # 踏み台用EC2
        # - 簡単のため、Public Subnet上に作成
        # - 接続はSSMを使って接続する
        bastion = ec2.Instance(
            self,
            'BastionInstance',
            instance_type=ec2.InstanceType('t3.nano'),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            vpc=vpc,
            security_group=sg_bastion,
            ssm_session_permissions=True,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )
        
        # DocumentDB
        docdb_cluster = docdb.DatabaseCluster(
            self,
            'DocumentDbCluster',
            instance_type=ec2.InstanceType('t4g.medium'),
            master_user=docdb.Login(username='dbuser'),
            vpc=vpc,
            cloud_watch_logs_retention=logs.RetentionDays.TWO_MONTHS,
            engine_version='5.0.0',
            instances=1,
            port=docdb_port,
            security_group=sg_docdb,
            storage_encrypted=True,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
        )