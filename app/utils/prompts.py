"""
OpenAI prompt templates for the medical quiz application.
"""


def get_vignette_prompt(recommendation: dict) -> str:
    """Prompt for generating clinical vignette and question based on a specific recommendation."""
    return f"""

ROLE
Tu es un générateur de vignettes cliniques pour médecins anesthésistes-réanimateurs. 
Chaque vignette est un quiz évaluant l’adhésion à UNE recommandation précise.

RECOMMANDATION À UTILISER:
Thème: {recommendation.get('theme', 'Non spécifié')}
Sujet: {recommendation.get('topic', 'Non spécifié')}
Recommandation: {recommendation.get('recommendation', '')}
   

OBJECTIF
1. Rédiger un cas clinique (3 à 5 phrases) réaliste, pertinent, centré sur la recommandation.
2. Poser UNE seule question claire, directement liée au cas.
3. La réponse idéale DOIT correspondre exactement (ou strictement équivalente) à la recommandation fournie.

CONTEXTE OBLIGATOIRE
- Spécialité : anesthésie-réanimation.
- Lieu : hopital.
- La situation clinique doit rendre l’application de la recommandation évidente et centrale.
- Style sobre, médical. Aucune écriture inclusive.

CONTRAINTES DE RÉDACTION
- 3 à 5 phrases maximum pour la vignette.
- Pas d’indices téléphonés ni formulations révélant explicitement la recommandation.
- Une seule question, fermée (attend une action/conduite précise).
- Ne pas inclure la réponse dans la vignette ou la question.
- Ne pas faire de piège.
- Pas de QCM ou de liste de choix.
- Markdown lisible et hiérarchisé.

VÉRIFICATIONS AVANT DE RENDRE
- Contexte hospitalier bien présent.
- Une seule question, une seule réponse idéale.
- Aucune écriture inclusive.
   
FORMAT DE RÉPONSE:
VIGNETTE:
[Cas clinique ici]

QUESTION:
[Question ici]"""


def get_scoring_prompt(recommendation: dict) -> str:
    """Prompt for scoring user answers."""
    return f"""

Ta mission : noter la réponse d'un utilisateur sur une échelle ENTIER 0–5, en la comparant à la recommandation de référence.

RECOMMANDATION DE RÉFÉRENCE:
- Recommandation (gold standard) : {recommendation.get('recommendation', '')}
- Grade : {recommendation.get('grade', 'Non spécifié')}
- Preuves (evidence) : {recommendation.get('evidence', '')}

INSTRUCTIONS:
1. Compare la réponse de l'utilisateur avec la recommandation de référence ({recommendation.get('recommendation', '')}).
2. Vérifie la pertinence de la réponse de l'utilisateur par rapport au cas clinique.
3. N'attends pas de la réponse de l'utilisateur des éléments non présents dans la recommandation de référence ({recommendation.get('recommendation', '')}) ou les preuves ({recommendation.get('evidence', '')}), pour générer le score de l'utilisateur.
3. Attribue un score ENTIER de 0 à 5 selon les critères de notations ci-après.
3. Fournis un feedback détaillé et pédagogique selon le format du feedback détaillé ci-après.

CRITÈRES DE NOTATION (0–5, entier):
- 5: Réponse excellente, complète et parfaitement adaptée à la situation clinique. Démontre une maîtrise claire de la recommandation et de son application pratique.
- 4: Réponse très bonne, complète avec des nuances mineures manquantes. Montre une excellente compréhension mais pourrait être légèrement plus précise.
- 3: Réponse correcte mais incomplète ou avec des nuances manquantes. Montre une compréhension générale mais pourrait être plus précise ou complète.
- 2: Réponse partiellement correcte, avec des erreurs significatives ou des omissions importantes. Montre une compréhension basique mais nécessite des améliorations.
- 1: Réponse inadéquate, incorrecte ou peu pertinente par rapport à la situation clinique présentée. Nécessite une révision des concepts fondamentaux.
- 0: Réponse très faible, complètement incorrecte, non pertinente ou absente. Indique un manque fondamental de compréhension.

FEEDBACK:
Fournis un retour structuré et argumenté (max. 150 mots):
* Indique clairement si la réponse de l'utilisateur est correcte, partiellement correcte, ou incorrecte au regard de la recommandation de référence ({recommendation.get('recommendation', '')}).
* Replace la réponse de l'utilisateur dans le contexte du cas clinique.
* Mentionne explicitement le niveau d'accord GRADE selon {recommendation.get('grade', '')}, mais ne l'utilise pas pour générer le score.
* Explique les preuves selon {recommendation.get('evidence', '')} et leur application au cas clinique. 
* Justifie pourquoi la recommandation s'applique (ou non) dans la situation décrite.
* Adopte un ton professionnel, confraternel et pédagogique, en vouvoiement. Aucune écriture inclusive.
* L'objectif est l'apprentissage et la consolidation des connaissances basées sur la recommendation
* Utilise des retours à la ligne et un Markdown simple, clair et hierarchisé.



FORMAT DE RÉPONSE:
SCORE: [0-5]
FEEDBACK: [Feedback détaillé et pédagogique]"""


