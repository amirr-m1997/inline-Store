import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SearchBox } from "../components/catalog/search-box";

describe("catalog search", () => {
  it("debounces input and exposes keyboard controls", () => {
    vi.useFakeTimers();
    const onSearch = vi.fn();
    render(<SearchBox onSearch={onSearch} />);
    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "bearing" } });
    expect(onSearch).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(449));
    expect(onSearch).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(1));
    expect(onSearch).toHaveBeenCalledWith("bearing");
    fireEvent.keyDown(input, { key: "Escape" });
    expect(onSearch).toHaveBeenLastCalledWith("");
    vi.useRealTimers();
  });
});
