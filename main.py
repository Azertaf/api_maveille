import requests
import json
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
API_KEY = "AIzaSyDVdrWXDaoUGSdTLOTqUk0MwhU1escnhHM"        # Remettez votre clé AIza...
SEARCH_ENGINE_ID = "249cae3d517ff4425" # Remettez votre ID cx...
# ---------------------

def rechercher_google(requete, nombre_resultats=3):
    print(f"🔎 Recherche Google pour : {requete}...")
    url = "https://www.googleapis.com/customsearch/v1"
    parametres = {'key': API_KEY, 'cx': SEARCH_ENGINE_ID, 'q': requete, 'num': nombre_resultats}
    
    try:
        reponse = requests.get(url, params=parametres)
        resultats = reponse.json()
        articles = []
        
        if 'items' in resultats:
            for item in resultats['items']:
                articles.append({'titre': item.get('title'), 'lien': item.get('link')})
            return articles
        else:
            return []
    except Exception as e:
        print(f"❌ Erreur Google : {e}")
        return []

def scrapper_page(url):
    print(f"   ⛏️  Scraping de : {url}...")
    try:
        # On se fait passer pour un navigateur classique (User-Agent)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        reponse = requests.get(url, headers=headers, timeout=10)
        
        if reponse.status_code == 200:
            soup = BeautifulSoup(reponse.text, 'html.parser')
            
            # On cherche les paragraphes <p>
            paragraphes = soup.find_all('p')
            texte_complet = " ".join([p.text for p in paragraphes])
            
            # On coupe si c'est trop long (pour l'affichage)
            resume = texte_complet[:500] + "..." 
            return resume
        else:
            return "❌ Accès refusé par le site."
    except Exception as e:
        return f"❌ Erreur de lecture : {e}"

# --- LE CHEF D'ORCHESTRE ---
if __name__ == "__main__":
    mot_cle = "Intelligence Artificielle innovation 2024"
    
    # 1. On cherche
    articles = rechercher_google(mot_cle)
    print(f"\n🎯 J'ai trouvé {len(articles)} articles. Début de l'extraction...\n")
    
    # 2. On lit chaque article
    for article in articles:
        print(f"------------------------------------------------")
        print(f"TITRE : {article['titre']}")
        print(f"LIEN  : {article['lien']}")
        
        # Le robot va lire le texte
        contenu = scrapper_page(article['lien'])
        print(f"\n📝 CONTENU EXTRAIT (Début) :\n{contenu}\n")