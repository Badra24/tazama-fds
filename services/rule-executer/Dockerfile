# SPDX-License-Identifier: Apache-2.0

ARG BUILD_IMAGE=node:20-bullseye
ARG RUN_IMAGE=gcr.io/distroless/nodejs20-debian11:nonroot

# Stage 1 (Build with Dev Deps)
FROM ${BUILD_IMAGE} AS builder
LABEL stage=build
# TS -> JS stage

ARG RULE_NAME="901"
ARG RULE_VERSION="2.1.0"

WORKDIR /home/app
COPY ./src ./src
COPY ./package*.json ./
COPY ./tsconfig.json ./
COPY .npmrc ./
ARG GH_TOKEN

# Only copy rule-903 directory if building Rule 903
COPY ./rule-90[3]/ ./rule-903/

# Use package.rule-903.json if Rule 903, otherwise use default package.json
RUN if [ "$RULE_NAME" = "903" ] && [ -f package.rule-903.json ]; then \
  cp package.rule-903.json package.json && npm install --package-lock-only --ignore-scripts; \
  fi

RUN npm ci --ignore-scripts
RUN npm run build

# Stage 2 (Remove Unneeded Node Modules)
FROM ${BUILD_IMAGE} AS dep-resolver
LABEL stage=pre-prod
# To filter out dev dependencies from final build

ARG RULE_NAME="901"
ARG RULE_VERSION="2.1.0"

COPY package*.json ./
COPY .npmrc ./
ARG GH_TOKEN

# Only copy rule-903 directory if building Rule 903
COPY ./rule-90[3]/ ./rule-903/

# Use package.rule-903.json if Rule 903
RUN if [ "$RULE_NAME" = "903" ] && [ -f package.rule-903.json ]; then \
  cp package.rule-903.json package.json && npm install --package-lock-only --ignore-scripts; \
  fi

RUN npm ci --omit=dev --ignore-scripts

# Stage 3 (Run Image - Everything above not included in final build)
FROM ${RUN_IMAGE} AS run-env
USER nonroot

ARG RULE_NAME="901"
ARG RULE_VERSION="2.1.0"

WORKDIR /home/app
COPY --from=dep-resolver /node_modules ./node_modules
COPY --from=builder /home/app/build ./build
# Only copy rule-903 for Rule 903 builds
COPY --from=builder /home/app/rule-90[3]/ ./rule-903/
COPY package.json ./
COPY deployment.yaml ./
COPY service.yaml ./

# Turn down the verbosity to default level.
ENV NPM_CONFIG_LOGLEVEL warn

ENV FUNCTION_NAME="rule-executer"
ENV RULE_VERSION=${RULE_VERSION}
ENV RULE_NAME=${RULE_NAME}
ENV NODE_ENV=production
ENV MAX_CPU=1

# Apm
ENV APM_ACTIVE=true
ENV APM_URL=http://apm-server.development.svc.cluster.local:8200/
ENV APM_SECRET_TOKEN=
ENV APM_SERVICE_NAME=rule-901

# Database
ENV RAW_HISTORY_DATABASE=raw_history
ENV RAW_HISTORY_DATABASE_HOST=
ENV RAW_HISTORY_DATABASE_PORT=
ENV RAW_HISTORY_DATABASE_USER=
ENV RAW_HISTORY_DATABASE_PASSWORD=
ENV RAW_HISTORY_DATABASE_CERT_PATH=/usr/local/share/ca-certificates/ca-certificates.crt

ENV CONFIGURATION_DATABASE=configuration
ENV CONFIGURATION_DATABASE_HOST=
ENV CONFIGURATION_DATABASE_PORT=
ENV CONFIGURATION_DATABASE_USER=
ENV CONFIGURATION_DATABASE_PASSWORD=
ENV CONFIGURATION_DATABASE_CERT_PATH=/usr/local/share/ca-certificates/ca-certificates.crt

ENV EVENT_HISTORY_DATABASE=event_history
ENV EVENT_HISTORY_DATABASE_HOST=
ENV EVENT_HISTORY_DATABASE_PORT=
ENV EVENT_HISTORY_DATABASE_USER=
ENV EVENT_HISTORY_DATABASE_PASSWORD=
ENV EVENT_HISTORY_DATABASE_CERT_PATH=/usr/local/share/ca-certificates/ca-certificates.crt

# NodeCache
ENV LOCAL_CACHETTL=300
ENV LOCAL_CACHE_ENABLED=true

#Nats
ENV STARTUP_TYPE=nats
ENV SERVER_URL=0.0.0.0:4222
ENV PRODUCER_STREAM=
ENV CONSUMER_STREAM=
ENV STREAM_SUBJECT=
ENV ACK_POLICY=Explicit
ENV PRODUCER_STORAGE=File
ENV PRODUCER_RETENTION_POLICY=Workqueue

# Logging
ENV LOG_LEVEL='info'
ENV SIDECAR_HOST=0.0.0.0:5000

# Execute watchdog command
CMD ["build/index.js"]
