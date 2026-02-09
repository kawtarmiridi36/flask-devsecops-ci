# Projet DevSecOps Flask

Ce projet implémente une chaîne DevSecOps complète.

## Pipeline CI/CD
- Tests automatiques
- Analyse de sécurité (SAST, DAST)
- Scan des dépendances
- Build et déploiement

## Équipe
- MIRIDI Kawtar
- ZAKI Yasmina

## 📝 Security Implementation Notes

### SAST Tooling Choice
Due to GitHub limitations for personal accounts (CodeQL requires Organization account), 
we use Bandit + Safety for SAST analysis. These provide equivalent security coverage.

### Complete DevSecOps Stack:
- **SAST**: Bandit (Python security) + Safety (dependencies)
- **Dependency Scanning**: pip-audit
- **IaC Security**: Checkov
- **Container Security**: Trivy
- **CI/CD**: GitHub Actions with security gates

All security checks are automated and required to pass before deployment.
