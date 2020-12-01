## Présentation du folder benchmark
Même organisation que le folder backend/tests, chaque dossier contient les données applicatives, les configurations et le fichier d'environment .env.

- Un fichier questions/réponses pour l'évaluation
- utils.py: fonctions utilisés dans les scripts
- bm25.py: script d'évaluation des metrics selon la recherche BM25
- sbert.py: script d'évaluation des metrics avec SBERT

Testé dans backend/tests/benchmark/test_bm25.py

# Installation de l'environnement d'execution
Modifier le fichier artifact:
```export INDEX_NAME = nom de l'index à créer, ex: bld-benchmarck
export DATA_PATH = chemin/vers/data (ex. ${APP_PATH}/backend/benchmark/bld/data)
export ENV_FILE = chemin/vers/.env (ex. ${APP_PATH}/backend/benchmark/bld/.env-bld)
export DC_UP_ARGS=
```

(Re)Fabriquer l'image docker du backend : `make backend-dev`.
Rentrer dans le container : `make backend-exec`

# Execution de bm25.py
Avoir de l'aide : `python -m benchmark.bm25 --help`
Le script s'execute de cette façon: `python -m benchmark.bm25 -base-path /data/user -qr QR_file_cleaned.csv -env .env -m dcg -index`
Arguments:
- -base-path: (optionel) Si précisé, le répertoire de base, sinon le répertoire du script lancé
- -qr: chemin de la base de test par rapport au base-path
- -env: chemin d'environement par rapport au base-path
- -m: la metric
Print la réponse de la requête _rank_eval (json)

# Evaluation des metrics
Les étapes du scripts sont détaillées en commentaire: récuperation des variables, indexation, injection des documents, création de la requête _rank_eval.
Documentation: https://www.elastic.co/guide/en/elasticsearch/reference/current/search-rank-eval.html

# Précisions
- Les modifications s'effectuent soient dans le map, soit dans la requête
- **Les settings des metrics sont hardcodés dans utils.metric_parameters**

# Améliorations futures:
- de-hardcoder sections
- settings des metrics
- sauvegarde du résulat
