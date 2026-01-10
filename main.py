import requests
import json
from bs4 import BeautifulSoup
from openai import OpenAI

# --- ZONE DE CONFIGURATION (VOS CLÉS) ---
GOOGLE_API_KEY = "AIzaSyDVdrWXDaoUGSdTLOTqUk0MwhU1escnhHM"     # La clé qui commence par AIza...
SEARCH_ENGINE_ID = "249cae3d517ff4425"        # L'ID cx...
OPENAI_API_KEY = "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"    # La clé qui commence par sk-...
# ----------------------------------------

# On initialise le cerveau (Client OpenAI)
client = OpenAI(api_key=OPENAI_API_KEY)

def rechercher_google(requete, nombre_resultats=2):
    print(f"🔎 Recherche Google pour : {requete}...")
    url = "https://www.googleapis.com/customsearch/v1"
    parametres = {'key': GOOGLE_API_KEY, 'cx': SEARCH_ENGINE_ID, 'q': requete, 'num': nombre_resultats}
    try:
        reponse = requests.get(url, params=parametres)
        resultats = reponse.json()
        articles = []
        if 'items' in resultats:
            for item in resultats['items']:
                articles.append({'titre': item.get('title'), 'lien': item.get('link')})
            return articles
        return []
    except Exception as e:
        print(f"❌ Erreur Google : {e}")
        return []

def scrapper_page(url):
    print(f"   ⛏️  Extraction du texte : {url}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        reponse = requests.get(url, headers=headers, timeout=10)
        if reponse.status_code == 200:
            soup = BeautifulSoup(reponse.text, 'html.parser')
            # On prend les paragraphes
            paragraphes = soup.find_all('p')
            texte_complet = " ".join([p.text for p in paragraphes])
            # On coupe à 3000 caractères pour ne pas payer trop cher d'IA
            return texte_complet[:3000]
        return None
    except Exception:
        return None

def resumer_avec_ia(texte_brut):
    print("   🧠 L'IA réfléchit et rédige le résumé...")
    try:
        prompt = (
            "Tu es un expert en veille technologique. "
            "Voici un texte brut extrait d'un site web (qui peut être en anglais). "
            "Fais-moi un résumé clair, en français, de 3 ou 4 phrases maximum. "
            "Va droit au but sur les faits importants.\n\n"
            f"TEXTE : {texte_brut}"
        )
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini", # Modèle rapide et pas cher
            messages=[
                {"role": "system", "content": "Tu es un assistant de synthèse."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Erreur IA : {e}"

# --- LE PROGRAMME PRINCIPAL ---
if __name__ == "__main__":
    mot_cle = "Intelligence Artificielle innovation 2024"
    
    # 1. Recherche
    articles = rechercher_google(mot_cle)
    print(f"\n🎯 {len(articles)} articles trouvés. Traitement en cours...\n")
    
    # 2. Boucle sur chaque article
    for article in articles:
        print(f"==================================================")
        print(f"SOURCE : {article['titre']}")
        print(f"LIEN   : {article['lien']}")
        
        # 3. Extraction
        texte_brut = scrapper_page(article['lien'])
        
        if texte_brut and len(texte_brut) > 500:
            # 4. Résumé IA
            resume = resumer_avec_ia(texte_brut)
            print(f"\n✨ RÉSUMÉ IA :\n{resume}\n")
        else:
            print("⚠️ Pas assez de texte trouvé sur cette page pour résumer.")