export type AssistantCatalogFilters = {
  species?: "dog" | "cat";
  city?: string;
  good_with_children?: boolean;
};

export function isAssistantCatalogQuery(message: string) {
  return /(adott\w*|cerc\w*.{0,24}(cane|gatto|animal)|looking for (a )?(dog|cat|pet)|find me (a )?(dog|cat|pet)|available animals|animali disponibili|schede disponibili)/i.test(message);
}

export function parseAssistantCatalogFilters(message: string): AssistantCatalogFilters {
  const filters: AssistantCatalogFilters = {};
  const text = message.trim();
  const asksForCats = /\b(gatt\w*|cat|cats|kitten|kittens)\b/i.test(text);
  const asksForDogs = /\b(can\w*|dog|dogs|puppy|puppies)\b/i.test(text);
  if (asksForCats !== asksForDogs) filters.species = asksForCats ? "cat" : "dog";

  const asksForChildren = /\b(bambin\w*|bimbi|children|kids)\b/i.test(text);
  // A household without children is not asking for an animal explicitly
  // assessed as child-compatible. Avoid turning the mention into a filter.
  const deniesChildren = /\b(?:non|not|without|no)\b.{0,28}\b(?:adatt\w*|compatibil\w*|good|suitable|safe)\b.{0,24}\b(?:bambin\w*|bimbi|children|kids)\b|\b(?:senza|without|no)\s+(?:bambin\w*|bimbi|children|kids)\b/i.test(text);
  if (asksForChildren && !deniesChildren) filters.good_with_children = true;

  const cityMatches = [...text.matchAll(/\b(?:vicino\s+a|near|around|in|a)\s+([\p{Lu}][\p{L}'-]*(?:\s+[\p{Lu}][\p{L}'-]*){0,3}?)(?=\s+(?:adatt\w*|compatibil\w*|con\b|per\b|ai?\b|bambin\w*|children\b|kids\b|with\b|without\b|no\b|good\b|suitable\b|for\b|in\b|near\b|around\b|and\b|or\b)|[,;.!?]|$)/giu)];
  const city = cityMatches.map((match) => match[1]?.trim()).find((candidate) => candidate && !/\b(?:dog|dogs|cat|cats|kitten|kittens|pet|pets)\b/i.test(candidate));
  if (city) filters.city = city;
  return filters;
}
