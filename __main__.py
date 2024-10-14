import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.core.v1 import Namespace, Service, Secret
from pulumi_kubernetes.apps.v1 import Deployment
from pulumi_kubernetes.networking.v1 import Ingress

domain_name = "localhost"


ns = Namespace("app-namespace")


app_secret = Secret(
    "tls-secret",
    metadata={"namespace": ns.metadata["name"]},
    string_data={
        "tls.crt": """<your certificate here>""",  # right now using self signed certs 
        "tls.key": """<your private key here>"""
    }
)

app_deployment = Deployment(
    "python-app-deployment",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {"matchLabels": {"app": "python-app"}},
        "replicas": 1,
        "template": {
            "metadata": {"labels": {"app": "python-app"}},
            "spec": {
                "containers": [{
                    "name": "python-app",
                    "image": "mightysanjay/monitor-app:v1",
                    "ports": [{"containerPort": 5000}],
                    "volumeMounts": [{
                        "name": "log-volume",
                        "mountPath": "/var/log/app"
                    }]
                }],
                "volumes": [{
                    "name": "log-volume",
                    "hostPath": {"path": "/var/log/app"}
                }]
            }
        }
    }
)


nginx_deployment = Deployment(
   "nginx-deployment",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {"matchLabels": {"app": "nginx"}},
        "replicas": 1,
        "template": {
            "metadata": {"labels": {"app": "nginx"}},
            "spec": {
                "initContainers": [
                    {
                        "name": "init-log-dir",
                        "image": "busybox",
                        "command": ["sh", "-c", "mkdir -p /var/log/nginx"],
                        "volumeMounts": [
                            {
                                "mountPath": "/var/log/nginx",
                                "name": "log-volume"
                            }
                        ]
                    }
                ],
                "containers": [{
                    "name": "nginx",
                    "image": "nginx:latest",
                    "ports": [{"containerPort": 80}],
                    "volumeMounts": [
                        {
                            "mountPath": "/var/log/nginx",
                            "name": "log-volume"
                        }
                    ]
                }],
                "volumes": [
                    {
                        "name": "log-volume",
                        "hostPath": {
                            "path": "/var/log/app"
                        }
                    }
                ]
            }
        }
    }
)


app_service = Service(
    "python-app-service",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {"app": "python-app"},
        "ports": [{"port": 5000, "targetPort": 5000}],
        "type": "ClusterIP",
    }
)

nginx_service = Service(
    "nginx-service",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {"app": "nginx"},
        "ports": [{"port": 80, "targetPort": 80}],
        "type": "ClusterIP",
    }
)

ingress = Ingress(
    "app-ingress",
    metadata={
        "namespace": ns.metadata["name"],
        "annotations": {
            "kubernetes.io/ingress.class": "nginx",
            "nginx.ingress.kubernetes.io/ssl-redirect": "true",
        },
    },
    spec={
        "tls": [{
            "hosts": [domain_name],
            "secretName": app_secret.metadata["name"]  
        }],
        "rules": [{
            "host": domain_name,
            "http": {
                "paths": [
                    {
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {"name": app_service.metadata["name"], "port": {"number": 5000}}
                        }
                    },
                    {
                        "path": "/monitor",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {"name": nginx_service.metadata["name"], "port": {"number": 80}}
                        }
                    }
                ]
            }
        }]
    }
)

pulumi.export("appUrl", pulumi.Output.concat("https://", domain_name, "/"))
pulumi.export("monitorUrl", pulumi.Output.concat("https://", domain_name, "/monitor"))