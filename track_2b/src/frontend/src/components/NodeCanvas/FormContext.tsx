"use client";

import { createContext, useContext } from "react";
import type { MapType } from "@/game/constants";
import type { UploadedContextSource } from "@/types/backend";

export interface FormState {
  notesText: string;
  setNotesText: (v: string) => void;
  numNpcs: number;
  setNumNpcs: (v: number) => void;
  numRounds: number;
  setNumRounds: (v: number) => void;
  objective: string;
  setObjective: (v: string) => void;
  mapId: MapType;
  setMapId: (v: MapType) => void;
  policySources: UploadedContextSource[];
  trendSources: UploadedContextSource[];
  uploadingPolicySources: boolean;
  uploadingTrends: boolean;
  isSimulating: boolean;
  record: boolean;
  setRecord: (v: boolean) => void;
  handlePolicyNarrativeFiles: (e: React.ChangeEvent<HTMLInputElement>) => void;
  removePolicySource: (sourceId: string) => void;
  handleTrendFiles: (e: React.ChangeEvent<HTMLInputElement>) => void;
  removeTrendSource: (sourceId: string) => void;
  handleSimulate: () => void;
  handleLoadCustomRun: () => void;
  handleLoadFile: (e: React.ChangeEvent<HTMLInputElement>) => void;
  loadingCustomRun: boolean;
}

export const FormContext = createContext<FormState>(null!);
export const useForm = () => useContext(FormContext);
