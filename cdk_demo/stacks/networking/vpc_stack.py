from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_certificatemanager as acm,
    CfnOutput,
)
from constructs import Construct
from ...utils.config import Config

class NetworkingStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Load configuration
        self.config = Config(stage)
        
        # Create VPC
        vpc = ec2.Vpc(
            self, "PocBackendVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )
        
        # Import the certificate
        certificate = acm.Certificate.from_certificate_arn(
            self, "Certificate",
            self.config.get("CERTIFICATE_ARN")
        )
        
        # Create security group for ALB
        alb_security_group = ec2.SecurityGroup(
            self, "AlbSecurityGroup",
            vpc=vpc,
            description="Security group for Application Load Balancer",
            allow_all_outbound=True
        )
        
        # Allow HTTPS inbound
        alb_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS inbound"
        )
        
        # Allow HTTP inbound (for redirect)
        alb_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP inbound"
        )
        
        # Create security group for ECS tasks
        ecs_security_group = ec2.SecurityGroup(
            self, "EcsSecurityGroup",
            vpc=vpc,
            description="Security group for ECS tasks",
            allow_all_outbound=True
        )
        
        # Allow traffic from ALB to ECS tasks
        ecs_security_group.add_ingress_rule(
            peer=alb_security_group,
            connection=ec2.Port.tcp(int(self.config.get("APP_PORT", 8000))),
            description="Allow traffic from ALB to ECS tasks"
        )
        
        # Outputs for other stacks to import
        CfnOutput(
            self, "VPCId",
            value=vpc.vpc_id,
            description="VPC ID",
            export_name=f"poc-networking-{stage}-vpc-id"
        )
        
        CfnOutput(
            self, "PublicSubnetIds",
            value=",".join([subnet.subnet_id for subnet in vpc.public_subnets]),
            description="Public subnet IDs",
            export_name=f"poc-networking-{stage}-public-subnet-ids"
        )
        
        CfnOutput(
            self, "PrivateSubnetIds",
            value=",".join([subnet.subnet_id for subnet in vpc.private_subnets]),
            description="Private subnet IDs",
            export_name=f"poc-networking-{stage}-private-subnet-ids"
        )
        
        CfnOutput(
            self, "CertificateArn",
            value=certificate.certificate_arn,
            description="Certificate ARN",
            export_name=f"poc-networking-{stage}-certificate-arn"
        )
        
        CfnOutput(
            self, "AlbSecurityGroupId",
            value=alb_security_group.security_group_id,
            description="ALB Security Group ID",
            export_name=f"poc-networking-{stage}-alb-security-group-id"
        )
        
        CfnOutput(
            self, "EcsSecurityGroupId",
            value=ecs_security_group.security_group_id,
            description="ECS Security Group ID",
            export_name=f"poc-networking-{stage}-ecs-security-group-id"
        )
        
        CfnOutput(
            self, "AvailabilityZones",
            value=",".join(vpc.availability_zones),
            description="Availability Zones",
            export_name=f"poc-networking-{stage}-azs"
        )
        
        # Store references for internal use
        self.vpc = vpc
        self.certificate = certificate
        self.alb_security_group = alb_security_group
        self.ecs_security_group = ecs_security_group 