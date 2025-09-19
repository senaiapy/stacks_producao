t order and tell me the results!

● STEP-BY-STEP MANUAL COMMANDS

  1. CONNECT TO SERVER:
  ssh root@217.79.184.8

  2. REMOVE EXISTING STACK:
  docker stack rm supabase
  sleep 10
  docker config rm supabase_kong_config 2>/dev/null || true

  3. PREPARE DIRECTORIES:
  mkdir -p /opt/supabase/config

  4. EXIT SERVER AND UPLOAD KONG CONFIG:
  exit
  scp supabase/volumes/api/kong.yml root@217.79.184.8:/opt/supabase/config/
  ssh root@217.79.184.8

  5. CREATE DOCKER CONFIG:
  cd /opt/supabase
  docker config create supabase_kong_config config/kong.yml

  6. CREATE YAML FILE:
  cat > /opt/supabase/supabase-web.yml << 'EOF'
 version: "3.8"

configs:
  kong_config:
    external: true
    name: supabase_kong_config

services:
    kong:
      image: kong:2.8.1
      hostname: "{{.Service.Name}}.{{.Task.Slot}}"
      networks:
        - app_network
        - traefik_public
      configs:
        - source: kong_config
          target: /var/lib/kong/kong.yml
      environment:
        KONG_DATABASE: "off"
        KONG_DECLARATIVE_CONFIG: /var/lib/kong/kong.yml
        KONG_DNS_ORDER: LAST,A,CNAME
        KONG_PLUGINS: request-transformer,cors,key-auth,acl,basic-auth
        KONG_NGINX_PROXY_PROXY_BUFFER_SIZE: 160k
        KONG_NGINX_PROXY_PROXY_BUFFERS: 64 160k
        SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao"
        SUPABASE_SERVICE_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NTY4Njg0MDAsImV4cCI6MTkxNDYzNDgwMH0.bZ8_RsHDV_LMWXfjKbaVtC1mX4DWcrMT6iqP6EHovnI
      deploy:
        mode: replicated
        replicas: 1
        labels:
          - "traefik.enable=true"
          - "traefik.constraint-label=traefik_public"
          - "traefik.http.routers.supabase-api.rule=Host(`supabase.senaia.in`)"
          - "traefik.http.routers.supabase-api.entrypoints=websecure"
          - "traefik.http.routers.supabase-api.tls.certresolver=letsencrypt"
          - "traefik.http.services.supabase-api.loadbalancer.server.port=8000"

    studio:
      image: supabase/studio:20250224-d10db0f
      hostname: "{{.Service.Name}}.{{.Task.Slot}}"
      networks:
        - app_network
        - traefik_public
      environment:
        STUDIO_PG_META_URL: http://meta:8080
        POSTGRES_PASSWORD: Ma1x1x0x!!Ma1x1x0x!!
        DEFAULT_ORGANIZATION_NAME: senaia.ai
        DEFAULT_PROJECT_NAME: senaia.ai
        SUPABASE_URL: http://kong:8000
        SUPABASE_PUBLIC_URL: https://supabase.senaia.in
        SUPABASE_ANON_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao
        SUPABASE_SERVICE_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NTY4Njg0MDAsImV4cCI6MTkxNDYzNDgwMH0.bZ8_RsHDV_LMWXfjKbaVtC1mX4DWcrMT6iqP6EHovnI
        AUTH_JWT_SECRET: DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz
      deploy:
        mode: replicated
        replicas: 1
        labels:
          - "traefik.enable=true"
          - "traefik.constraint-label=traefik_public"
          - "traefik.http.routers.supabase-studio.rule=Host(`studio.senaia.in`)"
          - "traefik.http.routers.supabase-studio.entrypoints=websecure"
          - "traefik.http.routers.supabase-studio.tls.certresolver=letsencrypt"
          - "traefik.http.services.supabase-studio.loadbalancer.server.port=3000"

      rest:
        image: postgrest/postgrest:v12.2.8
        hostname: "{{.Service.Name}}.{{.Task.Slot}}"
        networks:
          - app_network
        environment:
          PGRST_DB_URI: postgres://authenticator:Ma1x1x0x!!Ma1x1x0x!!@postgres:5432/chatwoot_database
          PGRST_DB_SCHEMAS: public,storage,graphql_public
          PGRST_DB_ANON_ROLE: anon
          PGRST_JWT_SECRET: DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz
          PGRST_OPENAPI_SERVER_PROXY_URI: https://supabase.senaia.in/rest/v1/
        deploy:
          mode: replicated
          replicas: 1

      meta:
        image: supabase/postgres-meta:v0.86.1
        hostname: "{{.Service.Name}}.{{.Task.Slot}}"
        networks:
          - app_network
        environment:
          PG_META_PORT: 8080
          PG_META_DB_HOST: postgres
          PG_META_DB_PORT: 5432
          PG_META_DB_NAME: chatwoot_database
          PG_META_DB_USER: postgres
          PG_META_DB_PASSWORD: Ma1x1x0x!!Ma1x1x0x!!
        deploy:
          mode: replicated
          replicas: 1

      storage:
        image: supabase/storage-api:v1.19.3
        hostname: "{{.Service.Name}}.{{.Task.Slot}}"
        networks:
          - app_network
        volumes:
          - supabase_storage:/var/lib/storage
        environment:
          ANON_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzU2ODY4NDAwLCJleHAiOjE5MTQ2MzQ4MDB9.92l2hcU3eK2GZCkzkLujEpl45fXqCN_p3Ad9qsxijao
          SERVICE_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NTY4Njg0MDAsImV4cCI6MTkxNDYzNDgwMH0.bZ8_RsHDV_LMWXfjKbaVtC1mX4DWcrMT6iqP6EHovnI
          POSTGREST_URL: http://rest:3000
          PGRST_JWT_SECRET: DV7ztkuZnEJWWKQ68haLZ2qIXCMRxODz
          DATABASE_URL: postgres://postgres:Ma1x1x0x!!Ma1x1x0x!!@postgres:5432/chatwoot_database
          FILE_SIZE_LIMIT: 52428800
          STORAGE_BACKEND: file
          FILE_STORAGE_BACKEND_PATH: /var/lib/storage
          TENANT_ID: stub
          REGION: stub
          GLOBAL_S3_BUCKET: stub
          # deploy section removed to fix duplicate key error
        deploy:
          mode: replicated
          replicas: 1 
  
volumes:
  supabase_storage:
    driver: local

networks:
  app_network:
    external: true
  traefik_public:
    external: true
  EOF

  7. SETUP DATABASE ROLES:

  #CONTAINER POSTGRES:
  psql -U chatwoot_database -d chatwoot_database 

CREATE ROLE anon;
CREATE ROLE authenticated LOGIN INHERIT;
CREATE ROLE service_role  LOGIN INHERIT;
CREATE ROLE authenticator WITH LOGIN  'Ma1x1x0x!!Ma1x1x0x!!' NOINHERIT;
GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT service_role TO authenticator;
  

  8. DEPLOY STACK:
  docker stack deploy -c supabase-web.yml supabase

  9. WAIT AND UPDATE TRAEFIK:
  sleep 30
  docker service update --force traefik_traefik
  sleep 15

  10. CHECK STATUS:
  docker service ls | grep supabase
  curl -I https://studio.senaia.in
  curl -I https://supabase.senaia.in
