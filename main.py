import requests
import time
import os
import datetime
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from openai import OpenAI

# --- IMPORTATION DES CLÉS ---
try:
    from secrets import GOOGLE_API_KEY, SEARCH_ENGINE_ID, OPENAI_API_KEY, WP_URL, WP_USER, WP_PASSWORD
except ImportError:
    print("⚠️ ERREUR : secrets.py introuvable !")
    exit()

client = OpenAI(api_key=OPENAI_API_KEY)

# --- CONFIGURATION DES FICHIERS ---
FICHIER_IND23 = "config_ind23.txt"
FICHIER_IND24 = "config_ind24.txt"
FICHIER_IND25 = "config_ind25.txt"

def charger_liste(nom_fichier):
    if os.path.exists(nom_fichier):
        with open(nom_fichier, "r", encoding="utf-8") as f:
            # On ignore les lignes vides
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

# --- OUTILS GOOGLE & IA ---
def rechercher_google(requete):
    url = "https://www.googleapis.com/customsearch/v1"
    parametres = {
        'key': GOOGLE_API_KEY, 
        'cx': SEARCH_ENGINE_ID, 
        'q': requete, 
        'num': 10,             # Max résultats par requête
        'dateRestrict': 'w1'   # Semaine dernière uniquement
    }
    try:
        reponse = requests.get(url, params=parametres)
        if reponse.status_code == 429:
            print("🔴 ERREUR QUOTA GOOGLE DÉPASSÉ (Activez la facturation !)")
            return []
        return reponse.json().get('items', [])
    except Exception:
        return []

def scrapper_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        reponse = requests.get(url, headers=headers, timeout=4)
        if reponse.status_code == 200:
            soup = BeautifulSoup(reponse.text, 'html.parser')
            for s in soup(["script", "style"]): s.extract()
            texte = soup.get_text()
            lines = (line.strip() for line in texte.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return '\n'.join(chunk for chunk in chunks if chunk)[:3500]
        return None
    except Exception:
        return None

def resumer_avec_ia(texte_brut, contexte):
    try:
        prompt = (
            f"CONTEXTE : Veille Métier ({contexte}). \n"
            "TÂCHE : Résume en 1 phrase l'info clé (nouveauté, loi, technique). "
            "Si hors-sujet, pub ou trop générique, réponds 'R.A.S'.\n"
            f"TEXTE : {texte_brut}"
        )
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content
    except Exception:
        return "Erreur IA"

def publier_wp(titre, contenu_html):
    endpoint = f"{WP_URL}/wp-json/wp/v2/posts"
    article = {'title': titre, 'content': contenu_html, 'status': 'draft'}
    try:
        reponse = requests.post(endpoint, auth=HTTPBasicAuth(WP_USER, WP_PASSWORD), json=article)
        if reponse.status_code == 201:
            print(f"✅ Article créé : {titre}")
        else:
            print(f"❌ Erreur WP : {reponse.status_code}")
    except Exception as e:
        print(f"❌ Erreur connexion WP : {e}")

# --- TRAITEMENT STANDARD (Ind 23 & 25) ---
def traiter_theme_classique(liste_mots, indicateur_nom, num_semaine):
    print(f"\n🔵 TRAITEMENT {indicateur_nom}...")
    titre_article = f"{indicateur_nom} - Semaine {num_semaine}"
    contenu = f"<p>Veille hebdomadaire pour {indicateur_nom} (Semaine {num_semaine}).</p><hr>"
    articles_trouves = False

    for mot in liste_mots:
        print(f"   📂 Sujet : {mot}")
        contenu += f"<h3>{mot}</h3><ul>"
        items = rechercher_google(mot)
        for item in items:
            texte = scrapper_page(item['lien'])
            if texte and len(texte) > 500:
                resume = resumer_avec_ia(texte, mot)
                if "R.A.S" not in resume:
                    contenu += f"<li><strong>{item['titre']}</strong><br>{resume}<br><a href='{item['lien']}'>Lire</a></li>"
                    articles_trouves = True
        contenu += "</ul>"
    
    if articles_trouves:
        publier_wp(titre_article, contenu)
    else:
        print(f"   🚫 Rien de pertinent pour {indicateur_nom}.")

# --- TRAITEMENT AVANCÉ (Ind 24 avec Mots-clés multiples) ---
def traiter_ind24(liste_lignes, num_semaine):
    print(f"\n🟠 TRAITEMENT INDICATEUR 24 ({len(liste_lignes)} profils)...")
    
    for ligne in liste_lignes:
        # On découpe la ligne par les virgules
        # Ex: "Webmaster, Wordpress, SEO" -> ["Webmaster", "Wordpress", "SEO"]
        mots_cles = [m.strip() for m in ligne.split(',') if m.strip()]
        
        if not mots_cles: continue # Si ligne vide
        
        metier_principal = mots_cles[0] # Le premier mot est le titre du métier
        details = ", ".join(mots_cles[1:]) # Les autres sont des précisions
        
        print(f"   🔨 Profil : {metier_principal} (+ {len(mots_cles)-1} mots-clés)")
        
        titre_article = f"Veille Ind. 24 : {metier_principal} - Semaine {num_semaine}"
        contenu = f"<p>Veille métier pour <strong>{metier_principal}</strong>.</p>"
        if details:
            contenu += f"<p><em>Mots-clés surveillés : {details}</em></p>"
        contenu += "<hr><ul>"
        
        compteur_articles_valides = 0
        
        # --- GÉNÉRATION INTELLIGENTE DES REQUÊTES ---
        liste_requetes = []
        
        # 1. Requête générale
        liste_requetes.append(f"Actualité métier {metier_principal}")
        liste_requetes.append(f"Réglementation {metier_principal} nouveauté")
        
        # 2. Requêtes précises (Métier + Mot clé secondaire)
        # Ex: "Actualité Webmaster Wordpress", "Nouveauté Webmaster SEO"
        for mot_secondaire in mots_cles[1:]:
            liste_requetes.append(f"Actualité {metier_principal} {mot_secondaire}")
            liste_requetes.append(f"Nouveauté {mot_secondaire} formation")

        # --- LANCEMENT DES RECHERCHES ---
        for requete in liste_requetes:
            if compteur_articles_valides >= 5: break # On s'arrête si on a assez d'infos
            
            # print(f"      🔎 Recherche : {requete}...") # Décommentez pour voir les détails
            items = rechercher_google(requete)
            
            for item in items:
                if compteur_articles_valides >= 5: break
                
                texte = scrapper_page(item['lien'])
                if texte and len(texte) > 500:
                    resume = resumer_avec_ia(texte, f"{metier_principal} ({requete})")
                    
                    if "R.A.S" not in resume:
                        print(f"      ✅ Trouvé : {item['titre'][:40]}...")
                        contenu += f"<li><strong>{item['titre']}</strong><br>{resume}<br><a href='{item['lien']}'>Source</a></li>"
                        compteur_articles_valides += 1
                        time.sleep(1)

        if compteur_articles_valides > 0:
            contenu += "</ul>"
            publier_wp(titre_article, contenu)
        else:
            print(f"      (Rien trouvé pour {metier_principal})")

# --- LANCEMENT ---
if __name__ == "__main__":
    semaine = datetime.date.today().isocalendar()[1]
    print(f"🚀 DÉMARRAGE ROBOT VEILLE - SEMAINE {semaine}")

    # Ind 23
    mots_23 = charger_liste(FICHIER_IND23)
    if mots_23: traiter_theme_classique(mots_23, "Indicateur 23 (Réglementaire)", semaine)

    # Ind 25
    mots_25 = charger_liste(FICHIER_IND25)
    if mots_25: traiter_theme_classique(mots_25, "Indicateur 25 (Pédago & Tech)", semaine)

    # Ind 24 (Complexe)
    lignes_24 = charger_liste(FICHIER_IND24)
    if lignes_24: traiter_ind24(lignes_24, semaine)
    
    print("\n🏁 TERMINE.")