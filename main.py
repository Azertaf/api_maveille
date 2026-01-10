import requests
import json

# --- CONFIGURATION (À REMPLACER) ---
API_KEY = "AIzaSyDVdrWXDaoUGSdTLOTqUk0MwhU1escnhHM"        # La clé qui commence par AIza...
SEARCH_ENGINE_ID = "249cae3d517ff4425" # L'ID qui ressemble à 0123...:abc...
# -----------------------------------

def rechercher_google(requete, nombre_resultats=3):
    print(f"🔎 Recherche en cours pour : {requete}...")
    
    url = "https://www.googleapis.com/customsearch/v1"
    
    parametres = {
        'key': API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': requete,
        'num': nombre_resultats
    }
    
    try:
        reponse = requests.get(url, params=parametres)
        resultats = reponse.json()
        
        # Vérifier si Google a renvoyé des résultats
        if 'items' in resultats:
            articles = []
            for item in resultats['items']:
                titre = item.get('title')
                lien = item.get('link')
                articles.append({'titre': titre, 'lien': lien})
                print(f"  Found: {titre}")
            return articles
        else:
            print("⚠️ Aucun résultat trouvé.")
            return []

    except Exception as e:
        print(f"❌ Erreur : {e}")
        return []

# --- TEST DU ROBOT ---
if __name__ == "__main__":
    mot_cle = "Intelligence Artificielle innovation 2024"
    articles_trouves = rechercher_google(mot_cle)
    
    print("\n--- RÉSUMÉ ---")
    print(f"J'ai récupéré {len(articles_trouves)} liens prêts à être scrapés !")
