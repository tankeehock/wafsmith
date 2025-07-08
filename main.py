from email.policy import default
import click
import wafsmith.cmd.evaluate
import wafsmith.cmd.create
import wafsmith.cmd.extract
from wafsmith.lib.console import init_logging
import logging

def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func
    return _add_options

_basic_options = [
    click.option("--debug", is_flag=True, help="Debug flag"),
    click.option("--threads", default=10, help="Specify the number of threads to be used during the invocation process. Default is 10")
]

_testing_options = [
    click.option("--payloads", required=True, help="Input directory / file containing the payloads"),
    click.option("--evaded", required=True, help="Specify the output file for evaded payload(s) if any"),
    click.option("--setup", required=True, help="Specify the directory which contains the docker compose enviornment setup"),
    click.option("--traffic", required=True, help="Specify directory / file containing business traffic content for simulation"),
    click.option("--position", default="url_parameters", help="Specify the postion of the payload in the HTTP request. Default is url_parameters"),
    click.option("--method", default="GET", help="Specify the HTTP method for the payload. Default is GET.")
]

_llm_options = [
    click.option("--api-key", required=True, help="API key"),
    click.option("--base-url", required=True, help="LLM service endpoint"),
    click.option("--model",required=True, help="AI model"),
]

_creation_options = [
    click.option("--rules",required=True, help="Specify the output file for generated WAF rules if any")
]

_extraction_options = [
    click.option("--logs", required=True, help="Input directory / file containing the logs"),
    click.option("--payloads", required=True, help="Specify the output file for extracted payload(s) if any")
]

def initialize(debug):
    # Show only relevant logs
    logging.getLogger("openai").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging_level = logging.INFO
    if debug:
        logging_level = logging.DEBUG
    init_logging(logging_level)

# Debug group
@click.group()
def cli():
    pass

@cli.command("evaluate")
@add_options(_basic_options)
@add_options(_testing_options)
def evaluate(payloads, evaded, setup, traffic, position, method, threads, debug):
    initialize(debug)
    wafsmith.cmd.evaluate.run(
        payloads, evaded, setup, traffic, position, method, threads
    )

@cli.command("create")
@add_options(_basic_options)
@add_options(_testing_options)
@add_options(_creation_options)
@add_options(_llm_options)
def create(payloads, evaded, rules, setup, traffic, position, method, threads, api_key, base_url, model, debug):
    initialize(debug)
    wafsmith.cmd.create.run(
        payloads, evaded, rules, setup, traffic, position, method, threads, api_key, base_url, model
    )

@cli.command("extract")
@add_options(_basic_options)
@add_options(_llm_options)
@add_options(_extraction_options)
def extract(logs, payloads, threads, api_key, base_url, model, debug):
    initialize(debug)
    wafsmith.cmd.extract.run(logs, payloads, threads, api_key, base_url, model)

if __name__ == "__main__":
    cli()
