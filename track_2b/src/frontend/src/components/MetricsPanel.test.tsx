import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { RunMetrics } from "@/types/backend";
import { MetricsPanel } from "./MetricsPanel";

const M: RunMetrics = {
  calls: 44, prompt_tokens: 55_000, completion_tokens: 14_000, cached_tokens: 12_000, cache_hit_rate: 0.218, mean_prompt_tokens: 1250,
  max_prompt_tokens: 2800, context_window: 262_144, mean_context_use: 0.0048, max_context_use: 0.0107, mean_latency_s: 5.4, p95_latency_s: 11.2,
  decode_tokens_per_s: 64, elapsed_s: 61, rate_limited: 0, gateway_retries: 1, downgraded: 0, failed: 0, models: { m: 44 }, model: "swiss-ai/Apertus-v1.5-70B",
  endpoint: "api.inference.cscs.ch", in_flight_limit: 8,
};

describe("MetricsPanel", () => {
  it("renders nothing without calls", () => {
    const { container } = render(<MetricsPanel metrics={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("is collapsed by default and shows tokens, cache and context use when opened", () => {
    render(<MetricsPanel metrics={M} />);
    expect(screen.getByTestId("metrics-panel")).toBeTruthy();
    expect(screen.queryByTestId("metrics-in")).toBeNull();
    fireEvent.click(screen.getByRole("button"));
    expect(screen.getByTestId("metrics-in").textContent).toContain("55,000");
    expect(screen.getByTestId("metrics-out").textContent).toContain("14,000");
    expect(screen.getByTestId("metrics-context").textContent).toContain("1.1 %");
    expect(screen.getByText(/api.inference.cscs.ch/)).toBeTruthy();
  });
});
