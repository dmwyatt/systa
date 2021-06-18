"""A stupid script for pulling the event constants off of microsoft's doc page
so you can paste them into code."""
import requests
from bs4 import BeautifulSoup


def parse():
    response = requests.get(
        "https://docs.microsoft.com/en-us/windows/desktop/WinAuto/event-constants"
    )
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find_all("table")[0]

    data = []

    for row in table.tbody.find_all("tr"):
        # cols = row.find_all('td')
        col_data = []
        dts = row.find_all("dt")
        assert len(dts) == 2
        event_name = dts[0].text.strip()
        event_value = dts[1].text.strip()
        print(f"{event_name} = {event_value}")

    #     cols = [ele.text.strip() for ele in cols]
    #     data.append(cols)
    #
    # pprint(data)


if __name__ == "__main__":
    parse()
