import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useRouter } from "next/navigation";
import NodeCanvas from "./index";

const { uploadContextSource, startSimulation } = vi.hoisted(() => ({
  uploadContextSource: vi.fn(),
  startSimulation: vi.fn(),
}));

vi.mock("@/services/wsClient", () => ({
  uploadContextSource,
  startSimulation,
}));

describe("NodeCanvas multimodal policy flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it("uploads a primary PDF, attaches a CSV, and starts the simulation", async () => {
    const mockPush = vi.fn();
    (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      push: mockPush,
    });

    uploadContextSource.mockImplementation(async (file: File) => {
      if (file.name.endsWith(".pdf")) {
        return {
          id: "src_policy",
          kind: "pdf",
          filename: file.name,
          label: "Primary Policy PDF",
          status: "ready",
          preview_text:
            "National industrial policy focused on strategic manufacturing.",
          summary:
            "National industrial policy focused on strategic manufacturing.",
          metadata: { page_count_estimate: 4 },
        };
      }

      return {
        id: "src_trend",
        kind: "csv",
        filename: file.name,
        label: file.name,
        status: "ready",
        preview_text: "Inflation rate: 3.1 -> 3.4 (up).",
        summary: "Inflation rate: 3.1 -> 3.4 (up).",
        metadata: {
          row_count: 12,
          columns: ["month", "inflation_rate"],
          indicator_snapshots: [],
        },
      };
    });
    startSimulation.mockResolvedValue("sim-123");

    render(<NodeCanvas />);

    const pdfInput = screen.getByTestId("policy-narrative-input");
    const pdfFile = new File(["pdf"], "policy.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(pdfInput, { target: { files: [pdfFile] } });

    await waitFor(() => {
      expect(screen.getByText("policy.pdf")).toBeInTheDocument();
    });

    const notesTextarea = screen.getByTestId("policy-textarea");
    fireEvent.change(notesTextarea, {
      target: {
        value: "Focus on inflation pass-through and lower-income households.",
      },
    });

    const npcsSlider = screen.getByTestId("npcs-slider");
    fireEvent.change(npcsSlider, { target: { value: "40" } });

    const roundsSlider = screen.getByTestId("rounds-slider");
    fireEvent.change(roundsSlider, { target: { value: "10" } });

    const objectiveTextarea = screen.getByTestId("objective-textarea");
    fireEvent.change(objectiveTextarea, {
      target: { value: "How does this affect local inflation?" },
    });

    const csvInput = screen.getByTestId("trend-csv-input");
    const csvFile = new File(
      ["month,inflation_rate\n2024-01,3.1"],
      "inflation.csv",
      {
        type: "text/csv",
      },
    );
    fireEvent.change(csvInput, { target: { files: [csvFile] } });

    await waitFor(() => {
      expect(screen.getByText("inflation.csv")).toBeInTheDocument();
    });

    const runButton = screen.getByTestId("run-button");
    expect(runButton).not.toBeDisabled();
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(startSimulation).toHaveBeenCalledWith({
        policy_source_ids: ["src_policy"],
        primary_policy_source_id: null,
        notes_text:
          "Focus on inflation pass-through and lower-income households.",
        trend_source_ids: ["src_trend"],
        num_rounds: 10,
        num_npcs: 40,
        objective: "How does this affect local inflation?",
        map_id: "citypack",
      });
    });

    expect(mockPush).toHaveBeenCalledWith("/simulate?id=sim-123");
  });

  it("disables the run button until a narrative file or long notes", () => {
    render(<NodeCanvas />);
    expect(screen.getByTestId("run-button")).toBeDisabled();
  });

  it("enables run with notes only when long enough", async () => {
    startSimulation.mockResolvedValue("sim-notes");
    const mockPush = vi.fn();
    (useRouter as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      push: mockPush,
    });
    const longNotes =
      "x".repeat(45) +
      " Standalone policy description for a text-only simulation run.";
    render(<NodeCanvas />);
    const notesTextarea = screen.getByTestId("policy-textarea");
    fireEvent.change(notesTextarea, {
      target: { value: longNotes },
    });
    expect(screen.getByTestId("run-button")).not.toBeDisabled();
    fireEvent.click(screen.getByTestId("run-button"));
    await waitFor(() => {
      expect(startSimulation).toHaveBeenCalledWith(
        expect.objectContaining({
          policy_source_ids: [],
          primary_policy_source_id: null,
          notes_text: longNotes,
        }),
      );
    });
    expect(mockPush).toHaveBeenCalledWith("/simulate?id=sim-notes");
  });

  it("uploads and displays CSV trend sources", async () => {
    uploadContextSource.mockResolvedValue({
      id: "src_trend",
      kind: "csv",
      filename: "gdp.csv",
      label: "gdp.csv",
      status: "ready",
      preview_text: "GDP: 2.1 -> 2.5 (up).",
      summary: "GDP: 2.1 -> 2.5 (up).",
      metadata: {
        row_count: 8,
        columns: ["quarter", "gdp_growth"],
        indicator_snapshots: [],
      },
    });

    render(<NodeCanvas />);
    const csvInput = screen.getByTestId("trend-csv-input");
    const csvFile = new File(["quarter,gdp_growth\n2024-Q1,2.1"], "gdp.csv", {
      type: "text/csv",
    });
    fireEvent.change(csvInput, { target: { files: [csvFile] } });

    await waitFor(() => {
      expect(screen.getByText("gdp.csv")).toBeInTheDocument();
      expect(screen.getByText("GDP: 2.1 -> 2.5 (up).")).toBeInTheDocument();
    });
  });
});
