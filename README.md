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