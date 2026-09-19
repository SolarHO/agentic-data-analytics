# Agentic Data Analytics Platform

자연어로 데이터 분석을 요청하면 AI Agent가 데이터와 비즈니스 정의를 바탕으로  
SQL 생성, 데이터 조회, 분석, 검증 및 결과 보고까지 수행하는 **AI 기반 데이터 분석 자동화 플랫폼**입니다.

현재는 Olist E-commerce 데이터를 기반으로 분석용 PostgreSQL 데이터베이스와  
Gold Query 및 자동 검증 환경을 구축했으며, 이후 LangGraph 기반 Text-to-SQL, RAG,  
Python Analysis, Kafka 기반 비동기 처리 및 Multi-Agent 구조로 확장할 예정입니다.

---

## 1. Project Overview

일반적인 데이터 분석 과정에서는 사용자의 분석 요청을 이해한 뒤 데이터 구조를 확인하고,
SQL을 작성하고, 결과를 검증하고, 다시 해석하는 과정이 반복됩니다.

이 프로젝트는 이러한 과정을 AI Agent 기반 Workflow로 자동화하는 것을 목표로 합니다.

최종적으로 다음과 같은 질문을 자연어로 처리할 수 있는 분석 시스템을 구현합니다.

> "배송 완료 주문의 평균 주문 금액은?"

> "월별 매출 추이를 분석해줘."

> "배송 지연과 리뷰 점수 사이에 어떤 관계가 있는지 분석해줘."

단순히 LLM이 SQL을 생성하는 것에서 끝나는 것이 아니라,

- 데이터베이스 스키마
- KPI 및 비즈니스 지표 정의
- 데이터 품질 정보
- SQL 실행 결과
- 분석 결과 검증

을 함께 활용하여 보다 신뢰할 수 있는 분석 Workflow를 구축하는 것이 핵심 목표입니다.

---

## 2. Target Architecture

```text
User / Slack
      │
      ▼
     n8n
      │
      ▼
   FastAPI
      │
      ▼
    Kafka
      │
      ▼
  LangGraph
      │
      ├── Context / RAG
      │
      ├── SQL Agent
      │
      ├── SQL Validator
      │
      ├── SQL Executor
      │
      ├── Python Analysis
      │
      ├── Result Validator
      │
      └── Report Agent
      │
      ▼
PostgreSQL / pgvector
      │
      ▼
 Analysis Result
      │
      ├── Slack
      └── BI Dashboard
```

> 위 구조는 프로젝트의 **목표 아키텍처**입니다.  
> 현재는 PostgreSQL 기반 분석 데이터 계층과 Gold Query 검증 환경까지 구현되어 있습니다.

---

## 3. Current Progress

### Data & Backend Foundation

- [o] Python 가상환경 구성
- [o] FastAPI 프로젝트 구조 구성
- [o] Docker 기반 PostgreSQL 16 환경 구축
- [o] FastAPI ↔ PostgreSQL 연결
- [o] Olist 데이터 프로파일링
- [o] Primary Key / Foreign Key 후보 검증
- [o] PostgreSQL Schema 설계
- [o] Olist 데이터 PostgreSQL 적재
- [o] 데이터 적재 Row Count 검증
- [o] Gold Query 작성
- [o] pytest 기반 Gold Query 자동 검증

### Agentic Analytics

- [ ] LangGraph Workflow
- [ ] Text-to-SQL Agent
- [ ] SQL Validator
- [ ] SQL Executor
- [ ] Result Validator
- [ ] RAG / pgvector
- [ ] Python Analysis Agent
- [ ] Report Agent

### Platform

- [ ] Kafka Worker
- [ ] Retry / DLQ
- [ ] n8n Workflow
- [ ] Slack Integration
- [ ] BI Integration

### Evaluation

- [ ] Text-to-SQL Evaluation
- [ ] Single-Agent Evaluation
- [ ] Multi-Agent Evaluation
- [ ] Accuracy / Latency / Token / Cost 비교

---

## 4. Dataset

프로젝트의 분석 데이터로 **Brazilian E-Commerce Public Dataset by Olist**를 사용합니다.

주요 데이터는 다음과 같습니다.

| Dataset | Description |
|---|---|
| Customers | 고객 정보 |
| Orders | 주문 정보 |
| Order Items | 주문 상품 정보 |
| Payments | 결제 정보 |
| Reviews | 리뷰 및 평점 |
| Products | 상품 정보 |
| Sellers | 판매자 정보 |
| Category Translation | 상품 카테고리 영문 변환 |
| Geolocation | 우편번호 기반 위치 정보 |

원본 CSV 파일은 Repository에 포함하지 않습니다.

데이터 파일은 로컬의 다음 경로에 배치하여 사용합니다.

```text
data/raw/
```

---

## 5. Database Design

데이터 분석 전 실제 데이터의 Key 관계와 데이터 품질을 검증한 뒤 PostgreSQL Schema를 설계했습니다.

주요 관계는 다음과 같습니다.

```text
customers
    │
    ▼
  orders
    │
    ├──────────────► order_payments
    │
    ├──────────────► order_reviews
    │
    ▼
order_items
    │
    ├──────────────► products
    │                   │
    │                   ▼
    │            category_translation
    │
    └──────────────► sellers
```

### Data Quality Findings

데이터를 직접 검증하는 과정에서 몇 가지 중요한 특성을 확인했습니다.

**1. `review_id`는 단독으로 Unique하지 않음**

`order_reviews` 데이터에서 `review_id` 중복이 존재하기 때문에 다음 복합키를 사용합니다.

```text
(review_id, order_id)
```

**2. Category Translation 데이터가 완전하지 않음**

`products`에 존재하는 다음 두 카테고리가 translation 데이터에 존재하지 않습니다.

```text
pc_gamer
portateis_cozinha_e_preparadores_de_alimentos
```

따라서 `products → category_translation` 관계에는 물리적인 Foreign Key를 적용하지 않고,
분석 시 `LEFT JOIN`을 사용합니다.

**3. Geolocation 데이터는 ZIP Prefix 기준으로 Unique하지 않음**

동일 ZIP Prefix에 여러 좌표 및 지역 정보가 존재하기 때문에 ZIP Prefix를 단순 Primary Key 또는
Foreign Key로 사용하지 않습니다.

상세한 데이터 모델 및 데이터 품질 내용은 향후 `docs/database.md`에서 관리할 예정입니다.

---

## 6. Data Ingestion

Olist 9개 데이터셋을 PostgreSQL에 적재하고 CSV와 데이터베이스의 Row Count를 비교하여
적재 결과를 검증했습니다.

| Table | Rows |
|---|---:|
| customers | 99,441 |
| category_translation | 71 |
| products | 32,951 |
| sellers | 3,095 |
| orders | 99,441 |
| order_items | 112,650 |
| order_payments | 103,886 |
| order_reviews | 99,224 |
| geolocation | 1,000,163 |
| **Total** | **1,550,922** |

---

## 7. Gold Queries

LLM이 생성한 SQL의 실행 성공 여부만으로는 분석 정확성을 판단하기 어렵습니다.

따라서 주요 비즈니스 질문에 대해 사람이 직접 작성하고 검증한 **Gold Query**를 구축하여
향후 Text-to-SQL Agent의 Ground Truth로 사용합니다.

현재 정의한 주요 분석 지표는 다음과 같습니다.

| Gold Query | Description |
|---|---|
| GQ01 | 배송 완료 주문 매출 |
| GQ02 | Average Order Value |
| GQ03 | 월별 상품 매출 |
| GQ04 | 카테고리별 상품 매출 |
| GQ05 | 배송 지연률 |
| GQ06 | 리뷰 점수 |

현재 검증된 주요 기준값:

| Metric | Result |
|---|---:|
| Delivered Orders | 96,478 |
| Sold Items | 110,197 |
| Product Revenue | 13,221,498.11 |
| Freight Value | 2,198,275.64 |
| Gross Item Value | 15,419,773.75 |
| Average Order Value | 137.04 |
| Delivery Delay Rate | 8.11% |
| Average Review Score | 4.09 |

### Metric Definition Example

Average Order Value는 상품의 평균 가격이 아니라 **주문 단위 매출의 평균**으로 정의합니다.

```text
order_items
      │
      │ GROUP BY order_id
      ▼
order revenue
      │
      │ AVG
      ▼
     AOV
```

이러한 지표 정의는 향후 RAG Context와 Agent Evaluation에도 활용할 예정입니다.

---

## 8. Automated Validation

Gold Query의 핵심 결과가 데이터베이스 또는 코드 변경으로 인해 달라지는 것을 감지하기 위해
`pytest` 기반 테스트를 구성했습니다.

현재 테스트 결과:

```text
test_delivered_sales_summary PASSED
test_average_order_value      PASSED
test_delivery_delay_rate      PASSED
test_review_summary           PASSED

4 passed
```

테스트 실행:

```bash
pytest tests/test_gold_queries.py -v
```

---

## 9. Tech Stack

| Area | Technology |
|---|---|
| Language | Python 3.12 |
| API | FastAPI |
| Database | PostgreSQL 16 |
| ORM / DB Access | SQLAlchemy, psycopg |
| Container | Docker / Docker Compose |
| Agent Workflow | LangGraph |
| LLM Integration | LangChain / OpenAI |
| Vector Database | pgvector (Planned) |
| Messaging | Apache Kafka (Planned) |
| Workflow Automation | n8n (Planned) |
| Analysis | Pandas / Python |
| Testing | pytest |
| BI | Tableau / Power BI (Planned) |

---

## 10. Project Structure

```text
agentic-data-analytics/
│
├── app/
│   ├── api/
│   ├── agents/
│   ├── db/
│   ├── graph/
│   └── main.py
│
├── data/
│   └── raw/                 # Local dataset (Git ignored)
│
├── docs/                    # Technical documentation
│
├── scripts/
│   ├── inspect_olist.py
│   ├── validate_keys.py
│   ├── validate_relationships.py
│   └── load_olist.py
│
├── sql/
│   ├── schema.sql
│   └── gold_queries.sql
│
├── tests/
│   └── test_gold_queries.py
│
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 11. Getting Started

### 1. Clone Repository

```bash
git clone <repository-url>
cd agentic-data-analytics
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

`.env.example`을 복사하여 `.env` 파일을 생성합니다.

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=analytics
DB_USER=analytics_user
DB_PASSWORD=<your-password>
```

### 5. Start PostgreSQL

```bash
docker compose up -d
```

### 6. Create Database Schema

Windows PowerShell:

```powershell
Get-Content sql\schema.sql |
docker exec -i analytics-postgres `
psql -U analytics_user -d analytics
```

### 7. Prepare Dataset

Olist CSV 파일을 다음 경로에 배치합니다.

```text
data/raw/
```

### 8. Load Data

```bash
python -m scripts.load_olist
```

### 9. Run Tests

```bash
pytest
```

---

## 12. Evaluation Plan

최종적으로 동일한 분석 질문에 대해 **Single-Agent와 Multi-Agent Workflow를 비교**할 예정입니다.

주요 평가 지표는 다음과 같습니다.

- SQL Execution Success Rate
- SQL Accuracy
- Analysis Result Accuracy
- Retry Count
- End-to-End Latency
- Token Usage
- LLM Cost

Gold Query를 Ground Truth로 사용하여 Agent 구조 변경이 실제 분석 품질을 개선하는지 정량적으로 평가하는 것이 목표입니다.

---

## 13. Documentation

README에는 프로젝트의 전체 구조와 핵심 내용만 유지하고,
세부적인 설계 및 실험 과정은 `docs/`에서 관리할 예정입니다.

| Document | Description |
|---|---|
| `docs/architecture.md` | 시스템 아키텍처 및 기술 선택 |
| `docs/database.md` | 데이터 모델 및 데이터 품질 |
| `docs/analytics.md` | KPI 정의 및 Gold Query |
| `docs/agent-workflow.md` | LangGraph / Agent Workflow |
| `docs/rag.md` | RAG 및 pgvector 설계 |
| `docs/evaluation.md` | Single-Agent / Multi-Agent 평가 |

---

## 14. Roadmap

```text
Phase 1  Data Foundation
         PostgreSQL / Schema / Ingestion / Gold Query
                         ✅

Phase 2  Agent Workflow
         LangGraph / Text-to-SQL / SQL Validation
                         ↓

Phase 3  Context & Analysis
         RAG / pgvector / Python Analysis
                         ↓

Phase 4  Data Platform
         Kafka / Worker / Retry / DLQ
                         ↓

Phase 5  Integration
         FastAPI / n8n / Slack / BI
                         ↓

Phase 6  Evaluation
         Single-Agent vs Multi-Agent
```

---

## Project Status

**Current Phase: Data Foundation → Agent Workflow**

데이터베이스 구축과 분석 Ground Truth 검증을 완료했으며,
현재 LangGraph 기반 Text-to-SQL Workflow 구현을 진행하고 있습니다.