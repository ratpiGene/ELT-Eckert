"""
C4.2.2 — Calcul distribué : rapprochement décès × contrats sous Apache Spark.

C'est la brique qui justifie le distribué par la donnée : le fichier des décès
cumulé se compte en dizaines de millions de lignes. Le rapprochement se fait sur
une clé d'identité probabiliste (nom + premier prénom + date de naissance),
faute d'identifiant national dans le périmètre — d'où la GRADUATION du résultat
en trois niveaux de confiance, exposée dans gold.contrat_desherence.

Exécution (depuis le conteneur spark-master, cf. README) :

    spark-submit \
      --master spark://spark-master:7077 \
      --packages org.postgresql:postgresql:42.7.4 \
      /opt/app/src/eckert/spark/rapprochement.py \
      --run-id manuel_$(date +%Y%m%dT%H%M%S)

Les paramètres de connexion se lisent dans l'environnement (voir .env), avec des
valeurs par défaut adaptées au réseau Docker Compose.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def _jdbc_url() -> str:
    hote = os.environ.get("PG_HOST", "postgres")
    port = os.environ.get("PG_PORT", "5432")
    base = os.environ.get("PG_DB", "eckert")
    return f"jdbc:postgresql://{hote}:{port}/{base}"


def _props() -> dict[str, str]:
    return {
        "user": os.environ.get("PG_USER", "elt_writer"),
        # Le mot de passe vient de l'environnement (ELT_WRITER_PASSWORD), jamais du code.
        "password": os.environ.get("PG_PASSWORD", os.environ.get("ELT_WRITER_PASSWORD", "")),
        "driver": "org.postgresql.Driver",
    }


def _lire(spark: SparkSession, requete: str) -> DataFrame:
    return (
        spark.read.format("jdbc")
        .option("url", _jdbc_url())
        .option("dbtable", requete)
        .options(**_props())
        .load()
    )


def rapprocher(spark: SparkSession, run_id: str) -> DataFrame:
    """Construit la table des contrats potentiellement en déshérence.

    Trois niveaux de confiance :
      - CERTAIN    : clé exacte + sexe concordant + lieu de naissance concordant
      - PROBABLE   : clé exacte (nom + premier prénom + date de naissance)
      - A_VERIFIER : homonymie — nom et date de naissance concordants mais
                     prénom différent (candidat à lever par un humain)
    """
    deces = _lire(spark, "silver.deces").alias("d")
    adherents = _lire(spark, "silver.adherent").alias("a")
    contrats = _lire(spark, "(SELECT * FROM silver.contrat WHERE statut = 'EN_COURS') AS c").alias(
        "c"
    )

    # --- Correspondance forte : clé de rapprochement identique ---------------
    forte = deces.join(
        adherents, F.col("d.cle_rapprochement") == F.col("a.cle_rapprochement"), "inner"
    ).select(
        F.col("a.adherent_id").alias("adherent_id"),
        F.col("a.nom").alias("nom"),
        F.col("a.prenoms").alias("prenoms"),
        F.col("a.date_naissance").alias("date_naissance"),
        F.col("d.date_deces").alias("date_deces"),
        F.when(
            (F.col("d.sexe") == F.col("a.sexe"))
            & (F.col("d.code_lieu_naissance") == F.col("a.code_insee_naiss")),
            F.lit("CERTAIN"),
        )
        .otherwise(F.lit("PROBABLE"))
        .alias("niveau_confiance"),
    )

    # --- Homonymie : même nom + même date de naissance, prénom différent -----
    cles_fortes = forte.select("adherent_id").distinct()
    homonymes = (
        deces.join(
            adherents,
            (F.col("d.nom") == F.col("a.nom"))
            & (F.col("d.date_naissance") == F.col("a.date_naissance"))
            & (F.col("d.prenoms") != F.col("a.prenoms")),
            "inner",
        )
        .select(
            F.col("a.adherent_id").alias("adherent_id"),
            F.col("a.nom").alias("nom"),
            F.col("a.prenoms").alias("prenoms"),
            F.col("a.date_naissance").alias("date_naissance"),
            F.col("d.date_deces").alias("date_deces"),
            F.lit("A_VERIFIER").alias("niveau_confiance"),
        )
        # on n'ajoute pas en « à vérifier » un adhérent déjà rapproché avec certitude
        .join(cles_fortes, "adherent_id", "left_anti")
    )

    candidats = forte.unionByName(homonymes)

    # --- Jointure aux contrats en cours et calcul des indicateurs métier -----
    resultat = (
        candidats.join(contrats, "adherent_id", "inner")
        .withColumn("jours_depuis_deces", F.datediff(F.current_date(), F.col("date_deces")))
        .withColumn("detecte_le", F.current_timestamp())
        .withColumn("run_id", F.lit(run_id))
        .select(
            F.col("c.contrat_id").alias("contrat_id"),
            "adherent_id",
            "nom",
            "prenoms",
            "date_naissance",
            "date_deces",
            "jours_depuis_deces",
            "niveau_confiance",
            F.col("c.capital_garanti").alias("capital_garanti"),
            "detecte_le",
            "run_id",
        )
    )
    return resultat


def ecrire(resultat: DataFrame) -> None:
    (
        resultat.write.format("jdbc")
        .option("url", _jdbc_url())
        .option("dbtable", "gold.contrat_desherence")
        .options(**_props())
        .mode("append")
        .save()
    )


def main() -> None:
    parseur = argparse.ArgumentParser(description="Rapprochement distribué décès × contrats")
    parseur.add_argument(
        "--run-id", default=f"spark_{datetime.now():%Y%m%dT%H%M%S}", help="Identifiant d'exécution"
    )
    args = parseur.parse_args()

    spark = SparkSession.builder.appName(f"eckert-rapprochement-{args.run_id}").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    resultat = rapprocher(spark, args.run_id)
    resultat.cache()

    total = resultat.count()
    par_niveau = {
        ligne["niveau_confiance"]: ligne["n"]
        for ligne in resultat.groupBy("niveau_confiance").agg(F.count("*").alias("n")).collect()
    }
    print("=" * 60)
    print(f"Rapprochement {args.run_id} — {total} contrats potentiellement en déshérence")
    for niveau in ("CERTAIN", "PROBABLE", "A_VERIFIER"):
        print(f"  {niveau:<12}: {par_niveau.get(niveau, 0)}")
    print("=" * 60)

    ecrire(resultat)
    print(f"Écrit dans gold.contrat_desherence (run_id={args.run_id}).")

    spark.stop()


if __name__ == "__main__":
    main()
