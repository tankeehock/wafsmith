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
uv run main.py extract --logs data/logs/sample-logs/sample-set-50 --payloads data/demo/output/evaded-payloads/sample-extract-50.payloads --api-key $ARK_API_KEY --base-url https://ark-ap-southeast.byteintl.net/api/v3 --model ep-20250405051644-vlkt5
```

### Create

``` bash
uv run main.py create --payloads data/demo/output/extracted-payloads --traffic data/experiment/business-traffic/ --setup ./cli-app/infra --evaded data/demo/output/evaded-payloads/get-evaded-payloads.txt --rules data/demo/output/modesecurity.rules --method GET --position url_parameter --api-key $ARK_API_KEY --base-url https://ark-ap-southeast.byteintl.net/api/v3 --model ep-20250405051644-vlkt5
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
- Improve the project file structure