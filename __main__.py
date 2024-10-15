import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.core.v1 import Namespace, Service, Secret
from pulumi_kubernetes.apps.v1 import Deployment
from pulumi_kubernetes.networking.v1 import Ingress


# Define your domain name
domain_name = "localhost"

# Create the namespace first
ns = Namespace("app-namespace")

# Create a secret (you can replace the data with your actual credentials)
app_secret = Secret(
    "tls-secret",
    metadata={"namespace": ns.metadata["name"]},
    string_data={
        "tls.crt": """-----BEGIN CERTIFICATE-----
MIIDKTCCAhGgAwIBAgIUAvShIZEAIeFugUg7HaRhNDhgm04wDQYJKoZIhvcNAQEL
BQAwJDESMBAGA1UEAwwJbG9jYWxob3N0MQ4wDAYDVQQKDAVNeU9yZzAeFw0yNDEw
MTEwOTQ2MDVaFw0yNTEwMTEwOTQ2MDVaMCQxEjAQBgNVBAMMCWxvY2FsaG9zdDEO
MAwGA1UECgwFTXlPcmcwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDB
ks8xAZRG/lLuy8rZBR2UD4BMBXn/XksUh+u49BblLEMNvOWxXL+3dmmEPrux9J/a
ePEP8Jyqtov2o+ur/yCmF2cLvnfvtlv4KNCXtpwMhIwgEWgeIj+CNdXLjsXtNPj7
zSVz0DwvS8MRSHS2juUlbHPulVqVxMzfOsLp38xhGqscXuevOuGmUDcD9wbXNNkQ
5Bk37TI+LK5NGbgKZsgplDcCEh63jHHhpE0obgttxgKUeBRw5lxpsHqIgr0Isv49
haeDyQ67JFXm87e03CHpUTnFEAx4/OfFfIjzZUKaa/Nk4KM0QKtP9L4/axPU/hzA
S8APdKKKvec3EXO5KkUrAgMBAAGjUzBRMB0GA1UdDgQWBBRHVTHiPtVIT+NhWTjY
adNN6stemjAfBgNVHSMEGDAWgBRHVTHiPtVIT+NhWTjYadNN6stemjAPBgNVHRMB
Af8EBTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQBwCZ9IQp872hjPANTnY2jg3s/S
cuV+20N5LJeqflBz8aRHq+upun0lDWW3p29AFrAyjrs+WNxL9MpdRtQT4crsC87b
vL0VtiZywNWWHrT0Eb6r5orCgJQPjTD/FpvDpaqpYBH/99mnPBoiemJbZYsYUqzV
oCLpmBAMwEDRXqjXZp2tXJQh8b8qTGBQM08yiItk/oHkyFIr3bGFIZ1NsHD+8TMs
OdIvCW3LN5fLg2R4gyZDrmV4y9Ry2HtZNRDOAAvYXUAtk1h7dPgCAqvLwpR4uIbI
lDFJjs+hJZtFGpi4dJi5pFPXxGXo8yGCVvhql6QEeZv10QQTzmvYQbv3TSCi
-----END CERTIFICATE-----""",
        "tls.key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDBks8xAZRG/lLu
y8rZBR2UD4BMBXn/XksUh+u49BblLEMNvOWxXL+3dmmEPrux9J/aePEP8Jyqtov2
o+ur/yCmF2cLvnfvtlv4KNCXtpwMhIwgEWgeIj+CNdXLjsXtNPj7zSVz0DwvS8MR
SHS2juUlbHPulVqVxMzfOsLp38xhGqscXuevOuGmUDcD9wbXNNkQ5Bk37TI+LK5N
GbgKZsgplDcCEh63jHHhpE0obgttxgKUeBRw5lxpsHqIgr0Isv49haeDyQ67JFXm
87e03CHpUTnFEAx4/OfFfIjzZUKaa/Nk4KM0QKtP9L4/axPU/hzAS8APdKKKvec3
EXO5KkUrAgMBAAECggEAdyKy8BdnufXm9t9oXf7/AFQ2AxPPzPKsxNsOogtgV/XQ
4xCiUXGi8Pgo4uJ1RIYpKB4NR2EwGwU0yTyD3Jyt7Gs02Y6FZHxYyDfegbE7A51E
XKw552nuqmYVyi159Y8Hunm9FjVQBU/co7NzWbRCpbDE/U7grJKuAKm6spQxxoS/
p2Uksj41FiVMU60cWidcw//+uIlQUB1XVDpvuf2lsYhYMfThhJPoFBKy8QqLpihM
Wj2aQzvGEzIVJeLmDlYXpTYXVY0xRnQdrW3wASyTNBsM0oQoMnGlv6sdnANWeKLK
IKcTPvL1LTdl/GAq7iGWpzn6G0WAMVVGLqaT+kQS8QKBgQDudC0RF3zqi2P3/lWe
3LiBSHLK7BlMH6lNr+U8dyIG+seZWwymobvrGU2PTX5w0SYxy6ehvCgAO9BAgc+G
LeVi6R82JETcELocju8KNj1t1H1EvqHGB9PkivlckkhTPkiqN6rjD2xwgLRTa637
d8zoCa9USeQR/DSz3ocmufF/yQKBgQDP0TWTcm+Xojjx3rI4AeAQps5LlS2RbjZ1
CNyXhijzevyPxrxu1B88ZC5BR+7/IpGE7GubL++FUdRrWqMEenHEnS5dcj+6r+pI
kQJQXdw1VJ5VRXye8EnbN07fo4oZAHF8oK7kuHfRoOjfvMf4wt2JbQPt+CbMQzpH
1x3spYCfUwKBgAzzBCuEcgUusqwaBL5O0Do9G/bHIYyPv5r3bWR+N7vXTJWYazR1
XgYjZqHcnHw173QO0jinRijVFrcaFZH81hMsA8Tl7VNiGSlJ3dNZJLbdLjxYeeKO
NESaA3ayfvj+TeXohgA0qzfk1WYeV+FrHRaQyBO0u4z6fEY0VHSW7nV5AoGBAJbo
TsVhZhNwY3WPx07QXcr5tfhAvbRLmhPmeXk2nOohtuEY6aB5PK13+fbBq5Vtnsot
e/5XEtF3GI9UY+hOmeqyUQbefdStBa3oTwvY/J1lcwxsxxALYTZktUvEz/VT0xUz
AY1pPujktfYyeev0ZTb0CNR3TIUrlFiypzI/BGWtAoGBAOi7q2Bn0j1sqQqz2n6Y
0/0jE47lFp48MHDdFhjMhFFkKoFijLWON+H0grqGHkM4TNSi1YTawJdHvBhfT4P/
++hjwex7mpfvPEvUE56ESPWE/cyBIU/2ox5IRtXrmotlDpCUnPiI7zAWpD2nHl8O
gYjz4W8K3SzqC/oB+Xb0Y8C9""",
    }
)

# Deploy your application
app_deployment = Deployment(
    "my-app-deployment",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {
            "match_labels": {"app": "my-app"}
        },
        "template": {
            "metadata": {
                "labels": {"app": "my-app"}
            },
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

# Deploy Grafana
grafana_deployment = Deployment(
    "grafana-deployment",
    metadata={"namespace": ns.metadata["name"]},
    spec={
        "selector": {
            "match_labels": {"app": "grafana"}
        },
        "template": {
            "metadata": {
                "labels": {"app": "grafana"}
            },
            "spec": {
                "containers": [{
                    "name": "grafana",
                    "image": "grafana/grafana:latest",
                    "ports": [{"container_port": 3000}],
                    "env": [
                        {
                            "name": "GF_SERVER_ROOT_URL",
                            "value": "%(protocol)s://%(domain)s/grafana/"
                        },
                        {
                            "name": "GF_SERVER_SERVE_FROM_SUB_PATH",
                            "value": "true"
                        }
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
            "hosts": ["localhost"],
            "secretName": app_secret.metadata["name"]
        }],
        "rules": [{
            "host": "localhost",
            "http": {
                "paths": [
                    {
                        "path": "/",
                        "pathType": "ImplementationSpecific",
                        "backend": {
                            "service": {"name": app_service.metadata["name"], "port": {"number": 5000}}
                        }
                    },
                    {
                        "path": "/grafana",
                        "pathType": "ImplementationSpecific",
                        "backend": {
                            "service": {"name": grafana_service.metadata["name"], "port": {"number": 3000}} 
                        }
                    }
                ]
            }
        }]
    }
)


pulumi.export("app_url", "http://localhost/")
pulumi.export("grafana_url", "http://localhost/grafana")
