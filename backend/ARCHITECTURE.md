# ArbitrageVault Backend - Architecture Documentation

## 🏗️ **System Architecture Overview**

### **Hybrid Architecture Pattern**

ArbitrageVault implements a **Hybrid Architecture** separating compute and data layers for optimal performance, scalability, and maintainability.

```
                    ┌─────────────────────────────────────────┐
                    │         PRODUCTION ENVIRONMENT          │
                    └─────────────────────────────────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
        ▼                               ▼                               ▼
┌─────────────────┐            ┌──────────────────┐            ┌─────────────────┐
│   FRONTEND      │            │    BACKEND       │            │    DATABASE     │
│                 │            │                  │            │                 │
│  React/Next.js  │◄───HTTP────┤  FastAPI + uv    │◄──AsyncPG──┤ Neon PostgreSQL │
│  (Future)       │            │  SQLAlchemy 2.0  │            │  300-500 conn   │
│                 │            │  Pydantic v2     │            │  Branch Support │
└─────────────────┘            └──────────────────┘            └─────────────────┘
                                        │                               
                               ┌──────────────────┐                    
                               │  EXTERNAL APIs   │                    
                               │  Keepa, OpenAI   │                    
                               └──────────────────┘                    
```

## 🎯 **Architecture Decisions & Benefits**

### **1. Hybrid Backend + Database Architecture**

#### **Decision**
- **Backend**: Render Web Service (Compute Layer)
- **Database**: Neon PostgreSQL (Data Layer)
- **Pattern**: Separation of concerns between compute and storage

#### **Benefits**
- **Scalability**: Independent scaling of compute vs storage resources
- **Performance**: 15x connection pool improvement (20 → 300-500 connections)
- **Reliability**: Database managed by Neon specialists, backend by Render
- **Cost Optimization**: Pay for compute and storage separately based on usage
- **Flexibility**: Can switch backend hosting without database migration

#### **Trade-offs**
- **Complexity**: Managing two services instead of one
- **Network Latency**: Slight increase due to external database connection
- **Configuration**: Need to manage connection strings and SSL certificates

---

*This architecture documentation reflects the current state of the ArbitrageVault backend and serves as a guide for future development and maintenance decisions.*