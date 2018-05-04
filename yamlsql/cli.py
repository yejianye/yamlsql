#!/usr/bin/env python
import click

from yamlsql.server import app

@click.group()
def cli():
    pass

@cli.command(help='Run HTTP server')
@click.option('--port', default=5000)
@click.option('--debug/--no-debug', default=False)
def runserver(port, debug):
    app.run(port=port, debug=debug)

if __name__ == '__main__':
    cli()
