FROM redis:latest

COPY ./ssl /usr/local/etc/redis/ssl
COPY ./redis.conf /usr/local/etc/redis/redis.conf

RUN chown -R redis:redis /usr/local/etc/redis/ssl && chmod 644 /usr/local/etc/redis/ssl/*

USER redis

CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]