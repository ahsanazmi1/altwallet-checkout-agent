{{/*
Expand the name of the chart.
*/}}
{{- define "altwallet-checkout-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "altwallet-checkout-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "altwallet-checkout-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "altwallet-checkout-agent.labels" -}}
helm.sh/chart: {{ include "altwallet-checkout-agent.chart" . }}
{{ include "altwallet-checkout-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "altwallet-checkout-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "altwallet-checkout-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "altwallet-checkout-agent.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "altwallet-checkout-agent.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the config map
*/}}
{{- define "altwallet-checkout-agent.configMapName" -}}
{{- if .Values.configMap.create }}
{{- printf "%s-config" (include "altwallet-checkout-agent.fullname" .) }}
{{- else }}
{{- .Values.configMap.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the secret
*/}}
{{- define "altwallet-checkout-agent.secretName" -}}
{{- if .Values.secrets.create }}
{{- printf "%s-secrets" (include "altwallet-checkout-agent.fullname" .) }}
{{- else }}
{{- .Values.secrets.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the persistent volume claim
*/}}
{{- define "altwallet-checkout-agent.pvcName" -}}
{{- printf "%s-data" (include "altwallet-checkout-agent.fullname" .) }}
{{- end }}

{{/*
Create the image name
*/}}
{{- define "altwallet-checkout-agent.image" -}}
{{- $registry := .Values.image.registry -}}
{{- $repository := .Values.image.repository -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- end }}

{{/*
Create the image pull secrets
*/}}
{{- define "altwallet-checkout-agent.imagePullSecrets" -}}
{{- if .Values.image.pullSecrets }}
{{- toYaml .Values.image.pullSecrets }}
{{- else if .Values.imagePullSecrets }}
{{- toYaml .Values.imagePullSecrets }}
{{- end }}
{{- end }}

{{/*
Create the resource requirements
*/}}
{{- define "altwallet-checkout-agent.resources" -}}
{{- toYaml .Values.resources }}
{{- end }}

{{/*
Create the node selector
*/}}
{{- define "altwallet-checkout-agent.nodeSelector" -}}
{{- toYaml .Values.nodeSelector }}
{{- end }}

{{/*
Create the tolerations
*/}}
{{- define "altwallet-checkout-agent.tolerations" -}}
{{- toYaml .Values.tolerations }}
{{- end }}

{{/*
Create the affinity
*/}}
{{- define "altwallet-checkout-agent.affinity" -}}
{{- toYaml .Values.affinity }}
{{- end }}
