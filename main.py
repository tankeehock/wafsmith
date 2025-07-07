import click
import wafsmith.cmd.evaluate


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--payloads", required=True, help="Input directory / file containing the payloads"
)
@click.option(
    "--evaded",
    required=True,
    help="Specify the output file for evaded payload(s) if any",
)
@click.option(
    "--setup",
    required=True,
    help="Specify the directory which contains the docker compose enviornment setup",
)
@click.option(
    "--traffic",
    required=True,
    help="Specify directory / file containing business traffic content for simulation",
)
@click.option(
    "--position",
    default="url_parameters",
    help="Specify the postion of the payload in the HTTP request. Default is url_parameters",
)
@click.option(
    "--method",
    default="GET",
    help="Specify the HTTP method for the payload. Default is GET.",
)
@click.option(
    "--threads",
    default=10,
    help="Specify the number of threads to be used during the rule generation process. Default is 10",
)
def evaluate(payloads, evaded, setup, traffic, position, method, threads):
    wafsmith.cmd.evaluate.run(
        payloads, evaded, setup, traffic, position, method, threads
    )
    pass


if __name__ == "__main__":
    cli()
