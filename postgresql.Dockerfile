# Custom PostgreSQL image with pgvector extension
FROM flyio/postgres-flex:17.2

# Install build dependencies and pgvector
USER root

# Install git and build tools needed for pgvector
RUN apt-get update && \
    apt-get install -y \
    git \
    build-essential \
    postgresql-server-dev-17 \
    && rm -rf /var/lib/apt/lists/*

# Clone and build pgvector
RUN git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && \
    make install && \
    rm -rf /tmp/pgvector

# Switch back to postgres user
USER postgres

# Copy the init scripts to be run on database startup
COPY --chown=postgres:postgres ./docker/postgresql/init/ /docker-entrypoint-initdb.d/
