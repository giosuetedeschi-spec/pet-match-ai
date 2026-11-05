import { describe, expect, test } from "bun:test";
import { isAssistantCatalogQuery, parseAssistantCatalogFilters } from "./assistant-catalog-query";
import { engineLabel } from "../app/it/assistente/AssistantChat";

describe("assistant read-only catalog query", () => {
  test("labels live retailer offers separately from RAG answers", () => {
    expect(engineLabel("commerce_lookup", {
      model: "model", fallback: "fallback", controlled: "controlled", safety: "safety", catalog: "catalog", commerce: "online offers", unknown: "unknown",
    })).toBe("online offers");
  });

  test("labels catalog lookup as a public catalogue result", () => {
    expect(engineLabel("catalog_lookup", {
      model: "model", fallback: "fallback", controlled: "controlled", safety: "safety", catalog: "catalog", commerce: "commerce", unknown: "unknown",
    })).toBe("catalog");
  });

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

  test("does not require child compatibility for a household without children", () => {
    expect(parseAssistantCatalogFilters("Cerco un cane per una famiglia senza bambini")).toEqual({ species: "dog" });
    expect(parseAssistantCatalogFilters("Looking for a dog without kids")).toEqual({ species: "dog" });
  });

  test("stops city capture before compatibility and negation wording", () => {
    expect(parseAssistantCatalogFilters("Cerco un cane a Torino compatibile con bambini")).toEqual({
      species: "dog", city: "Torino", good_with_children: true,
    });
    expect(parseAssistantCatalogFilters("Find me a dog in Turin without kids")).toEqual({
      species: "dog", city: "Turin",
    });
  });

  test("does not force one species when the adopter asks for dogs or cats", () => {
    expect(parseAssistantCatalogFilters("Looking to adopt a dog or cat in Turin")).toEqual({ city: "Turin" });
  });
});
