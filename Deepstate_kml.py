#!/usr/bin/env python3
import simplekml
import json
import urllib3
import subprocess
import os
import time
from datetime import datetime

def fetch_geojson():
    http = urllib3.PoolManager()
    response = http.request('GET', "https://deepstatemap.live/api/history/last.geojson")
    return json.loads(response.data.decode('utf-8'))

def generate_kml(data):
    iconURL = "https://deepstatemap.live/images/custom/"
    kml = simplekml.Kml()

    for feature in data['features']:
        properties = feature['properties']
        geom = feature['geometry']
        geom_type = geom['type']
        description = properties.get("description", "")

        if geom_type == 'Polygon':
            pol = kml.newpolygon(name=properties['name'],
                                 description=description,
                                 outerboundaryis=geom['coordinates'][0])
            pol.style.linestyle.color = simplekml.Color.hex(properties['stroke'][1:])
            pol.style.linestyle.width = properties['stroke-width']
            opacity = int(properties['fill-opacity'] * 100)
            pol.style.polystyle.color = simplekml.Color.changealphaint(opacity, simplekml.Color.hex(properties['fill'][1:]))

        elif geom_type == 'GeometryCollection':
            for geomColl in geom['geometries']:
                if geomColl['type'] == 'Polygon':
                    pol = kml.newpolygon(name=properties['name'],
                                         description=description,
                                         outerboundaryis=geomColl['coordinates'][0])
                    pol.style.linestyle.color = simplekml.Color.hex(properties['stroke'][1:])
                    pol.style.linestyle.width = properties['stroke-width']
                    opacity = int(properties['fill-opacity'] * 100)
                    pol.style.polystyle.color = simplekml.Color.changealphaint(opacity, simplekml.Color.hex(properties['fill'][1:]))

        elif geom_type == 'LineString':
            kml.newlinestring(name=properties['name'],
                              description=description,
                              coords=geom['coordinates'])

        elif geom_type == 'Point':
            iconStr = "{icon="
            iconStrStart = description.find(iconStr)
            if iconStrStart != -1:
                try:
                    iconStrEnd = description.index(',', iconStrStart)
                except ValueError:
                    iconStrEnd = description.index('}', iconStrStart)
                iconName = description[iconStrStart + len(iconStr):iconStrEnd]
                iconPath = iconURL + iconName + ".png"
            else:
                iconPath = ""

            pt = kml.newpoint(name=properties['name'],
                              description="",
                              coords=[geom['coordinates']])
            if iconPath:
                pt.style.iconstyle.icon.href = iconPath
                pt.style.labelstyle.scale = 0

        else:
            print("Unknown geometry type:", geom_type)

    return kml

def is_repo_dirty():
    output = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8")
    return bool(output.strip())

def commit_and_push_to_github(repo_dir, file_name):
    try:
        os.chdir(repo_dir)
        subprocess.run(["git", "add", file_name], check=True)
        subprocess.run(["git", "add", "Deepstate_kml.py"], check=True)

        if not is_repo_dirty():
            print("No changes detected in Git. Skipping commit.")
            return

        commit_message = f"Update {file_name} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)

        print(f"Committed and pushed {file_name} to GitHub successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error during Git operations: {e}")

def main():
    while True:
        try:
            data = fetch_geojson()
            kml = generate_kml(data)

            output_path = "C:\\Users\\adrie\\Deepstate_KML\\deepstate.kml"
            kml.save(output_path)
            print(f"KML saved to {output_path}")

            repo_dir = os.path.dirname(output_path)
            file_name = os.path.basename(output_path)
            commit_and_push_to_github(repo_dir, file_name)

        except Exception as e:
            print(f"Error occurred: {e}")

        print("Waiting 10 minutes before next update...")
        time.sleep(600)

if __name__ == "__main__":
    main()
