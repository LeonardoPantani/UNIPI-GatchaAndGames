FROM mysql:9.1.0

COPY ./init.sql /docker-entrypoint-initdb.d/
COPY ./mock_data.sql /docker-entrypoint-initdb.d/