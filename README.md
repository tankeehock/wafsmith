# WAFSMITH

_A complete rewrite from Node.js to Python!_

## Setup

``` bash
# install uv
uv sync
```

## Run

### Extract

``` bash
uv run main.py extract --logs data/logs/sample-logs --payloads data/logs/extracted-payloads --api-key $ARK_API_KEY --base-url https://ark-ap-southeast.byteintl.net/api/v3 --model ep-20250405051644-vlkt5 --debug
```

### Create

``` bash
uv run main.py create --payloads data/test-dataset/payload-dataset-10 --traffic data/experiment/business-traffic/ --setup ./cli-app/infra --evaded data/experiment/payloadallthings/demo/output/post/evaded-payloads.txt --method GET --position url_parameter --api-key $ARK_API_KEY --base-url https://ark-ap-southeast.byteintl.net/api/v3 --model ep-20250405051644-vlkt5
```


### Evaluate
``` bash
uv run main.py evaluate --payloads data/test-dataset/payload-dataset-100 --traffic data/experiment/business-traffic/ --setup ./cli-app/infra --evaded data/experiment/payloadallthings/demo/output/post/evaded-payloads.txt --method post --position http-body
```

## TODO
- Troubleshoot the accuracy of the Create Workflow
    - Statistics for the evaded payloads after rules aggregation may not tally
- Refactor code, rebase classes to model sub-directory
- Improve code readability and logging output