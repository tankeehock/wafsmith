#!/bin/bash
export OPENAPI_ENDPOINT="hello-world"
export OPENAPI_MODEL="hello-world"
export API_KEY="hello-world"

export RISK_TYPE="demo"
export METHOD="POST"
export POSITION="http-body"

# evaluate
lwrc evaluate ../data/payloadallthings/${RISK_TYPE} -t ../data/experiment/business-traffic/ -s ./infra -e ../data/experiment/payloadallthings/${RISK_TYPE}/output/${METHOD}/evaded-payloads.txt -m ${METHOD}$ -p ${POSITION}

lwrc create ../data/experiment/payloadallthings/${RISK_TYPE}/output/${METHOD}/evaded-payloads.txt -t ../data/experiment/business-traffic/ -s ./infra -o ../data/experiment/payloadallthings/${RISK_TYPE}/output/${METHOD}/custom-${RISK_TYPE}-modsecurity-rules.conf -e ../data/experiment/payloadallthings/${RISK_TYPE}/output/${METHOD}/evaded-after-rule-creation.txt -k ${ARK_API_KEY} -b ${OPENAPI_ENDPOINT} -l ${OPENAPI_MODEL} -m ${METHOD}$ -p ${POSITION} -x 50

# move the generated rules over to the rules folder
cp ../data/experiment/payloadallthings/${RISK_TYPE}/output/${METHOD}/custom-${RISK_TYPE}-modsecurity-rules.conf ./infra/rules/custom-${RISK_TYPE}-modsecurity-rules.conf

lwrc evaluate ../data/payloadallthings/${RISK_TYPE} -t ../data/experiment/business-traffic/ -s ./infra -e ../data/experiment/payloadallthings/${RISK_TYPE}/output/${METHOD}/evaded-payloads-after-rules-creation.txt -m ${METHOD}$ -p ${POSITION}