# README

Source: https://github.com/coreruleset/modsecurity-crs-docker

``` bash
# Downloading CRS ruleset
git clone https://github.com/coreruleset/coreruleset.git
cd coreruleset/rules

# Running owasp/modsecurity-crs:nginx image
docker run -p 8080:8080 -ti -e PARANOIA=4 -v rules:/opt/owasp-crs/rules:ro --rm owasp/modsecurity-crs:nginx
```

## File Directory
- ./rules-tuning : Tuning rules for CRS
- ./nginx : Configuration and log files for Nginx
- ./modsecurity: Configuration and log files for Modsecurity
- ./web-app : Web Application Simulating Business Opearations

## Deployment

```
docker compose up
```

**Update Rules After Deployment**
``` bash
# Requires the container to be restarted
# update the rules in  /rules
docker compose restart crs-nginx
```

### web-app
Web Application Simulating Business Opearations
``` bash
docker build . -t web-app
docker run -p 3000:3000 -t web-app
```

## Others

``` bash
docker stop $(docker ps -q)
docker rm $(docker ps -a -q)
docker rmi $(docker images -q)
docker rmi $(docker images -f "dangling=true" -q)
```