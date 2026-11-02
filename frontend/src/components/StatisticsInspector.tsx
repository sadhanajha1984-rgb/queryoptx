import React, { useState } from "react";
import { Database, Table, Key, Hash, FileText, Layers, Search } from "lucide-react";
import { CatalogSchemaResponse, TableStatDTO } from "../types";

interface StatisticsInspectorProps {
  catalog: CatalogSchemaResponse | null;
  activeDbName?: string;
}

export const StatisticsInspector: React.FC<StatisticsInspectorProps> = ({ catalog, activeDbName }) => {
  const [selectedTable, setSelectedTable] = useState<string>("");
  const [searchFilter, setSearchFilter] = useState<string>("");

  if (!catalog || Object.keys(catalog.tables).length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500 text-xs">
        Loading database statistics and catalog metadata...
      </div>
    );
  }

  const tableNames = Object.keys(catalog.tables);
  const activeTableName = selectedTable || tableNames[0];
  const activeTable: TableStatDTO = catalog.tables[activeTableName];

  const filteredColumns = Object.values(activeTable.columns).filter((c) =>
    c.column_name.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-100 flex items-center space-x-2">
            <Database className="w-4 h-4 text-indigo-400" />
            <span>Database Catalog Statistics & Index Metadata</span>
            {activeDbName && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                {activeDbName}
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real statistics used by the Cardinality Estimator and Cost Model for scan & join pricing.
          </p>
        </div>

        <div className="text-xs font-mono text-slate-400 bg-slate-900 px-3 py-1 rounded-lg border border-slate-800">
          Total Tables: <span className="text-indigo-400 font-bold">{catalog.total_tables}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Left Table Selector */}
        <div className="md:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-3 shadow-lg space-y-1">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block px-2 py-1">
            Relations
          </span>
          <div className="space-y-1 max-h-96 overflow-y-auto">
            {tableNames.map((name) => {
              const tbl = catalog.tables[name];
              const isSelected = activeTableName === name;
              return (
                <button
                  key={name}
                  onClick={() => setSelectedTable(name)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium flex items-center justify-between transition-all ${
                    isSelected
                      ? "bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/30"
                      : "text-slate-300 hover:bg-slate-800"
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate">
                    <Table className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{tbl.table_name}</span>
                  </div>
                  <span className={`text-[10px] font-mono ${isSelected ? "text-indigo-200" : "text-slate-500"}`}>
                    {tbl.row_count.toLocaleString()} rows
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Table Details */}
        <div className="md:col-span-3 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-5">
          {/* Table Header & Size Metrics */}
          <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-4 gap-3">
            <div>
              <div className="flex items-center space-x-2">
                <Table className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-slate-100 font-mono">{activeTable.table_name}</h3>
              </div>
              <span className="text-xs text-slate-400 mt-0.5 block">
                Physical Storage & Cardinality Profile
              </span>
            </div>

            <div className="flex items-center space-x-3 text-xs">
              <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Row Count</span>
                <span className="font-mono font-bold text-emerald-400">
                  {activeTable.row_count.toLocaleString()}
                </span>
              </div>

              <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Disk Pages</span>
                <span className="font-mono font-bold text-indigo-400">
                  {activeTable.page_count.toLocaleString()} ({(activeTable.page_count * 8).toLocaleString()} KB)
                </span>
              </div>

              <div className="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Avg Row Width</span>
                <span className="font-mono font-bold text-purple-400">
                  {activeTable.average_row_width_bytes} bytes
                </span>
              </div>
            </div>
          </div>

          {/* Indexes List */}
          <div>
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5 mb-2">
              <Key className="w-3.5 h-3.5 text-amber-400" />
              <span>Available Indexes ({activeTable.indexes.length})</span>
            </span>
            <div className="flex flex-wrap gap-2">
              {activeTable.indexes.map((idx, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 rounded-md text-xs font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20"
                >
                  {idx}
                </span>
              ))}
            </div>
          </div>

          {/* Column Statistics Table */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                <Layers className="w-3.5 h-3.5 text-indigo-400" />
                <span>Column Distributions & Selectivity Inputs</span>
              </span>

              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Filter column..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="bg-slate-950 text-xs pl-8 pr-3 py-1 rounded-lg border border-slate-800 text-slate-300 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-3 py-2 font-semibold">Column Name</th>
                    <th className="px-3 py-2 font-semibold">Data Type</th>
                    <th className="px-3 py-2 font-semibold">Distinct Values (N_distinct)</th>
                    <th className="px-3 py-2 font-semibold">Null Fraction</th>
                    <th className="px-3 py-2 font-semibold">Indexed</th>
                    <th className="px-3 py-2 font-semibold">Index Name</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {filteredColumns.map((col, i) => (
                    <tr key={i} className="hover:bg-slate-800/30">
                      <td className="px-3 py-2 font-bold text-slate-200">{col.column_name}</td>
                      <td className="px-3 py-2 text-indigo-300">{col.data_type}</td>
                      <td className="px-3 py-2 text-emerald-400 font-bold">{col.distinct_values.toLocaleString()}</td>
                      <td className="px-3 py-2 text-slate-400">{(col.null_fraction * 100).toFixed(1)}%</td>
                      <td className="px-3 py-2">
                        {col.has_index ? (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-sans font-semibold">
                            YES
                          </span>
                        ) : (
                          <span className="text-slate-500 font-sans text-[11px]">No</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-slate-400 text-[11px] truncate max-w-[150px]">
                        {col.index_name || "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
