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
        "tls.crt": """-----BEGIN CERTIFICATE-----
                    -----END CERTIFICATE-----""",
        "tls.key": """-----BEGIN PRIVATE KEY-----
                    -----END PRIVATE KEY-----"""
    }
)

app_deployment = Deployment(
    "my-app-deployment",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {"match_labels": {"app": "my-app"}},
        "template": {
            "metadata": {"labels": {"app": "my-app"}},
            "spec": {
                "containers": [{
                    "name": "my-app",
                    "image": "smenaria/monitor-app:v1",
                    "ports": [{"container_port": 5000}],
                }],
            },
        },
    },
)

app_service = Service(
    "my-app-service",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": app_deployment.spec.selector.match_labels,
        "ports": [{"port": 5000, "target_port": 5000}],
        "type": "ClusterIP",
    },
)


grafana_deployment = Deployment(
    "grafana-deployment",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {"match_labels": {"app": "grafana"}},
        "template": {
            "metadata": {"labels": {"app": "grafana"}},
            "spec": {
                "containers": [{
                    "name": "grafana",
                    "image": "grafana/grafana:latest",
                    "ports": [{"container_port": 3000, "host_port": 3000}],
                    "env": [
                        {"name": "GF_SERVER_ROOT_URL", "value": f"http://{domain_name}/grafana/"},
                        {"name": "GF_SERVER_SERVE_FROM_SUB_PATH", "value": "true"},
                    ]
                }],
            },
        },
    },
)

grafana_service = Service(
    "grafana-service",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": grafana_deployment.spec.selector.match_labels,
        "ports": [{"port": 3000, "target_port": 3000}],
        "type": "ClusterIP",
    },
)


node_exporter_daemonset = k8s.apps.v1.DaemonSet(
    "node-exporter",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {"match_labels": {"app": "node-exporter"}},
        "template": {
            "metadata": {"labels": {"app": "node-exporter"}},
            "spec": {
                "containers": [{
                    "name": "node-exporter",
                    "image": "quay.io/prometheus/node-exporter:latest",
                    "ports": [{"container_port": 9100, "host_port": 9100}],
                    "volumeMounts": [
                        {"name": "proc", "mountPath": "/host/proc", "readOnly": True},
                        {"name": "sys", "mountPath": "/host/sys", "readOnly": True},
                    ],
                    "args": [
                        "--path.procfs=/host/proc",
                        "--path.sysfs=/host/sys",
                        "--collector.filesystem.ignored-mount-points",
                        "^/(sys|proc|dev|host|etc)($|/)",
                    ],
                }],
                "volumes": [
                    {"name": "proc", "hostPath": {"path": "/proc"}},
                    {"name": "sys", "hostPath": {"path": "/sys"}}
                ],
            }
        }
    }
)


prometheus_config = k8s.core.v1.ConfigMap(
    "prometheus-config",
    metadata={"namespace": ns.metadata["name"]},
    data={
        "prometheus.yml": """
        global:
          scrape_interval: 15s
        scrape_configs:
          - job_name: 'node-exporter'
            static_configs:
              - targets: ['node-exporter-service-1a98bfe6:9100']
        """
    }
)

node_exporter_service = k8s.core.v1.Service(
    "node-exporter-service",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {"app": "node-exporter"},
        "ports": [{"port": 9100, "target_port": 9100}],
        "type": "ClusterIP",
    }
)

prometheus_deployment = Deployment(
    "prometheus-deployment",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {"match_labels": {"app": "prometheus"}},
        "template": {
            "metadata": {"labels": {"app": "prometheus"}},
            "spec": {
                "containers": [{
                    "name": "prometheus",
                    "image": "prom/prometheus:latest",
                    "ports": [{"container_port": 9090, "host_port": 9090}],
                    "args": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus",
                        "--web.external-url=/prometheus"
                    ],
                    "volumeMounts": [{
                        "name": "config-volume",
                        "mountPath": "/etc/prometheus/prometheus.yml",
                        "subPath": "prometheus.yml"
                    }],
                    "securityContext": {
                        "runAsUser": 65534, 
                        "runAsGroup": 65534,
                        "fsGroup": 65534
                    }
                }],
                "volumes": [{
                    "name": "config-volume",
                    "configMap": {
                        "name": prometheus_config.metadata["name"],
                        "items": [{
                            "key": "prometheus.yml",
                            "path": "prometheus.yml"
                        }]
                    }
                }]
            }
        }
    }
)

prometheus_service = Service(
    "prometheus-service",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": prometheus_deployment.spec.selector.match_labels,
        "ports": [{"port": 9090, "target_port": 9090}],
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
            #  "nginx.ingress.kubernetes.io/rewrite-target": "/$2"
        },
    },
    spec={
        "tls": [{"hosts": ["localhost"], "secretName": app_secret.metadata["name"]}],
        "rules": [{
            "host": "localhost",
            "http": {
                "paths": [
                    {"path": "/", "pathType": "Prefix", "backend": {"service": {"name": app_service.metadata["name"], "port": {"number": 5000}}}},
                    {"path": "/grafana", "pathType": "Prefix", "backend": {"service": {"name": grafana_service.metadata["name"], "port": {"number": 3000}}}},
                    {"path": "/prometheus", "pathType": "Prefix", "backend": {"service": {"name": prometheus_service.metadata["name"], "port": {"number": 9090}}}},
                ]
            }
        }]
    }
)

pulumi.export("app_url", "https://localhost/")
pulumi.export("grafana_url", "https://localhost/grafana")
pulumi.export("prometheus_url", "https://localhost/prometheus")