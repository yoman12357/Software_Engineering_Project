"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { Check, FileText, Shield, Database, Globe } from "lucide-react";
import { cn } from "../../lib/utils";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Textarea } from "../../components/ui/Textarea";
import { Badge } from "../../components/ui/Badge";
import { Label } from "../../components/ui/Label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../../components/ui/Dialog";
import type { Requirement } from "../../api/types";

interface RequirementEditorProps {
  requirement: Requirement;
  open: boolean;
  onClose: () => void;
  onSave: (updates: Partial<Requirement>) => void;
  isSaving?: boolean;
}

const categoryLabels: Record<string, string> = {
  functional: "Functional",
  security: "Security",
  non_functional: "Non-Functional",
  data: "Data",
  network: "Network",
};

const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  functional: FileText,
  security: Shield,
  non_functional: FileText,
  data: Database,
  network: Globe,
};

export function RequirementEditor({ requirement, open, onClose, onSave, isSaving }: RequirementEditorProps) {
  const [title, setTitle] = useState(requirement.title);
  const [statement, setStatement] = useState(requirement.statement);
  const [rationale, setRationale] = useState(requirement.rationale);
  const [acceptanceCriteria, setAcceptanceCriteria] = useState(requirement.acceptance_criteria);
  const [priority, setPriority] = useState(requirement.priority);
  const [confidence, setConfidence] = useState(requirement.confidence);
  const [userConfirmed, setUserConfirmed] = useState(requirement.user_confirmed);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    setTitle(requirement.title);
    setStatement(requirement.statement);
    setRationale(requirement.rationale);
    setAcceptanceCriteria(requirement.acceptance_criteria);
    setPriority(requirement.priority);
    setConfidence(requirement.confidence);
    setUserConfirmed(requirement.user_confirmed);
    setErrors({});
  }, [requirement, open]);

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!title.trim()) newErrors.title = "Title is required";
    if (!statement.trim()) newErrors.statement = "Statement is required";
    if (!acceptanceCriteria.trim()) newErrors.acceptanceCriteria = "Acceptance criteria is required";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validate()) return;
    onSave({
      title: title.trim(),
      statement: statement.trim(),
      rationale: rationale.trim(),
      acceptance_criteria: acceptanceCriteria.trim(),
      priority,
      confidence,
      user_confirmed: userConfirmed,
    });
    onClose();
  };

  if (!open) return null;

  return createPortal(
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Requirement: {requirement.id}</DialogTitle>
        </DialogHeader>
        <div className="space-y-6 p-4">
          {/* Category badge */}
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
              {categoryIcons[requirement.category] && (() => {
                const Icon = categoryIcons[requirement.category];
                return <Icon className="h-5 w-5" />;
              })()}
            </div>
            <Badge variant="outline" className="text-sm">{categoryLabels[requirement.category]}</Badge>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="req-title">Title</Label>
            <Input
              id="req-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              error={errors.title}
              placeholder="Requirement title"
            />
          </div>

          {/* Statement */}
          <div className="space-y-2">
            <Label htmlFor="req-statement">Statement</Label>
            <Textarea
              id="req-statement"
              value={statement}
              onChange={(e) => setStatement(e.target.value)}
              error={errors.statement}
              placeholder="The system shall..."
              rows={4}
            />
          </div>

          {/* Rationale */}
          <div className="space-y-2">
            <Label htmlFor="req-rationale">Rationale</Label>
            <Textarea
              id="req-rationale"
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              placeholder="Why is this requirement needed?"
              rows={3}
            />
          </div>

          {/* Acceptance Criteria */}
          <div className="space-y-2">
            <Label htmlFor="req-acceptance">Acceptance Criteria</Label>
            <Textarea
              id="req-acceptance"
              value={acceptanceCriteria}
              onChange={(e) => setAcceptanceCriteria(e.target.value)}
              error={errors.acceptanceCriteria}
              placeholder="GIVEN ... WHEN ... THEN ..."
              rows={4}
            />
            <p className="text-xs text-muted-foreground">Use GIVEN-WHEN-THEN format for clarity</p>
          </div>

          {/* Priority & Confidence */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Priority</Label>
              <div className="flex gap-2">
                {["must", "should", "could"].map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPriority(p as "must" | "should" | "could")}
                    className={cn(
                      "flex-1 px-3 py-2 rounded-lg border text-sm font-medium transition-all",
                      priority === p
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-card border-border hover:border-primary/50"
                    )}
                  >
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label>Confidence</Label>
              <div className="flex gap-2">
                {["high", "medium", "low"].map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setConfidence(c as "high" | "medium" | "low")}
                    className={cn(
                      "flex-1 px-3 py-2 rounded-lg border text-sm font-medium transition-all",
                      confidence === c
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-card border-border hover:border-primary/50"
                    )}
                  >
                    {c.charAt(0).toUpperCase() + c.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* User Confirmed */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
            <input
              type="checkbox"
              id="req-confirmed"
              checked={userConfirmed}
              onChange={(e) => setUserConfirmed(e.target.checked)}
              className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
            />
            <label htmlFor="req-confirmed" className="text-sm font-medium cursor-pointer">
              Mark as user confirmed
            </label>
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving} loading={isSaving}>
            Save Changes
            <Check className="h-4 w-4" />
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>,
    document.body
  );
}

export default RequirementEditor;
