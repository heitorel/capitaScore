# 🏆 CapitaScore — League of Legends Stats Platform

![Java](https://img.shields.io/badge/Java-21-red?style=for-the-badge\&logo=openjdk)
![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.3.0-6DB33F?style=for-the-badge\&logo=springboot\&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge\&logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0-blue?style=for-the-badge\&logo=mysql)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![Contributions](https://img.shields.io/badge/Contributions-Welcome-orange?style=for-the-badge)

Plataforma completa que integra dados da Riot API (League of Legends), processa métricas avançadas de desempenho entre amigos e gera rankings automáticos.

O sistema é dividido em:

* **API Spring Boot (Java 21)** — ingestão + armazenamento de dados brutos
* **Módulo Python** — processamento de métricas + cálculo de final score

---

# 📌 Sumário

* Arquitetura Geral
* Tecnologias
* Estrutura do Projeto
* Instalação e Configuração
* Banco de Dados
* Sincronização de Partidas
* Métricas (Python)
* Endpoint de Ranking
* Roadmap
* Autor

---

# 🧱 Arquitetura Geral

```
                 ┌─────────────────────┐
                 │     Riot API        │
                 │ (Match + Timeline)  │
                 └─────────┬───────────┘
                           │
           [1] ingestão    │  🔑 API KEY
                           ▼
         ┌────────────────────────────────┐
         │      Spring Boot API           │
         │  - MatchIngestionService       │
         │  - RiotMatchClient             │
         │  - Members Sync                │
         │  - Ranking Controller          │
         └──────────┬─────────────────────┘
                    │  grava RAW
                    ▼
              ┌─────────────┐
              │    MySQL     │
              │ matches      │
              │ match_part.  │
              │ timelines    │
              │ p_match_met. │ ← resultado final
              └───────┬─────┘
                      │ lê RAW
        [2] métricas  ▼
            ┌───────────────────────────────┐
            │         Python Module         │
            │  compute_metrics.py           │
            │  - métricas brutas            │
            │  - normalização               │
            │  - final_score                │
            │  - INSERT em player_match_*   │
            └───────────────────────────────┘
```

---

# ⚙️ Tecnologias

## Backend

* Java 21
* Spring Boot 3
* Spring Web
* Spring Data JPA / Hibernate
* MySQL 8

## Python

* Python 3.10+
* pymysql
* json, csv

---

# 📂 Estrutura do Projeto

```text
src/main/java/com/capao/capitascore
│
├── common
│   └── BaseEntity.java
│
├── config
│   ├── RestConfig.java
│   └── RiotApiProperties.java
│
├── controller
│   ├── MatchController.java
│   ├── MemberController.java
│   └──RankingController.java
│
├── domain
│   ├── dto
│   │   ├── MemberRankingDto.java
│   │   └── PlayerRankingDto.java
│   ├── entity
│   │   ├── Match.java
│   │   ├── MatchParticipant.java
│   │   ├── MatchTimeline.java
│   │   ├── Member.java
│   │   ├── MemberRankingMetrics.java
│   │   └── PlayerMatchMetrics.java
│   ├── repository
│   │   ├── MatchParticipantRepository.java
│   │   ├── MatchRepository.java
│   │   ├── MatchTimelineRepository.java
│   │   ├── MemberRankingMetricsRepository.java
│   │   ├── MemberRepository.java
│   │   └── PlayerMatchMetricsRepository.java
│   └── service
│       └── MatchIngestionService.java
│
├── riot
│   ├── client
│   │   └── RiotMatchClientImpl.java
│   └── dto
│       ├── MatchDto.java
│       ├── MatchInfoDto.java
│       ├── MatchMetadataDto.java
│       ├── ParticipantDto.java
│       └── TimelineDto.java
│
└── CapitascoreApplication.java

python/
└── compute_metrics.py
```

---

# 🛠️ Instalação e Configuração

## 1. Clone o repositório

```bash
git clone https://github.com/heitorel/capitaScore.git
cd capitascore
```

## 2. Crie o banco MySQL

```sql
CREATE DATABASE capitascore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 3. Configure o arquivo application.yml

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/capitascore
    username: root
    password: root
  jpa:
    hibernate:
      ddl-auto: update

riot:
  api-key: ${RIOT_API_KEY}
  americas-base-url: https://americas.api.riotgames.com
  match-base-path: /lol/match/v5
```

## 4. Suba a aplicação

```bash
mvn spring-boot:run
```

---

# 🗄️ Banco de Dados

Todas as tabelas são criadas automaticamente via Hibernate.

### RAW Tables

* members
* matches
* match_participants
* match_timelines

### Processed

* player_match_metrics (gerada pelo Python)

---

# 🔄 Sincronização de Partidas

## Sync global

```http
POST /api/matches/sync/all?start=0&count=6
```

Processo:

* Busca todos os membros
* Para cada PUUID:

    * Busca match IDs
    * match.json
    * timeline.json
    * salva tudo no MySQL

---

# 🧮 Métricas (Python)

Execute:

```bash
python python/compute_metrics.py
```

## O script realiza:

### ✔️ Métricas brutas

* KDA
* Dano/minuto
* Gold/minuto
* CS/min
* Kill Participation
* XP/min
* Visão/min
* CC/min
* Mortes/min
* Dano recebido/min

### ✔️ Normalizações (0–100)

### ✔️ Final Score (fórmula ponderada)

### ✔️ Exportação CSV

### ✔️ Inserção no MySQL

---

# 📊 Endpoint de Ranking

```http
GET /api/ranking?minGames=3
```

### Exemplo:

```json
[
  {
    "puuid": "xxxxxx",
    "nome": "xxxxx",
    "nick": "xxxxxxx",
    "avgFinalScore": 84.2,
    "gamesPlayed": 12
  }
]
```

---

# 🚀 Roadmap

* [ ] Dashboard (React/Next.js)
* [ ] Gráficos tipo Radar
* [ ] Ranking por role
* [ ] Histórico de temporadas
* [ ] Scheduler automático
* [ ] Notificações Discord/WhatsApp
* [ ] Heatmaps e análise de movimento
* [ ] Build efficiency

---

# 👨‍💻 Autor

Projeto desenvolvido por **Heitor (Capão.CapitaScore)**.
