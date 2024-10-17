import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.core.v1 import Namespace, Service, Secret, ConfigMap
from pulumi_kubernetes.apps.v1 import Deployment, DaemonSet
from pulumi_kubernetes.networking.v1 import Ingress


config = pulumi.Config()




domain_name = config.get("domain_name")
namespace_name = config.get("namespace_name")


app_service_name = config.get("appServiceName")
grafana_service_name = config.get("grafanaServiceName")
prometheus_service_name = config.get("prometheusServiceName")
node_exporter_service_name = config.get("nodeExporterServiceName")




app_image = config.get("app_image")
grafana_image = config.get("grafana_image")
prometheus_image = config.get("prometheus_image")
node_exporter_image = config.get("node_exporter_image")


app_port = config.get_int("app_port")
grafana_port = config.get_int("grafana_port")
prometheus_port = config.get_int("prometheus_port")
node_exporter_port = config.get_int("node_exporter_port")


ns = Namespace(namespace_name)


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


# Application Deployment
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
                    "image": app_image,
                    "ports": [{"container_port": app_port}]
                }],
            },
        },
    },
)


# Application Service
app_service = Service(
    app_service_name,
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": app_deployment.spec.selector.match_labels,
        "ports": [{"port": app_port, "target_port": app_port}],
        "type": "ClusterIP",
    },
)


# Grafana Deployment and Service
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
                    "image": grafana_image,
                    "ports": [{"container_port": grafana_port}],
                    "env": [
                        {"name": "GF_SERVER_ROOT_URL", "value": f"http://{domain_name}/grafana/"},
                        {"name": "GF_SERVER_SERVE_FROM_SUB_PATH", "value": "true"},
                    ],
                }],
            },
        },
    },
)


grafana_service = Service(
    grafana_service_name,
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": grafana_deployment.spec.selector.match_labels,
        "ports": [{"port": grafana_port, "target_port": grafana_port}],
        "type": "ClusterIP",
    },
)


# Node Exporter DaemonSet and Service
node_exporter_daemonset = DaemonSet(
    "node-exporter",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {"match_labels": {"app": "node-exporter"}},
        "template": {
            "metadata": {"labels": {"app": "node-exporter"}},
            "spec": {
                "containers": [{
                    "name": "node-exporter",
                    "image": node_exporter_image,
                    "ports": [{"container_port": node_exporter_port}],
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


node_exporter_service = Service(
    node_exporter_service_name,
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {"app": "node-exporter"},
        "ports": [{"port": node_exporter_port, "target_port": node_exporter_port}],
        "type": "ClusterIP",
    }
)


# Prometheus ConfigMap
prometheus_config = ConfigMap(
    "prometheus-config",
    metadata={"namespace": ns.metadata["name"]},
    data={
        "prometheus.yml": f"""
        global:
          scrape_interval: 15s
        scrape_configs:
          - job_name: 'node-exporter'
            static_configs:
              - targets: ['{node_exporter_service.metadata["name"]}:{node_exporter_port}']
        """
    }
)


# Prometheus Deployment and Service
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
                    "image": prometheus_image,
                    "ports": [{"container_port": prometheus_port}],
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
                        "fsGroup": 65534,
                    },
                }],
                "volumes": [{
                    "name": "config-volume",
                    "configMap": {
                        "name": prometheus_config.metadata["name"],
                        "items": [{"key": "prometheus.yml", "path": "prometheus.yml"}]
                    }
                }],
            },
        },
    },
)


prometheus_service = Service(
    prometheus_service_name,
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": prometheus_deployment.spec.selector.match_labels,
        "ports": [{"port": prometheus_port, "target_port": prometheus_port}],
        "type": "ClusterIP",
    }
)


# Ingress
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
        "tls": [{"hosts": [domain_name], "secretName": app_secret.metadata["name"]}],
        "rules": [{
            "host": domain_name,
            "http": {
                "paths": [
                    {"path": "/", "pathType": "Prefix", "backend": {"service": {"name": app_service.metadata["name"], "port": {"number": app_port}}}},
                    {"path": "/grafana", "pathType": "Prefix", "backend": {"service": {"name": grafana_service.metadata["name"], "port": {"number": grafana_port}}}},
                    {"path": "/prometheus", "pathType": "Prefix", "backend": {"service": {"name": prometheus_service.metadata["name"], "port": {"number": prometheus_port}}}},
                ],
            },
        }],
    }
)


# Exports
pulumi.export("app_url", f"https://{domain_name}/")
pulumi.export("grafana_url", f"https://{domain_name}/grafana")
pulumi.export("prometheus_url", f"https://{domain_name}/prometheus")
