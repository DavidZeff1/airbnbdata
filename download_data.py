import os
import requests
import time

# Mapping of directory path to (listings.csv.gz URL, listings.csv URL)
data_map = {
    "data/The Netherlands/Amsterdam": (
        "https://data.insideairbnb.com/the-netherlands/north-holland/amsterdam/2025-09-11/data/listings.csv.gz",
        "https://data.insideairbnb.com/the-netherlands/north-holland/amsterdam/2025-09-11/visualisations/listings.csv"
    ),
    "data/The Netherlands/Rotterdam": (
        "https://data.insideairbnb.com/the-netherlands/south-holland/rotterdam/2025-09-25/data/listings.csv.gz",
        "https://data.insideairbnb.com/the-netherlands/south-holland/rotterdam/2025-09-25/visualisations/listings.csv"
    ),
    "data/The Netherlands/The Hague": (
        "https://data.insideairbnb.com/the-netherlands/south-holland/the-hague/2025-09-25/data/listings.csv.gz",
        "https://data.insideairbnb.com/the-netherlands/south-holland/the-hague/2025-09-25/visualisations/listings.csv"
    ),
    "data/Belgium/Antwerp": (
        "https://data.insideairbnb.com/belgium/vlg/antwerp/2025-09-28/data/listings.csv.gz",
        "https://data.insideairbnb.com/belgium/vlg/antwerp/2025-09-28/visualisations/listings.csv"
    ),
    "data/Belgium/Brussels": (
        "https://data.insideairbnb.com/belgium/bru/brussels/2025-09-23/data/listings.csv.gz",
        "https://data.insideairbnb.com/belgium/bru/brussels/2025-09-23/visualisations/listings.csv"
    ),
    "data/Belgium/Ghent": (
        "https://data.insideairbnb.com/belgium/vlg/ghent/2025-09-26/data/listings.csv.gz",
        "https://data.insideairbnb.com/belgium/vlg/ghent/2025-09-26/visualisations/listings.csv"
    ),
    "data/Greece/Athens": (
        "https://data.insideairbnb.com/greece/attica/athens/2025-09-26/data/listings.csv.gz",
        "https://data.insideairbnb.com/greece/attica/athens/2025-09-26/visualisations/listings.csv"
    ),
    "data/Greece/Crete": (
        "https://data.insideairbnb.com/greece/crete/crete/2025-09-28/data/listings.csv.gz",
        "https://data.insideairbnb.com/greece/crete/crete/2025-09-28/visualisations/listings.csv"
    ),
    "data/Greece/South Aegean": (
        "https://data.insideairbnb.com/greece/south-aegean/south-aegean/2025-09-23/data/listings.csv.gz",
        "https://data.insideairbnb.com/greece/south-aegean/south-aegean/2025-09-23/visualisations/listings.csv"
    ),
    "data/Greece/Thessaloniki": (
        "https://data.insideairbnb.com/greece/central-macedonia/thessaloniki/2025-09-26/data/listings.csv.gz",
        "https://data.insideairbnb.com/greece/central-macedonia/thessaloniki/2025-09-26/visualisations/listings.csv"
    ),
    "data/Spain/Barcelona": (
        "https://data.insideairbnb.com/spain/catalonia/barcelona/2025-09-14/data/listings.csv.gz",
        "https://data.insideairbnb.com/spain/catalonia/barcelona/2025-09-14/visualisations/listings.csv"
    ),
    "data/Spain/Euskadi": (
        "https://data.insideairbnb.com/spain/pv/euskadi/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/spain/pv/euskadi/2025-09-29/visualisations/listings.csv"
    ),
    "data/Spain/Girona": (
        "https://data.insideairbnb.com/spain/catalonia/girona/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/spain/catalonia/girona/2025-09-29/visualisations/listings.csv"
    ),
    "data/Spain/Madrid": (
        "https://data.insideairbnb.com/spain/comunidad-de-madrid/madrid/2025-09-14/data/listings.csv.gz",
        "https://data.insideairbnb.com/spain/comunidad-de-madrid/madrid/2025-09-14/visualisations/listings.csv"
    ),
    "data/Spain/Malaga": (
        "https://data.insideairbnb.com/spain/andaluc%C3%ADa/malaga/2025-09-30/data/listings.csv.gz",
        "https://data.insideairbnb.com/spain/andaluc%C3%ADa/malaga/2025-09-30/visualisations/listings.csv"
    ),
    "data/Spain/Mallorca": (
        "https://data.insideairbnb.com/spain/islas-baleares/mallorca/2025-09-21/data/listings.csv.gz",
        "https://data.insideairbnb.com/spain/islas-baleares/mallorca/2025-09-21/visualisations/listings.csv"
    ),
    "data/Spain/Menorca": (
        "https://data.insideairbnb.com/spain/islas-baleares/menorca/2025-09-30/data/listings.csv.gz",
        "https://data.insideairbnb.com/spain/islas-baleares/menorca/2025-09-30/visualisations/listings.csv"
    ),
    "data/Spain/Sevilla": (
        "https://data.insideairbnb.com/spain/andaluc%C3%ADa/sevilla/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/spain/andaluc%C3%ADa/sevilla/2025-09-29/visualisations/listings.csv"
    ),
    "data/Spain/Valencia": (
        "https://data.insideairbnb.com/spain/vc/valencia/2025-09-23/data/listings.csv.gz",
        "https://data.insideairbnb.com/spain/vc/valencia/2025-09-23/visualisations/listings.csv"
    ),
    "data/Italy/Bergamo": (
        "https://data.insideairbnb.com/italy/lombardia/bergamo/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/italy/lombardia/bergamo/2025-09-29/visualisations/listings.csv"
    ),
    "data/Italy/Bologna": (
        "https://data.insideairbnb.com/italy/emilia-romagna/bologna/2025-09-22/data/listings.csv.gz",
        "https://data.insideairbnb.com/italy/emilia-romagna/bologna/2025-09-22/visualisations/listings.csv"
    ),
    "data/Italy/Florence": (
        "https://data.insideairbnb.com/italy/toscana/florence/2025-09-22/data/listings.csv.gz",
        "https://data.insideairbnb.com/italy/toscana/florence/2025-09-22/visualisations/listings.csv"
    ),
    "data/Italy/Milan": (
        "https://data.insideairbnb.com/italy/lombardy/milan/2025-09-22/data/listings.csv.gz",
        "https://data.insideairbnb.com/italy/lombardy/milan/2025-09-22/visualisations/listings.csv"
    ),
    "data/Italy/Naples": (
        "https://data.insideairbnb.com/italy/campania/naples/2025-09-22/data/listings.csv.gz",
        "https://data.insideairbnb.com/italy/campania/naples/2025-09-22/visualisations/listings.csv"
    ),
    "data/Italy/Puglia": (
        "https://data.insideairbnb.com/italy/puglia/puglia/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/italy/puglia/puglia/2025-09-29/visualisations/listings.csv"
    ),
    "data/Italy/Rome": (
        "https://data.insideairbnb.com/italy/lazio/rome/2025-09-14/data/listings.csv.gz",
        "https://data.insideairbnb.com/italy/lazio/rome/2025-09-14/visualisations/listings.csv"
    ),
    "data/Italy/Sicily": (
        "https://data.insideairbnb.com/italy/sicilia/sicily/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/italy/sicilia/sicily/2025-09-29/visualisations/listings.csv"
    ),
    "data/Italy/Trentino": (
        "https://data.insideairbnb.com/italy/trentino-alto-adige-s%C3%BCdtirol/trentino/2025-09-30/data/listings.csv.gz",
        "https://data.insideairbnb.com/italy/trentino-alto-adige-s%C3%BCdtirol/trentino/2025-09-30/visualisations/listings.csv"
    ),
    "data/Italy/Venice": (
        "https://data.insideairbnb.com/italy/veneto/venice/2025-09-11/data/listings.csv.gz",
        "https://data.insideairbnb.com/italy/veneto/venice/2025-09-11/visualisations/listings.csv"
    ),
    "data/Germany/Berlin": (
        "https://data.insideairbnb.com/germany/be/berlin/2025-09-23/data/listings.csv.gz",
        "https://data.insideairbnb.com/germany/be/berlin/2025-09-23/visualisations/listings.csv"
    ),
    "data/Germany/Munich": (
        "https://data.insideairbnb.com/germany/bv/munich/2025-09-27/data/listings.csv.gz",
        "https://data.insideairbnb.com/germany/bv/munich/2025-09-27/visualisations/listings.csv"
    ),
    "data/France/Bordeaux": (
        "https://data.insideairbnb.com/france/nouvelle-aquitaine/bordeaux/2025-09-18/data/listings.csv.gz",
        "https://data.insideairbnb.com/france/nouvelle-aquitaine/bordeaux/2025-09-18/visualisations/listings.csv"
    ),
    "data/France/Lyon": (
        "https://data.insideairbnb.com/france/auvergne-rhone-alpes/lyon/2025-09-18/data/listings.csv.gz",
        "https://data.insideairbnb.com/france/auvergne-rhone-alpes/lyon/2025-09-18/visualisations/listings.csv"
    ),
    "data/France/Paris": (
        "https://data.insideairbnb.com/france/ile-de-france/paris/2025-09-12/data/listings.csv.gz",
        "https://data.insideairbnb.com/france/ile-de-france/paris/2025-09-12/visualisations/listings.csv"
    ),
    "data/France/Pays Basque": (
        "https://data.insideairbnb.com/france/pyr%C3%A9n%C3%A9es-atlantiques/pays-basque/2025-09-21/data/listings.csv.gz",
        "https://data.insideairbnb.com/france/pyr%C3%A9n%C3%A9es-atlantiques/pays-basque/2025-09-21/visualisations/listings.csv"
    ),
    "data/United Kingdom/Bristol": (
        "https://data.insideairbnb.com/united-kingdom/england/bristol/2025-09-26/data/listings.csv.gz",
        "https://data.insideairbnb.com/united-kingdom/england/bristol/2025-09-26/visualisations/listings.csv"
    ),
    "data/United Kingdom/Edinburgh": (
        "https://data.insideairbnb.com/united-kingdom/scotland/edinburgh/2025-09-21/data/listings.csv.gz",
        "https://data.insideairbnb.com/united-kingdom/scotland/edinburgh/2025-09-21/visualisations/listings.csv"
    ),
    "data/United Kingdom/Greater Manchester": (
        "https://data.insideairbnb.com/united-kingdom/england/greater-manchester/2025-09-26/data/listings.csv.gz",
        "https://data.insideairbnb.com/united-kingdom/england/greater-manchester/2025-09-26/visualisations/listings.csv"
    ),
    "data/United Kingdom/London": (
        "https://data.insideairbnb.com/united-kingdom/england/london/2025-09-14/data/listings.csv.gz",
        "https://data.insideairbnb.com/united-kingdom/england/london/2025-09-14/visualisations/listings.csv"
    ),
    "data/Hungary/Budapest": (
        "https://data.insideairbnb.com/hungary/k%C3%B6z%C3%A9p-magyarorsz%C3%A1g/budapest/2025-09-25/data/listings.csv.gz",
        "https://data.insideairbnb.com/hungary/k%C3%B6z%C3%A9p-magyarorsz%C3%A1g/budapest/2025-09-25/visualisations/listings.csv"
    ),
    "data/Denmark/Copenhagen": (
        "https://data.insideairbnb.com/denmark/hovedstaden/copenhagen/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/denmark/hovedstaden/copenhagen/2025-09-29/visualisations/listings.csv"
    ),
    "data/Ireland/Dublin": (
        "https://data.insideairbnb.com/ireland/leinster/dublin/2025-09-16/data/listings.csv.gz",
        "https://data.insideairbnb.com/ireland/leinster/dublin/2025-09-16/visualisations/listings.csv"
    ),
    "data/Ireland/Ireland": (
        "https://data.insideairbnb.com/ireland/2025-09-26/data/listings.csv.gz",
        "https://data.insideairbnb.com/ireland/2025-09-26/visualisations/listings.csv"
    ),
    "data/Switzerland/Geneva": (
        "https://data.insideairbnb.com/switzerland/geneva/geneva/2025-09-28/data/listings.csv.gz",
        "https://data.insideairbnb.com/switzerland/geneva/geneva/2025-09-28/visualisations/listings.csv"
    ),
    "data/Switzerland/Vaud": (
        "https://data.insideairbnb.com/switzerland/vd/vaud/2025-11-01/data/listings.csv.gz",
        "https://data.insideairbnb.com/switzerland/vd/vaud/2025-11-01/visualisations/listings.csv"
    ),
    "data/Switzerland/Zurich": (
        "https://data.insideairbnb.com/switzerland/z%C3%BCrich/zurich/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/switzerland/z%C3%BCrich/zurich/2025-09-29/visualisations/listings.csv"
    ),
    "data/Turkey/Istanbul": (
        "https://data.insideairbnb.com/turkey/marmara/istanbul/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/turkey/marmara/istanbul/2025-09-29/visualisations/listings.csv"
    ),
    "data/Portugal/Lisbon": (
        "https://data.insideairbnb.com/portugal/lisbon/lisbon/2025-09-21/data/listings.csv.gz",
        "https://data.insideairbnb.com/portugal/lisbon/lisbon/2025-09-21/visualisations/listings.csv"
    ),
    "data/Portugal/Porto": (
        "https://data.insideairbnb.com/portugal/norte/porto/2025-09-21/data/listings.csv.gz",
        "https://data.insideairbnb.com/portugal/norte/porto/2025-09-21/visualisations/listings.csv"
    ),
    "data/Czech Republic/Prague": (
        "https://data.insideairbnb.com/czech-republic/prague/prague/2025-09-23/data/listings.csv.gz",
        "https://data.insideairbnb.com/czech-republic/prague/prague/2025-09-23/visualisations/listings.csv"
    ),
    "data/Latvia/Riga": (
        "https://data.insideairbnb.com/latvia/riga/riga/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/latvia/riga/riga/2025-09-29/visualisations/listings.csv"
    ),
    "data/Sweden/Stockholm": (
        "https://data.insideairbnb.com/sweden/stockholms-l%C3%A4n/stockholm/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/sweden/stockholms-l%C3%A4n/stockholm/2025-09-29/visualisations/listings.csv"
    ),
    "data/Norway/Oslo": (
        "https://data.insideairbnb.com/norway/oslo/oslo/2025-09-29/data/listings.csv.gz",
        "https://data.insideairbnb.com/norway/oslo/oslo/2025-09-29/visualisations/listings.csv"
    ),
    "data/Malta/Malta": (
        "https://data.insideairbnb.com/malta/2025-09-26/data/listings.csv.gz",
        "https://data.insideairbnb.com/malta/2025-09-26/visualisations/listings.csv"
    ),
    "data/Austria/Vienna": (
        "https://data.insideairbnb.com/austria/vienna/vienna/2025-09-14/data/listings.csv.gz",
        "https://data.insideairbnb.com/austria/vienna/vienna/2025-09-14/visualisations/listings.csv"
    ),
}

def download_file(url, target_path):
    print(f"Downloading {url} to {target_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Done.")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def main():
    base_dir = "/Users/davidzeff/Desktop/Data Science Projects/airbnb"
    for relative_dir, (gz_url, csv_url) in data_map.items():
        full_dir = os.path.join(base_dir, relative_dir)
        
        # Ensure directory exists
        if not os.path.exists(full_dir):
            print(f"Directory not found, creating: {full_dir}")
            os.makedirs(full_dir, exist_ok=True)
        
        # Download listings.csv.gz
        gz_target = os.path.join(full_dir, "listings.csv.gz")
        if not os.path.exists(gz_target):
            download_file(gz_url, gz_target)
        else:
            print(f"Skipping {gz_target}, already exists.")
            
        # Download listings.csv
        csv_target = os.path.join(full_dir, "listings.csv")
        if not os.path.exists(csv_target):
            download_file(csv_url, csv_target)
        else:
            print(f"Skipping {csv_target}, already exists.")

if __name__ == "__main__":
    main()
