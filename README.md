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
uv run main.py extract --logs data/logs/xss-sample-50/ --payloads data/demo/extracted-payloads/extracted-payloads-from-sample-log.payloads --api-key $OPENAI_API_KEY --base-url https://api.openai.com/v1 --model gpt-4.1-mini
```

### Create

``` bash
uv run main.py create --payloads data/demo/extracted-payloads --traffic data/test-dataset/business-traffic --setup ./cli-app/infra --evaded data/demo/evaded.payloads --rules data/demo/output/modesecurity.rules --method GET --position url_parameter --api-key $OPENAI_API_KEY --base-url https://api.openai.com/v1 --model gpt-4.1-mini
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