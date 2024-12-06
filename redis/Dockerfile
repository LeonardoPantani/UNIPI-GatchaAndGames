FROM redis:7.4.1

COPY ./redis.conf /usr/local/etc/redis/redis.conf
COPY ./ssl /usr/local/etc/redis/certs

RUN chown -R redis:redis /usr/local/etc/redis/certs && chmod 600 /usr/local/etc/redis/certs/*

USER redis

EXPOSE 6379

CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]