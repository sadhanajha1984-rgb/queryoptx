import React, { useState } from "react";
import {
  Database, Plus, Trash2, CheckCircle, RefreshCw, Terminal,
  FolderPlus, Layers, Pencil, X, Save, AlertTriangle
} from "lucide-react";
import { DatabaseInfoDTO } from "../types";
import { api } from "../services/api";

interface DatabaseManagerViewProps {
  databases: DatabaseInfoDTO[];
  activeDbId: string;
  onSwitchDb: (dbId: string) => void;
  onCreateDb: (name: string, description: string, ddl: string) => Promise<void>;
  onDeleteDb: (dbId: string) => void;
  onExecuteDDL: (dbId: string, ddl: string) => Promise<void>;
  onRefresh: () => void;
}

const SAMPLE_TEMPLATES = [
  {
    name: "E-Commerce & Logistics",
    desc: "Online shopping store with inventory, buyers, tracking and warehouse supplies",
    sql: `-- E-Commerce Logistics Schema
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    membership TEXT DEFAULT 'standard',
    city TEXT
);

CREATE TABLE warehouses (
    warehouse_id INTEGER PRIMARY KEY,
    location TEXT,
    capacity INTEGER
);

CREATE TABLE items (
    item_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    warehouse_id INTEGER
);

CREATE TABLE user_purchases (
    purchase_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    item_id INTEGER,
    purchase_date TEXT,
    quantity INTEGER
);

CREATE INDEX idx_items_price ON items(price);
CREATE INDEX idx_purchases_user ON user_purchases(user_id);
CREATE INDEX idx_purchases_item ON user_purchases(item_id);

INSERT INTO users VALUES (1, 'Rohan', 'gold', 'Mumbai'), (2, 'Priya', 'platinum', 'Delhi'), (3, 'Amit', 'silver', 'Bengaluru'), (4, 'Sneha', 'gold', 'Pune');
INSERT INTO warehouses VALUES (10, 'Western Hub', 50000), (20, 'Northern Hub', 35000);
INSERT INTO items VALUES (101, 'MacBook Pro M3', 1899.99, 10), (102, 'Mechanical Keyboard', 129.50, 10), (103, 'Noise-Cancel Headset', 249.00, 20), (104, '4K Monitor', 499.00, 20);
INSERT INTO user_purchases VALUES (1001, 1, 101, '2026-03-01', 1), (1002, 1, 102, '2026-03-05', 2), (1003, 2, 103, '2026-03-10', 1), (1004, 3, 104, '2026-03-15', 1), (1005, 4, 101, '2026-03-20', 1);
`
  },
  {
    name: "Hospital & Healthcare",
    desc: "Patients, doctors, departments, and medical appointments",
    sql: `-- Hospital Healthcare Schema
CREATE TABLE hospital_depts (
    dept_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE doctors (
    doctor_id INTEGER PRIMARY KEY,
    doctor_name TEXT NOT NULL,
    dept_id INTEGER,
    fee REAL
);

CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY,
    patient_name TEXT NOT NULL,
    age INTEGER,
    gender TEXT
);

CREATE TABLE appointments (
    apt_id INTEGER PRIMARY KEY,
    doctor_id INTEGER,
    patient_id INTEGER,
    appointment_date TEXT,
    status TEXT
);

CREATE INDEX idx_doctors_dept ON doctors(dept_id);
CREATE INDEX idx_apt_doctor ON appointments(doctor_id);
CREATE INDEX idx_apt_patient ON appointments(patient_id);

INSERT INTO hospital_depts VALUES (1, 'Cardiology'), (2, 'Neurology'), (3, 'Orthopedics');
INSERT INTO doctors VALUES (11, 'Dr. Sen', 1, 1200.0), (12, 'Dr. Kapoor', 2, 1500.0), (13, 'Dr. Mehta', 3, 900.0);
INSERT INTO patients VALUES (201, 'John Doe', 45, 'M'), (202, 'Jane Smith', 32, 'F'), (203, 'Robert Brown', 60, 'M');
INSERT INTO appointments VALUES (1, 11, 201, '2026-04-01', 'Completed'), (2, 12, 202, '2026-04-02', 'Confirmed'), (3, 11, 203, '2026-04-03', 'Completed');
`
  }
];

// ─── Edit Schema Panel (inline per card) ─────────────────────────────────────
interface EditSchemaPanelProps {
  db: DatabaseInfoDTO;
  onClose: () => void;
  onSaved: () => void;
  onExecuteDDL: (dbId: string, ddl: string) => Promise<void>;
  onAdded: () => void;
}

const EditSchemaPanel: React.FC<EditSchemaPanelProps> = ({
  db,
  onClose,
  onSaved,
  onExecuteDDL,
  onAdded
}) => {
  const [editName, setEditName] = useState(db.name);
  const [editDesc, setEditDesc] = useState(db.description);
  const [editDdl, setEditDdl] = useState(db.schema_ddl || "");
  const [additionalDdl, setAdditionalDdl] = useState("");
  const [saving, setSaving] = useState(false);
  const [executingAdditionalDdl, setExecutingAdditionalDdl] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddDdl = async () => {
    if (!additionalDdl.trim()) return;

    setError(null);
    setExecutingAdditionalDdl(true);
    try {
      await onExecuteDDL(db.db_id, additionalDdl);
      setAdditionalDdl("");
      onAdded();
    } catch (err: any) {
      setError(err.message || "SQL changes could not be applied.");
    } finally {
      setExecutingAdditionalDdl(false);
    }
  };

  const handleSave = async () => {
    if (!editDdl.trim()) {
      setError("Schema DDL cannot be empty — include at least one CREATE TABLE statement.");
      return;
    }
    setError(null);
    setSaving(true);
    try {
      await api.resetDatabaseSchema(db.db_id, editDdl, editName, editDesc);
      onSaved();
      onClose();
    } catch (err: any) {
      setError(err.message || "Schema reset failed.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mt-3 bg-slate-950 border border-amber-500/40 rounded-xl p-4 space-y-3">
      <div className="space-y-2 rounded-lg border border-emerald-800/60 bg-emerald-950/20 p-3">
        <div>
          <h4 className="text-xs font-semibold text-emerald-300">Add to existing schema</h4>
          <p className="mt-1 text-[11px] text-slate-400">
            Run new CREATE TABLE, CREATE INDEX, or INSERT statements without dropping existing tables or data.
          </p>
        </div>
        <textarea
          value={additionalDdl}
          onChange={(e) => setAdditionalDdl(e.target.value)}
          rows={5}
          spellCheck={false}
          aria-label={`Additional SQL for ${db.name}`}
          placeholder={"CREATE TABLE projects (project_id INTEGER PRIMARY KEY, name TEXT);\nINSERT INTO projects (name) VALUES ('Compiler Optimization');"}
          className="w-full bg-slate-900 text-emerald-300 font-mono text-xs p-3 rounded-lg border border-slate-700 focus:outline-none focus:border-emerald-500 resize-y leading-relaxed"
        />
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleAddDdl}
            disabled={executingAdditionalDdl || !additionalDdl.trim()}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-700 hover:bg-emerald-600 text-white transition disabled:opacity-50"
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>{executingAdditionalDdl ? "Applying SQL…" : "Add Without Reset"}</span>
          </button>
        </div>
      </div>

      {/* Warning */}
      <div className="flex items-start space-x-2 p-2 rounded-lg bg-amber-950/30 border border-amber-800/60 text-xs text-amber-300">
        <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
        <span>
          <strong>Full Reset:</strong> Saving will drop all existing tables and re-create the database
          from the SQL below. All current data will be lost.
        </span>
      </div>

      {/* Name & Desc */}
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-[10px] font-semibold text-slate-400 mb-1">Database Name</label>
          <input
            type="text"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            className="w-full bg-slate-900 text-slate-100 text-xs px-2 py-1.5 rounded-lg border border-slate-700 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div>
          <label className="block text-[10px] font-semibold text-slate-400 mb-1">Description</label>
          <input
            type="text"
            value={editDesc}
            onChange={(e) => setEditDesc(e.target.value)}
            className="w-full bg-slate-900 text-slate-100 text-xs px-2 py-1.5 rounded-lg border border-slate-700 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* DDL Editor */}
      <div>
        <label className="block text-[10px] font-semibold text-slate-400 mb-1">
          Full Schema SQL (CREATE TABLE, CREATE INDEX, INSERT INTO …)
        </label>
        <textarea
          value={editDdl}
          onChange={(e) => setEditDdl(e.target.value)}
          rows={10}
          spellCheck={false}
          placeholder="-- Paste your complete schema here&#10;CREATE TABLE ...&#10;INSERT INTO ...;"
          className="w-full bg-slate-900 text-emerald-300 font-mono text-xs p-3 rounded-lg border border-slate-700 focus:outline-none focus:border-indigo-500 resize-y leading-relaxed"
        />
      </div>

      {error && (
        <div className="text-xs text-rose-300 bg-rose-950/40 border border-rose-800/60 rounded-lg p-2">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end space-x-2">
        <button
          type="button"
          onClick={onClose}
          className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
        >
          <X className="w-3.5 h-3.5" />
          <span>Cancel</span>
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-md transition disabled:opacity-50"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{saving ? "Saving & Reloading…" : "Save & Reload Schema"}</span>
        </button>
      </div>
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────
export const DatabaseManagerView: React.FC<DatabaseManagerViewProps> = ({
  databases,
  activeDbId,
  onSwitchDb,
  onCreateDb,
  onDeleteDb,
  onExecuteDDL,
  onRefresh
}) => {
  const [newDbName, setNewDbName] = useState("");
  const [newDbDesc, setNewDbDesc] = useState("");
  const [newDbDdl, setNewDbDdl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [ddlError, setDdlError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Execute more DDL in active database
  const [moreDdl, setMoreDdl] = useState("");
  const [isExecutingMore, setIsExecutingMore] = useState(false);

  // Track which db card has the edit panel open (null = none)
  const [editingDbId, setEditingDbId] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDbName.trim()) {
      setDdlError("Database name is required.");
      return;
    }
    setDdlError(null);
    setSuccessMsg(null);
    setIsSubmitting(true);
    try {
      await onCreateDb(newDbName, newDbDesc, newDbDdl);
      setSuccessMsg(`Database "${newDbName}" created and activated!`);
      setNewDbName("");
      setNewDbDesc("");
      setNewDbDdl("");
    } catch (err: any) {
      setDdlError(err.message || "Failed to create database");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExecuteMoreDdl = async () => {
    if (!moreDdl.trim()) return;
    setDdlError(null);
    setSuccessMsg(null);
    setIsExecutingMore(true);
    try {
      await onExecuteDDL(activeDbId, moreDdl);
      setSuccessMsg("Statements executed into active database successfully!");
      setMoreDdl("");
    } catch (err: any) {
      setDdlError(err.message || "Execution error");
    } finally {
      setIsExecutingMore(false);
    }
  };

  const loadTemplate = (tmpl: typeof SAMPLE_TEMPLATES[0]) => {
    setNewDbName(tmpl.name);
    setNewDbDesc(tmpl.desc);
    setNewDbDdl(tmpl.sql);
  };

  return (
    <div className="space-y-6">
      {/* Title & Info Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-slate-100">
              Database Workspace: User-Defined &amp; Predefined Databases
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Build custom relational databases with your own tables, foreign keys, indexes, and tuples.
            QueryOptX will analyze, optimize (DP, Greedy, Branch &amp; Bound), and execute queries directly on your custom schemas!
          </p>
        </div>

        <button
          onClick={onRefresh}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Catalogs</span>
        </button>
      </div>

      {/* Messages */}
      {successMsg && (
        <div className="p-3 bg-emerald-950/40 border border-emerald-800/80 rounded-xl text-xs text-emerald-300 flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
      {ddlError && (
        <div className="p-3 bg-rose-950/40 border border-rose-800/80 rounded-xl text-xs text-rose-300 flex items-center space-x-2">
          <span>{ddlError}</span>
        </div>
      )}

      {/* Database Selection Grid */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center space-x-2">
          <Layers className="w-4 h-4 text-purple-400" />
          <span>Available Databases ({databases.length})</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {databases.map((db) => {
            const isActive = db.db_id === activeDbId;
            const isEditing = editingDbId === db.db_id;

            return (
              <div
                key={db.db_id}
                className={`bg-slate-900 border rounded-xl p-4 shadow-lg flex flex-col justify-between transition-all ${
                  isActive
                    ? "border-emerald-500/60 ring-2 ring-emerald-500/30"
                    : "border-slate-800 hover:border-slate-700"
                }`}
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-sm text-slate-100">{db.name}</span>
                        {isActive && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                            ACTIVE
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] px-2 py-0.5 mt-1 rounded bg-slate-800 text-slate-400 font-mono inline-block">
                        {db.is_custom ? "User-Created DB" : "Predefined Academic Benchmark"}
                      </span>
                    </div>

                    {/* Action buttons: Edit + Delete (custom only) */}
                    {db.is_custom && (
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => setEditingDbId(isEditing ? null : db.db_id)}
                          className={`p-1 rounded transition ${
                            isEditing
                              ? "text-amber-400 bg-amber-950/40"
                              : "text-slate-500 hover:text-amber-400 hover:bg-amber-950/30"
                          }`}
                          title={isEditing ? "Close editor" : "Edit schema"}
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => onDeleteDb(db.db_id)}
                          className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-rose-950/30 transition"
                          title="Delete database"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}
                  </div>

                  <p className="text-xs text-slate-400 mt-2 line-clamp-2">{db.description}</p>

                  <div className="mt-3 pt-2 border-t border-slate-800/80">
                    <span className="text-[10px] text-slate-500 font-bold uppercase">
                      Tables ({db.table_count}):
                    </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {db.tables.map((t, idx) => (
                        <span
                          key={idx}
                          className="px-1.5 py-0.5 rounded text-[10px] bg-slate-950 text-indigo-300 border border-slate-800 font-mono"
                        >
                          {t}
                        </span>
                      ))}
                      {db.tables.length === 0 && (
                        <span className="text-[10px] text-slate-500 italic">No tables created yet</span>
                      )}
                    </div>
                  </div>

                  {/* Edit schema panel — inline below the card header */}
                  {isEditing && (
                    <EditSchemaPanel
                      db={db}
                      onClose={() => setEditingDbId(null)}
                      onExecuteDDL={onExecuteDDL}
                      onAdded={() => {
                        setSuccessMsg(`SQL changes applied to "${db.name}" without resetting its existing tables.`);
                        onRefresh();
                      }}
                      onSaved={() => {
                        setSuccessMsg(`Schema of "${db.name}" reset and reloaded successfully!`);
                        onRefresh();
                      }}
                    />
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                  <span className="text-[11px] text-slate-500 font-mono">ID: {db.db_id}</span>
                  {!isActive ? (
                    <button
                      onClick={() => onSwitchDb(db.db_id)}
                      className="px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition"
                    >
                      Set Active
                    </button>
                  ) : (
                    <span className="text-xs font-bold text-emerald-400 flex items-center space-x-1">
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Ready in Workbench</span>
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Two Columns: 1. Create New Custom DB, 2. Run DDL / Insert in Active DB */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Create Database Form */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <FolderPlus className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-100">
                Create New Custom Database
              </h3>
            </div>

            {/* Quick Templates */}
            <div className="flex items-center space-x-1 text-[11px]">
              <span className="text-slate-500">Quick Template:</span>
              {SAMPLE_TEMPLATES.map((tmpl, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => loadTemplate(tmpl)}
                  className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 text-[10px]"
                >
                  {tmpl.name}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Database Name</label>
              <input
                type="text"
                value={newDbName}
                onChange={(e) => setNewDbName(e.target.value)}
                placeholder="e.g. Banking Systems DB, Hospital Patient Records..."
                className="w-full bg-slate-950 text-slate-100 text-xs px-3 py-2 rounded-lg border border-slate-800 focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Description (Optional)</label>
              <input
                type="text"
                value={newDbDesc}
                onChange={(e) => setNewDbDesc(e.target.value)}
                placeholder="Short description of this schema's domain..."
                className="w-full bg-slate-950 text-slate-100 text-xs px-3 py-2 rounded-lg border border-slate-800 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Schema SQL &amp; Sample Data (CREATE TABLE, CREATE INDEX, INSERT)
              </label>
              <textarea
                value={newDbDdl}
                onChange={(e) => setNewDbDdl(e.target.value)}
                rows={10}
                placeholder={"CREATE TABLE departments (...);\nCREATE TABLE employees (...);\nCREATE INDEX idx_salary ON employees(salary);\nINSERT INTO departments VALUES (...);"}
                className="w-full bg-slate-950 text-emerald-300 font-mono text-xs p-3 rounded-lg border border-slate-800 focus:outline-none focus:border-indigo-500 resize-y leading-relaxed"
                spellCheck={false}
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2 rounded-lg text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-600/25 transition disabled:opacity-50"
            >
              {isSubmitting ? "Creating & Generating Statistics..." : "Create Custom Database & Set Active"}
            </button>
          </form>
        </div>

        {/* Execute DDL / Inserts in Active DB */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <Terminal className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-100">
                Execute Schema Changes in Active DB ({activeDbId})
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-1">
              Add new tables, create B-Tree indexes, or insert more tuples into the <strong>active</strong> database without resetting it.
            </p>
            <p className="text-xs text-slate-500 mb-4">
              ⚡ To replace or edit existing tables — use the <strong className="text-amber-300">✏ pencil icon</strong> on any user-created database card above.
            </p>

            <textarea
              value={moreDdl}
              onChange={(e) => setMoreDdl(e.target.value)}
              rows={10}
              placeholder={"-- Add another table or index to the active database:\nCREATE TABLE projects (project_id INT PRIMARY KEY, name TEXT);\nCREATE INDEX idx_proj_name ON projects(name);\nINSERT INTO projects VALUES (1, 'Compiler Optimization');"}
              className="w-full bg-slate-950 text-amber-300 font-mono text-xs p-3 rounded-lg border border-slate-800 focus:outline-none focus:border-amber-500 resize-y leading-relaxed"
              spellCheck={false}
            />
          </div>

          <div className="mt-4">
            <button
              type="button"
              onClick={handleExecuteMoreDdl}
              disabled={isExecutingMore || !moreDdl.trim()}
              className="w-full py-2 rounded-lg text-xs font-bold bg-amber-600 hover:bg-amber-500 text-white shadow-md shadow-amber-600/20 transition disabled:opacity-50"
            >
              {isExecutingMore ? "Executing..." : "Execute & Refresh Statistics"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
