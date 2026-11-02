import React, { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { SqlEditor } from "./components/SqlEditor";
import { QueryAnalysisCard } from "./components/QueryAnalysisCard";
import { PlanTreeVisualizer } from "./components/PlanTreeVisualizer";
import { AlgorithmComparison } from "./components/AlgorithmComparison";
import { CostBreakdownChart } from "./components/CostBreakdownChart";
import { EstimatedVsActualCard } from "./components/EstimatedVsActualCard";
import { StatisticsInspector } from "./components/StatisticsInspector";
import { BenchmarkSuite } from "./components/BenchmarkSuite";
import { CacheMonitor } from "./components/CacheMonitor";
import { EducationGuideModal } from "./components/EducationGuideModal";
import { DatabaseManagerView } from "./components/DatabaseManagerView";
import { api } from "./services/api";
import {
  BenchmarkResponse,
  CacheStatusResponse,
  CatalogSchemaResponse,
  DatabaseInfoDTO,
  OptimizationComparisonResponse,
  QueryAnalysisResponse,
  QueryExecutionResponse,
  WorkloadItem
} from "./types";
import { ArrowRight, Sparkles, RefreshCw, Zap, ShieldAlert, Layers } from "lucide-react";

export const App: React.FC = () => {
  // Navigation & Modal state
  const [activeTab, setActiveTab] = useState<string>("optimizer");
  const [isTheoryGuideOpen, setIsTheoryGuideOpen] = useState<boolean>(false);
  const [backendOnline, setBackendOnline] = useState<boolean>(true);

  // Workbench SQL state
  const defaultSql = `SELECT s.name, c.title, e.grade
FROM students s
JOIN enrollments e ON s.student_id = e.student_id
JOIN courses c ON e.course_id = c.course_id
WHERE s.gpa >= 3.50 AND s.department = 'Computer Science';`;

  const [sql, setSql] = useState<string>(defaultSql);
  const [selectedWorkloadId, setSelectedWorkloadId] = useState<string>("");
  const [useCache, setUseCache] = useState<boolean>(true);

  // Data states
  const [workloads, setWorkloads] = useState<WorkloadItem[]>([]);
  const [databases, setDatabases] = useState<DatabaseInfoDTO[]>([]);
  const [activeDbId, setActiveDbId] = useState<string>("default_univ");
  const [analysis, setAnalysis] = useState<QueryAnalysisResponse | null>(null);
  const [optimization, setOptimization] = useState<OptimizationComparisonResponse | null>(null);
  const [execution, setExecution] = useState<QueryExecutionResponse | null>(null);
  const [catalog, setCatalog] = useState<CatalogSchemaResponse | null>(null);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkResponse | null>(null);
  const [cacheStatus, setCacheStatus] = useState<CacheStatusResponse | null>(null);

  // Loading states
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [isBenchmarking, setIsBenchmarking] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Plan view selector (Original Logical, Rewritten Logical, Optimal Physical)
  const [planViewMode, setPlanViewMode] = useState<"optimal_physical" | "rewritten_logical" | "original_logical">(
    "optimal_physical"
  );

  // Initial data loading
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [health, workloadsData, catalogData, cacheData, dbListData] = await Promise.all([
        api.checkHealth().catch(() => ({ status: "offline" })),
        api.getWorkloads().catch(() => []),
        api.getCatalog().catch(() => null),
        api.getCacheStatus().catch(() => null),
        api.listDatabases().catch(() => [])
      ]);

      setBackendOnline(health.status === "online");
      setWorkloads(workloadsData);
      setCatalog(catalogData);
      setCacheStatus(cacheData);
      setDatabases(dbListData);
      const active = dbListData.find((d: DatabaseInfoDTO) => d.is_active);
      if (active) setActiveDbId(active.db_id);

      // Auto-run initial analysis
      handleAnalyze(defaultSql);
    } catch (err: any) {
      console.error("Initial load error:", err);
    }
  };

  const handleSelectWorkload = (item: WorkloadItem) => {
    setSelectedWorkloadId(item.id);
    setSql(item.sql);
    setErrorMessage(null);
    handleAnalyze(item.sql);
  };

  const handleAnalyze = async (queryToAnalyze?: string, targetDbId?: string) => {
    const q = queryToAnalyze || sql;
    const dbToUse = targetDbId || activeDbId;
    setIsAnalyzing(true);
    setErrorMessage(null);
    try {
      const res = await api.analyzeQuery(q, dbToUse);
      setAnalysis(res);
      if (!res.is_valid && res.error_message) {
        setErrorMessage(res.error_message);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to analyze query");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleOptimize = async () => {
    setIsOptimizing(true);
    setErrorMessage(null);
    try {
      const res = await api.optimizeQuery(sql, useCache, activeDbId);
      setOptimization(res);
      // Refresh cache metrics
      api.getCacheStatus().then((c) => setCacheStatus(c));
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to optimize query");
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    setErrorMessage(null);
    try {
      const res = await api.executeQuery(sql, "dynamic_programming", activeDbId);
      setExecution(res);
      setActiveTab("execution"); // switch to estimated vs actual tab
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to execute query");
    } finally {
      setIsExecuting(false);
    }
  };

  const handleSwitchDb = async (dbId: string) => {
    try {
      await api.switchDatabase(dbId);
      setActiveDbId(dbId);
      const [dbs, cat] = await Promise.all([
        api.listDatabases(),
        api.getCatalog(dbId)
      ]);
      setDatabases(dbs);
      setCatalog(cat);
      // If custom database has tables, suggest a sample query
      const chosen = dbs.find((d: DatabaseInfoDTO) => d.db_id === dbId);
      if (chosen && chosen.tables.length > 0) {
        const t1 = chosen.tables[0];
        const t2 = chosen.tables.length > 1 ? chosen.tables[1] : null;
        if (t2) {
          setSql(`SELECT * FROM ${t1} t1 JOIN ${t2} t2 LIMIT 10;`);
        } else {
          setSql(`SELECT * FROM ${t1} LIMIT 10;`);
        }
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to switch database");
    }
  };

  const handleCreateDb = async (name: string, description: string, ddl: string) => {
    const created = await api.createDatabase(name, description, ddl);
    setActiveDbId(created.db_id);
    const [dbs, cat] = await Promise.all([
      api.listDatabases(),
      api.getCatalog(created.db_id)
    ]);
    setDatabases(dbs);
    setCatalog(cat);
    if (created.tables.length > 0) {
      const t1 = created.tables[0];
      const t2 = created.tables.length > 1 ? created.tables[1] : null;
      if (t2) {
        setSql(`SELECT * FROM ${t1} t1 JOIN ${t2} t2 LIMIT 10;`);
      } else {
        setSql(`SELECT * FROM ${t1} LIMIT 10;`);
      }
    }
  };

  const handleDeleteDb = async (dbId: string) => {
    try {
      await api.deleteDatabase(dbId);
      const dbs = await api.listDatabases();
      setDatabases(dbs);
      const active = dbs.find((d: DatabaseInfoDTO) => d.is_active) || dbs[0];
      if (active) {
        setActiveDbId(active.db_id);
        const cat = await api.getCatalog(active.db_id);
        setCatalog(cat);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to delete database");
    }
  };

  const handleExecuteDDL = async (dbId: string, ddl: string) => {
    await api.executeDDL(dbId, ddl);
    const [dbs, cat] = await Promise.all([
      api.listDatabases(),
      api.getCatalog(dbId)
    ]);
    setDatabases(dbs);
    setCatalog(cat);
  };

  const handleRefreshDatabases = async () => {
    const [dbs, cat] = await Promise.all([
      api.listDatabases(),
      api.getCatalog(activeDbId)
    ]);
    setDatabases(dbs);
    setCatalog(cat);
  };

  const handleRunBenchmark = async (scale: number) => {
    setIsBenchmarking(true);
    setErrorMessage(null);
    try {
      const res = await api.runBenchmark(scale);
      setBenchmarkData(res);
    } catch (err: any) {
      setErrorMessage(err.message || "Benchmark execution failed");
    } finally {
      setIsBenchmarking(false);
    }
  };

  const handleClearCache = async () => {
    try {
      await api.clearCache();
      const updated = await api.getCacheStatus();
      setCacheStatus(updated);
    } catch (err: any) {
      console.error("Failed to clear cache", err);
    }
  };

  const getBestPlanNode = () => {
    if (!optimization) return null;
    if (planViewMode === "original_logical") return optimization.original_logical_plan;
    if (planViewMode === "rewritten_logical") return optimization.rewritten_logical_plan;
    const best = optimization.best_algorithm;
    return optimization.algorithms[best]?.execution_plan || null;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenTheoryGuide={() => setIsTheoryGuideOpen(true)}
        backendOnline={backendOnline}
        cacheHitRate={cacheStatus?.hit_rate_percent || 0}
        activeDbName={databases.find((d) => d.db_id === activeDbId)?.name || activeDbId}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Global Error Banner if any */}
        {errorMessage && (
          <div className="mb-6 p-4 bg-rose-950/50 border border-rose-800 rounded-xl text-xs text-rose-200 flex items-start space-x-3 shadow-lg">
            <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-bold text-rose-300">System Notification</h4>
              <p className="mt-0.5 text-slate-300">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Tab 1: Optimizer Workbench */}
        {activeTab === "optimizer" && (
          <div className="space-y-6">
            {/* SQL Editor */}
            <SqlEditor
              sql={sql}
              setSql={setSql}
              onAnalyze={() => handleAnalyze()}
              onOptimize={handleOptimize}
              onExecute={handleExecute}
              isAnalyzing={isAnalyzing}
              isOptimizing={isOptimizing}
              isExecuting={isExecuting}
              workloads={workloads}
              selectedWorkloadId={selectedWorkloadId}
              onSelectWorkload={handleSelectWorkload}
              useCache={useCache}
              setUseCache={setUseCache}
              activeDbName={databases.find((d) => d.db_id === activeDbId)?.name || activeDbId}
              availableTables={databases.find((d) => d.db_id === activeDbId)?.tables || Object.keys(catalog?.tables || {})}
            />

            {/* AST Decomposition */}
            <QueryAnalysisCard analysis={analysis} />

            {/* Plan Display Selector and Tree */}
            {optimization && (
              <div className="space-y-4">
                {/* Plan mode selector tabs */}
                <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900 p-2 rounded-xl border border-slate-800">
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => setPlanViewMode("optimal_physical")}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                        planViewMode === "optimal_physical"
                          ? "bg-emerald-600 text-white shadow-md"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      Best Execution Plan ({optimization.best_algorithm.replace("_", " ").toUpperCase()})
                    </button>

                    <button
                      onClick={() => setPlanViewMode("rewritten_logical")}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                        planViewMode === "rewritten_logical"
                          ? "bg-indigo-600 text-white shadow-md"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      Rewritten Logical Plan
                    </button>

                    <button
                      onClick={() => setPlanViewMode("original_logical")}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                        planViewMode === "original_logical"
                          ? "bg-slate-700 text-white shadow-md"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      Original Canonical Plan
                    </button>
                  </div>

                  <div className="flex items-center space-x-2 text-xs font-mono text-slate-400 px-2">
                    <span className="text-[10px] text-slate-500">Cache Status:</span>
                    <span className={optimization.cache_hit ? "text-emerald-400 font-bold" : "text-slate-300"}>
                      {optimization.cache_hit ? "HIT (Reused)" : "MISS (Optimized)"}
                    </span>
                  </div>
                </div>

                {/* Rewrite Provenance Steps */}
                {optimization.rewrite_steps.length > 0 && planViewMode !== "original_logical" && (
                  <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg space-y-2">
                    <div className="flex items-center space-x-2 text-indigo-400 font-bold text-xs uppercase tracking-wider">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Rule-Based Query Rewrite Transformations Applied:</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">
                      {optimization.rewrite_steps.map((rw, idx) => (
                        <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 text-xs">
                          <span className="font-bold text-indigo-300 font-sans">{rw.rule_name}</span>
                          <p className="text-slate-300 mt-1">{rw.description}</p>
                          <div className="mt-2 text-[10px] text-slate-400 font-mono space-y-0.5">
                            <div><span className="text-slate-500">Before:</span> {rw.before_summary}</div>
                            <div><span className="text-emerald-400">After:</span> {rw.after_summary}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Plan Tree Visualizer */}
                <PlanTreeVisualizer
                  plan={getBestPlanNode()}
                  title={
                    planViewMode === "optimal_physical"
                      ? `Selected Optimal Physical Plan (${optimization.algorithms[optimization.best_algorithm]?.algorithm_name})`
                      : planViewMode === "rewritten_logical"
                      ? "Rewritten Relational Algebra Logical Plan (Pushdowns Applied)"
                      : "Original Canonical Logical Plan (Unoptimized)"
                  }
                  isOptimal={planViewMode === "optimal_physical"}
                />

                {/* Cost Breakdown */}
                {optimization.algorithms[optimization.best_algorithm] && (
                  <CostBreakdownChart
                    costBreakdown={optimization.algorithms[optimization.best_algorithm].cost_breakdown}
                  />
                )}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Databases (Custom & Predefined) */}
        {activeTab === "databases" && (
          <DatabaseManagerView
            databases={databases}
            activeDbId={activeDbId}
            onSwitchDb={handleSwitchDb}
            onCreateDb={handleCreateDb}
            onDeleteDb={handleDeleteDb}
            onExecuteDDL={handleExecuteDDL}
            onRefresh={handleRefreshDatabases}
          />
        )}

        {/* Tab 3: Algorithm Comparison */}
        {activeTab === "comparison" && (
          <AlgorithmComparison optimization={optimization} />
        )}

        {/* Tab 4: Estimated vs Actual Execution */}
        {activeTab === "execution" && (
          <EstimatedVsActualCard execution={execution} />
        )}

        {/* Tab 5: Database Statistics */}
        {activeTab === "statistics" && (
          <StatisticsInspector
            catalog={catalog}
            activeDbName={databases.find((d) => d.db_id === activeDbId)?.name || activeDbId}
          />
        )}

        {/* Tab 6: Automated Benchmarks */}
        {activeTab === "benchmarks" && (
          <BenchmarkSuite
            benchmarkData={benchmarkData}
            isRunning={isBenchmarking}
            onRunBenchmark={handleRunBenchmark}
          />
        )}

        {/* Tab 7: Plan Cache */}
        {activeTab === "cache" && (
          <CacheMonitor
            cacheStatus={cacheStatus}
            onClearCache={handleClearCache}
            onRefresh={() => api.getCacheStatus().then((c) => setCacheStatus(c))}
          />
        )}
      </main>

      {/* Educational Theory Guide Modal */}
      <EducationGuideModal
        isOpen={isTheoryGuideOpen}
        onClose={() => setIsTheoryGuideOpen(false)}
      />

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-4 text-center text-xs text-slate-500">
        QueryOptX • Intelligent Database Query Optimization Platform • Analysis and Design of Algorithms (AOA)
      </footer>
    </div>
  );
};
export default App;
