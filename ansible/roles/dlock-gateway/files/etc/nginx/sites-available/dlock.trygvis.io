server {
    listen 80;
    server_name dlock.trygvis.io;

    location / {
        proxy_pass http://localhost:5000;
    }

    include "./dlock.trygvis.io.allow";
    deny all;

    listen 443 ssl; # managed by Certbot
ssl_certificate /etc/letsencrypt/live/dlock.trygvis.io/fullchain.pem; # managed by Certbot
ssl_certificate_key /etc/letsencrypt/live/dlock.trygvis.io/privkey.pem; # managed by Certbot
ssl_session_cache shared:le_nginx_SSL:1m; # managed by Certbot
ssl_session_timeout 1440m; # managed by Certbot

ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # managed by Certbot
ssl_prefer_server_ciphers on; # managed by Certbot

ssl_ciphers "ECDHE-ECDSA-AES128-GCM-SHA256 ECDHE-ECDSA-AES256-GCM-SHA384 ECDHE-ECDSA-AES128-SHA ECDHE-ECDSA-AES256-SHA 
ECDHE-ECDSA-AES128-SHA256 ECDH$

    if ($scheme != "https") {
        return 301 https://$host$request_uri;
    } # managed by Certbot
}
