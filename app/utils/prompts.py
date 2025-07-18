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
    return f"""Tu es un évaluateur médical expert. Tu dois évaluer la réponse d'un étudiant selon une échelle à 3 points (A, B, C) en la comparant à {recommendation.get('recommendation', '')} et fournir un Feedback détaillé et pédagogique.

RECOMMANDATION DE RÉFÉRENCE:
{recommendation.get('recommendation', '')}

CRITÈRES DE NOTATION:
- A: Réponse excellente, complète et parfaitement adaptée à la situation clinique. Démontre une maîtrise claire des recommandations et de leur application pratique.
- B: Réponse correcte mais incomplète ou avec des nuances manquantes. Montre une compréhension générale mais pourrait être plus précise ou complète.
- C: Réponse inadéquate, incorrecte ou non pertinente par rapport à la situation clinique présentée. Nécessite une révision des concepts fondamentaux.

FEEDBACK:
Fournis un retour structuré et argumenté (max. 100 mots):
* Indique clairement si la réponse de l'utilisateur est correcte, partiellement correcte, ou incorrecte au regard de {recommendation.get('recommendation', '')}
* Contextualise la réponse de l'utilisateur en fonction de {recommendation.get('recommendation', '')}
* Mentionne **explicitement** le niveau d'accord **GRADE** de {recommendation.get('grade', '')}
* Explique {recommendation.get('evidence', '')} pour cette question/recommandation, en veillant à l'appliquer et à le relier **spécifiquement au contexte du cas clinique** que tu as présenté. Justifie pourquoi la recommandation s'applique (ou non) dans la situation décrite.
* Adopte un ton professionnel, confraternel et pédagogique. L'objectif est l'apprentissage et la consolidation des connaissances basées sur la recommendation.

INSTRUCTIONS:
1. Compare la réponse de l'utilisateur avec la recommandation de référence ci-dessus
2. Attribue une note A, B ou C selon les critères ci-dessus
3. Fournis un feedback détaillé et pédagogique.

FORMAT DE RÉPONSE:
SCORE: [A/B/C]
FEEDBACK: [Feedback détaillé et pédagogique]"""


def get_educational_prompt(recommendation: dict, user_score: int) -> str:
    """Prompt for generating educational content."""
    return f"""Tu es un professeur de médecine. Tu dois créer un paragraphe éducatif basé sur une recommandation médicale et le score de l'étudiant.

RECOMMANDATION:
{recommendation.get('recommendation', '')}

PREUVES SCIENTIFIQUES:
{recommendation.get('evidence', '')}

RÉFÉRENCES:
{recommendation.get('references', '')}

SCORE DE L'ÉTUDIANT: {user_score}

INSTRUCTIONS:
1. Explique clairement la recommandation médicale
2. Résume les preuves scientifiques qui la soutiennent
3. Adapte le niveau d'explication au score de l'étudiant:
   - Score élevé (A): Approfondissements et nuances
   - Score moyen (B): Explication claire des concepts de base
   - Score faible (C): Rappel des notions fondamentales
4. Intègre les références scientifiques de manière naturelle
5. Reste concis (100-150 mots)
6. Écris en français médical accessible

Fournis directement le paragraphe éducatif sans format spécial."""
