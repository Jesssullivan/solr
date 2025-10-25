# Dockerfile for SOLR-17885 New UI Test
# Builds Solr from apache/solr main with new Kotlin/Compose UI
# SOLR-17885 (PR #3704 by @malliaridis) already handles reverse proxy auth correctly

FROM eclipse-temurin:21-jdk-jammy AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Clone Apache Solr with SOLR-17885 merged (new UI)
WORKDIR /build
RUN git clone --depth 1 --branch main https://github.com/apache/solr.git . && \
    git log --oneline -n 1

# Build Solr with new UI included (skip tests only)
RUN ./gradlew assemble -x test

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
