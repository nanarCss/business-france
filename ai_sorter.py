# -*- coding: utf-8 -*-
import os
import json
import time
import google.generativeai as genai

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

PROFIL_CANDIDAT = """
Je suis un ingénieur systèmes Linux / DevOps / Cloud / SRE avec une forte appétence pour la Data.

COMPÉTENCES PRINCIPALES :
- Systèmes Linux : administration, hardening, troubleshooting, scripting, gestion de parcs serveurs
- DevOps & SRE : CI/CD (GitLab CI, GitHub Actions, Jenkins), Infrastructure as Code (Terraform, Ansible, Pulumi)
- Containers & Orchestration : Docker, Kubernetes (notions), Helm
- Cloud : AWS, GCP, Azure (notions et pratique)
- Monitoring & Observabilité : Prometheus, Grafana, Datadog, ELK Stack, Nagios, Zabbix
- Scripting & Automation : Python, Bash, Go
- Réseau : TCP/IP, DNS, DHCP, firewalls, VPN, reverse proxy (Nginx, HAProxy)
- Data Engineering : pipelines de données, ETL, SQL, Kafka, Spark (niveau intermédiaire)

POSTES RECHERCHÉS (par ordre de préférence) :
1. Administrateur Systèmes Linux / Ingénieur Systèmes
2. DevOps Engineer / SRE / Platform Engineer
3. Cloud Engineer / Infrastructure Engineer
4. Ingénieur Infrastructure / Infra & Ops
5. Data Engineer avec composante DevOps/Cloud
6. MLOps Engineer
7. IT Finance / DevOps dans la finance de marché

CE QUE J'AIME :
- Missions avec de la responsabilité technique
- Environnements Linux (Debian, Ubuntu, RHEL, CentOS...)
- Automatisation et amélioration continue
- Administration et exploitation d'infrastructure
- Environnements Cloud ou hybrides
- Grandes entreprises ou scale-ups avec de vraies infras
- Bonne rémunération VIE et grandes villes en Asie

CE QUE JE N'AIME PAS :
- Support utilisateur / helpdesk / N1-N2
- Postes purement fonctionnels ou commerciaux
- Postes 100% Windows sans composante Linux
- Missions sans aucune composante technique
"""

def trier_offres_ia(offres):
    """Trie les offres par pertinence via Gemini et attribue un score 0-100"""
    if not offres:
        return []
    
    if not GEMINI_API_KEY:
        print("⚠️ Pas de clé API Gemini, pas de tri sémantique.")
        return offres

    print(f"🤖 Analyse IA de {len(offres)} offre(s)...")
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        # Préparer le prompt
        offres_text = ""
        for i, o in enumerate(offres):
            offres_text += f"ID {i}:\n"
            offres_text += f"Titre: {o['titre']}\n"
            offres_text += f"Entreprise: {o['entreprise']}\n"
            offres_text += f"Lieu: {o['lieu']}\n"
            offres_text += f"Mission: {o['mission'][:400]}\n\n"
            
        prompt = f"""
        Voici une liste d'offres d'emploi VIE et mon profil.
        
        MON PROFIL:
        {PROFIL_CANDIDAT}
        
        TACHE:
        Pour chaque offre, attribue un score de pertinence de 0 à 100 :
        - 90-100 : parfaitement aligné (DevOps/SRE/Cloud en Asie, grande entreprise)
        - 70-89  : très pertinent (bon match technique même si pas 100% DevOps)
        - 50-69  : intéressant (Data Engineer, IT Finance avec infra cloud)
        - 30-49  : peu pertinent (trop fonctionnel, mauvais match technique)
        - 0-29   : hors sujet (support, commercial, pas tech)
        
        Retourne UNIQUEMENT un tableau JSON d'objets avec "id" (int), "score" (int 0-100), "raison" (string courte max 15 mots).
        Exemple: [{{"id": 0, "score": 85, "raison": "SRE Kubernetes chez Société Générale, parfait match"}}, ...]
        
        IMPORTANT: Ne mets PAS de markdown autour. Juste le JSON brut.
        
        LISTE DES OFFRES:
        {offres_text}
        """
        
        max_retries = 3
        response = None
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                break
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Quota" in error_msg:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Quota Gemini atteint. Attente de 60 secondes avant réessai ({attempt + 1}/{max_retries})...")
                        time.sleep(60)
                    else:
                        raise e
                else:
                    raise e
                    
        text_resp = response.text.strip()
        
        # Nettoyage si l'IA met du markdown
        if text_resp.startswith('```json'): text_resp = text_resp[7:]
        if text_resp.startswith('```'): text_resp = text_resp[3:]
        if text_resp.endswith('```'): text_resp = text_resp[:-3]
        text_resp = text_resp.strip()
        
        resultats = json.loads(text_resp)
        
        # Indexer les résultats par ID
        scores_map = {}
        for r in resultats:
            scores_map[r['id']] = {'score': r['score'], 'raison': r.get('raison', '')}
        
        # Attribuer les scores aux offres
        for i, offre in enumerate(offres):
            if i in scores_map:
                offre['score_ia'] = scores_map[i]['score']
                offre['raison_ia'] = scores_map[i]['raison']
            else:
                offre['score_ia'] = 0
                offre['raison_ia'] = ''
        
        # Trier par score décroissant
        offres_triees = sorted(offres, key=lambda x: x.get('score_ia', 0), reverse=True)
        
        # Log les top offres
        for o in offres_triees[:5]:
            print(f"  🏆 {o['score_ia']}/100 — {o['titre'][:45]} | {o.get('raison_ia', '')}")
                
        print(f"✅ Tri IA effectué ({len(offres_triees)} offres scorées)")
        return offres_triees
        
    except Exception as e:
        print(f"❌ Erreur Gemini: {e}")
        return offres # Fallback ordre original
