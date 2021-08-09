from pathlib import Path

from conf import get_latest_version


def make_html(url: str) -> str:
    return f"""
<html>
  <head>
    <meta http-equiv="refresh" content="0; url='{url}'" />
  </head>
  <body>
    <p>Please follow <a href="{url}">this link</a>.</p>
  </body>
</html>
"""


if __name__ == "__main__":
    version = get_latest_version()

    print(f"Latest version: {version}")

    index = Path("./build/html/index.html")

    with index.open("w") as f:
        html = make_html(f"{version}/")
        f.write(html)

    print(f"Wrote to {str(index)}:")
    print(html)
