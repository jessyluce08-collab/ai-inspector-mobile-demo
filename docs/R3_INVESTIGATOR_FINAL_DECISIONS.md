# Décisions finales de l’investigateur — R3

**À renseigner et approuver par la personne réellement responsable. Ce document est un projet, pas une autorisation. Aucun troisième ticket général de préparation n’est requis.**

## A. Informations factuelles nécessaires

- Responsable ou organisation : **[NON RENSEIGNÉ]**
- Contact accessible aux volontaires : **[NON RENSEIGNÉ]**
- Destinataires autorisés et canal manuel de retour du JSON : **[NON RENSEIGNÉ]**
- Stockage sécurisé et personnes ayant accès : **[NON RENSEIGNÉ — description communicable, sans identifiants d’accès]**
- Conservation, échéance et méthode de suppression : **[NON RENSEIGNÉ]**
- Retrait : contact, procédure, délai et limites après agrégation/publication : **[NON RENSEIGNÉ]**
- Détermination effectivement faite concernant l’éthique, l’institution et la protection des données : **[NON RENSEIGNÉ]**. Indiquer la conclusion réelle et son responsable. Ne pas inventer d’approbation ou d’exemption ; ne pas imposer de procédure institutionnelle si elle n’est réellement pas applicable.

Ces éléments renseignent les champs correspondants d’INVESTIGATOR_CONFIG.template.json. Le fichier complété et le registre restent privés. Seules les informations destinées au volontaire sont intégrées à la page ; aucune note privée supplémentaire ne doit y être publiée.

## B. Décisions sur le protocole

Proposition existante, **non encore approuvée** : au maximum six adultes admissibles et consentants, une seule session admissible par volontaire, et au maximum quatorze jours de recrutement/collecte à partir de la première session autorisée. Aucun remplacement pour non-retour, abstention, résultat inattendu ou session partielle.

Décision de l’investigateur : **[ACCORD EXPLICITE OU MODIFICATION PROSPECTIVE AVANT TOUTE INSCRIPTION]**. Les chiffres sont des plafonds opérationnels d’un pilote de faisabilité, pas une justification de puissance statistique.

## C. Autorisation prospective et publication

**Déclaration proposée à examiner, et non accord donné par Codex :**

« Après vérification des informations ci-dessus, des obligations réellement applicables et du protocole identifié par son empreinte, j’autorise prospectivement ce petit pilote selon les plafonds approuvés. Je comprends qu’aucune invitation ne peut partir avant l’horodatage externe, la vérification du candidat exact, son verrouillage et mon approbation distincte de sa publication. Les essais techniques, anciens ou nouveaux, ne seront pas inclus dans les observations du pilote. »

Décision réelle : **[NON DONNÉE]**. Responsable/signataire : **[À RENSEIGNER]**. Date et heure avec fuseau : **[À RENSEIGNER]**. Empreinte du protocole examiné : **[À RENSEIGNER]**.

Après construction et vérification : examiner le HTML exact, ses informations/consentement et son empreinte SHA-256 ; compléter DEPLOYMENT_APPROVAL.template.json avec une approbation réelle, l’empreinte et l’URL directe exactes. Une approbation générale ne vaut pas approbation d’un autre fichier. Ne publier ni configuration privée, ni registre, ni résultats.

## D. Horodatage externe avant la première inscription

1. Finaliser le protocole, les informations et la version d’analyse, sans aucune observation de pilote.
2. Publier ces documents non personnels et leurs empreintes sur un support horodaté vérifiable. Le dépôt GitHub existant suffit pour un **horodatage externe de version**, sans nouveau compte : conserver le lien permanent vers le commit effectivement publié et sa date externe. Ne pas appeler cela un enregistrement dans un registre scientifique spécialisé si ce n’en est pas un. Un commit local ou une date saisie dans Markdown ne suffit pas.
3. Renseigner la référence/date réelles et l’autorisation prospective dans la configuration privée. Exécuter la commande `final_release.py prepare` documentée dans R3_FINAL_ACTIVATION.md ; elle refuse une configuration incomplète, construit un nouveau dossier immuable et vérifie le candidat exact.
4. Publier le verrou et les empreintes finales avant toute inscription ; conserver un reçu séparé pointant vers le commit publié, sans chercher à inclure sa propre empreinte. Une version provisoire antérieure ne vaut pas enregistrement du verrou final.
5. Donner l’approbation de publication du fichier exact, publier ce nouveau dossier en conservant les anciennes pages, puis vérifier les octets servis. Faire le court contrôle Android/iOS des seuls ajouts de consentement/export ; aucun nouvel audit géométrique instrumenté n’est demandé.
6. Une fois ces conditions satisfaites, l’investigateur décide réellement du lancement des invitations. À défaut, le résultat reste **CONDITIONAL GO — TECHNICALLY READY, INVESTIGATOR ACTION REQUIRED**. Transmettre les renseignements et décisions manquants constitue la suite humaine de cette mission, pas une nouvelle mission générale d’optimisation.
