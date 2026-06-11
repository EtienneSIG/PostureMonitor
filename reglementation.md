# Reglementation - Outil de suivi de posture

## Portee
Ce document recense les reglementations principales applicables a un outil de suivi de posture (camera, analyse de posture, alertes, donnees utilisateur) pour l'Europe et l'Amerique du Nord.

Hypothese produit actuelle:
- application logicielle de posture avec traitement d'image
- possible collecte de donnees personnelles, et potentiellement de donnees sensibles selon l'usage
- usage B2C ou B2B (incluant eventuellement le contexte entreprise)

> Note: ce document est un support de pilotage produit/conformite et ne remplace pas un avis juridique.

---

## 1) Europe

### UE - RGPD
- Applicabilite: traitement de donnees personnelles (images, metriques de posture, identifiants, journaux)
- Exigences clefs:
  - base legale de traitement
  - minimisation des donnees
  - limitation des finalites
  - information transparente des utilisateurs
  - duree de conservation definie
  - droits des personnes (acces, suppression, opposition, etc.)
  - mesures de securite techniques et organisationnelles
  - DPIA si risque eleve (ex: surveillance systematique)

### UE - ePrivacy (cookies/traceurs)
- Applicabilite: application web ou composant web utilisant des traceurs
- Exigences clefs:
  - consentement pour traceurs non essentiels
  - possibilite de retrait du consentement
  - preuve du consentement

### UE - AI Act
- Applicabilite: fonctionnalites IA selon cas d'usage et niveau de risque
- Exigences clefs (selon classification):
  - transparence sur l'usage de l'IA
  - gouvernance, documentation, gestion des risques
  - supervision humaine
  - journalisation

### UE - MDR (dispositif medical)
- Applicabilite: si le produit revendique une finalite medicale
- Exigences clefs:
  - marquage CE (si applicable)
  - systeme qualite et gestion des risques
  - evaluation clinique et suivi post-market

### UE - Droit du travail et surveillance des salaries (niveau national)
- Applicabilite: usage en environnement professionnel
- Exigences clefs:
  - proportionnalite de la surveillance
  - information prealable
  - eventuelles consultations obligatoires selon pays

---

## 2) Amerique du Nord

## Etats-Unis

### Federal - FTC Act (Section 5)
- Applicabilite: pratiques commerciales, promesses privacy/securite
- Exigences clefs:
  - ne pas etre trompeur dans la communication
  - niveau de securite raisonnable
  - coherence entre documentation et pratique reelle

### Etats - lois privacy (ex: CCPA/CPRA en Californie)
- Applicabilite: selon volume de donnees, chiffre d'affaires, et perimetre etat
- Exigences clefs:
  - droits consommateurs (acces, suppression, correction)
  - gestion du opt-out selon les cas
  - obligations contractuelles avec prestataires
  - regles renforcies sur donnees sensibles

### Etats - lois biometrie (ex: BIPA Illinois)
- Applicabilite: capture/traitement de donnees biometrie selon definitions locales
- Exigences clefs:
  - consentement explicite prealable
  - politique de retention/destruction
  - restrictions d'usage/divulgation

### US - HIPAA (si contexte sante couvert)
- Applicabilite: uniquement pour entites couvertes et partenaires concernes
- Exigences clefs:
  - protection des PHI
  - exigences de securite/confidentialite
  - accords contractuels adequats

### US - COPPA (mineurs)
- Applicabilite: service cible les moins de 13 ans ou collecte en connaissance de cause
- Exigences clefs:
  - consentement parental verifiable
  - notice specifique
  - minimisation de la collecte

## Canada

### Federal - PIPEDA
- Applicabilite: secteur prive (hors exceptions provinciales)
- Exigences clefs:
  - consentement valable
  - finalites raisonnables
  - minimisation collecte/utilisation/conservation
  - securite proportionnee
  - acces/correction

### Provincial - ex: Quebec Loi 25
- Applicabilite: selon activite et province
- Exigences clefs:
  - gouvernance vie privee
  - evaluation d'impact
  - transparence accrue
  - gestion des incidents

## Mexique (si deploiement North America elargi)

### LFPDPPP
- Applicabilite: donnees personnelles dans le secteur prive
- Exigences clefs:
  - notice de confidentialite
  - consentement selon sensibilite
  - droits ARCO
  - securite et transferts encadres

---

## 3) Tableau de suivi conformite (a mettre a jour)

Utiliser ce tableau comme backlog conformite. Une ligne = un sujet reglementaire/action concrete a suivre.

| ID | Region | Reglementation | Sujet a couvrir | Impact technique (UI/Backend/Stockage/Logs/Secu) | Action technique initiale | Niveau de priorite | Statut | Statut dev | Owner | Echeance cible | Derniere mise a jour | Preuve/livrable attendu | Commentaires |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EU-01 | Europe | RGPD | Cartographie des donnees (video, metriques, logs) | Backend, Stockage, Logs | Inventorier les flux et creer un schema des donnees traitees/stockees | Haute | A faire | Non demarre |  |  |  | Registre des traitements |  |
| EU-02 | Europe | RGPD | Base legale par finalite | UI, Backend | Associer chaque finalite a une base legale et tracer la source de consentement si necessaire | Haute | A faire | Non demarre |  |  |  | Note juridique interne |  |
| EU-03 | Europe | RGPD | Politique de retention + suppression auto | Backend, Stockage | Implementer TTL/suppression planifiee pour logs et donnees posture | Haute | A faire | Non demarre |  |  |  | Politique de retention versionnee |  |
| EU-04 | Europe | RGPD | Gestion des droits utilisateurs (acces/suppression) | UI, Backend, Stockage | Ajouter endpoints/export/suppression et ecran de demande utilisateur | Haute | A faire | Non demarre |  |  |  | Procedure + ticket demo |  |
| EU-05 | Europe | ePrivacy | Consentement traceurs non essentiels | UI, Backend, Logs | Ajouter un module consentement et journaliser preuve + retrait | Moyenne | A faire | Non demarre |  |  |  | CMP ou mecanisme equivalent |  |
| EU-06 | Europe | AI Act | Qualification du niveau de risque IA | Backend, Logs, Secu | Documenter pipeline IA, jeux de donnees, controles humains et journalisation | Haute | A faire | Non demarre |  |  |  | Memo de classification IA |  |
| EU-07 | Europe | MDR | Verification de non-qualification medicale (ou plan CE) | UI, Backend, Documentation | Verifier claims dans UI/README et retirer vocabulaire medical non valide | Haute | A faire | Non demarre |  |  |  | Position paper claims produit |  |
| NA-01 | Etats-Unis | FTC Act | Alignement promesses marketing vs realite produit | UI, Backend, Secu | Creer checklist release pour valider les claims et controles securite | Haute | A faire | Non demarre |  |  |  | Revue legal/marketing |  |
| NA-02 | Etats-Unis | CCPA/CPRA etats | Droits consommateurs + processus de reponse | UI, Backend, Stockage | Implementer flux DSAR (acces/suppression/correction) + suivi des delais | Haute | A faire | Non demarre |  |  |  | Procedure operationnelle |  |
| NA-03 | Etats-Unis | BIPA et lois biometrie | Consentement explicite + retention biometrie | UI, Backend, Stockage, Logs | Activer consentement explicite avant capture et suppression automatique des donnees biometrie | Haute | A faire | Non demarre |  |  |  | Politique biometrie publiee |  |
| NA-04 | Etats-Unis | COPPA | Evaluation exposition mineurs | UI, Backend | Ajouter controle d'age/eligibilite et blocage collecte si mineur non autorise | Moyenne | A faire | Non demarre |  |  |  | Decision documentee |  |
| NA-05 | Canada | PIPEDA | Notice + consentement + minimisation | UI, Backend, Stockage | Adapter notices Canada et limiter les champs collectes au strict necessaire | Haute | A faire | Non demarre |  |  |  | Privacy notice Canada |  |
| NA-06 | Canada | Loi 25 (QC) | Evaluation d'impact + gouvernance | Backend, Logs, Secu | Mettre en place journal incidents, procedure escalade et trace des decisions automatisees | Moyenne | A faire | Non demarre |  |  |  | PIA + registre incidents |  |
| NA-07 | Mexique | LFPDPPP | Notice + droits ARCO + transferts | UI, Backend, Stockage | Ajouter flux ARCO et documenter transferts internationaux de donnees | Moyenne | A faire | Non demarre |  |  |  | Politique locale Mexique |  |

### Legende statuts
- A faire
- En cours
- Bloque
- A valider (Legal)
- Fait

### Legende statut dev
- Non demarre
- Spec
- Dev en cours
- Pret QA
- QA en cours
- Pret prod
- En production

---

## 4) Rythme de mise a jour recommande

- Frequence: a chaque release majeure et au minimum une fois par trimestre
- Gouvernance: revue croisee Produit + Tech + Legal
- Regle pratique: aucune fonctionnalite sensible (camera, profilage, biometrie, RH, sante) ne passe en production sans mise a jour de ce tableau

---

## 5) Audit interne (priorisation par sprint)

Objectif: verifier rapidement la conformite minimale, puis monter en maturite sans bloquer le developpement.

| Sprint | Horizon | Objectif audit | Items cibles | Livrables attendus | Gate de sortie |
|---|---|---|---|---|---|
| Sprint 0 | Semaine 1 | Cadrage des risques et donnees | EU-01, EU-02, EU-07, NA-01 | Cartographie des donnees, matrice base legale, revue des claims produit | Aucun claim sensible non justifie |
| Sprint 1 | Semaines 2-3 | Mise en place des controles de base | EU-03, EU-04, NA-02, NA-03 | Spec technique DSAR, retention auto, consentement explicite biometrie | Parcours droits utilisateur testable de bout en bout |
| Sprint 2 | Semaines 4-5 | Tracabilite et gouvernance | EU-05, EU-06, NA-05, NA-06 | Logs de consentement, registre incidents, documentation IA | Preuves consultables et horodatees |
| Sprint 3 | Semaines 6-7 | Regionalisation et durcissement | NA-04, NA-07 + ecarts ouverts | Plan mineurs (si applicable), flux ARCO, plan de remediations | 0 ecart critique ouvert |

### Checklist audit interne
- Perimetre: les fonctionnalites camera/posture actives sont listees.
- Donnees: chaque donnee collecte a une finalite, une base legale, une retention.
- UX: les ecrans consentement et demandes droits sont accessibles et comprehensibles.
- Technique: suppression/export fonctionne sur donnees et logs associes.
- Securite: controles d'acces, chiffrement, et journalisation des actions sensibles.
- Documentation: politique privacy, notes de decisions, preuves de tests.

### Mode de scoring recommande
- Critique: non-conformite susceptible de bloquer la mise en production.
- Majeur: risque eleve mais contournable temporairement avec mitigation documentee.
- Mineur: amelioration de maturite sans risque immediat.

### Cadence de pilotage
- Point hebdomadaire Produit/Tech/Legal (30 min).
- Mise a jour du tableau a chaque changement de statut dev.
- Revue finale avant release avec decision Go/No-Go.
