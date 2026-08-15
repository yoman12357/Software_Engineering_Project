"use client";

import { CheckCircle, AlertCircle, FileText, Shield, Database, Globe } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import type { Requirement } from "../../api/types";

interface AcceptanceCriteriaProps {
  requirements: Requirement[];
  filter?: "all" | "passed" | "failed" | "pending";
}

const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  functional: FileText,
  security: Shield,
  non_functional: FileText,
  data: Database,
  network: Globe,
};

export function AcceptanceCriteria({ requirements }: AcceptanceCriteriaProps) {
  const filteredRequirements = requirements;

  if (filteredRequirements.length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
        <p>No acceptance criteria available.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {filteredRequirements.map((req) => {
        const CategoryIcon = categoryIcons[req.category] || FileText;
        return (
          <div key={req.id} className="p-4 rounded-lg border border-border bg-card">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-lg bg-primary/10 text-primary flex-shrink-0">
                <CategoryIcon className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-mono text-sm text-muted-foreground">{req.id}</span>
                  <Badge variant="outline" size="sm">{req.category}</Badge>
                </div>
                <h4 className="font-medium mb-2">{req.title}</h4>
                <div className="bg-muted/50 rounded p-3 text-sm">
                  <pre className="whitespace-pre-wrap font-mono text-foreground">{req.acceptance_criteria}</pre>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="icon" className="h-7 w-7 text-success hover:bg-success/10">
                  <CheckCircle className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:bg-destructive/10">
                  <AlertCircle className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default AcceptanceCriteria;
