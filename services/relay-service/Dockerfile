# SPDX-License-Identifier: Apache-2.0
# Developed By Paysys Labs

# Use Node.js as the base image
FROM node:20-alpine

ARG GH_TOKEN

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to the container
COPY services/relay-service/package*.json ./

# Configure npm to use GitHub token for @tazama-lf packages
RUN echo "@tazama-lf:registry=https://npm.pkg.github.com" > .npmrc && \
    echo "//npm.pkg.github.com/:_authToken=${GH_TOKEN}" >> .npmrc

# Copy locally cloned nats-relay-plugin
COPY relay-service-integration-nats /tmp/nats-relay-plugin

# Build nats-relay-plugin inside container (needs .npmrc for frms-coe-lib)
RUN cp .npmrc /tmp/nats-relay-plugin/.npmrc && \
    cd /tmp/nats-relay-plugin && \
    npm install --ignore-scripts && \
    npm run build && \
    cd /app

# Install dependencies from npm and nats-relay-plugin from local (ignore scripts to skip husky)
RUN npm install --ignore-scripts && npm install --ignore-scripts /tmp/nats-relay-plugin

# Copy the rest of the application code to the container
COPY services/relay-service/ .

# Build the TypeScript code
RUN npm run build

# Environment variables (May require changes based on requirements)
ENV STARTUP_TYPE=nats
ENV NODE_ENV=dev
ENV SERVER_URL=nats://localhost:4222 
ENV FUNCTION_NAME=messageRelayService
ENV OUTPUT_TO_JSON=true
ENV PRODUCER_STREAM=destination.subject
ENV CONSUMER_STREAM=interdiction-service
ENV DESTINATION_TRANSPORT_TYPE=@tazama-lf/nats-relay-plugin

ENV APM_ACTIVE=true
ENV APM_SERVICE_NAME=relay-service
ENV APM_URL=http://apm-server.development.svc.cluster.local:8200/
ENV APM_SECRET_TOKEN=

ENV LOGSTASH_LEVEL='info'
ENV SIDECAR_HOST=0.0.0.0:5000

# Expose the port the app runs on
EXPOSE 3000

# Command to start the application
CMD ["npm", "start"]
