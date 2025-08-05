# WAFSMITH

Leveraging on LLM's abilities to mimic cognitive human agents, WAFSmith aims to reduce the friction of WAF rule governance from rule creation to deployment in minutes. It is designed as a highly disruptive tool to augment Blue Team operations in a rapidly evolving threat landscape. It was developed to enhance Blue Team's capabilities to respond to threats in a fast and effective manner, without compromising business operations. The solution is first of the kind, especially in the open source landscape, a novel approach to solve a challenging problem of WAF rule governance.

Whitepaper: https://docs.google.com/document/d/1Uf7WtzsISM9nGY8pc53-eoZa1ce8hNAs9JrMOPFLkX4/edit?usp=sharing

_A complete rewrite from Node.js to Python!_

## Setup


### Prerequisites

1. `uv` package management
In this rewrite, we use [`uv`](https://github.com/astral-sh/uv) to manage the dependencies.

``` bash
# install uv
uv sync
```

2. Set up the docker images
```bash
cd cli-app/infra
docker compose up
# To check if the docker containers run properly
curl 127.0.0.1 
# expect to see `Hello, World!`
docker compose down
```

3. Export the variables

``` bash
export OPENAPI_ENDPOINT="https://api.openai.com/v1"
export OPENAPI_MODEL="o1"
export API_KEY="hello-world"
```

## Run

### Extract

``` bash
Usage: main.py extract [OPTIONS]

Options:
  --debug            Debug flag
  --threads INTEGER  Specify the number of threads to be used during the
                     invocation process. Default is 10
  --api-key TEXT     API key  [required]
  --base-url TEXT    LLM service endpoint  [required]
  --model TEXT       AI model  [required]
  --logs TEXT        Input directory / file containing the logs  [required]
  --payloads TEXT    Specify the output file for extracted payload(s) if any
                     [required]
  --help             Show this message and exit.
```

``` bash
uv run main.py extract --logs data/logs/sample-logs/sample-set-50 --payloads data/demo/output/evaded-payloads/sample-extract-50.payloads --api-key $API_KEY --base-url $OPENAPI_ENDPOINT --model $OPENAPI_MODEL
```

### Create
``` bash
Usage: main.py create [OPTIONS]

Options:
  --debug            Debug flag
  --threads INTEGER  Specify the number of threads to be used during the
                     invocation process. Default is 10
  --payloads TEXT    Input directory / file containing the payloads
                     [required]
  --evaded TEXT      Specify the output file for evaded payload(s) if any
                     [required]
  --setup TEXT       Specify the directory which contains the docker compose
                     enviornment setup  [required]
  --traffic TEXT     Specify directory / file containing business traffic
                     content for simulation  [required]
  --position TEXT    Specify the postion of the payload in the HTTP request.
                     Default is url_parameters
  --method TEXT      Specify the HTTP method for the payload. Default is GET.
  --rules TEXT       Specify the output file for generated WAF rules if any
                     [required]
  --api-key TEXT     API key  [required]
  --base-url TEXT    LLM service endpoint  [required]
  --model TEXT       AI model  [required]
  --help             Show this message and exit.
```


``` bash
uv run main.py create --payloads data/demo/output/extracted-payloads --traffic data/experiment/business-traffic/ --setup ./cli-app/infra --evaded data/demo/output/evaded-payloads/get-evaded-payloads.txt --rules data/demo/output/modesecurity.rules --method GET --position url_parameter --api-key $API_KEY --base-url $OPENAPI_ENDPOINT --model $OPENAPI_MODEL
```

### Evaluate

``` bash
Usage: main.py evaluate [OPTIONS]

Options:
  --debug            Debug flag
  --threads INTEGER  Specify the number of threads to be used during the
                     invocation process. Default is 10
  --payloads TEXT    Input directory / file containing the payloads
                     [required]
  --evaded TEXT      Specify the output file for evaded payload(s) if any
                     [required]
  --setup TEXT       Specify the directory which contains the docker compose
                     enviornment setup  [required]
  --traffic TEXT     Specify directory / file containing business traffic
                     content for simulation  [required]
  --position TEXT    Specify the postion of the payload in the HTTP request.
                     Default is url_parameters
  --method TEXT      Specify the HTTP method for the payload. Default is GET.
  --help             Show this message and exit.
```

``` bash
uv run main.py evaluate --payloads data/test-dataset/payload-dataset-100 --traffic data/experiment/business-traffic/ --setup ./cli-app/infra --evaded data/experiment/payloadallthings/demo/output/post/evaded-payloads.txt --method post --position http-body
```

# Troubleshooting

- Issues with Docker persmissions
Depending on how your Docker is installed, wafsmith might have issues trying to instantiate the docker containers. As such, these entries in the in the docker compose file has been commented out. If you want to access the log files, do ensure that you can mount the folders from your docker.

```bash
./modsecurity/modsecurity.conf:/etc/modsecurity.d/modsecurity.conf
./nginx/logs:/var/log/nginx
```