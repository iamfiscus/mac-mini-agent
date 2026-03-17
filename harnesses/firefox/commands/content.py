"""Extract page content from DOM — faster and more accurate than OCR."""

import json

import click

from connection import connect


@click.command()
@click.option("--format", "fmt", type=click.Choice(["text", "html"]), default="text")
@click.option("--selector", "-s", default=None, help="CSS selector to extract from")
@click.option("--json-output", "--json", is_flag=True)
@click.pass_context
def content(ctx, fmt, selector, json_output):
    """Extract page text or HTML content from the DOM."""
    host = ctx.obj["host"]
    port = ctx.obj["port"]

    with connect(host, port) as client:
        title = client.title
        url = client.get_url()

        if selector:
            from marionette_driver.by import By
            element = client.find_element(By.CSS_SELECTOR, selector)
            if fmt == "html":
                text = element.get_attribute("outerHTML")
            else:
                text = element.text
        else:
            if fmt == "html":
                text = client.page_source
            else:
                # Get text content of body
                text = client.execute_script(
                    "return document.body.innerText;"
                )

    if json_output:
        click.echo(json.dumps({
            "status": "ok",
            "title": title,
            "url": url,
            "format": fmt,
            "content": text,
            "length": len(text),
        }))
    else:
        click.echo(text)
