from aws_cdk import aws_iam as iam
from constructs import Construct

def create_execution_role(scope: Construct, id: str, service_name: str) -> iam.Role:
    """Create execution role for ECS tasks"""
    return iam.Role(
        scope, f"{id}ExecutionRole",
        assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
        ],
        role_name=f"{service_name}-execution-role"
    )

def create_task_role(scope: Construct, id: str, service_name: str) -> iam.Role:
    """Create task role for ECS tasks"""
    return iam.Role(
        scope, f"{id}TaskRole",
        assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        managed_policies=[
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
        ],
        role_name=f"{service_name}-task-role"
    ) 