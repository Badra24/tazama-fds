# SPDX-License-Identifier: Apache-2.0
# REST Relay Service - Built from local clone to avoid 401/403

FROM node:20-alpine

ARG GH_TOKEN

WORKDIR /app

# Copy relay-service base package.json
COPY services/relay-service/package*.json ./

# Configure npm for private packages
RUN echo "@tazama-lf:registry=https://npm.pkg.github.com" > .npmrc && \
    echo "//npm.pkg.github.com/:_authToken=${GH_TOKEN}" >> .npmrc

# Copy locally cloned rest-relay-plugin (avoids 401/403 from npm registry)
COPY relay-service-integration-rest /tmp/rest-relay-plugin

# Build rest-relay-plugin inside container
RUN cp .npmrc /tmp/rest-relay-plugin/.npmrc && \
    cd /tmp/rest-relay-plugin && \
    npm install --ignore-scripts && \
    npm run build && \
    cd /app

# Install dependencies and rest-relay-plugin from local build
RUN npm install --ignore-scripts && npm install --ignore-scripts /tmp/rest-relay-plugin

# Copy relay-service source code
COPY services/relay-service/ .

# Build TypeScript
RUN npm run build

# Environment variables for REST transport
ENV STARTUP_TYPE=nats
ENV NODE_ENV=dev
ENV SERVER_URL=nats://localhost:4222 
ENV FUNCTION_NAME=messageRelayServiceRest
ENV OUTPUT_TO_JSON=true
ENV CONSUMER_STREAM=relay-service
ENV PRODUCER_STREAM=tazama.evaluation.result
ENV DESTINATION_TRANSPORT_TYPE=@tazama-lf/rest-relay-plugin

# REST-specific configuration (push to transfer-service callback)
ENV DESTINATION_TRANSPORT_URL=http://host.docker.internal:8080/transfer/v1/fds/callback
ENV AUTH_HEALTH_URL=http://host.docker.internal:8080/transfer/v1/health
ENV AUTH_TOKEN_URL=http://host.docker.internal:8080/transfer/v1/fds/auth/token
ENV AUTH_USERNAME=relay-service
ENV AUTH_PASSWORD=relay-service-secret
ENV MAX_SOCKETS=50
ENV RETRY_ATTEMPTS=3

ENV APM_ACTIVE=false
ENV APM_SERVICE_NAME=relay-service-rest
ENV SIDECAR_HOST=0.0.0.0:5000

EXPOSE 3000

CMD ["npm", "start"]
