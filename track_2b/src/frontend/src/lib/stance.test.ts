import { describe, expect, it } from "vitest";
import { stanceLabel, stancePoll } from "./stance";

describe("stance", () => {
  it("labels with the backend thresholds", () => {
    expect(stanceLabel(0.7)).toBe("for");
    expect(stanceLabel(-0.4)).toBe("against");
    expect(stanceLabel(0.15)).toBe("undecided");
    expect(stanceLabel(-0.15)).toBe("undecided");
  });

  it("polls only residents that carry a stance", () => {
    expect(stancePoll([{}, {}])).toBeNull();
    expect(stancePoll([{ stance: 0.9 }, { stance: -0.5 }, { stance: 0 }, {}])).toEqual({
      for: 1,
      against: 1,
      undecided: 1,
      n: 3,
    });
  });
});
