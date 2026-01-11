import requests
import json
import time
import os
from bs4 import BeautifulSoup
from openai import OpenAI

# --- IMPORTATION DES CLÉS SÉCURISÉES ---
try:
    from secrets import GOOGLE_API_KEY, SEARCH_ENGINE_ID, OPENAI_API_KEY
except ImportError:
    print("⚠️ ERREUR CRITIQUE : Le fichier secrets.py est introuvable !")
    exit()
# ---------------------------------------

client = OpenAI(api_key=OPENAI_API_KEY)

# --- CHARGEMENT DES MOTS-CLÉS EXTERNES ---
def charger_mots_cles():
    nom_fichier = "mots_cles.txt"
    liste = []
    
    if os.path.exists(nom_fichier):
        with open(nom_fichier, "r", encoding="utf-8") as f:
            # On lit chaque ligne et on enlève les espaces vides
            lignes = f.readlines()
            for ligne in lignes:
                mot_propre = ligne.strip()
                if mot_propre: # Si la ligne n'est pas vide
                    liste.append(mot_propre)
        print(f"📋 Configuration chargée : {len(liste)} thèmes trouvés dans {nom_fichier}.")
        return liste
    else:
        print(f"⚠️ ATTENTION : Fichier {nom_fichier} introuvable.")
        print("   -> Utilisation de la liste de secours par défaut.")
        return ["Veille juridique formation professionnelle"] # Liste de secours

# On initialise la liste au démarrage
LISTE_MOTS_CLES = charger_mots_cles()
# -----------------------------------------

def rechercher_google(requete):
    print(f"🔎 Recherche (7 jours) : {requete}...")
    url = "https://www.googleapis.com/customsearch/v1"
    parametres = {
        'key': GOOGLE_API_KEY, 
        'cx': SEARCH_ENGINE_ID, 
        'q': requete, 
        'num': 10, 
        'dateRestrict': 'w1'
    }
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
    print(f"   ⛏️  Lecture : {url[:60]}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        reponse = requests.get(url, headers=headers, timeout=5)
        if reponse.status_code == 200:
            soup = BeautifulSoup(reponse.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.extract()
            texte = soup.get_text()
            lines = (line.strip() for line in texte.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            texte_propre = '\n'.join(chunk for chunk in chunks if chunk)
            return texte_propre[:4000]
        return None
    except Exception:
        return None

def resumer_avec_ia(texte_brut, contexte):
    try:
        prompt = (
            f"CONTEXTE : Veille Qualiopi. Sujet : {contexte}. \n"
            "TÂCHE : Résume en 1 phrase l'info clé. Si hors-sujet ou pub, réponds 'R.A.S'.\n\n"
            f"TEXTE : {texte_brut}"
        )
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es concis."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erreur IA : {e}"

# --- PROGRAMME PRINCIPAL ---
if __name__ == "__main__":
    if not LISTE_MOTS_CLES:
        print("⛔ Aucun mot-clé à traiter. Arrêt.")
        exit()

    print(f"🚀 DÉMARRAGE DE LA VEILLE SUR {len(LISTE_MOTS_CLES)} SUJETS\n")
    
    compteur_total = 0
    
    for mot_cle in LISTE_MOTS_CLES:
        print(f"==================================================")
        print(f"📂 THÈME : {mot_cle.upper()}")
        
        articles = rechercher_google(mot_cle)
        print(f"   -> {len(articles)} articles récents.")
        
        for article in articles:
            texte = scrapper_page(article['lien'])
            
            if texte and len(texte) > 500:
                resume = resumer_avec_ia(texte, mot_cle)
                if "R.A.S" not in resume and "Erreur" not in resume:
                    print(f"\n✅ {article['titre']}")
                    print(f"🔗 {article['lien']}")
                    print(f"💡 {resume}\n")
                    compteur_total += 1
            time.sleep(1)
        time.sleep(2)

    print(f"\n🏁 FIN. {compteur_total} résumés générés.")