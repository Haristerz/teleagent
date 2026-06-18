FROM public.ecr.aws/lambda/python:3.11

# Install build tools (avoid openssl-devel conflict)
RUN yum install -y \
    gcc10 gcc10-c++ gcc10-binutils make \
    wget tar gzip \
    zlib-devel \
    && ln -sf /usr/bin/gcc10-gcc /usr/bin/gcc \
    && ln -sf /usr/bin/gcc10-g++ /usr/bin/g++ \
    && ln -sf /usr/bin/gcc10-gcc /usr/bin/cc \
    && ln -sf /usr/bin/gcc10-ar /usr/bin/ar \
    && ln -sf /usr/bin/gcc10-ranlib /usr/bin/ranlib \
    && yum clean all

# Build newer SQLite (required by ChromaDB)
RUN cd /tmp && \
    wget https://www.sqlite.org/2024/sqlite-autoconf-3450200.tar.gz && \
    tar xzf sqlite-autoconf-3450200.tar.gz && \
    cd sqlite-autoconf-3450200 && \
    ./configure --prefix=/usr/local && \
    make -j$(nproc) && \
    make install && \
    rm -rf /tmp/sqlite*

# Make Python/runtime use new sqlite library
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"
ENV PATH="/usr/local/bin:${PATH}"

# Install Rust (needed by some Python packages)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt --target .

COPY app/ ./app/

CMD ["app.lambda_handler.lambda_handler"]