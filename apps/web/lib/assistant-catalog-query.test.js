import { describe, expect, test } from "bun:test";
import { isAssistantCatalogQuery, parseAssistantCatalogFilters } from "./assistant-catalog-query";

describe("assistant read-only catalog query", () => {
  test("extracts species, exact city, and child compatibility constraints", () => {
    const message = "Cerco un cane a Torino adatto ai bambini";
    expect(isAssistantCatalogQuery(message)).toBe(true);
    expect(parseAssistantCatalogFilters(message)).toEqual({ species: "dog", city: "Torino", good_with_children: true });
  });

  test("extracts a multiword city from the English query", () => {
    expect(parseAssistantCatalogFilters("Find me a cat in Reggio Emilia with kids")).toEqual({
      species: "cat", city: "Reggio Emilia", good_with_children: true,
    });
  });

  test("does not treat the English article before a species as a city", () => {
    expect(parseAssistantCatalogFilters("Find me a cat in Turin good with kids")).toEqual({
      species: "cat", city: "Turin", good_with_children: true,
    });
  });

  test("does not invent city or child filters when they were not requested", () => {
    expect(parseAssistantCatalogFilters("Cerco un gatto da adottare")).toEqual({ species: "cat" });
  });

  test("does not force one species when the adopter asks for dogs or cats", () => {
    expect(parseAssistantCatalogFilters("Looking to adopt a dog or cat in Turin")).toEqual({ city: "Turin" });
  });
});
