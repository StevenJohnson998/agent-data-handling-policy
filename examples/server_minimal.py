"""Minimal ADHP server — 10 lines."""

from adhp import ADHPServer

server = ADHPServer(
    name="MinimalServer",
    config="examples/configs/eu_standard.json",
)


@server.tool()
def echo(text: str) -> str:
    return text


if __name__ == "__main__":
    server.run(port=8000)
