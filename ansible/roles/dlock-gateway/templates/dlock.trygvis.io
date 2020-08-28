server {
    listen 80;
    server_name {{web_hostname}};

    location / {
        proxy_pass http://localhost:5000;
    }

    location /kibana {
        proxy_pass http://localhost:5601;
    }

# deny everything except for whitelisted IPs
#{% for ip in vault_http_api_allow %}
#    allow {{ ip }};
# {% endfor %}
#    deny all;
# 2020-08-28: customer wants unblocked access
     allow all;

    location /.well-known/ {
        root /var/www/html;
        allow all;
    }

{% if dlock_gateway__enable_https|bool %}
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/{{ certbot_host }}/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/{{ certbot_host }}/privkey.pem; # managed by Certbot
    ssl_session_cache shared:le_nginx_SSL:1m; # managed by Certbot
    ssl_session_timeout 1440m; # managed by Certbot

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # managed by Certbot
    ssl_prefer_server_ciphers on; # managed by Certbot

    ssl_ciphers 'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES256-SHA:ECDHE-ECDSA-DES-CBC3-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA:!DSS';

    if ($scheme != "https") {
        return 301 https://$host$request_uri;
    } # managed by Certbot
{% else %}
# HTTPS disabled by ansible config, set dlock_gateway__enable_https to enable
{% endif %}
}
