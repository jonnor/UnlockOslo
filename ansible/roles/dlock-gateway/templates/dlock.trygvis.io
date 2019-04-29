server {
    listen 80;
    server_name {{web_hostname}};

# deny everything except for whitelisted IPs
{% for ip in vault_http_api_allow %}
    allow {{ ip }};
{% endfor %}
    deny all;

    location / {
        proxy_pass http://localhost:5000;
    }
}
