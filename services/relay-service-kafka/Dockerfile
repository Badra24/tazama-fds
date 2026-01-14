# SPDX-License-Identifier: Apache-2.0
# Kafka Relay Service - Built from local clone to avoid 401/403

FROM node:20-alpine

ARG GH_TOKEN

WORKDIR /app

# Copy relay-service base package.json
COPY services/relay-service/package*.json ./

# Configure npm for private packages
RUN echo "@tazama-lf:registry=https://npm.pkg.github.com" > .npmrc && \
    echo "//npm.pkg.github.com/:_authToken=${GH_TOKEN}" >> .npmrc

# Copy locally cloned kafka-relay-plugin (avoids 401/403 from npm registry)
COPY relay-service-integration-kafka /tmp/kafka-relay-plugin

# Build kafka-relay-plugin inside container
RUN cp .npmrc /tmp/kafka-relay-plugin/.npmrc && \
    cd /tmp/kafka-relay-plugin && \
    npm install --ignore-scripts && \
    npm run build && \
    cd /app

# Install dependencies and kafka-relay-plugin from local build
RUN npm install --ignore-scripts && npm install --ignore-scripts /tmp/kafka-relay-plugin

# Copy relay-service source code
COPY services/relay-service/ .

# Build TypeScript
RUN npm run build

# Environment variables for Kafka transport
ENV STARTUP_TYPE=nats
ENV NODE_ENV=dev
ENV SERVER_URL=nats://localhost:4222 
ENV FUNCTION_NAME=messageRelayServiceKafka
ENV OUTPUT_TO_JSON=true
ENV CONSUMER_STREAM=relay-service
ENV PRODUCER_STREAM=tazama.evaluation.result
ENV DESTINATION_TRANSPORT_TYPE=@tazama-lf/kafka-relay-plugin

# Kafka-specific configuration
ENV KAFKA_CLIENT_ID=tazama-relay-kafka
ENV KAFKA_DESTINATION_TRANSPORT_URL=localhost:9092
ENV KAFKA_PRODUCER_STREAM=tazama.evaluation.result
ENV KAFKA_MAX_IN_FLIGHT_REQUESTS=5

ENV APM_ACTIVE=false
ENV APM_SERVICE_NAME=relay-service-kafka
ENV SIDECAR_HOST=0.0.0.0:5000

EXPOSE 3000

CMD ["npm", "start"]
