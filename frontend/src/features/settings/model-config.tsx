export function ModelConfig() {
  return (
    <div className="space-y-4 rounded-xl border border-border bg-card p-4">
      <h3 className="text-sm font-semibold text-foreground">
        Model Configuration
      </h3>
      <div className="space-y-3">
        <ConfigField label="LLM Model" value="gpt-4o" />
        <ConfigField label="Embedding Model" value="text-embedding-3-small" />
        <ConfigField label="Embedding Dimensions" value="1536" />
      </div>

      <div className="mt-4 rounded-lg bg-surface-2 p-3">
        <p className="text-xs text-muted-foreground">
          Model configuration is managed through environment variables.
          Update <code className="font-mono text-primary">OPENAI_MODEL</code>{" "}
          and <code className="font-mono text-primary">EMBEDDING_MODEL</code>{" "}
          in your environment to change these settings.
        </p>
      </div>
    </div>
  );
}

export function RetrievalConfig() {
  return (
    <div className="space-y-4 rounded-xl border border-border bg-card p-4">
      <h3 className="text-sm font-semibold text-foreground">
        Retrieval Settings
      </h3>
      <div className="space-y-3">
        <ConfigField label="Chunk Size" value="512 characters" />
        <ConfigField label="Chunk Overlap" value="50 characters" />
        <ConfigField label="Top-K Retrieval" value="10" />
        <ConfigField label="Rerank Top-K" value="5" />
      </div>
    </div>
  );
}

function ConfigField({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="rounded bg-surface-2 px-2 py-0.5 font-mono text-xs text-foreground">
        {value}
      </span>
    </div>
  );
}
