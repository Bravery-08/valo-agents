from curl_cffi import requests
from bs4 import BeautifulSoup
import csv
import os


def getmappool():
    page = requests.get("https://www.thespike.gg/valorant/maps/map-pool")
    soup = BeautifulSoup(page.text, "html.parser")

    all_a = soup.find_all('a')
    # for i in range(len(all_a)):
    #     print(i, all_a[i])

    start = 14
    map_pool = []
    for ind in range(start, start+7):
        map_pool.append(all_a[ind].get_text().split()[0])

    return map_pool


def getagents(map):
    agents = {}
    url = 'https://api.tracker.gg/api/v2/valorant/insights/agents?playlist=competitive&map={}&division=radiant'.format(
        map.lower())
    result = requests.get(url, impersonate="chrome110").json()
    data = result["data"]["insights"]

    agents = {
        agent["metadata"]["name"]: {
            "role": agent["metadata"]["className"],
            "winrate": agent["stats"]["wlPercentage"]["value"],
            "played": agent["stats"]["playedPct"]["value"]
        }
        for agent in data
    }
    sorted_agents = sorted(
        agents.items(),
        key=lambda item: (item[1]["winrate"], item[1]["played"]),
        reverse=True
    )

    target_roles = {"Duelist", "Initiator", "Controller", "Sentinel"}
    best_agents = {"Map": map}
    extra_candidate_added = False
    ind = 1

    for name, stats in sorted_agents:
        if stats["played"] < 1:
            continue

        if stats["role"] in target_roles:
            best_agents[ind] = name
            ind += 1
            target_roles.remove(stats["role"])
        elif not extra_candidate_added:
            best_agents[ind] = name
            ind += 1
            extra_candidate_added = True

        if not target_roles and extra_candidate_added:
            break

    return best_agents


def writedata():
    map_pool = getmappool()
    csv_path = "C:\\Users\\shaur\\OneDrive\\Documents\\Code\\Python\\Valo\\valodata.csv"

    # Read old data if file exists
    old_data = {}
    if os.path.exists(csv_path):
        with open(csv_path, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Use Map as key
                old_data[row['Map']] = row

    with open(csv_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['Map', 1, 2, 3, 4, 5])
        writer.writeheader()

        for map in map_pool:
            d = getagents(map)

            # Fill missing keys or empty values from old_data if available
            if map in old_data:
                old_row = old_data[map]
                for key in ['Map', 1, 2, 3, 4, 5]:
                    # Since d keys are int except Map, convert to string when reading old_row
                    old_value = old_row.get(
                        str(key), '') if key != 'Map' else old_row.get('Map', '')
                    # If key missing or empty in current dict, fill from old
                    if key not in d or not d[key]:
                        d[key] = old_value

            writer.writerow(d)
            print(map + ' updated :)')


writedata()
os.startfile(
    "C:\\Users\\shaur\\OneDrive\\Documents\\Code\\Python\\Valo\\valodata.csv")

# print(getmappool())
