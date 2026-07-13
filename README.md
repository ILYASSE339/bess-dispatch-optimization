# Flexible Asset Optimisation on Electricity Markets

Optimisation du dispatch d'un portefeuille d'actifs flexibles (BESS, éolien, centrale gaz)
sur le marché spot électrique français — données réelles ENTSO-E.

## Ce que fait ce projet

- **Modèle MILP** de dispatch optimal sur horizon 24h (cvxpy)
- **Pipeline de données** ENTSO-E → nettoyage → modèle
- **Backtest P&L** sur données historiques réelles
- **Portefeuille multi-actifs** : BESS + éolien + centrale gaz (en cours)
- **Couche stochastique** Monte Carlo sur les prix (à venir)

## Stack

- Python · cvxpy · pandas · plotly
- Données : ENTSO-E Transparency Platform

## Structure

## Résultats backtest 2024

| Métrique | Valeur |
|---|---|
| Période | 2024 — 365 jours |
| Profit total | 56 425 EUR |
| Profit moyen / jour | 154.59 EUR |
| Meilleure journée | 17 avril 2024 — 401 EUR |
| Jours profitables | 365 / 365 |
| Capacité finale | 1.923 MWh (dégradation aging) |

> **Limite :** modèle déterministe avec perfect foresight sur les prix J+1.
> En production, les prix seraient forecastés — ce qui réduirait la performance réelle.
> La couche stochastique (Monte Carlo) est la prochaine étape.