from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
    aws_logs as logs,
    aws_ecr_assets as ecr_assets,
    aws_applicationautoscaling as appscaling,
    Duration,
    CfnOutput,
    Fn,
)
from constructs import Construct
from ...utils.config import Config
from ..shared.roles import create_execution_role, create_task_role

class BackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Load configuration
        self.config = Config(stage)
        
        # Import VPC from networking stack
        vpc = ec2.Vpc.from_vpc_attributes(
            self, "ImportedVPC",
            vpc_id=Fn.import_value(f"poc-networking-{stage}-vpc-id"),
            public_subnet_ids=Fn.import_value(f"poc-networking-{stage}-public-subnet-ids").split(","),
            private_subnet_ids=Fn.import_value(f"poc-networking-{stage}-private-subnet-ids").split(","),
            availability_zones=Fn.import_value(f"poc-networking-{stage}-azs").split(",")
        )
        
        # Create subnet objects for ALB (needs proper subnet objects, not just IDs)
        public_subnet_ids = Fn.split(",", Fn.import_value(f"poc-networking-{stage}-public-subnet-ids"))
        public_subnets = [
            ec2.Subnet.from_subnet_id(self, f"PublicSubnet{i}", Fn.select(i, public_subnet_ids))
            for i in range(2)  # We know we have 2 AZs
        ]
        
        # Create subnet objects for ECS service
        private_subnet_ids = Fn.split(",", Fn.import_value(f"poc-networking-{stage}-private-subnet-ids"))
        private_subnets = [
            ec2.Subnet.from_subnet_id(self, f"PrivateSubnet{i}", Fn.select(i, private_subnet_ids))
            for i in range(2)  # We know we have 2 AZs
        ]
        
        # Import certificate from networking stack
        certificate = acm.Certificate.from_certificate_arn(
            self, "ImportedCertificate",
            Fn.import_value(f"poc-networking-{stage}-certificate-arn")
        )
        
        # Import security groups from networking stack
        alb_security_group = ec2.SecurityGroup.from_security_group_id(
            self, "ImportedAlbSecurityGroup",
            Fn.import_value(f"poc-networking-{stage}-alb-security-group-id"),
            allow_all_outbound=True
        )
        
        ecs_security_group = ec2.SecurityGroup.from_security_group_id(
            self, "ImportedEcsSecurityGroup",
            Fn.import_value(f"poc-networking-{stage}-ecs-security-group-id"),
            allow_all_outbound=True
        )
        
        # Create ECS Cluster
        cluster = ecs.Cluster(
            self, "PocBackendCluster",
            vpc=vpc,
            cluster_name=f"poc-backend-{stage}",
            enable_fargate_capacity_providers=True
        )
        
        # Create roles using shared utilities
        execution_role = create_execution_role(self, "PocBackend", f"poc-backend-{stage}")
        task_role = create_task_role(self, "PocBackend", f"poc-backend-{stage}")
        
        # Create Task Definition
        task_definition = ecs.FargateTaskDefinition(
            self, "PocBackendTaskDef",
            memory_limit_mib=int(self.config.get("APP_MEMORY", 512)),
            cpu=int(self.config.get("APP_CPU", 256)),
            execution_role=execution_role,
            task_role=task_role
        )
        
        # Add container to task definition
        container = task_definition.add_container(
            "PocBackendContainer",
            image=ecs.ContainerImage.from_asset(
                directory=".",
                file="Dockerfiles/Dockerfile",
                platform=ecr_assets.Platform.LINUX_AMD64
            ),
            port_mappings=[ecs.PortMapping(container_port=int(self.config.get("APP_PORT", 8000)))],
            environment={
                "ENVIRONMENT": self.config.get("ENVIRONMENT", "development"),
                "LOG_LEVEL": self.config.get("LOG_LEVEL", "INFO"),
                "STAGE": stage
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="poc-backend",
                log_retention=logs.RetentionDays.ONE_WEEK
            ),
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                retries=3,
                start_period=Duration.seconds(60)
            )
        )
        
        # Create Application Load Balancer
        alb = elbv2.ApplicationLoadBalancer(
            self, "PocBackendALB",
            vpc=vpc,
            internet_facing=True,
            load_balancer_name=f"poc-backend-{stage}-alb",
            security_group=alb_security_group,
            vpc_subnets=ec2.SubnetSelection(subnets=public_subnets)
        )
        
        # Create HTTPS listener
        https_listener = alb.add_listener(
            "HttpsListener",
            port=443,
            protocol=elbv2.ApplicationProtocol.HTTPS,
            certificates=[certificate],
            default_action=elbv2.ListenerAction.fixed_response(
                status_code=404,
                content_type="text/plain",
                message_body="Not Found"
            )
        )
        
        # Create Fargate Service
        service = ecs.FargateService(
            self, "PocBackendService",
            cluster=cluster,
            task_definition=task_definition,
            service_name=f"poc-backend-{stage}",
            desired_count=int(self.config.get("CONTAINER_COUNT", 1)),
            assign_public_ip=False,
            vpc_subnets=ec2.SubnetSelection(subnets=private_subnets),
            security_groups=[ecs_security_group]
        )
        
        # Configure Auto Scaling
        scaling = service.auto_scale_task_count(
            min_capacity=1,
            max_capacity=2
        )
        
        # Add CPU-based scaling policy
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60)
        )
        
        # Add target group to ALB
        target_group = https_listener.add_targets(
            "PocBackendTarget",
            port=int(self.config.get("APP_PORT", 8000)),
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[service],
            health_check=elbv2.HealthCheck(
                path="/health",
                port=str(self.config.get("APP_PORT", 8000)),
                healthy_http_codes="200",
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                healthy_threshold_count=2,
                unhealthy_threshold_count=3
            )
        )
        
        # Create Route53 hosted zone (assuming it exists)
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone",
            domain_name=self.config.get("DOMAIN_NAME")
        )
        
        # Create A record
        route53.ARecord(
            self, "PocBackendARecord",
            zone=hosted_zone,
            record_name=self.config.get("SUBDOMAIN"),
            target=route53.RecordTarget.from_alias(
                targets.LoadBalancerTarget(alb)
            )
        )
        
        # Outputs
        CfnOutput(
            self, "ServiceURL",
            value=f"https://{self.config.get_domain_name()}",
            description="URL of the deployed service"
        )
        
        CfnOutput(
            self, "LoadBalancerDNS",
            value=alb.load_balancer_dns_name,
            description="DNS name of the load balancer"
        )
        
        CfnOutput(
            self, "ClusterName",
            value=cluster.cluster_name,
            description="Name of the ECS cluster"
        ) 