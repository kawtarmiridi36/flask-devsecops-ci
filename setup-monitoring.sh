#!/bin/bash
echo "🚀 Setting up Prometheus + Grafana Monitoring Stack"

# Install Helm if not present
if ! command -v helm &> /dev/null; then
    echo "Installing Helm..."
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

# Add repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Create namespace
kubectl create namespace monitoring 2>/dev/null || true

# Install stack
echo "Installing kube-prometheus-stack..."
helm upgrade --install prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=admin \
  --set prometheus.service.type=NodePort \
  --set grafana.service.type=NodePort \
  --set prometheus.prometheusSpec.replicas=2 \
  --atomic --wait --timeout 10m

# Create ServiceMonitor
echo "Creating ServiceMonitor for Flask app..."
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: flask-devsecops-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: flask-test
  namespaceSelector:
    matchNames:
    - production
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
