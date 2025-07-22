"""
OpenAI prompt templates for the medical quiz application.
"""


def get_vignette_prompt(recommendation: dict) -> str:
    """Prompt for generating clinical vignette and question based on a specific recommendation."""
    return f"""1. **Sélection De la Recommendation :** Pour chaque nouveau quiz, tu reçois en entrée la recommandation à partir de laquelle tu dois créer le cas clinique.

   RECOMMANDATION À UTILISER:
   Thème: {recommendation.get('theme', 'Non spécifié')}
   Sujet: {recommendation.get('topic', 'Non spécifié')}
   Recommandation: {recommendation.get('recommendation', '')}
   Grade: {recommendation.get('grade', 'Non spécifié')}
   Preuves: {recommendation.get('evidence', '')}



2. **Création du Cas Clinique :** Formule un court cas clinique (3-5 phrases maximum) réaliste et pertinent à partir de  "{recommendation.get('topic', '')}" pour un médecin anesthésiste-réanimateur. Ce cas doit se dérouler dans le contexte d'une prise en charge en déchocage (trauma center de niveau 1 en France) et mettre en scène une situation clinique où  "{recommendation.get('topic', '')}" est directement applicable. Le cas doit être suffisamment détaillé pour contextualiser la question, mais rester concis.

3. **Poser la Question :** À la suite du cas clinique, pose une question claire et précise à l'utilisateur. Cette question doit être directement liée au cas clinique présenté et à  "{recommendation.get('topic', '')}".

FORMAT DE RÉPONSE:
VIGNETTE:
[Cas clinique ici]

QUESTION:
[Question ici]"""


def get_scoring_prompt(recommendation: dict) -> str:
    """Prompt for scoring user answers."""
    return f"""Tu es un évaluateur médical expert. Tu dois évaluer la réponse d'un étudiant selon une échelle de 0 à 5 (0 = très faible ; 5 = excellent) en la comparant à {recommendation.get('recommendation', '')} et fournir un Feedback détaillé et pédagogique.

RECOMMANDATION DE RÉFÉRENCE:
{recommendation.get('recommendation', '')}

CRITÈRES DE NOTATION:
- 5: Réponse excellente, complète et parfaitement adaptée à la situation clinique. Démontre une maîtrise claire des recommandations et de leur application pratique.
- 4: Réponse très bonne, complète avec des nuances mineures manquantes. Montre une excellente compréhension mais pourrait être légèrement plus précise.
- 3: Réponse correcte mais incomplète ou avec des nuances manquantes. Montre une compréhension générale mais pourrait être plus précise ou complète.
- 2: Réponse partiellement correcte, avec des erreurs significatives ou des omissions importantes. Montre une compréhension basique mais nécessite des améliorations.
- 1: Réponse inadéquate, incorrecte ou peu pertinente par rapport à la situation clinique présentée. Nécessite une révision des concepts fondamentaux.
- 0: Réponse très faible, complètement incorrecte, non pertinente ou absente. Indique un manque fondamental de compréhension.

FEEDBACK:
Fournis un retour structuré et argumenté (max. 100 mots):
* Indique clairement si la réponse de l'utilisateur est correcte, partiellement correcte, ou incorrecte au regard de {recommendation.get('recommendation', '')}
* Contextualise la réponse de l'utilisateur en fonction de {recommendation.get('recommendation', '')}
* Mentionne **explicitement** le niveau d'accord **GRADE** de {recommendation.get('grade', '')}
* Explique {recommendation.get('evidence', '')} pour cette question/recommandation, en veillant à l'appliquer et à le relier **spécifiquement au contexte du cas clinique** que tu as présenté. Justifie pourquoi la recommandation s'applique (ou non) dans la situation décrite.
* Adopte un ton professionnel, confraternel et pédagogique. Utilise le vouvoiement (exemple: "Votre réponse est..."; "Vous avez...")
* L'objectif est l'apprentissage et la consolidation des connaissances basées sur la recommendation.

INSTRUCTIONS:
1. Compare la réponse de l'utilisateur avec la recommandation de référence ci-dessus
2. Attribue une note de 0 à 5 selon les critères ci-dessus
3. Fournis un feedback détaillé et pédagogique.

FORMAT DE RÉPONSE:
SCORE: [0-5]
FEEDBACK: [Feedback détaillé et pédagogique]"""


