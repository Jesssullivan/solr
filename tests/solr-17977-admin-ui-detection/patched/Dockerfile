# Dockerfile for SOLR-17977 Patched Test
# Builds Solr from Jesssullivan/solr main branch (PR #3807) with security.js fix
# Demonstrates the fix: Multi-indicator security detection works behind reverse proxy

FROM eclipse-temurin:21-jdk-jammy AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Clone source code from Jesssullivan/solr main branch (has the fix)
WORKDIR /build
RUN git clone --depth 1 --branch main https://github.com/Jesssullivan/solr.git . && \
    git log --oneline -n 1

# Build Solr (skip tests and new UI - include legacy webapp with fix)
RUN ./gradlew assemble -x test -x :solr:ui:assemble

# Runtime stage
FROM eclipse-temurin:21-jre-jammy

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    bash \
    lsof \
    procps \
    wget \
    netcat \
    && rm -rf /var/lib/apt/lists/*

# Create solr user
RUN groupadd -r -g 8983 solr && \
    useradd -r -u 8983 -g solr solr

# Copy built Solr from builder
COPY --from=builder /build/solr/packaging/build/solr-* /opt/solr/
WORKDIR /opt/solr

# Set up Solr home
RUN mkdir -p /var/solr && \
    chown -R solr:solr /var/solr /opt/solr

# Expose Solr port
EXPOSE 8983

# Switch to solr user
USER solr

# Set working directory for solr commands
WORKDIR /opt/solr

# Start Solr directly (no init script needed - using external bootstrap)
CMD ["bin/solr", "start", "-f", "-z", "zookeeper:2181"]
