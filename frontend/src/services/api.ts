/**
 * API Service for QueryOptX Backend
 */
import {
  BenchmarkResponse,
  CacheStatusResponse,
  CatalogSchemaResponse,
  DatabaseInfoDTO,
  OptimizationComparisonResponse,
  QueryAnalysisResponse,
  QueryExecutionResponse,
  TableStatDTO,
  WorkloadItem
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const api = {
  async checkHealth(): Promise<{ status: string; service: string; version: string }> {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error("Health check failed");
    return res.json();
  },

  async analyzeQuery(sql: string, db_id?: string): Promise<QueryAnalysisResponse> {
    const res = await fetch(`${API_BASE_URL}/query/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sql, db_id })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to analyze query");
    }
    return res.json();
  },

  async optimizeQuery(sql: string, useCache: boolean = true, db_id?: string): Promise<OptimizationComparisonResponse> {
    const res = await fetch(`${API_BASE_URL}/query/optimize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sql, use_cache: useCache, db_id })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to optimize query");
    }
    return res.json();
  },

  async executeQuery(sql: string, algorithm: string = "dynamic_programming", db_id?: string): Promise<QueryExecutionResponse> {
    const res = await fetch(`${API_BASE_URL}/query/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sql, algorithm, db_id })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Execution failed");
    }
    return res.json();
  },

  async runBenchmark(scale: number = 10000): Promise<BenchmarkResponse> {
    const res = await fetch(`${API_BASE_URL}/query/benchmark`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scale })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Benchmark run failed");
    }
    return res.json();
  },

  async getCatalog(db_id?: string): Promise<CatalogSchemaResponse> {
    const url = db_id ? `${API_BASE_URL}/statistics?db_id=${encodeURIComponent(db_id)}` : `${API_BASE_URL}/statistics`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch catalog statistics");
    return res.json();
  },

  async getTableStatistics(table: string, db_id?: string): Promise<TableStatDTO> {
    const url = db_id ? `${API_BASE_URL}/statistics/${table}?db_id=${encodeURIComponent(db_id)}` : `${API_BASE_URL}/statistics/${table}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch stats for table ${table}`);
    return res.json();
  },

  async listDatabases(): Promise<DatabaseInfoDTO[]> {
    const res = await fetch(`${API_BASE_URL}/databases`);
    if (!res.ok) throw new Error("Failed to fetch databases list");
    return res.json();
  },

  async createDatabase(name: string, description: string = "", ddl_sql: string = ""): Promise<DatabaseInfoDTO> {
    const res = await fetch(`${API_BASE_URL}/databases/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description, ddl_sql })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to create database");
    }
    return res.json();
  },

  async switchDatabase(db_id: string): Promise<{ message: string; active_db_id: string }> {
    const res = await fetch(`${API_BASE_URL}/databases/switch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ db_id })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to switch database");
    }
    return res.json();
  },

  async deleteDatabase(db_id: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE_URL}/databases/${db_id}`, {
      method: "DELETE"
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to delete database");
    }
    return res.json();
  },

  async executeDDL(db_id: string, ddl_sql: string): Promise<{ status: string; message: string; statements_executed: number; tables: string[] }> {
    const res = await fetch(`${API_BASE_URL}/databases/execute-ddl`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ db_id, ddl_sql })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to execute DDL / statements");
    }
    return res.json();
  },

  async resetDatabaseSchema(
    db_id: string,
    ddl_sql: string,
    name?: string,
    description?: string
  ): Promise<DatabaseInfoDTO> {
    const res = await fetch(`${API_BASE_URL}/databases/reset-schema`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ db_id, ddl_sql, name, description })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Schema reset failed");
    }
    return res.json();
  },

  async getCacheStatus(): Promise<CacheStatusResponse> {
    const res = await fetch(`${API_BASE_URL}/cache`);
    if (!res.ok) throw new Error("Failed to fetch cache status");
    return res.json();
  },

  async clearCache(): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE_URL}/cache/clear`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to clear plan cache");
    return res.json();
  },

  async getWorkloads(): Promise<WorkloadItem[]> {
    const res = await fetch(`${API_BASE_URL}/workloads`);
    if (!res.ok) throw new Error("Failed to fetch workloads");
    return res.json();
  }
};
