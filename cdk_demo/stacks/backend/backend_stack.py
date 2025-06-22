from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
    aws_iam as iam,
    aws_logs as logs,
    aws_ecr_assets as ecr_assets,
    aws_applicationautoscaling as appscaling,
    Duration,
    CfnOutput,
)
from constructs import Construct
from ...utils.config import Config

class BackendStack(Stack):

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
        
        # Create ECS Cluster
        cluster = ecs.Cluster(
            self, "PocBackendCluster",
            vpc=vpc,
            cluster_name=f"poc-backend-{stage}",
            enable_fargate_capacity_providers=True
        )
        
        # Create Task Definition
        task_definition = ecs.FargateTaskDefinition(
            self, "PocBackendTaskDef",
            memory_limit_mib=int(self.config.get("APP_MEMORY", 512)),
            cpu=int(self.config.get("APP_CPU", 256)),
            execution_role=self._create_execution_role(),
            task_role=self._create_task_role()
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
            load_balancer_name=f"poc-backend-{stage}-alb"
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
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
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
        
        CfnOutput(
            self, "VPCId",
            value=vpc.vpc_id,
            description="VPC ID"
        )
    
    def _create_execution_role(self) -> iam.Role:
        """Create execution role for ECS tasks"""
        return iam.Role(
            self, "PocBackendExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )
    
    def _create_task_role(self) -> iam.Role:
        """Create task role for ECS tasks"""
        return iam.Role(
            self, "PocBackendTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        ) 